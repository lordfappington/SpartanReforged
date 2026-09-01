#!/usr/bin/env python3
"""Build the transparent runtime copy of the locked Reforged pointer artwork.

The canonical JPEG is never rewritten.  Its connected pointer body retains the
source RGB samples verbatim; only the black-composited edge/glow pixels are
converted to straight-alpha RGBA for use over the menu background.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections import deque

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[3]
ASSET_ROOT = ROOT / "assets/reforged/frontend/main-menu/pointer/approved"
SOURCE = ASSET_ROOT / "source/spartan-selection-pointer-approved.jpg"
RUNTIME = ASSET_ROOT / "runtime/spartan-selection-pointer-approved.png"
METADATA = ASSET_ROOT / "metadata/spartan-selection-pointer-approved.json"
EXPECTED_SOURCE_SHA256 = "8938fde3105960d2db38b86c8914ea90e79474ad950e556b818d6059d4752833"
CORE_THRESHOLD = 8


def sha256_path(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _largest_component(mask: bytearray, width: int, height: int) -> bytearray:
    visited = bytearray(width * height)
    largest: list[int] = []
    for start, enabled in enumerate(mask):
        if not enabled or visited[start]:
            continue
        visited[start] = 1
        queue = deque([start])
        component: list[int] = []
        while queue:
            index = queue.popleft()
            component.append(index)
            x, y = index % width, index // width
            for neighbour in (index - 1, index + 1, index - width, index + width):
                if neighbour < 0 or neighbour >= width * height or visited[neighbour]:
                    continue
                nx, ny = neighbour % width, neighbour // width
                if abs(nx - x) + abs(ny - y) != 1 or not mask[neighbour]:
                    continue
                visited[neighbour] = 1
                queue.append(neighbour)
        if len(component) > len(largest):
            largest = component
    result = bytearray(width * height)
    for index in largest:
        result[index] = 255
    return result


def _fill_holes(core: bytearray, width: int, height: int) -> bytearray:
    outside = bytearray(width * height)
    queue: deque[int] = deque()
    for x in range(width):
        for index in (x, (height - 1) * width + x):
            if not core[index] and not outside[index]:
                outside[index] = 1; queue.append(index)
    for y in range(height):
        for index in (y * width, y * width + width - 1):
            if not core[index] and not outside[index]:
                outside[index] = 1; queue.append(index)
    while queue:
        index = queue.popleft()
        x, y = index % width, index // width
        for neighbour in (index - 1, index + 1, index - width, index + width):
            if neighbour < 0 or neighbour >= width * height or outside[neighbour] or core[neighbour]:
                continue
            nx, ny = neighbour % width, neighbour // width
            if abs(nx - x) + abs(ny - y) != 1:
                continue
            outside[neighbour] = 1; queue.append(neighbour)
    return bytearray(255 if core[i] or not outside[i] else 0 for i in range(width * height))


def build_runtime() -> dict[str, object]:
    if sha256_path(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise ValueError("locked approved pointer source hash mismatch")
    with Image.open(SOURCE) as opened:
        opened.load()
        if opened.format != "JPEG" or opened.mode != "RGB" or opened.size != (1280, 427):
            raise ValueError(f"unexpected approved pointer source: {opened.format}/{opened.mode}/{opened.size}")
        source = opened.copy()

    width, height = source.size
    pixels = list(source.getdata())
    signal = bytearray(max(pixel) for pixel in pixels)
    candidate = bytearray(value > CORE_THRESHOLD for value in signal)
    core = _fill_holes(_largest_component(candidate, width, height), width, height)
    rgba: list[tuple[int, int, int, int]] = []
    for index, rgb in enumerate(pixels):
        if core[index]:
            rgba.append((*rgb, 255))
        else:
            rgba.append((0, 0, 0, 0))

    runtime_full = Image.new("RGBA", source.size)
    runtime_full.putdata(rgba)
    visible_bounds = runtime_full.getchannel("A").getbbox()
    if visible_bounds is None:
        raise RuntimeError("approved pointer matte produced no visible pixels")
    runtime = runtime_full.crop(visible_bounds)
    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    runtime.save(RUNTIME, "PNG", optimize=False, compress_level=9)

    metadata: dict[str, object] = {
        "schemaVersion": 1,
        "status": "HUMAN_APPROVED_LOCKED_PRODUCTION_ART",
        "source": {
            "path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "format": "JPEG",
            "dimensions": list(source.size),
            "mode": "RGB",
            "bytes": SOURCE.stat().st_size,
            "sha256": sha256_path(SOURCE),
            "preservedByteIdentically": True,
        },
        "runtime": {
            "path": str(RUNTIME.relative_to(ROOT)).replace("\\", "/"),
            "format": "PNG",
            "dimensions": list(runtime.size),
            "mode": "RGBA",
            "sha256": sha256_path(RUNTIME),
            "sourceVisibleBounds": list(visible_bounds),
            "alphaBounds": list(runtime.getchannel("A").getbbox() or ()),
        },
        "matte": {
            "required": True,
            "reason": "approved JPEG contains a black field and no alpha channel",
            "coreThreshold": CORE_THRESHOLD,
            "method": "largest connected body plus hole fill; retained body pixels preserve source RGB exactly; high-resolution alpha edge is filtered only during menu scaling",
            "visualRedesign": False,
        },
    }
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


if __name__ == "__main__":
    print(json.dumps(build_runtime(), indent=2))
