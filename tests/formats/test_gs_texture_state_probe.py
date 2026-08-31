"""Synthetic tests for bounded GS texture/alpha state helpers."""

from __future__ import annotations

import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from gs_texture_state_probe import (  # noqa: E402
    GsTextureStateError,
    alpha_test_gequal,
    cloud_runtime_tex0_template,
    decode_tex0,
    decode_texa,
    modulate_alpha,
    rgb_only_failed_writes,
)


class GsTextureStateTests(unittest.TestCase):
    def test_cloud_runtime_tex0_fields(self) -> None:
        state = decode_tex0(cloud_runtime_tex0_template(0x0000000221B00000, 256, 256))
        self.assertEqual(
            (state.tbw, state.psm, state.tw, state.th, state.tcc, state.tfx,
             state.cpsm, state.csm, state.csa, state.cld),
            (4, 0x1B, 8, 8, 1, 0, 0, 0, 0, 1),
        )

    def test_texa_decoder(self) -> None:
        state = decode_texa(0x0000008000008080)
        self.assertEqual((state.ta0, state.aem, state.ta1), (0x80, 1, 0x80))

    def test_modulate_rgba_and_rgb_only_modes(self) -> None:
        self.assertEqual(modulate_alpha(0x80, 0x80, 1), 0x80)
        self.assertEqual(modulate_alpha(0x40, 0x20, 1), 0x10)
        self.assertEqual(modulate_alpha(0x40, 0x00, 0), 0x40)

    def test_alpha_test_and_rgb_only_failure(self) -> None:
        self.assertTrue(alpha_test_gequal(0x80, 0x80))
        self.assertFalse(alpha_test_gequal(0x7F, 0x80))
        self.assertEqual(rgb_only_failed_writes(), {"rgb": True, "alpha": False, "depth": False})

    def test_invalid_alpha_is_rejected(self) -> None:
        with self.assertRaises(GsTextureStateError):
            modulate_alpha(0x100, 0x80, 1)


if __name__ == "__main__":
    unittest.main()
