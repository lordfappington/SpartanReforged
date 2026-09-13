"""Synthetic tests for the bounded rigid-skinned PSQ/BNS decoder."""

from __future__ import annotations

import pathlib
import struct
import sys
import tempfile
import unittest

ANALYSIS = pathlib.Path(__file__).resolve().parents[2] / "tools" / "analysis"
sys.path.insert(0, str(ANALYSIS))

from psq_character import (  # noqa: E402
    CharacterFormatError, export_obj, parse_bns, parse_psq, transformed_positions,
)


def vertex(x: float, adc: float, bone_offset: int) -> bytes:
    return struct.pack("<10fII", x, 0.0, 0.0, adc, 0.0, 1.0, 0.0, 0.0, x, 0.5, bone_offset, 0)


def psq_fixture() -> bytes:
    records = [vertex(0.0, 2048.0, 0), vertex(1.0, 2048.0, 0), vertex(2.0, 0.0, 0),
               vertex(3.0, 0.0, 4), vertex(4.0, 2048.0, 4), vertex(5.0, 0.0, 4)]
    return struct.pack("<III", len(records), 4, 2) + b"".join(records)


def bns_fixture() -> bytes:
    records = struct.pack("<3fi", 1.0, 2.0, 3.0, -1) + struct.pack("<3fi", 4.0, 5.0, 6.0, 0)
    return b"bns2" + struct.pack("<I", 2) + records + bytes((2, 7, 8))


class PsqCharacterTests(unittest.TestCase):
    def test_header_records_adc_topology_and_secondary_range(self) -> None:
        mesh = parse_psq(psq_fixture())
        self.assertEqual(len(mesh.vertices), 6)
        self.assertEqual(mesh.secondary_range_start, 4)
        self.assertEqual(mesh.bone_count, 2)
        self.assertEqual(mesh.triangles, ((0, 1, 2), (2, 1, 3), (4, 3, 5)))

    def test_rigid_bone_offsets_and_rest_pose_transforms(self) -> None:
        mesh = parse_psq(psq_fixture())
        skeleton = parse_bns(bns_fixture())
        self.assertEqual([v.bone_id for v in mesh.vertices], [0, 0, 0, 1, 1, 1])
        self.assertEqual(skeleton.world_translations, ((1.0, 2.0, 3.0), (5.0, 7.0, 9.0)))
        self.assertEqual(transformed_positions(mesh, skeleton)[3], (8.0, 7.0, 9.0))

    def test_bns_hierarchy_and_trailing_table(self) -> None:
        skeleton = parse_bns(bns_fixture())
        self.assertEqual([bone.parent for bone in skeleton.bones], [-1, 0])
        self.assertEqual(skeleton.trailing_index_count, 2)
        self.assertEqual(skeleton.trailing_indices, (7, 8))

    def test_invalid_adc_and_bone_offset_rejected(self) -> None:
        malformed = bytearray(psq_fixture())
        struct.pack_into("<f", malformed, 12 + 3 * 48 + 12, 1.0)
        with self.assertRaisesRegex(CharacterFormatError, "ADC"):
            parse_psq(bytes(malformed))
        malformed = bytearray(psq_fixture())
        struct.pack_into("<I", malformed, 12 + 3 * 48 + 40, 3)
        with self.assertRaisesRegex(CharacterFormatError, "bone offset"):
            parse_psq(bytes(malformed))

    def test_absent_secondary_range_sentinel(self) -> None:
        data = bytearray(psq_fixture())
        struct.pack_into("<I", data, 4, 9_999_999)
        self.assertEqual(parse_psq(bytes(data)).secondary_range_start, 6)

    def test_truncated_inputs_rejected(self) -> None:
        with self.assertRaisesRegex(CharacterFormatError, "size"):
            parse_psq(psq_fixture()[:-1])
        with self.assertRaisesRegex(CharacterFormatError, "truncated"):
            parse_bns(bns_fixture()[:-2])

    def test_private_obj_export_preserves_topology_and_texture_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            psq, bns, texture = root / "mesh.psq", root / "bones.bns", root / "texture.png"
            psq.write_bytes(psq_fixture())
            bns.write_bytes(bns_fixture())
            texture.write_bytes(b"synthetic")
            output = root / "mesh.obj"
            export_obj(psq, bns, output, texture)
            self.assertEqual(output.read_text().count("\nf "), 3)
            self.assertIn("usemtl original_diffuse", output.read_text())
            self.assertIn(texture.resolve().as_posix(), output.with_suffix(".mtl").read_text())


if __name__ == "__main__":
    unittest.main()
