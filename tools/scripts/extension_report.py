#!/usr/bin/env python3
"""Summarize file extensions in a directory tree as CSV and JSON."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Directory to report on (read-only)")
    parser.add_argument("--csv", type=Path, help="CSV output path (default: extensions.csv)")
    parser.add_argument("--json", type=Path, help="JSON output path (default: extensions.json)")
    parser.add_argument("--examples", type=int, default=5, help="Maximum example paths per extension (default: 5)")
    args = parser.parse_args()
    if args.examples < 0:
        parser.error("--examples must be zero or greater")
    root = args.directory.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    groups: dict[str, list[tuple[str, int]]] = defaultdict(list)
    files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    for path in files:
        extension = path.suffix.lower() or "<none>"
        groups[extension].append((path.relative_to(root).as_posix(), path.stat().st_size))

    rows: list[dict[str, object]] = []
    for extension in sorted(groups):
        entries = groups[extension]
        smallest = min(entries, key=lambda item: (item[1], item[0]))
        largest = max(entries, key=lambda item: (item[1], item[0]))
        rows.append({
            "extension": extension,
            "file_count": len(entries),
            "total_bytes": sum(size for _, size in entries),
            "smallest_file": smallest[0],
            "smallest_bytes": smallest[1],
            "largest_file": largest[0],
            "largest_bytes": largest[1],
            "example_paths": [name for name, _ in entries[: args.examples]],
        })

    csv_path = (args.csv or Path("extensions.csv")).resolve()
    json_path = (args.json or Path("extensions.json")).resolve()
    fields = ["extension", "file_count", "total_bytes", "smallest_file", "smallest_bytes", "largest_file", "largest_bytes", "example_paths"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            csv_row["example_paths"] = " | ".join(row["example_paths"])
            writer.writerow(csv_row)
    with json_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(rows, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Reported {len(files)} files across {len(rows)} extensions; wrote {csv_path} and {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

