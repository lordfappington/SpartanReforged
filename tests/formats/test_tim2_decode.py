"""Synthetic, non-copyrighted tests for the narrow TIM2 decoder."""

from __future__ import annotations

import hashlib
import pathlib
import struct
import sys
import unittest

CONVERSION = pathlib.Path(__file__).resolve().parents[2] / "tools" / "conversion"
sys.path.insert(0, str(CONVERSION))

from tim2_decode import Tim2FormatError, decode_tim2, encode_png  # noqa: E402


def _align(value: int, boundary: int = 16) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def synthetic_tim2(
    *, width: int = 2, height: int = 2, image_type: int = 4,
    clut_type: int = 1, indices: bytes = bytes((0, 1, 2, 3)),
    palette: list[int | tuple[int, int, int, int]] | None = None,
    mip_sizes: tuple[int, ...] | None = None,
) -> bytes:
    """Build a structurally valid one-picture TIM2 using caller-supplied data."""
    colors = 16 if image_type == 4 else 256
    color_bytes = 2 if clut_type == 1 else 4
    if palette is None:
        palette = [0x8000] * colors if clut_type == 1 else [(0, 0, 0, 0)] * colors
    if mip_sizes is None:
        base_size = width * height // 2 if image_type == 4 else width * height
        mip_sizes = (base_size,)
    mip_count = len(mip_sizes)
    header_size = 48 if mip_count == 1 else _align(0x40 + 4 * mip_count)
    image_size = sum(mip_sizes)
    image_start = _align(header_size)
    clut_start = _align(image_start + image_size)
    clut_size = colors * color_bytes
    total_size = clut_start + clut_size
    picture = bytearray(total_size)
    struct.pack_into(
        "<IIIHHBBBBHH", picture, 0, total_size, clut_size, image_size,
        header_size, colors, 0, mip_count, clut_type, image_type, width, height,
    )
    if mip_count > 1:
        for level, size in enumerate(mip_sizes):
            struct.pack_into("<I", picture, 0x40 + level * 4, size)
    if image_type == 4:
        packed = bytearray(
            indices[offset] | indices[offset + 1] << 4
            for offset in range(0, len(indices), 2)
        )
    else:
        packed = bytearray(indices)
    picture[image_start:image_start + len(packed)] = packed
    for index, color in enumerate(palette):
        if clut_type == 1:
            struct.pack_into("<H", picture, clut_start + index * 2, int(color))
        else:
            picture[clut_start + index * 4:clut_start + index * 4 + 4] = bytes(color)
    header = bytearray(16)
    header[:4] = b"TIM2"
    header[4:8] = bytes((4, 0, 1, 0))
    return bytes(header + picture)


def base_rgb5a1_fixture() -> bytes:
    return synthetic_tim2(palette=[0x801F, 0x83E0, 0xFC00, 0xFFFF] + [0x8000] * 12)


