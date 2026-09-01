#!/usr/bin/env python3
"""Archive the human-approved main-menu background without visual changes."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[3]
APPROVED_ROOT = ROOT / "assets/reforged/frontend/main-menu/background/approved"
SOURCE_PATH = APPROVED_ROOT / "source/spartan-background-approved.jpg"
RUNTIME_PATH = APPROVED_ROOT / "runtime/spartan-background-approved.jpg"
METADATA_PATH = APPROVED_ROOT / "metadata/spartan-background-approved.json"
EXPECTED_SHA256 = "76ceaa4eb1a68f85824205e70df86b068196d6b378b8eee802cc531a14c7fad5"
EXPECTED_SIZE = (1280, 720)


def sha256_path(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_source(path: pathlib.Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"approved background is missing: {path}")
    digest = sha256_path(path)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"approved background hash mismatch: {digest}")
    with Image.open(path) as image:
        image.load()
        if image.format != "JPEG" or image.mode != "RGB" or image.size != EXPECTED_SIZE:
            raise ValueError(f"unexpected approved background: {image.format}/{image.mode}/{image.size}")
    return {
        "suppliedFilename": path.name,
        "sha256": digest,
        "fileSize": path.stat().st_size,
        "format": "JPEG",
        "mode": "RGB",
        "dimensions": list(EXPECTED_SIZE),
    }


def copy_exact(source: pathlib.Path, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        raise RuntimeError(f"byte-exact copy validation failed: {target}")


def integrate(source: pathlib.Path) -> dict[str, object]:
    source_info = inspect_source(source)
    copy_exact(source, SOURCE_PATH)
    copy_exact(source, RUNTIME_PATH)
    metadata: dict[str, object] = {
        "schemaVersion": 1,
        "approvalStatus": "HUMAN APPROVED",
        "source": {**source_info, "path": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/")},
        "runtime": {
            "path": str(RUNTIME_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_path(RUNTIME_PATH),
            "sourceAndRuntimeByteIdentical": True,
            "viewportPolicy": "scale complete 16:9 plate into central composition without crop",
        },
        "processing": {
            "visualDesignAltered": False,
            "colourGradePerformed": False,
            "sharpeningPerformed": False,
            "cropPerformed": False,
            "sourceFileReencoded": False,
        },
        "ornamentalBands": {
            "bakedIntoApprovedPlate": True,
            "placeholderOverlayEnabled": False,
        },
        "provenance": "human-supplied and human-approved SpartanReforged project artwork",
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, required=True)
    args = parser.parse_args()
    print(json.dumps(integrate(args.source.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
