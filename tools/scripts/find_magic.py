#!/usr/bin/env python3
"""Display hexadecimal and ASCII headers for a file or directory tree."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterator


def iter_files(target: Path) -> Iterator[tuple[Path, str]]:
    if target.is_file():
        yield target, target.name
        return
    files = (path for path in target.rglob("*") if path.is_file())
    for path in sorted(files, key=lambda item: item.relative_to(target).as_posix()):
        yield path, path.relative_to(target).as_posix()


def format_header(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset : offset + width]
        hexadecimal = " ".join(f"{byte:02x}" for byte in chunk).ljust(width * 3 - 1)
        ascii_text = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
        lines.append(f"{offset:08x}  {hexadecimal}  |{ascii_text}|")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="File or directory to scan (read-only)")
    parser.add_argument("--bytes", type=int, default=64, dest="byte_count", help="Header bytes to read (default: 64)")
    args = parser.parse_args()
    if args.byte_count < 0:
        parser.error("--bytes must be zero or greater")
    target = args.target.expanduser().resolve()
    if not target.exists():
        parser.error(f"path does not exist: {target}")

    for path, label in iter_files(target):
        with path.open("rb") as stream:
            data = stream.read(args.byte_count)
        print(f"== {label} ({path.stat().st_size} bytes) ==")
        print(format_header(data) if data else "<empty>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

