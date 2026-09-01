"""Structural tests for clean-geometry Reforged logo Pass 2."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/reforged/frontend/build_main_menu_logo_pass2.py"
SPEC = importlib.util.spec_from_file_location("build_main_menu_logo_pass2_test", MODULE_PATH)
assert SPEC and SPEC.loader
PASS2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PASS2
SPEC.loader.exec_module(PASS2)
METADATA = json.loads((PASS2.METADATA_ROOT / "logo-pass2.json").read_text(encoding="utf-8"))


class MainMenuLogoPass2Tests(unittest.TestCase):
    def test_original_hash_and_pass1_are_retained(self) -> None:
        pass1 = PASS2.load_module("pass1_retention_test", PASS2.PASS1_MODULE)
        self.assertEqual(pass1.sha256_path(pass1.SOURCE_TM2), PASS2.EXPECTED_TM2_SHA256)
        self.assertTrue((PASS2.PASS1_ROOT / "logo_source/logo_geometry.svg").is_file())
        self.assertTrue((PASS2.PASS1_ROOT / "logo_runtime/logo-A.png").is_file())
        self.assertTrue(METADATA["pass1Retained"])

    def test_pass2_is_separate_and_does_not_trace_raster_contours(self) -> None:
        self.assertTrue(PASS2.PASS2_ROOT.resolve().is_relative_to(PASS2.LOGO_ROOT.resolve()))
        self.assertNotEqual(PASS2.PASS2_ROOT, PASS2.PASS1_ROOT)
        method = METADATA["geometry"]["method"].casefold()
        self.assertIn("no raster contour tracing", method)
        self.assertIn("line/cubic-bezier", method)

    def test_master_uses_straight_lines_and_deliberate_cubics(self) -> None:
        library = PASS2.glyphs()
        line_commands = sum(command[0] == "L" for glyph in library.values() for contour in glyph.contours for command in contour.commands)
        curve_commands = sum(command[0] == "C" for glyph in library.values() for contour in glyph.contours for command in contour.commands)
        self.assertGreater(line_commands, 40)
        self.assertGreaterEqual(curve_commands, 10)
        self.assertIn("straight central stem", library["T"].construction)
        self.assertIn("four deliberate cubic outer arcs", library["O"].construction)

    def test_repeated_glyphs_reference_one_definition(self) -> None:
        root = ET.parse(PASS2.SOURCE_ROOT / "logo_clean_geometry.svg").getroot()
        hrefs = [element.attrib.get("href") for element in root if element.tag.endswith("use")]
        self.assertGreaterEqual(hrefs.count("#glyph-A"), 4)
        self.assertGreaterEqual(hrefs.count("#glyph-R"), 3)
        self.assertGreaterEqual(hrefs.count("#glyph-T"), 4)
        self.assertEqual(METADATA["geometry"]["repeatedGlyphPolicy"], "every occurrence references the same glyph definition")

    def test_master_bounds_and_runtime_dimensions(self) -> None:
        with Image.open(PASS2.MASK_ROOT / "logo-clean-mask.png") as mask:
            self.assertEqual(mask.size, PASS2.MASTER_SIZE)
            bounds = mask.getbbox()
            self.assertIsNotNone(bounds)
            assert bounds
            self.assertGreater(bounds[0], 0); self.assertGreater(bounds[1], 0)
            self.assertLess(bounds[2], PASS2.MASTER_SIZE[0]); self.assertLess(bounds[3], PASS2.MASTER_SIZE[1])
        for name in ("2A", "2B", "2C"):
            with Image.open(PASS2.RUNTIME_ROOT / f"logo-pass{name}.png") as image:
                self.assertEqual(image.size, PASS2.MASTER_SIZE)
                self.assertEqual(image.mode, "RGBA")

    def test_all_candidates_share_geometry_and_alpha(self) -> None:
        alphas = []
        for name in ("2A", "2B", "2C"):
            with Image.open(PASS2.RUNTIME_ROOT / f"logo-pass{name}.png") as image:
                alphas.append(image.getchannel("A").tobytes())
        self.assertEqual(alphas[0], alphas[1])
        self.assertEqual(alphas[0], alphas[2])

    def test_flare_is_separate_blue_white_component(self) -> None:
        flare_path = PASS2.MASK_ROOT / "logo-blue-flare.png"
        self.assertNotEqual(flare_path, PASS2.RUNTIME_ROOT / "logo-pass2-preferred.png")
        with Image.open(flare_path) as flare:
            self.assertEqual(flare.size, (2520, 252))
            self.assertEqual(flare.mode, "RGBA")
            extrema = flare.getchannel("A").getextrema()
            self.assertGreater(extrema[1], 0)
        self.assertTrue(METADATA["flare"]["separate"])

    def test_metadata_and_preference_are_pending_review(self) -> None:
        self.assertEqual(METADATA["preferred"], "2A")
        self.assertIn("PENDING HUMAN", METADATA["preferenceStatus"])
        for name in ("2A", "2B", "2C"):
            self.assertEqual(PASS2.sha256(PASS2.RUNTIME_ROOT / f"logo-pass{name}.png"), METADATA["variants"][name]["sha256"])

    def test_pass2_is_retained_but_approved_art_is_runtime_selection(self) -> None:
        tokens = json.loads(PASS2.TOKENS_PATH.read_text(encoding="utf-8"))
        self.assertTrue((PASS2.RUNTIME_ROOT / "logo-pass2-preferred.png").is_file())
        self.assertEqual(tokens["assets"]["logo"], "logo/approved/runtime/spartan-logo-approved.png")
        self.assertIsNone(tokens["assets"]["logoFlare"])
        self.assertIsNone(tokens["assets"]["foregroundEnvironment"])

    def test_1080p_4k_and_ultrawide_placement(self) -> None:
        ui = PASS2.load_module("main_menu_reforged_pass2_test", PASS2.UI_MODULE)
        tokens = ui.load_json(PASS2.TOKENS_PATH)
        p1080 = ui.layout_for_viewport(1920, 1080, tokens).point(*tokens["logo"]["position"])
        p4k = ui.layout_for_viewport(3840, 2160, tokens).point(*tokens["logo"]["position"])
        wide = ui.layout_for_viewport(3440, 1440, tokens)
        self.assertEqual(p1080, (130.0, 90.0))
        self.assertEqual(p4k, (260.0, 180.0))
        self.assertAlmostEqual(wide.point(*tokens["logo"]["position"])[0], 613.3333333333)
        self.assertGreater(wide.composition_x, 0)


if __name__ == "__main__":
    unittest.main()
