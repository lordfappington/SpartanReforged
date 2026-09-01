#!/usr/bin/env python3
"""Read-only public-release audit for tracked files and reachable Git history.

The report records paths and finding types, never matching credential values.
It is intentionally conservative and complements, rather than replaces, human
provenance review.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
from collections import defaultdict
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
SUSPICIOUS_EXTENSIONS = {
    ".iso", ".bin", ".pak", ".tm2", ".psq", ".bns", ".anm", ".pss",
    ".elf", ".img", ".raw", ".dump", ".bios", ".mem", ".savestate",
    ".gs", ".rrc", ".cap", ".rdc", ".blend1", ".bms",
}
SUSPICIOUS_PATH_TERMS = (
    "game-extracted", "game-original", "disc", "original", "preservation",
    "level00", "frontend", "extract", "dump", "capture", "reference",
    "sles_533.93", "models.bin", "general.pak", "e_data.pak",
)
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("private-key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("github-token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{30,}\b")),
    ("aws-access-key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("slack-token", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("jwt", re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    (
        "credential-assignment",
        re.compile(
            rb"(?im)^\s*(?:password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)"
            rb"\s*[:=]\s*['\"]?[A-Za-z0-9/+_.-]{16,}"
        ),
    ),
)
PERSONAL_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("windows-user-profile", re.compile(rb"(?i)[A-Z]:\\Users\\([^\\\r\n]+)")),
    ("unix-home", re.compile(b"/" + rb"home/([^/\s]+)")),
    ("email-address", re.compile(rb"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
)


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=input_bytes, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True,
    ).stdout


def tracked_paths() -> list[str]:
    return [item.decode("utf-8", "surrogateescape") for item in git("ls-files", "-z").split(b"\0") if item]


def reachable_objects(revision: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for line in git("rev-list", "--objects", revision).splitlines():
        oid, separator, path = line.partition(b" ")
        if separator:
            result[oid.decode()].append(path.decode("utf-8", "surrogateescape"))
        else:
            result.setdefault(oid.decode(), [])
    return result


def object_metadata(oids: list[str]) -> dict[str, tuple[str, int]]:
    if not oids:
        return {}
    request = ("\n".join(oids) + "\n").encode()
    output = git("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", input_bytes=request)
    result: dict[str, tuple[str, int]] = {}
    for line in output.decode().splitlines():
        oid, kind, size = line.split()
        result[oid] = (kind, int(size))
    return result


def blob_bytes(oid: str) -> bytes:
    return git("cat-file", "blob", oid)


def binary_kind(data: bytes) -> str | None:
    if data.startswith(b"\x7fELF"):
        return "ELF executable"
    if len(data) >= 32774 and data[32769:32774] == b"CD001":
        return "ISO-9660 image"
    if data.startswith(b"PK\x03\x04"):
        return "ZIP archive"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG image"
    if data.startswith(b"GIF8"):
        return "GIF image"
    if b"\x00" in data[:8192]:
        return "binary"
    return None


def findings(data: bytes, patterns: tuple[tuple[str, re.Pattern[bytes]], ...]) -> list[str]:
    return [name for name, pattern in patterns if pattern.search(data)]


def audit(revision: str) -> dict[str, Any]:
    tracked = tracked_paths()
    current: list[dict[str, Any]] = []
    for path_string in tracked:
        path = ROOT / path_string
        data = path.read_bytes()
        kind = binary_kind(data)
        current.append({
            "path": path_string.replace("\\", "/"),
            "size": len(data),
            "extension": path.suffix.lower(),
            "binaryKind": kind,
            "suspiciousExtension": path.suffix.lower() in SUSPICIOUS_EXTENSIONS,
            "suspiciousPathTerms": [term for term in SUSPICIOUS_PATH_TERMS if term in path_string.casefold()],
            "secretTypes": findings(data, SECRET_PATTERNS),
            "personalInfoTypes": findings(data, PERSONAL_PATTERNS) if kind is None else [],
        })

    paths_by_oid = reachable_objects(revision)
    metadata = object_metadata(list(paths_by_oid))
    blobs = {oid: value for oid, value in metadata.items() if value[0] == "blob"}
    historical: list[dict[str, Any]] = []
    for oid, (_kind, size) in blobs.items():
        paths = [path.replace("\\", "/") for path in paths_by_oid.get(oid, [])]
        data = blob_bytes(oid)
        kind = binary_kind(data)
        extensions = sorted({pathlib.PurePosixPath(path).suffix.lower() for path in paths})
        historical.append({
            "oid": oid,
            "paths": paths,
            "size": size,
            "binaryKind": kind,
            "suspiciousExtensions": [ext for ext in extensions if ext in SUSPICIOUS_EXTENSIONS],
            "suspiciousPathTerms": sorted({
                term for path in paths for term in SUSPICIOUS_PATH_TERMS if term in path.casefold()
            }),
            "secretTypes": findings(data, SECRET_PATTERNS),
            "personalInfoTypes": findings(data, PERSONAL_PATTERNS) if kind is None else [],
        })

    historical_paths = sorted({path for item in historical for path in item["paths"]})
    current_paths = {item["path"] for item in current}
    deleted_paths = [path for path in historical_paths if path not in current_paths]
    return {
        "revision": revision,
        "trackedFileCount": len(current),
        "reachableObjectCount": len(paths_by_oid),
        "reachableBlobCount": len(historical),
        "current": {
            "suspicious": [item for item in current if item["suspiciousExtension"] or item["suspiciousPathTerms"] or item["binaryKind"]],
            "secretFindings": [item for item in current if item["secretTypes"]],
            "personalInfoFindings": [item for item in current if item["personalInfoTypes"]],
            "largest": sorted(current, key=lambda item: item["size"], reverse=True)[:20],
        },
        "history": {
            "suspicious": [item for item in historical if item["suspiciousExtensions"] or item["suspiciousPathTerms"] or item["binaryKind"]],
            "secretFindings": [item for item in historical if item["secretTypes"]],
            "personalInfoFindings": [item for item in historical if item["personalInfoTypes"]],
            "largestBlobs": sorted(historical, key=lambda item: item["size"], reverse=True)[:20],
            "deletedPaths": deleted_paths,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    report = audit(args.revision)
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
