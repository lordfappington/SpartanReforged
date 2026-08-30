"""Synthetic tests for aggregate MODELS V4-8 analysis."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))
sys.path.insert(0, str(ROOT / "tools" / "conversion"))

from models_v4_probe import (  # noqa: E402
    channel_matrix,
    group_batches_by_material,
    rows_for_batches,
    signed8,
)
from spartan_models import Batch, ModelsFormatError  # noqa: E402


def batch(material: int, attribute=((0, 64, 127, 128), (255, 32, 1, 128))) -> Batch:
    count = len(attribute)
    return Batch(
        descriptor_id=material,
        local_index=0,
        global_index=material,
        material_id=material,
        positions=tuple((float(index), 0.0, 0.0) for index in range(count)),
        controls=tuple(0x8000 for _ in range(count)),
        uv_raw=tuple((index * 4096, 0) for index in range(count)),
        attributes_v4_8=tuple(attribute),
        packet_span=0x40,
    )


class V4ProbeTests(unittest.TestCase):
    def test_signed_unsigned_conversion(self) -> None:
        self.assertEqual([signed8(value) for value in (0, 127, 128, 255)], [0, 127, -128, -1])

    def test_rows_and_channel_statistics_preserve_bytes(self) -> None:
        rows = rows_for_batches((batch(2),))
        self.assertEqual([row["attribute"] for row in rows], [(0, 64, 127, 128), (255, 32, 1, 128)])
        stats = channel_matrix(rows)
        self.assertEqual(stats["recordCount"], 2)
        self.assertEqual(stats["unsigned"][0]["minimum"], 0)
        self.assertEqual(stats["unsigned"][0]["maximum"], 255)
        self.assertEqual(stats["unsigned"][3]["frequency"], {"128": 2})
        self.assertEqual(stats["signed"][0]["minimum"], -1)

    def test_grouping_is_by_material_and_deterministic(self) -> None:
        grouped = group_batches_by_material((batch(3), batch(1), batch(3)))
        self.assertEqual(list(grouped), [1, 3])
        self.assertEqual(len(grouped[1]), 1)
        self.assertEqual(len(grouped[3]), 2)

    def test_cardinality_mismatch_is_rejected(self) -> None:
        broken = batch(0)
        broken = Batch(
            broken.descriptor_id, broken.local_index, broken.global_index, broken.material_id,
            broken.positions[:1], broken.controls, broken.uv_raw, broken.attributes_v4_8, broken.packet_span,
        )
        with self.assertRaisesRegex(ModelsFormatError, "cardinality"):
            rows_for_batches((broken,))


if __name__ == "__main__":
    unittest.main()
