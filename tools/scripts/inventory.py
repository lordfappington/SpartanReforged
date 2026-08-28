#!/usr/bin/env python3
"""Create deterministic CSV and JSON inventories of a directory tree."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterator


def iter_files(root: Path) -> Iterator[Path]:
    files = (path for path in root.rglob("*") if path.is_file())
    yield from sorted(files, key=lambda path: path.relative_to(root).as_posix())


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def make_rows(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in iter_files(root):
        relative = path.relative_to(root).as_posix()
        rows.append({
            "relative_path": relative,
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory to inventory (read-only)")
    parser.add_argument("--csv", type=Path, help="CSV output path (default: inventory.csv)")
    parser.add_argument("--json", type=Path, help="JSON output path (default: inventory.json)")
    args = parser.parse_args()

    root = args.directory.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    csv_path = (args.csv or Path("inventory.csv")).resolve()
    json_path = (args.json or Path("inventory.json")).resolve()
    rows = make_rows(root)

    fields = ["relative_path", "filename", "extension", "size_bytes", "sha256"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with json_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(rows, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Inventoried {len(rows)} files; wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