class Tim2DecodeTests(unittest.TestCase):
    def test_psmt4_rgb5a1_palette_alpha_dimensions_and_nibble_order(self) -> None:
        image = decode_tim2(base_rgb5a1_fixture())
        self.assertEqual((image.width, image.height), (2, 2))
        self.assertEqual(image.indices, bytes((0, 1, 2, 3)))
        self.assertEqual(image.palette[0], (248, 0, 0, 255))
        self.assertEqual(image.palette[1], (0, 248, 0, 255))
        self.assertEqual(image.palette[2], (0, 0, 248, 255))
        self.assertEqual(image.palette[3], (248, 248, 248, 255))
        self.assertEqual(len(image.rgba), 16)
        png = encode_png(image)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(
            hashlib.sha256(png).hexdigest().upper(),
            "EF55A768A3B149DA7ACCA5758D70A336500E1D0084E145C24DC918E64BA7F2B2",
        )

    def test_rgb5a1_transparent_palette_bit(self) -> None:
        self.assertEqual(
            decode_tim2(synthetic_tim2(palette=[0x001F] + [0x8000] * 15)).palette[0][3], 0,
        )

    def test_psmt4_rgba8888_and_ps2_alpha_expansion(self) -> None:
        palette = [(1, 2, 3, 0), (4, 5, 6, 64), (7, 8, 9, 128), (10, 11, 12, 255)]
        palette += [(0, 0, 0, 0)] * 12
        image = decode_tim2(synthetic_tim2(clut_type=3, palette=palette))
        self.assertEqual(image.palette[:4], (
            (1, 2, 3, 0), (4, 5, 6, 128), (7, 8, 9, 255), (10, 11, 12, 255),
        ))

    def test_psmt8_rgb5a1_uses_csm1_palette_permutation(self) -> None:
        palette = [0x8000] * 256
        palette[16] = 0x801F  # Logical palette 8 is stored at 16.
        palette[8] = 0x83E0   # Logical palette 16 is stored at 8.
        image = decode_tim2(synthetic_tim2(
            image_type=5, indices=bytes((8, 16, 0, 31)), palette=palette,
        ))
        self.assertEqual(image.palette[8], (248, 0, 0, 255))
        self.assertEqual(image.palette[16], (0, 248, 0, 255))
        self.assertEqual(image.rgba[:8], bytes((248, 0, 0, 255, 0, 248, 0, 255)))

    def test_psmt8_rgba8888_csm1_and_alpha(self) -> None:
        palette = [(0, 0, 0, 0)] * 256
        palette[16] = (11, 22, 33, 64)
        image = decode_tim2(synthetic_tim2(
            image_type=5, clut_type=3, indices=bytes((8, 0, 0, 0)), palette=palette,
        ))
        self.assertEqual(image.palette[8], (11, 22, 33, 128))
        self.assertEqual(image.rgba[:4], bytes((11, 22, 33, 128)))

    def test_declared_mip_sizes_are_validated(self) -> None:
        data = synthetic_tim2(
            width=8, height=8, indices=bytes(range(16)) * 4, mip_sizes=(32, 8, 2),
        )
        self.assertEqual(decode_tim2(data).mip_sizes, (32, 8, 2))
        malformed = bytearray(data)
        struct.pack_into("<I", malformed, 16 + 0x40 + 4, 9)
        with self.assertRaisesRegex(Tim2FormatError, "mip"):
            decode_tim2(bytes(malformed))

    def test_malformed_magic_rejected(self) -> None:
        data = bytearray(base_rgb5a1_fixture())
        data[:4] = b"NOPE"
        with self.assertRaisesRegex(Tim2FormatError, "magic"):
            decode_tim2(bytes(data))

    def test_truncated_payload_rejected(self) -> None:
        with self.assertRaisesRegex(Tim2FormatError, "size"):
            decode_tim2(base_rgb5a1_fixture()[:-1])

    def test_invalid_psmt4_dimensions_rejected(self) -> None:
        data = bytearray(base_rgb5a1_fixture())
        struct.pack_into("<H", data, 16 + 20, 3)
        with self.assertRaisesRegex(Tim2FormatError, "dimensions"):
            decode_tim2(bytes(data))

    def test_invalid_palette_size_rejected(self) -> None:
        data = bytearray(base_rgb5a1_fixture())
        struct.pack_into("<H", data, 16 + 14, 15)
        with self.assertRaisesRegex(Tim2FormatError, "CLUT"):
            decode_tim2(bytes(data))

    def test_unsupported_clut_type_rejected(self) -> None:
        data = bytearray(base_rgb5a1_fixture())
        data[16 + 18] = 2
        with self.assertRaisesRegex(Tim2FormatError, "CLUT type"):
            decode_tim2(bytes(data))

    def test_unsupported_image_type_rejected(self) -> None:
        data = bytearray(base_rgb5a1_fixture())
        data[16 + 19] = 3
        with self.assertRaisesRegex(Tim2FormatError, "image type"):
            decode_tim2(bytes(data))


if __name__ == "__main__":
    unittest.main()
