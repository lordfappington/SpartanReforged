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


def synthetic_tim2() -> bytes:
    # 2x2, indices 0,1,2,3 (packed low nibble first), one mip, RGB5A1.
    picture = bytearray(96)
    struct.pack_into("<IIIHHBBBBHH", picture, 0, 96, 32, 2, 48, 16, 0, 1, 1, 4, 2, 2)
    picture[48:50] = bytes((0x10, 0x32))
    palette_offset = 64
    colors = (0x801F, 0x83E0, 0xFC00, 0xFFFF) + (0x8000,) * 12
    for index, color in enumerate(colors):
        struct.pack_into("<H", picture, palette_offset + index * 2, color)
    header = bytearray(16)
    header[:4] = b"TIM2"
    header[4:8] = bytes((4, 0, 1, 0))
    return bytes(header + picture)


class Tim2DecodeTests(unittest.TestCase):
    def test_palette_alpha_dimensions_and_nibble_order(self) -> None:
        image = decode_tim2(synthetic_tim2())
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

    def test_transparent_palette_bit(self) -> None:
        data = bytearray(synthetic_tim2())
        struct.pack_into("<H", data, 16 + 64, 0x001F)
        self.assertEqual(decode_tim2(bytes(data)).palette[0][3], 0)

    def test_malformed_magic_rejected(self) -> None:
        data = bytearray(synthetic_tim2())
        data[:4] = b"NOPE"
        with self.assertRaisesRegex(Tim2FormatError, "magic"):
            decode_tim2(bytes(data))

    def test_unsupported_image_type_rejected(self) -> None:
        data = bytearray(synthetic_tim2())
        data[16 + 19] = 3
        with self.assertRaisesRegex(Tim2FormatError, "image type"):
            decode_tim2(bytes(data))


if __name__ == "__main__":
    unittest.main()
