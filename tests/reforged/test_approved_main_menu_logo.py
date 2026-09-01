"""Deterministic integration tests for the human-approved Reforged logo."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/reforged/frontend/integrate_approved_main_menu_logo.py"
SPEC = importlib.util.spec_from_file_location("approved_logo_integration_test", MODULE_PATH)
assert SPEC and SPEC.loader
APPROVED = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = APPROVED
SPEC.loader.exec_module(APPROVED)
METADATA = json.loads(APPROVED.METADATA_PATH.read_text(encoding="utf-8"))
TOKENS = json.loads(APPROVED.TOKENS_PATH.read_text(encoding="utf-8"))


class ApprovedMainMenuLogoTests(unittest.TestCase):
    def test_archival_and_runtime_copies_are_byte_exact(self) -> None:
        expected = APPROVED.EXPECTED_SOURCE_SHA256
        self.assertEqual(APPROVED.sha256_path(APPROVED.SOURCE_PATH), expected)
        self.assertEqual(APPROVED.sha256_path(APPROVED.RUNTIME_PATH), expected)
        self.assertEqual(APPROVED.SOURCE_PATH.read_bytes(), APPROVED.RUNTIME_PATH.read_bytes())

    def test_source_metadata_and_alpha(self) -> None:
        self.assertEqual(METADATA["approvalStatus"], "HUMAN APPROVED")
        self.assertEqual(METADATA["source"]["dimensions"], [2172, 724])
        self.assertEqual(METADATA["source"]["format"], "PNG")
        self.assertEqual(METADATA["source"]["mode"], "RGBA")
        self.assertTrue(METADATA["source"]["alpha"]["present"])
        self.assertEqual(METADATA["source"]["alpha"]["range"], [0, 255])
        with Image.open(APPROVED.RUNTIME_PATH) as image:
            self.assertEqual((image.format, image.mode, image.size), ("PNG", "RGBA", (2172, 724)))

    def test_approved_art_is_not_reconstructed_or_cleaned(self) -> None:
        processing = METADATA["processing"]
        self.assertFalse(processing["visualDesignAltered"])
        self.assertFalse(processing["vectorisationAttempted"])
        self.assertFalse(processing["cleanupPerformed"])
        self.assertFalse(processing["resizePerformed"])
        self.assertTrue(processing["sourceAndRuntimeByteIdentical"])

    def test_runtime_uses_complete_approved_raster(self) -> None:
        self.assertEqual(
            TOKENS["assets"]["logo"],
            "logo/approved/runtime/spartan-logo-approved.png",
        )
        self.assertIsNone(TOKENS["assets"]["logoFlare"])
        self.assertIsNone(TOKENS["assets"]["logoGlintMask"])
        self.assertFalse(METADATA["layers"]["dividerExtractionAttempted"])
        self.assertFalse(METADATA["layers"]["flareExtractionAttempted"])

    def test_pass1_and_pass2_research_are_retained(self) -> None:
        pass1 = ROOT / "assets/reforged/frontend/main-menu/logo/logo_runtime/logo-A.png"
        pass2 = ROOT / "assets/reforged/frontend/main-menu/logo/pass2/logo_runtime/logo-pass2A.png"
        self.assertTrue(pass1.is_file())
        self.assertTrue(pass2.is_file())
        self.assertTrue(METADATA["retainedResearch"]["pass2BevelResearchRetained"])

    def test_layout_scales_uniformly_and_preserves_ultrawide_anchor(self) -> None:
        ui = APPROVED.load_ui_module()
        self.assertEqual(METADATA["runtime"]["designPosition"], [130, 90])
        self.assertEqual(METADATA["runtime"]["nominalDisplay1080p"], [630, 210])
        self.assertEqual(METADATA["runtime"]["nominalDisplay1440p"], [840, 280])
        self.assertEqual(METADATA["runtime"]["nominalDisplay4k"], [1260, 420])
        wide = ui.layout_for_viewport(2560, 1080, TOKENS)
        self.assertEqual(wide.composition_x, 320.0)
        self.assertEqual(wide.point(*TOKENS["logo"]["position"]), (450.0, 90.0))

    def test_original_mode_contract_remains_separate(self) -> None:
        ui = APPROVED.load_ui_module()
        screen = ui.build_main_start()
        original = ui.MenuState(screen, "new_game", ui.PresentationMode.ORIGINAL)
        reforged = ui.MenuState(screen, "new_game", ui.PresentationMode.REFORGED)
        self.assertEqual(original.screen, reforged.screen)
        self.assertNotEqual(original.presentation, reforged.presentation)


if __name__ == "__main__":
    unittest.main()
