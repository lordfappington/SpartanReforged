#!/usr/bin/env python3
"""Compare two directory trees by relative path and SHA-256 digest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def index_tree(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*") if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory_a", type=Path)
    parser.add_argument("directory_b", type=Path)
    args = parser.parse_args()
    root_a = args.directory_a.expanduser().resolve()
    root_b = args.directory_b.expanduser().resolve()
    if not root_a.is_dir() or not root_b.is_dir():
        parser.error("both arguments must be directories")

    files_a, files_b = index_tree(root_a), index_tree(root_b)
    names_a, names_b = set(files_a), set(files_b)
    identical: list[str] = []
    changed: list[str] = []
    for name in sorted(names_a & names_b):
        (identical if sha256_file(files_a[name]) == sha256_file(files_b[name]) else changed).append(name)

    sections = (
        ("IDENTICAL", identical),
        ("CHANGED", changed),
        ("ONLY IN A", sorted(names_a - names_b)),
        ("ONLY IN B", sorted(names_b - names_a)),
    )
    for title, entries in sections:
        print(f"{title} ({len(entries)})")
        for entry in entries:
            print(f"  {entry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

