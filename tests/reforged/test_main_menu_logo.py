"""Deterministic structural tests for the Reforged logo production asset."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/reforged/frontend/build_main_menu_logo.py"
SPEC = importlib.util.spec_from_file_location("build_main_menu_logo_test", MODULE_PATH)
assert SPEC and SPEC.loader
LOGO = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LOGO
SPEC.loader.exec_module(LOGO)
METADATA_PATH = ROOT / "assets/reforged/frontend/main-menu/logo/metadata/logo.json"


class MainMenuLogoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

    def test_original_hashes_remain_canonical(self) -> None:
        self.assertEqual(LOGO.sha256_path(LOGO.REFERENCE), LOGO.EXPECTED_REFERENCE_SHA256)
        self.assertEqual(LOGO.sha256_path(LOGO.SOURCE_TM2), LOGO.EXPECTED_TM2_SHA256)

    def test_original_measured_geometry(self) -> None:
        base, _flare = LOGO.load_original_layers()
        geometry = LOGO.measure_geometry(base)
        self.assertEqual(geometry.visible_alpha_bounds, (2, 1, 184, 64))
        self.assertEqual(geometry.spartan_bounds, (2, 1, 170, 36))
        self.assertEqual(geometry.subtitle_bounds, (2, 41, 171, 64))
        self.assertEqual(geometry.trademark_bounds, (169, 2, 184, 12))
        self.assertEqual(geometry.line_gap, 9)

    def test_master_aspect_ratio_and_dimensions(self) -> None:
        self.assertEqual(self.metadata["master"]["dimensions"], [2520, 840])
        self.assertEqual(self.metadata["master"]["canvasAspectRatio"], 3.0)
        for name in "ABC":
            with Image.open(LOGO.RUNTIME_ROOT / f"logo-{name}.png") as image:
                self.assertEqual(image.size, (2520, 840))
                self.assertEqual(image.mode, "RGBA")

    def test_alpha_bounds_are_internal_and_nonempty(self) -> None:
        bounds = self.metadata["master"]["visibleAlphaBounds"]
        self.assertGreater(bounds[0], 0)
        self.assertGreater(bounds[1], 0)
        self.assertLess(bounds[2], 2520)
        self.assertLess(bounds[3], 840)
        self.assertGreater(bounds[2], bounds[0])
        self.assertGreater(bounds[3], bounds[1])

    def test_runtime_outputs_match_metadata_hashes(self) -> None:
        for name in "ABC":
            path = LOGO.RUNTIME_ROOT / f"logo-{name}.png"
            self.assertEqual(LOGO.sha256_path(path), self.metadata["variants"][name]["sha256"])
        self.assertEqual(
            (LOGO.RUNTIME_ROOT / "logo-preferred.png").read_bytes(),
            (LOGO.RUNTIME_ROOT / "logo-A.png").read_bytes(),
        )

    def test_vector_master_has_custom_paths_and_no_font_dependency(self) -> None:
        path = LOGO.SOURCE_ROOT / "logo_geometry.svg"
        root = ET.parse(path).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        self.assertTrue(root.findall(f"{namespace}path"))
        self.assertFalse(root.findall(f".//{namespace}text"))
        self.assertIsNone(self.metadata["typography"]["font"])

    def test_layers_and_asset_availability(self) -> None:
        for path in (
            LOGO.MASK_ROOT / "logo-base-mask.png",
            LOGO.MASK_ROOT / "logo-glow.png",
            LOGO.MASK_ROOT / "logo-glint-mask.png",
            LOGO.MASK_ROOT / "logo-flare.png",
        ):
            self.assertTrue(path.is_file(), path)

    def test_reforged_path_separation(self) -> None:
        for path in (LOGO.SOURCE_ROOT, LOGO.RUNTIME_ROOT, LOGO.MASK_ROOT, LOGO.METADATA_ROOT):
            self.assertTrue(path.resolve().is_relative_to((ROOT / "assets/reforged").resolve()))
        self.assertFalse(LOGO.SOURCE_TM2.resolve().is_relative_to(LOGO.ASSET_ROOT.resolve()))

    def test_display_scaling_and_ultrawide_anchor(self) -> None:
        ui_path = ROOT / "tools/reforged/frontend/main_menu_reforged.py"
        spec = importlib.util.spec_from_file_location("main_menu_reforged_logo_test", ui_path)
        assert spec and spec.loader
        ui = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = ui
        spec.loader.exec_module(ui)
        tokens = ui.load_json(ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json")
        self.assertEqual(self.metadata["runtime"]["nominalDisplay1080p"], [630, 210])
        self.assertEqual(self.metadata["runtime"]["nominalDisplay4k"], [1260, 420])
        wide = ui.layout_for_viewport(3440, 1440, tokens)
        self.assertAlmostEqual(wide.point(*tokens["logo"]["position"])[0], 613.3333333333)
        self.assertGreater(wide.composition_x, 0)

    def test_preference_is_pending_human_review(self) -> None:
        self.assertEqual(self.metadata["preferredVariant"], "A")
        self.assertIn("PENDING HUMAN ART REVIEW", self.metadata["preferenceStatus"])


if __name__ == "__main__":
    unittest.main()
