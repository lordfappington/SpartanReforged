#!/usr/bin/env python3
"""Extract locked PlayStation shield prompts from the approved 2x2 sheet."""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections import deque

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[3]
ASSET_ROOT = ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved"
SOURCE = ASSET_ROOT / "source/spartan-playstation-shields-approved.jpg"
RUNTIME_ROOT = ASSET_ROOT / "runtime"
METADATA = ASSET_ROOT / "metadata/spartan-playstation-shields-approved.json"
EXPECTED_SOURCE_SHA256 = "0ad9b4e09f91602617516cd48e992d0e421bb1a39ff86ca680441f384fbb8af6"
CORE_THRESHOLD = 8
CANVAS_SIZE = 448
VISIBLE_DIAMETER = 416
QUADRANTS = {
    "triangle": (0, 0, 640, 416),
    "circle": (640, 0, 1280, 416),
    "cross": (0, 416, 640, 853),
    "square": (640, 416, 1280, 853),
}


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
                if neighbour < 0 or neighbour >= width * height or visited[neighbour] or not mask[neighbour]:
                    continue
                nx, ny = neighbour % width, neighbour // width
                if abs(nx - x) + abs(ny - y) != 1:
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


def _extract(quadrant: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    width, height = quadrant.size
    pixels = list(quadrant.getdata())
    mask = bytearray(max(pixel) > CORE_THRESHOLD for pixel in pixels)
    alpha = _fill_holes(_largest_component(mask, width, height), width, height)
    rgba = Image.new("RGBA", quadrant.size)
    rgba.putdata([(*rgb, alpha[index]) if alpha[index] else (0, 0, 0, 0) for index, rgb in enumerate(pixels)])
    bounds = rgba.getchannel("A").getbbox()
    if bounds is None:
        raise RuntimeError("shield extraction produced no visible pixels")
    return rgba.crop(bounds), bounds


def _normalize(shield: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    scale = VISIBLE_DIAMETER / max(shield.size)
    size = (max(1, round(shield.width * scale)), max(1, round(shield.height * scale)))
    resized = shield.resize(size, Image.Resampling.LANCZOS)
    bounds = resized.getchannel("A").getbbox()
    if bounds is None:
        raise RuntimeError("normalized shield has no visible pixels")
    visible = resized.crop(bounds)
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE))
    x = round((CANVAS_SIZE - visible.width) / 2)
    y = round((CANVAS_SIZE - visible.height) / 2)
    canvas.paste(visible, (x, y), visible)
    return canvas, (x, y, x + visible.width, y + visible.height)


def build_runtime() -> dict[str, object]:
    if sha256_path(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise ValueError("locked approved prompt sheet hash mismatch")
    with Image.open(SOURCE) as opened:
        opened.load()
        if opened.format != "JPEG" or opened.mode != "RGB" or opened.size != (1280, 853):
            raise ValueError(f"unexpected prompt sheet: {opened.format}/{opened.mode}/{opened.size}")
        sheet = opened.copy()

    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    assets: dict[str, object] = {}
    for semantic, quadrant_bounds in QUADRANTS.items():
        extracted, local_bounds = _extract(sheet.crop(quadrant_bounds))
        runtime, visible_bounds = _normalize(extracted)
        output = RUNTIME_ROOT / f"spartan-prompt-{semantic}-approved.png"
        runtime.save(output, "PNG", optimize=False, compress_level=9)
        source_bounds = (
            quadrant_bounds[0] + local_bounds[0], quadrant_bounds[1] + local_bounds[1],
            quadrant_bounds[0] + local_bounds[2], quadrant_bounds[1] + local_bounds[3],
        )
        assets[semantic] = {
            "path": str(output.relative_to(ROOT)).replace("\\", "/"),
            "format": "PNG", "mode": "RGBA",
            "dimensions": [CANVAS_SIZE, CANVAS_SIZE],
            "sourceBounds": list(source_bounds),
            "visibleBounds": list(visible_bounds),
            "visibleSize": [visible_bounds[2] - visible_bounds[0], visible_bounds[3] - visible_bounds[1]],
            "sha256": sha256_path(output),
        }

    metadata: dict[str, object] = {
        "schemaVersion": 1,
        "status": "HUMAN_APPROVED_LOCKED_PRODUCTION_ART",
        "source": {
            "path": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
            "format": "JPEG", "dimensions": list(sheet.size), "mode": "RGB",
            "bytes": SOURCE.stat().st_size, "sha256": sha256_path(SOURCE),
            "preservedByteIdentically": True,
        },
        "normalization": {
            "canvasDimensions": [CANVAS_SIZE, CANVAS_SIZE],
            "targetVisibleDiameter": VISIBLE_DIAMETER,
            "uniformScalingOnly": True,
            "opticalCentre": [CANVAS_SIZE // 2, CANVAS_SIZE // 2],
            "backgroundRemoval": "largest connected shield body above black-field threshold; enclosed dark shield pixels filled; source RGB retained before uniform normalization",
            "visualRedesign": False,
        },
        "assets": assets,
    }
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


if __name__ == "__main__":
    print(json.dumps(build_runtime(), indent=2))
