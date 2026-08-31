"""Synthetic tests for the Reforged main-menu reference tooling."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/reforged/frontend/main_menu_design_kit.py"
SPEC = importlib.util.spec_from_file_location("main_menu_design_kit", MODULE_PATH)
assert SPEC and SPEC.loader
KIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = KIT
SPEC.loader.exec_module(KIT)


class MainMenuDesignKitTests(unittest.TestCase):
    def test_script_parser_and_target_menu(self) -> None:
        script = """TPAGE page image.tm2
FONT font14
TEXTURE region page 0 0 128 128
SPRITE sprite region 8 16 32 32
TEXT label_text label 0 0 64 32 0 7
ITEMS group sprite label_text
MENU main_start group
LABEL label hello
EMITTER smoke region 1 2 3
"""
        model = KIT.parse_script(script)
        self.assertEqual(KIT.expand_group(model, "group"), ["sprite", "label_text"])
        self.assertEqual(model.menus["main_start"], ["group"])
        self.assertEqual(model.emitters["smoke"].values, (1, 2, 3))

    def test_normalized_texture_bounds(self) -> None:
        region = KIT.TextureRegion("quarter", "page", 128, 0, 128, 128, 1)
        self.assertEqual(KIT.normalized_crop_box(region, (64, 64)), (32, 0, 64, 32))
        with self.assertRaises(KIT.DesignKitError):
            KIT.normalized_crop_box(KIT.TextureRegion("bad", "page", 250, 0, 16, 16, 1), (64, 64))

    def test_glyph_advance_and_bounds(self) -> None:
        atlas = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        advances = [4] * 256
        dim = bytes([16]) + bytes([0xCD]) * 63 + b"".join(value.to_bytes(2, "little") for value in advances)
        rendered, advance = KIT.render_text(atlas, dim, "AB", 32, 16)
        self.assertEqual(rendered.size, (32, 16))
        self.assertEqual(advance, 8)

    def test_coordinate_mapping(self) -> None:
        mapping = KIT.aspect_mapping(1920, 1080)
        self.assertEqual((mapping["centralWidth"], mapping["centralHeight"]), (1440, 1080))
        self.assertEqual(mapping["sideExtensionEach"], 240)
        self.assertAlmostEqual(mapping["scaleXFromLogical"], 2.8125)

    def test_reference_composition_is_deterministic(self) -> None:
        image = Image.new("RGBA", (8, 8), (10, 20, 30, 255))
        a = KIT._modulate(image, (128, 128, 128), 128).tobytes()
        b = KIT._modulate(image, (128, 128, 128), 128).tobytes()
        self.assertEqual(a, b)
        self.assertEqual(a[:4], bytes((10, 20, 30, 255)))


if __name__ == "__main__":
    unittest.main()
