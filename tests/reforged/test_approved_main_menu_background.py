"""Deterministic integration tests for the approved Reforged background."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/reforged/frontend/integrate_approved_main_menu_background.py"
SPEC = importlib.util.spec_from_file_location("approved_background_integration_test", MODULE_PATH)
assert SPEC and SPEC.loader
APPROVED = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = APPROVED
SPEC.loader.exec_module(APPROVED)


class ApprovedMainMenuBackgroundTests(unittest.TestCase):
    def test_source_and_runtime_are_byte_exact(self) -> None:
        self.assertEqual(APPROVED.sha256_path(APPROVED.SOURCE_PATH), APPROVED.EXPECTED_SHA256)
        self.assertEqual(APPROVED.sha256_path(APPROVED.RUNTIME_PATH), APPROVED.EXPECTED_SHA256)
        self.assertEqual(APPROVED.SOURCE_PATH.read_bytes(), APPROVED.RUNTIME_PATH.read_bytes())

    def test_metadata_and_format(self) -> None:
        metadata = json.loads(APPROVED.METADATA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(metadata["approvalStatus"], "HUMAN APPROVED")
        self.assertFalse(metadata["processing"]["visualDesignAltered"])
        self.assertFalse(metadata["processing"]["sourceFileReencoded"])
        with Image.open(APPROVED.RUNTIME_PATH) as image:
            self.assertEqual((image.format, image.mode, image.size), ("JPEG", "RGB", (1280, 720)))

    def test_tokens_bind_background_and_suppress_duplicate_bands(self) -> None:
        tokens = json.loads((ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json").read_text(encoding="utf-8"))
        self.assertEqual(
            tokens["assets"]["background"],
            "background/approved/runtime/spartan-background-approved.jpg",
        )
        self.assertTrue(tokens["background"]["approvedPlateIncludesOrnamentBands"])


if __name__ == "__main__":
    unittest.main()
