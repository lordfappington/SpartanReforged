"""Synthetic tests for the bounded MODELS VU1/GIF state decoder."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from vu1_models_probe import Vu1ProbeError, decode_giftag, decode_prim  # noqa: E402


class Vu1ModelsProbeTests(unittest.TestCase):
    def test_prim_25c_decodes_models_state(self) -> None:
        prim = decode_prim(0x25C)
        self.assertEqual(
            (prim.primitive, prim.iip, prim.tme, prim.fge, prim.abe,
             prim.aa1, prim.fst, prim.ctxt, prim.fix),
            (4, 1, 1, 0, 1, 0, 0, 1, 0),
        )

    def test_models_giftag_template(self) -> None:
        tag = decode_giftag(0x8000 | 37, 0x312E4000, 0x412)
        self.assertEqual((tag.nloop, tag.eop, tag.pre, tag.flg, tag.nreg), (37, 1, 1, 0, 3))
        self.assertEqual(tag.registers, (2, 1, 4))
        self.assertEqual(tag.prim.raw, 0x25C)

    def test_zero_nreg_means_sixteen(self) -> None:
        tag = decode_giftag(1, 0, 0xFEDCBA9876543210)
        self.assertEqual(tag.nreg, 16)
        self.assertEqual(tag.registers[0], 0)
        self.assertEqual(tag.registers[-1], 0xF)

    def test_prim_rejects_out_of_range_bits(self) -> None:
        with self.assertRaisesRegex(Vu1ProbeError, "11-bit"):
            decode_prim(0x800)


if __name__ == "__main__":
    unittest.main()
