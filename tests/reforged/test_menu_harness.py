"""Deterministic tests for the interactive menu adapter."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "tools/reforged/frontend"
sys.path.insert(0, str(FRONTEND))
SPEC = importlib.util.spec_from_file_location("menu_harness", FRONTEND / "menu_harness.py")
assert SPEC and SPEC.loader
HARNESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HARNESS
SPEC.loader.exec_module(HARNESS)
UI = HARNESS.ui


class MenuHarnessTests(unittest.TestCase):
    def test_navigation_wrap_and_semantic_confirm(self) -> None:
        state = UI.MenuState(UI.build_main_start(maxlevel=1), "new_game")
        self.assertEqual(state.navigate(UI.InputAction.UP).selected_id, "extras")
        self.assertEqual(state.navigate(UI.InputAction.DOWN).selected_id, "load_game")
        self.assertEqual(state.confirm(), UI.MenuAction.NEW_GAME)

    def test_locked_and_unlocked_replay_confirmation(self) -> None:
        locked = UI.MenuState(UI.build_main_start(maxlevel=0), "single_mission_replay")
        unlocked = UI.MenuState(UI.build_main_start(maxlevel=1), "single_mission_replay")
        self.assertIsNone(locked.confirm())
        self.assertEqual(unlocked.confirm(), UI.MenuAction.SINGLE_MISSION_REPLAY)

    def test_navigation_repeat_has_immediate_delay_and_interval(self) -> None:
        repeat = HARNESS.InputRepeater(initial_delay=.32, interval=.115)
        self.assertEqual(repeat.press("keyboard", UI.InputAction.DOWN, 1.0), [UI.InputAction.DOWN])
        self.assertEqual(repeat.press("keyboard", UI.InputAction.DOWN, 1.1), [])
        self.assertEqual(repeat.poll(1.319), [])
        self.assertEqual(repeat.poll(1.320), [UI.InputAction.DOWN])
        self.assertEqual(repeat.poll(1.434), [])
        self.assertEqual(repeat.poll(1.435), [UI.InputAction.DOWN])
        repeat.release("keyboard", UI.InputAction.DOWN)
        self.assertEqual(repeat.poll(9.0), [])

    def test_confirm_and_back_are_keydown_edges(self) -> None:
        harness = object.__new__(HARNESS.MenuHarness)
        harness.last_profile = "keyboard"
        harness.frame_dirty = False
        harness.repeater = HARNESS.InputRepeater()
        harness._apply_action = mock.Mock()
        normal = type("Key", (), {"key": HARNESS.pygame.K_RETURN, "mod": 0, "repeat": False})()
        repeated = type("Key", (), {"key": HARNESS.pygame.K_RETURN, "mod": 0, "repeat": True})()
        harness._handle_keydown(normal, 1.0)
        harness._handle_keydown(repeated, 1.1)
        harness._apply_action.assert_called_once_with(UI.InputAction.CONFIRM)
        harness._apply_action.reset_mock()
        escape = type("Key", (), {"key": HARNESS.pygame.K_ESCAPE, "mod": 0, "repeat": False})()
        harness._handle_keydown(escape, 1.2)
        harness._apply_action.assert_called_once_with(UI.InputAction.BACK)

    def test_device_profiles_and_controller_semantics(self) -> None:
        self.assertEqual(HARNESS.controller_profile("Sony DualSense Wireless Controller"), "playstation")
        self.assertEqual(HARNESS.controller_profile("Xbox Wireless Controller"), "xbox")
        self.assertEqual(HARNESS.controller_button_action("playstation", 0), UI.InputAction.CONFIRM)
        self.assertEqual(HARNESS.controller_button_action("playstation", 3), UI.InputAction.BACK)
        self.assertEqual(HARNESS.controller_button_action("xbox", 0), UI.InputAction.CONFIRM)
        self.assertEqual(HARNESS.controller_button_action("xbox", 1), UI.InputAction.BACK)
        self.assertEqual(UI.development_prompt_symbol("keyboard", "ENTER"), "ENT")
        self.assertEqual(UI.development_prompt_symbol("keyboard", "ESCAPE"), "ESC")

    def test_maxlevel_debug_toggle_rebuilds_shared_screen(self) -> None:
        harness = object.__new__(HARNESS.MenuHarness)
        harness.maxlevel = 0
        harness.state = UI.MenuState(UI.build_main_start(0), "single_mission_replay")
        harness.frame_dirty = False
        harness._set_notice = mock.Mock()
        harness._prewarm_current_context = mock.Mock()
        harness._toggle_maxlevel()
        self.assertEqual(harness.maxlevel, 1)
        self.assertFalse(harness.state.selected.locked)
        self.assertTrue(harness.frame_dirty)
        harness._prewarm_current_context.assert_called_once_with()

    def test_resolution_presets_and_physical_clamping(self) -> None:
        self.assertEqual(set(HARNESS.RESOLUTION_PRESETS.values()), {
            (1920, 1080), (2560, 1440), (3840, 2160), (2560, 1080),
        })
        fitted = HARNESS.fit_window_size((3840, 2160), (1920, 1080))
        self.assertLessEqual(fitted[0], round(1920 * .90))
        self.assertLessEqual(fitted[1], round(1080 * .86))
        self.assertAlmostEqual(fitted[0] / fitted[1], 16 / 9, places=2)


if __name__ == "__main__":
    unittest.main()
