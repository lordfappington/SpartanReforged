#!/usr/bin/env python3
"""Strict native-resolution decoder for geometry-required LEVEL00 TIM2.

Supported intentionally narrowly: one-picture TIM2 v4 containers containing
PSMT4 or PSMT8 indexed pixels with RGB5A1 or RGBA8888 CLUTs. Unsupported
variants fail explicitly. Source files are read-only and output is permitted
only beneath a directory named ``temp``.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import pathlib
import struct
import sys
import zlib
from dataclasses import dataclass


class Tim2FormatError(ValueError):
    """Raised when a TIM2 file is malformed or outside the supported subset."""


@dataclass(frozen=True)
class Tim2Image:
    width: int
    height: int
    mip_count: int
    mip_sizes: tuple[int, ...]
    palette: tuple[tuple[int, int, int, int], ...]
    indices: bytes
    rgba: bytes
    image_type: int
    clut_type: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise Tim2FormatError(f"u16 read exceeds file at 0x{offset:X}")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise Tim2FormatError(f"u32 read exceeds file at 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


def _align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _expand_rgb5(value: int) -> int:
    # This matches verified Noesis references: 5-bit channels
    # occupy the high five bits of the resulting byte (0..248).
    return value << 3


def _mip_size(width: int, height: int, image_type: int) -> int:
    pixels = width * height
    if image_type == 4:
        if width % 2:
            raise Tim2FormatError(f"PSMT4 mip width must be even, got {width}")
        return pixels // 2
    if image_type == 5:
        return pixels
    raise Tim2FormatError(f"unsupported image type {image_type}")


def _decode_rgb5a1(value: int) -> tuple[int, int, int, int]:
    return (
        _expand_rgb5(value & 0x1F),
        _expand_rgb5((value >> 5) & 0x1F),
        _expand_rgb5((value >> 10) & 0x1F),
        255 if value & 0x8000 else 0,
    )


def _decode_rgba8888(value: bytes) -> tuple[int, int, int, int]:
    if len(value) != 4:
        raise Tim2FormatError("truncated RGBA8888 palette entry")
    r, g, b, alpha_ps2 = value
    # GS alpha uses 0x80 as 1.0. Noesis independently confirms doubling with
    # saturation for every geometry-used 32-bit CLUT in LEVEL00.
    return r, g, b, min(255, alpha_ps2 * 2)


def _csm1_palette_index(index: int) -> int:
    """Map a logical PSMT8 index to the stored CSM1 palette position."""
    return (index & ~0x18) | ((index & 0x08) << 1) | ((index & 0x10) >> 1)


def decode_tim2(data: bytes) -> Tim2Image:
    if len(data) < 0x40:
        raise Tim2FormatError("file is too small for TIM2 and picture headers")
    if data[:4] != b"TIM2":
        raise Tim2FormatError("missing TIM2 magic")
    version, container_format = data[4], data[5]
    picture_count = _u16(data, 6)
    if version != 4 or container_format != 0 or picture_count != 1:
        raise Tim2FormatError(
            f"unsupported container: version={version}, format={container_format}, pictures={picture_count}"
        )

    picture = 0x10
    total_size = _u32(data, picture)
    clut_size = _u32(data, picture + 4)
    image_size = _u32(data, picture + 8)
    header_size = _u16(data, picture + 12)
    clut_colors = _u16(data, picture + 14)
    picture_format = data[picture + 16]
    mip_count = data[picture + 17]
    clut_type = data[picture + 18]
    image_type = data[picture + 19]
    width = _u16(data, picture + 20)
    height = _u16(data, picture + 22)

    if picture_format != 0:
        raise Tim2FormatError(f"unsupported picture format {picture_format}")
    if image_type not in (4, 5):
        raise Tim2FormatError(f"unsupported image type {image_type}; only IDTEX4/PSMT4 and IDTEX8/PSMT8 are implemented")
    if clut_type not in (1, 3):
        raise Tim2FormatError(f"unsupported CLUT type {clut_type}; only RGB5A1 and RGBA8888 are implemented")
    expected_colors = 16 if image_type == 4 else 256
    bytes_per_color = 2 if clut_type == 1 else 4
    if clut_colors != expected_colors or clut_size != expected_colors * bytes_per_color:
        raise Tim2FormatError(
            f"invalid CLUT for image type {image_type}: type={clut_type}, "
            f"colors={clut_colors}, bytes={clut_size}"
        )
    if not width or not height or (image_type == 4 and width % 2):
        raise Tim2FormatError(f"invalid indexed dimensions {width}x{height} for image type {image_type}")
    if not mip_count or mip_count > 7:
        raise Tim2FormatError(f"invalid/unsupported mip count {mip_count}")
    if header_size < 0x30 + max(0, mip_count - 1) * 4:
        raise Tim2FormatError("picture header is too short for its mip table")
    picture_end = picture + total_size
    if picture_end != len(data):
        raise Tim2FormatError(
            f"picture size/file size mismatch: picture ends 0x{picture_end:X}, file is 0x{len(data):X}"
        )

    # For multiple mip levels, TIM2 stores an explicit size for every level in
    # the extended header.  A single level's size follows from image_size.
    if mip_count == 1:
        mip_sizes = (image_size,)
    else:
        mip_table = picture + 0x40
        if mip_table + mip_count * 4 > picture + header_size:
            raise Tim2FormatError("mip-size table exceeds picture header")
        mip_sizes = tuple(_u32(data, mip_table + index * 4) for index in range(mip_count))
    if any(size <= 0 for size in mip_sizes) or sum(mip_sizes) != image_size:
        raise Tim2FormatError("mip sizes do not form the declared image payload")
    expected_mip_sizes = tuple(
        _mip_size(max(1, width >> level), max(1, height >> level), image_type)
        for level in range(mip_count)
    )
    if mip_sizes != expected_mip_sizes:
        raise Tim2FormatError(f"mip sizes mismatch: declared {mip_sizes}, expected {expected_mip_sizes}")

    image_start = _align(picture + header_size, 16)
    image_end = image_start + image_size
    clut_start = _align(image_end, 16)
    clut_end = clut_start + clut_size
    if image_start < picture + header_size or image_end > picture_end or clut_end > picture_end:
        raise Tim2FormatError("TIM2 image or CLUT payload exceeds picture bounds")
    if any(data[image_end:clut_start]) or any(data[clut_end:picture_end]):
        raise Tim2FormatError("non-zero bytes found in TIM2 alignment padding")

    stored_palette: list[tuple[int, int, int, int]] = []
    for index in range(clut_colors):
        if clut_type == 1:
            stored_palette.append(_decode_rgb5a1(_u16(data, clut_start + index * 2)))
        else:
            entry_start = clut_start + index * 4
            stored_palette.append(_decode_rgba8888(data[entry_start:entry_start + 4]))
    # Spartan's PSMT8 TIM2 palettes are stored in GS CSM1 order. PSMT4 has
    # only 16 colors and requires no 8/16 block exchange.
    palette = (
        tuple(stored_palette[_csm1_palette_index(index)] for index in range(256))
        if image_type == 5 else tuple(stored_palette)
    )

    packed = data[image_start:image_start + mip_sizes[0]]
    if image_type == 4:
        indices = bytearray(width * height)
        for source_index, value in enumerate(packed):
            indices[source_index * 2] = value & 0x0F
            indices[source_index * 2 + 1] = value >> 4
    else:
        indices = bytearray(packed)
    if len(indices) != width * height or (indices and max(indices) >= len(palette)):
        raise Tim2FormatError("decoded indexed image stream is invalid")
    rgba = bytes(channel for index in indices for channel in palette[index])
    if len(rgba) != width * height * 4:
        raise Tim2FormatError("decoded RGBA stream has the wrong size")
    return Tim2Image(
        width, height, mip_count, mip_sizes, palette, bytes(indices), rgba,
        image_type, clut_type,
    )


def encode_png(image: Tim2Image) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)

    header = struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)
    stride = image.width * 4
    rows = b"".join(b"\x00" + image.rgba[y * stride:(y + 1) * stride] for y in range(image.height))
    return signature + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")


def decode_file(source: pathlib.Path) -> tuple[Tim2Image, bytes, dict[str, object]]:
    source_data = source.read_bytes()
    image = decode_tim2(source_data)
    png = encode_png(image)
    alpha_values = image.rgba[3::4]
    report: dict[str, object] = {
        "source": str(source.resolve()),
        "sourceSha256": sha256(source_data),
        "sourceBytes": len(source_data),
        "width": image.width,
        "height": image.height,
        "pixelCount": image.width * image.height,
        "imageType": image.image_type,
        "pixelFormat": (
            "PSMT4 / IDTEX4 (4-bit indexed)" if image.image_type == 4
            else "PSMT8 / IDTEX8 (8-bit indexed)"
        ),
        "paletteFormat": (
            f"RGB5A1 / {len(image.palette)}-entry CLUT" if image.clut_type == 1
            else f"RGBA8888 (PS2 alpha doubled) / {len(image.palette)}-entry CLUT"
        ),
        "paletteCount": len(image.palette),
        "palette": [list(color) for color in image.palette],
        "mipCount": image.mip_count,
        "mipSizes": list(image.mip_sizes),
        "indexRange": [min(image.indices), max(image.indices)],
        "alphaRange": [min(alpha_values), max(alpha_values)],
        "rgbaSha256": sha256(image.rgba),
        "pngSha256": sha256(png),
        "pngBytes": len(png),
        "imageLayout": (
            "row-major packed indices, low nibble first; no image unswizzle"
            if image.image_type == 4 else
            "row-major one-byte indices; no image unswizzle"
        ),
        "clutPermutation": (
            "none" if image.image_type == 4 else
            "PSMT8 CSM1: exchange palette index bit 3 with bit 4"
        ),
    }
    return image, png, report


def _allowed_output(path: pathlib.Path) -> bool:
    return "temp" in {part.casefold() for part in path.resolve().parts}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()
    outputs = [args.output] + ([args.report] if args.report else [])
    if args.output.suffix.casefold() != ".png" or any(not _allowed_output(path) for path in outputs):
        parser.error("PNG and report outputs must be beneath a temp directory")
    _, png, report = decode_file(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(png)
    report["output"] = str(args.output.resolve())
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Tim2FormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
