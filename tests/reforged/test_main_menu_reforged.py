"""Synthetic tests for the additive Reforged main-menu foundation."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools/reforged/frontend/main_menu_reforged.py"
SPEC = importlib.util.spec_from_file_location("main_menu_reforged", MODULE_PATH)
assert SPEC and SPEC.loader
UI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = UI
SPEC.loader.exec_module(UI)
TOKENS = UI.load_json(ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json")


class MainMenuReforgedTests(unittest.TestCase):
    def test_1080p_layout(self) -> None:
        layout = UI.layout_for_viewport(1920, 1080, TOKENS)
        self.assertEqual(layout.scale, 1.0)
        self.assertEqual(layout.safe_rect, (96.0, 54.0, 1824.0, 1026.0))

    def test_1440p_and_4k_scaling(self) -> None:
        self.assertAlmostEqual(UI.layout_for_viewport(2560, 1440, TOKENS).scale, 4 / 3)
        self.assertEqual(UI.layout_for_viewport(3840, 2160, TOKENS).scale, 2.0)

    def test_21x9_safe_area_and_32x9_extensions(self) -> None:
        wide = UI.layout_for_viewport(2560, 1080, TOKENS)
        self.assertEqual((wide.composition_x, wide.background_extension_left), (320.0, 320.0))
        self.assertGreaterEqual(wide.safe_rect[0], wide.composition_x)
        superwide = UI.layout_for_viewport(3840, 1080, TOKENS)
        self.assertEqual((superwide.background_extension_left, superwide.background_extension_right), (960.0, 960.0))

    def test_4x3_fallback_keeps_safe_area_visible(self) -> None:
        layout = UI.layout_for_viewport(1440, 1080, TOKENS)
        self.assertEqual(layout.scale, 0.75)
        self.assertGreaterEqual(layout.safe_rect[0], 0)
        self.assertLessEqual(layout.safe_rect[2], 1440)
        self.assertGreaterEqual(layout.safe_rect[1], 0)
        self.assertLessEqual(layout.safe_rect[3], 1080)

    def test_menu_spacing_and_navigation(self) -> None:
        screen = UI.build_main_start(maxlevel=3)
        state = UI.MenuState(screen, "new_game")
        self.assertEqual(TOKENS["menu"]["itemSpacing"], 82)
        self.assertEqual(state.navigate(UI.InputAction.DOWN).selected_id, "load_game")
        self.assertEqual(state.navigate(UI.InputAction.UP).selected_id, "extras")

    def test_locked_state_preserves_original_condition(self) -> None:
        locked = UI.MenuState(UI.build_main_start(maxlevel=0), "single_mission_replay")
        unlocked = UI.MenuState(UI.build_main_start(maxlevel=1), "single_mission_replay")
        self.assertTrue(locked.selected.locked)
        self.assertEqual(locked.selected.lock_condition, "maxlevel == 0")
        self.assertIsNone(locked.confirm())
        self.assertEqual(unlocked.confirm(), UI.MenuAction.SINGLE_MISSION_REPLAY)

    def test_semantic_prompt_mapping(self) -> None:
        self.assertEqual(UI.resolve_prompt("playstation", UI.InputAction.CONFIRM), "CROSS")
        self.assertEqual(UI.resolve_prompt("playstation", UI.InputAction.BACK), "TRIANGLE")
        self.assertEqual(UI.resolve_prompt("xbox", UI.InputAction.CONFIRM), "A")
        self.assertEqual(UI.resolve_prompt("keyboard", UI.InputAction.BACK), "ESCAPE")

    def test_text_wrapping_respects_width(self) -> None:
        font = UI._font(18)
        lines = UI.wrap_text("one two three four five six", 80, font)
        self.assertGreater(len(lines), 1)
        from PIL import Image, ImageDraw
        probe = ImageDraw.Draw(Image.new("L", (1, 1)))
        self.assertTrue(all(probe.textlength(line, font=font) <= 80 for line in lines))

    def test_original_and_reforged_are_explicitly_separate(self) -> None:
        original = UI.MenuState(UI.build_main_start(), "new_game", UI.PresentationMode.ORIGINAL)
        reforged = UI.MenuState(UI.build_main_start(), "new_game", UI.PresentationMode.REFORGED)
        self.assertEqual(original.screen, reforged.screen)
        self.assertNotEqual(original.presentation, reforged.presentation)
        with self.assertRaises(ValueError):
            UI.render_wireframe(320, 180, original, TOKENS, UI.load_json(UI.DEFAULT_LOCALE)["strings"])

    def test_missing_asset_uses_named_fallback(self) -> None:
        self.assertEqual(UI.missing_asset_fallback("foregroundEnvironment", TOKENS), "placeholder:foregroundEnvironment")
        configured = {**TOKENS, "assets": {**TOKENS["assets"], "foregroundEnvironment": "foreground.webp"}}
        self.assertEqual(UI.missing_asset_fallback("foregroundEnvironment", configured), "foreground.webp")

    def test_render_layers_and_effect_budgets_are_explicit(self) -> None:
        self.assertEqual([layer.value for layer in UI.RenderLayer], list(range(11)))
        effects = UI.default_atmosphere_effects()
        self.assertEqual({effect.semantic_id for effect in effects}, {
            "mist_back", "smoke_back", "embers_front", "logo_glint", "selected_glow"
        })
        self.assertTrue(all(effect.excludes_ui_safe_regions for effect in effects))
        self.assertTrue(all(effect.reduced_motion_instances <= effect.max_instances for effect in effects))

    def test_production_navigation_uses_licensed_cinzel(self) -> None:
        self.assertEqual(TOKENS["typography"]["fontFamily"], "Cinzel")
        self.assertEqual(TOKENS["typography"]["fontLicense"], "SIL Open Font License 1.1")
        for filename in TOKENS["typography"]["fontFiles"].values():
            self.assertTrue((ROOT / "assets/reforged/frontend/main-menu" / filename).is_file())
        self.assertEqual(TOKENS["typography"]["MenuPrimary"], 52)
        self.assertEqual(TOKENS["typography"]["MenuPrimarySelected"], 56)

    def test_material_typography_has_real_internal_layers(self) -> None:
        selected_font = UI._font(56, TOKENS, "bold")
        for state in ("selected", "unselected", "locked"):
            layers, _ = UI.build_material_text_layers("NEW GAME", selected_font, state)
            self.assertIsNotNone(layers["face"].getbbox())
            self.assertIsNotNone(layers["light_bevel"].getbbox())
            self.assertIsNotNone(layers["opposing_bevel"].getbbox())
            self.assertIsNotNone(layers["inset"].getbbox())
            self.assertLess(sum(layers["inset"].getdata()), sum(layers["glyph"].getdata()))

    def test_material_states_are_visibly_distinct_without_stroke_expansion(self) -> None:
        font = UI._font(56, TOKENS, "bold")
        renders = {}
        for state in ("selected", "unselected", "locked"):
            canvas = Image.new("RGB", (500, 100), (7, 13, 23))
            UI.render_material_text(canvas, (20, 10), "NEW GAME", font, state)
            renders[state] = canvas.tobytes()
        self.assertEqual(len(set(renders.values())), 3)
        self.assertNotIn("strokeWidth", TOKENS["typography"])

    def test_locked_material_has_reduced_specular_contrast(self) -> None:
        selected = UI.MATERIAL_PALETTES["selected"]
        locked = UI.MATERIAL_PALETTES["locked"]
        selected_span = sum(selected["highlight"]) - sum(selected["opposing"])
        locked_span = sum(locked["highlight"]) - sum(locked["opposing"])
        self.assertLess(locked_span, selected_span)


if __name__ == "__main__":
    unittest.main()
