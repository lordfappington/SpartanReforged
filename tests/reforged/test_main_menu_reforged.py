"""Synthetic tests for the additive Reforged main-menu foundation."""

from __future__ import annotations

import importlib.util
import hashlib
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
POINTER_SOURCE = ROOT / "assets/reforged/frontend/main-menu/pointer/approved/source/spartan-selection-pointer-approved.jpg"
POINTER_RUNTIME = ROOT / "assets/reforged/frontend/main-menu/pointer/approved/runtime/spartan-selection-pointer-approved.png"
PROMPT_SOURCE = ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved/source/spartan-playstation-shields-approved.jpg"
PROMPT_RUNTIME = {
    "TRIANGLE": ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved/runtime/spartan-prompt-triangle-approved.png",
    "CIRCLE": ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved/runtime/spartan-prompt-circle-approved.png",
    "CROSS": ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved/runtime/spartan-prompt-cross-approved.png",
    "SQUARE": ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved/runtime/spartan-prompt-square-approved.png",
}
PROMPT_HASHES = {
    "TRIANGLE": "83fb48f84a6cec78b2bac5bc2d9c5a8cd06749fe08a11dcd490deef746d3d35c",
    "CIRCLE": "f70305a12930d273708e62995c0b8086d051d90c4fc7e60deb7fe680d5622662",
    "CROSS": "6cb1178304bc5e027fc0c3f1c8ec4ae9719af904f3d7ab59cd659bd2dfa1d97e",
    "SQUARE": "f3760801744438327e3bda04e828ba4eca062c2c98435636628b8599363ed342",
}


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

    def test_approved_playstation_prompt_assets_are_normalized_and_locked(self) -> None:
        self.assertEqual(hashlib.sha256(PROMPT_SOURCE.read_bytes()).hexdigest(), "0ad9b4e09f91602617516cd48e992d0e421bb1a39ff86ca680441f384fbb8af6")
        centres = []
        for glyph, path in PROMPT_RUNTIME.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), PROMPT_HASHES[glyph])
            with Image.open(path) as prompt:
                self.assertEqual((prompt.format, prompt.mode, prompt.size), ("PNG", "RGBA", (448, 448)))
                bounds = prompt.getchannel("A").getbbox()
                self.assertIsNotNone(bounds)
                assert bounds is not None
                self.assertEqual(max(bounds[2] - bounds[0], bounds[3] - bounds[1]), 416)
                centres.append(((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2))
        self.assertTrue(all(abs(x - 224) <= .5 and abs(y - 224) <= .5 for x, y in centres))

    def test_playstation_prompt_assets_remain_semantic_and_directly_rendered(self) -> None:
        expected_ids = {"TRIANGLE": "glyphTriangle", "CIRCLE": "glyphCircle", "CROSS": "glyphCross", "SQUARE": "glyphSquare"}
        canvas = Image.new("RGB", (400, 100), (7, 13, 23))
        for glyph, asset_id in expected_ids.items():
            self.assertEqual(UI.resolve_playstation_prompt_asset(glyph, TOKENS), PROMPT_RUNTIME[glyph])
            stats = UI.render_playstation_prompt_shield(canvas, (50, 50), 52, glyph, TOKENS)
            self.assertEqual(stats["visibleDiameter"], 52)
            self.assertIn(TOKENS["assets"][asset_id], str(stats["asset"]))
        self.assertEqual(UI.resolve_prompt("playstation", UI.InputAction.CONFIRM), "CROSS")
        self.assertEqual(UI.resolve_prompt("playstation", UI.InputAction.BACK), "TRIANGLE")
        self.assertNotIn("ellipse", UI.render_playstation_prompt_shield.__code__.co_names)

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
        self.assertEqual(TOKENS["menu"]["itemSpacing"], 82)

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
        selected = UI.SELECTED_ILLUMINATION
        locked = UI.MATERIAL_PALETTES["locked"]
        selected_span = sum(selected["thinRim"]) - sum(selected["opposingEdge"])
        locked_span = sum(locked["highlight"]) - sum(locked["opposing"])
        self.assertLess(locked_span, selected_span)

    def test_selected_state_uses_clipped_internal_illumination(self) -> None:
        font = UI._font(56, TOKENS, "bold")
        layers, _ = UI.build_material_text_layers("NEW GAME", font, "selected")
        illumination = UI.build_selected_illumination_masks(layers["glyph"], 1.0, "NEW GAME")
        for name in ("internal_light", "thin_edge", "hotspots"):
            self.assertIsNotNone(illumination[name].getbbox())
            escaped = UI.ImageChops.subtract(illumination[name], layers["glyph"])
            self.assertIsNone(escaped.getbbox(), f"{name} escaped glyph coverage")
        settings = UI.SELECTED_ILLUMINATION
        internal_energy = (
            sum(illumination["interior"].getdata()) * settings["amberTransitionOpacity"]
            + sum(illumination["internal_light"].getdata()) * settings["internalLightOpacity"]
            + sum(illumination["hotspots"].getdata()) * settings["hotspotOpacity"]
        )
        structural_energy = (
            sum(illumination["thin_edge"].getdata()) * settings["thinRimOpacity"]
            + sum(layers["opposing_bevel"].getdata()) * settings["opposingEdgeOpacity"]
        )
        self.assertGreater(internal_energy, structural_energy)

    def test_selected_state_has_independent_halo_and_no_bronze_inset(self) -> None:
        font = UI._font(56, TOKENS, "bold")
        canvas = Image.new("RGB", (500, 100), (7, 13, 23))
        stats = UI.render_material_text(canvas, (20, 10), "NEW GAME", font, "selected")
        self.assertIn("internal_light", stats)
        self.assertIn("hotspots", stats)
        self.assertIn("thin_edge", stats)
        self.assertNotIn("inset", stats)
        self.assertGreater(UI.SELECTED_ILLUMINATION["haloRadius"], 0)

    def test_unselected_pixel_baseline_is_preserved(self) -> None:
        font = UI._font(52, TOKENS, "regular")
        canvas = Image.new("RGB", (500, 100), (7, 13, 23))
        UI.render_material_text(canvas, (20, 10), "LOAD GAME", font, "unselected")
        self.assertEqual(
            hashlib.sha256(canvas.tobytes()).hexdigest(),
            "2ec52ee699316366116dec1803d859230936b7c6201584b50ab115192b7d6fa7",
        )

    def test_selected_and_locked_typography_baselines_are_preserved(self) -> None:
        selected = Image.new("RGB", (500, 100), (7, 13, 23))
        UI.render_material_text(selected, (20, 10), "NEW GAME", UI._font(56, TOKENS, "bold"), "selected")
        self.assertEqual(hashlib.sha256(selected.tobytes()).hexdigest(), "9ae1d673a299412f8b7d827435fcf1bbd3ec4e920ecb8456d2ccb7d0f1da61c1")
        locked = Image.new("RGB", (700, 100), (7, 13, 23))
        UI.render_material_text(locked, (20, 10), "SINGLE MISSION REPLAY", UI._font(52, TOKENS, "regular"), "locked")
        self.assertEqual(hashlib.sha256(locked.tobytes()).hexdigest(), "686906c1a92ee647371de644df4e80a0c8de29f648a5fde76eff8dc4d1883e01")

    def test_approved_pointer_assets_are_locked_and_active(self) -> None:
        self.assertEqual(hashlib.sha256(POINTER_SOURCE.read_bytes()).hexdigest(), "8938fde3105960d2db38b86c8914ea90e79474ad950e556b818d6059d4752833")
        self.assertEqual(hashlib.sha256(POINTER_RUNTIME.read_bytes()).hexdigest(), "c3c174f1fe035bb02d7c39eb43917c0c4ecbdb80056bd16ae8862631a1077425")
        self.assertEqual(TOKENS["assets"]["selectionMarker"], "pointer/approved/runtime/spartan-selection-pointer-approved.png")
        with Image.open(POINTER_RUNTIME) as pointer:
            self.assertEqual((pointer.format, pointer.mode, pointer.size), ("PNG", "RGBA", (1228, 282)))
            self.assertEqual(pointer.getchannel("A").getbbox(), (0, 0, 1228, 282))

    def test_old_procedural_pointer_is_inactive(self) -> None:
        self.assertFalse(hasattr(UI, "build_pointer_layers"))
        self.assertFalse(hasattr(UI, "POINTER_MATERIAL"))
        canvas = Image.new("RGB", (300, 100), (7, 13, 23))
        stats = UI.render_selection_pointer(canvas, (150, 50), 96, 22)
        self.assertTrue(str(stats["asset"]).endswith("spartan-selection-pointer-approved.png"))
        self.assertEqual((stats["renderedWidth"], stats["renderedHeight"]), (96, 22))

    def test_pointer_tip_remains_anchored_to_selected_item(self) -> None:
        layout = UI.layout_for_viewport(1920, 1080, TOKENS)
        new_state = UI.MenuState(UI.build_main_start(), "new_game")
        load_state = UI.MenuState(UI.build_main_start(), "load_game")
        self.assertEqual(UI.selected_pointer_tip_for_state(layout, new_state, TOKENS), (155.0, 375.0))
        self.assertEqual(UI.selected_pointer_tip_for_state(layout, load_state, TOKENS), (155.0, 457.0))

    def test_pointer_scale_and_alignment_are_resolution_independent(self) -> None:
        state = UI.MenuState(UI.build_main_start(), "load_game")
        tip_1080 = UI.selected_pointer_tip_for_state(UI.layout_for_viewport(1920, 1080, TOKENS), state, TOKENS)
        tip_4k = UI.selected_pointer_tip_for_state(UI.layout_for_viewport(3840, 2160, TOKENS), state, TOKENS)
        self.assertEqual(tip_4k, (tip_1080[0] * 2, tip_1080[1] * 2))
        self.assertEqual(TOKENS["menu"]["markerSize"], [96, 22])

    def test_selected_luminance_is_label_driven_not_new_game_special_cased(self) -> None:
        font = UI._font(56, TOKENS, "bold")
        fields = []
        for label in ("NEW GAME", "LOAD GAME"):
            layers, _ = UI.build_material_text_layers(label, font, "selected")
            illumination = UI.build_selected_illumination_masks(layers["glyph"], 1.0, label)
            self.assertIsNotNone(illumination["internal_light"].getbbox())
            fields.append(hashlib.sha256(illumination["internal_light"].tobytes()).hexdigest())
        self.assertNotEqual(fields[0], fields[1])


if __name__ == "__main__":
    unittest.main()
