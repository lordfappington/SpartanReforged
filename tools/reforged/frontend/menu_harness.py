#!/usr/bin/env python3
"""Interactive Windows development harness for the shared Reforged main menu."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from dataclasses import dataclass, field
from typing import Iterable

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

import main_menu_reforged as ui


RESOURCE_ROOT = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parents[3]))
ASSET_ROOT = RESOURCE_ROOT / "assets/reforged/frontend/main-menu"
TOKENS_PATH = ASSET_ROOT / "main_menu_tokens.json"
LOCALE_PATH = ASSET_ROOT / "locales/en.json"
ui.ROOT = RESOURCE_ROOT
ui.DEFAULT_TOKENS = TOKENS_PATH
ui.DEFAULT_LOCALE = LOCALE_PATH

TARGET_FPS = 60
REPEAT_INITIAL_DELAY_SECONDS = 0.32
REPEAT_INTERVAL_SECONDS = 0.115
AXIS_PRESS_THRESHOLD = 0.55
ACTION_NOTICE_SECONDS = 1.6
DESIGN_SIZE = (1920, 1080)
RESOLUTION_PRESETS = {
    pygame.K_F1: (1920, 1080),
    pygame.K_F2: (2560, 1440),
    pygame.K_F3: (3840, 2160),
    pygame.K_F4: (2560, 1080),
}


@dataclass
class InputRepeater:
    initial_delay: float = REPEAT_INITIAL_DELAY_SECONDS
    interval: float = REPEAT_INTERVAL_SECONDS
    held: dict[tuple[str, ui.InputAction], float] = field(default_factory=dict)

    def press(self, source: str, action: ui.InputAction, now: float) -> list[ui.InputAction]:
        key = (source, action)
        if key in self.held:
            return []
        self.held[key] = now + self.initial_delay
        return [action]

    def release(self, source: str, action: ui.InputAction) -> None:
        self.held.pop((source, action), None)

    def release_source(self, source: str) -> None:
        self.held = {key: value for key, value in self.held.items() if key[0] != source}

    def poll(self, now: float) -> list[ui.InputAction]:
        actions: list[ui.InputAction] = []
        for key, due in tuple(self.held.items()):
            if now < due:
                continue
            actions.append(key[1])
            while due <= now:
                due += self.interval
            self.held[key] = due
        return actions


def controller_profile(name: str) -> str:
    normalized = name.casefold()
    playstation_terms = ("dualsense", "dualshock", "playstation", "sony", "ps4", "ps5")
    is_playstation = normalized.strip() == "wireless controller" or any(
        term in normalized for term in playstation_terms
    )
    return "playstation" if is_playstation else "xbox"


def controller_button_action(profile: str, button: int) -> ui.InputAction | None:
    if button == 0:
        return ui.InputAction.CONFIRM
    if profile == "playstation" and button == 3:
        return ui.InputAction.BACK
    if profile != "playstation" and button == 1:
        return ui.InputAction.BACK
    if button == 11:
        return ui.InputAction.UP
    if button == 12:
        return ui.InputAction.DOWN
    return None


def fit_window_size(target: tuple[int, int], desktop: tuple[int, int]) -> tuple[int, int]:
    max_width = max(640, round(desktop[0] * .90))
    max_height = max(360, round(desktop[1] * .86))
    ratio = min(1.0, max_width / target[0], max_height / target[1])
    return max(640, round(target[0] * ratio)), max(360, round(target[1] * ratio))


def _scaled_destination(source_size: tuple[int, int], target_size: tuple[int, int]) -> pygame.Rect:
    ratio = min(target_size[0] / source_size[0], target_size[1] / source_size[1])
    width, height = round(source_size[0] * ratio), round(source_size[1] * ratio)
    return pygame.Rect((target_size[0] - width) // 2, (target_size[1] - height) // 2, width, height)


class MenuHarness:
    def __init__(self, smoke_test: bool = False, smoke_report: pathlib.Path | None = None) -> None:
        pygame.init()
        pygame.joystick.init()
        self.tokens = ui.load_json(TOKENS_PATH)
        self.strings = ui.load_json(LOCALE_PATH)["strings"]
        self.maxlevel = 0
        self.state = ui.MenuState(ui.build_main_start(self.maxlevel), "new_game")
        self.virtual_size = DESIGN_SIZE
        desktop_sizes = pygame.display.get_desktop_sizes()
        self.desktop_size = desktop_sizes[0] if desktop_sizes else DESIGN_SIZE
        self.fullscreen = False
        self.screen = self._create_window()
        pygame.display.set_caption("SpartanReforged — Main Menu Development Harness")
        self.clock = pygame.time.Clock()
        self.repeater = InputRepeater()
        self.controller_direction: ui.InputAction | None = None
        self.joysticks: dict[int, pygame.joystick.JoystickType] = {}
        self.last_profile = "keyboard"
        self.last_action = "READY"
        self.notice_until = 0.0
        self.hud_enabled = False
        self.frame_dirty = True
        self.frame_surface: pygame.Surface | None = None
        self.frame_cache: dict[tuple[tuple[int, int], int, str, str], pygame.Surface] = {}
        self.running = True
        self.smoke_test = smoke_test
        self.smoke_report = smoke_report
        self.smoke_started = time.perf_counter()
        self.smoke_navigation_sent = False
        self.smoke_result = {"windowInitialized": True, "rendererInitialized": False, "assetsLoaded": False, "navigationVerified": False, "cleanShutdown": False}
        self._discover_joysticks()
        self._prewarm_current_context()

    def _create_window(self) -> pygame.Surface:
        if self.fullscreen:
            return pygame.display.set_mode(self.desktop_size, pygame.NOFRAME | pygame.DOUBLEBUF, vsync=1)
        physical = fit_window_size(self.virtual_size, self.desktop_size)
        return pygame.display.set_mode(physical, pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1)

    def _discover_joysticks(self) -> None:
        for index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(index)
            joystick.init()
            self.joysticks[joystick.get_instance_id()] = joystick
        if self.joysticks:
            self.last_profile = controller_profile(next(iter(self.joysticks.values())).get_name())

    def _add_joystick(self, device_index: int) -> None:
        joystick = pygame.joystick.Joystick(device_index)
        joystick.init()
        self.joysticks[joystick.get_instance_id()] = joystick

    def _set_notice(self, text: str) -> None:
        self.last_action = text
        self.notice_until = time.perf_counter() + ACTION_NOTICE_SECONDS

    def _navigate(self, action: ui.InputAction) -> None:
        previous = self.state.selected_id
        self.state = self.state.navigate(action)
        if self.state.selected_id != previous:
            self._set_notice(f"SELECT: {self.state.selected_id.upper()}")
            self.frame_dirty = True

    def _confirm(self) -> None:
        action = self.state.confirm()
        if action is None:
            self._set_notice("LOCKED ACTION REJECTED")
        else:
            self._set_notice(f"CONFIRM: {action.value}")

    def _back(self) -> None:
        self._set_notice("BACK")

    def _apply_action(self, action: ui.InputAction) -> None:
        if action in (ui.InputAction.UP, ui.InputAction.DOWN):
            self._navigate(action)
        elif action is ui.InputAction.CONFIRM:
            self._confirm()
        elif action is ui.InputAction.BACK:
            self._back()

    def _toggle_maxlevel(self) -> None:
        self.maxlevel = 0 if self.maxlevel else 1
        self.state = ui.MenuState(ui.build_main_start(self.maxlevel), self.state.selected_id)
        self._set_notice(f"DEV MAXLEVEL: {self.maxlevel}")
        self.frame_dirty = True
        self._prewarm_current_context()

    def _toggle_fullscreen(self) -> None:
        self.fullscreen = not self.fullscreen
        self.screen = self._create_window()
        self._set_notice("BORDERLESS FULLSCREEN" if self.fullscreen else "WINDOWED")

    def _set_resolution(self, size: tuple[int, int]) -> None:
        self.virtual_size = size
        if not self.fullscreen:
            self.screen = self._create_window()
        self._set_notice(f"LOGICAL VIEWPORT: {size[0]}x{size[1]}")
        self.frame_dirty = True
        self._prewarm_current_context()

    def _keyboard_action(self, key: int) -> ui.InputAction | None:
        if key in (pygame.K_UP, pygame.K_w):
            return ui.InputAction.UP
        if key in (pygame.K_DOWN, pygame.K_s):
            return ui.InputAction.DOWN
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            return ui.InputAction.CONFIRM
        if key == pygame.K_ESCAPE:
            return ui.InputAction.BACK
        return None

    def _handle_keydown(self, event: pygame.event.Event, now: float) -> None:
        if event.key == pygame.K_F10:
            self.running = False
            return
        if event.key in (pygame.K_F11, pygame.K_RETURN) and (event.key == pygame.K_F11 or event.mod & pygame.KMOD_ALT):
            self._toggle_fullscreen()
            return
        if event.key == pygame.K_F6:
            self._toggle_maxlevel()
            return
        if event.key == pygame.K_F8:
            self.hud_enabled = not self.hud_enabled
            return
        if event.key in RESOLUTION_PRESETS:
            self._set_resolution(RESOLUTION_PRESETS[event.key])
            return
        action = self._keyboard_action(event.key)
        if action is None:
            return
        self.last_profile = "keyboard"
        self.frame_dirty = True
        if action in (ui.InputAction.UP, ui.InputAction.DOWN):
            for repeated in self.repeater.press("keyboard", action, now):
                self._apply_action(repeated)
        elif not getattr(event, "repeat", False):
            self._apply_action(action)

    def _handle_keyup(self, event: pygame.event.Event) -> None:
        action = self._keyboard_action(event.key)
        if action in (ui.InputAction.UP, ui.InputAction.DOWN):
            self.repeater.release("keyboard", action)

    def _controller_nav(self) -> tuple[ui.InputAction | None, str | None]:
        for joystick in self.joysticks.values():
            profile = controller_profile(joystick.get_name())
            for hat_index in range(joystick.get_numhats()):
                y = joystick.get_hat(hat_index)[1]
                if y > 0:
                    return ui.InputAction.UP, profile
                if y < 0:
                    return ui.InputAction.DOWN, profile
            if joystick.get_numaxes() > 1:
                axis = joystick.get_axis(1)
                if axis < -AXIS_PRESS_THRESHOLD:
                    return ui.InputAction.UP, profile
                if axis > AXIS_PRESS_THRESHOLD:
                    return ui.InputAction.DOWN, profile
            if joystick.get_numbuttons() > 12:
                if joystick.get_button(11):
                    return ui.InputAction.UP, profile
                if joystick.get_button(12):
                    return ui.InputAction.DOWN, profile
        return None, None

    def _update_controller_repeat(self, now: float) -> None:
        direction, profile = self._controller_nav()
        if direction == self.controller_direction:
            return
        if self.controller_direction is not None:
            self.repeater.release("controller", self.controller_direction)
        self.controller_direction = direction
        if direction is not None:
            if profile and profile != self.last_profile:
                self.last_profile = profile
                self.frame_dirty = True
            for action in self.repeater.press("controller", direction, now):
                self._apply_action(action)

    def _process_events(self, now: float) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.screen = pygame.display.set_mode((max(640, event.w), max(360, event.h)), pygame.RESIZABLE | pygame.DOUBLEBUF)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event, now)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event)
            elif event.type == pygame.JOYDEVICEADDED:
                self._add_joystick(event.device_index)
            elif event.type == pygame.JOYDEVICEREMOVED:
                self.joysticks.pop(event.instance_id, None)
                self.repeater.release_source("controller")
                self.controller_direction = None
            elif event.type == pygame.JOYBUTTONDOWN:
                joystick = self.joysticks.get(event.instance_id)
                profile = controller_profile(joystick.get_name()) if joystick else "xbox"
                action = controller_button_action(profile, event.button)
                if action in (ui.InputAction.CONFIRM, ui.InputAction.BACK):
                    self.last_profile = profile
                    self.frame_dirty = True
                    self._apply_action(action)

    def _frame_key(self, state: ui.MenuState) -> tuple[tuple[int, int], int, str, str]:
        return self.virtual_size, self.maxlevel, self.last_profile, state.selected_id

    def _render_state_surface(self, state: ui.MenuState) -> pygame.Surface:
        frame = ui.render_wireframe(
            *self.virtual_size, state, self.tokens, self.strings,
            profile=self.last_profile,
        )
        return pygame.image.frombytes(frame.tobytes(), frame.size, "RGB").convert()

    def _prewarm_current_context(self) -> None:
        """Cache all six shared-renderer states for responsive navigation."""
        self.frame_cache.clear()
        for item in self.state.screen.items:
            state = ui.MenuState(self.state.screen, item.semantic_id, self.state.presentation)
            self.frame_cache[self._frame_key(state)] = self._render_state_surface(state)
        self.frame_surface = self.frame_cache[self._frame_key(self.state)]
        self.frame_dirty = False
        self.smoke_result["rendererInitialized"] = True
        self.smoke_result["assetsLoaded"] = True

    def _render_shared_frame(self) -> None:
        key = self._frame_key(self.state)
        self.frame_surface = self.frame_cache.get(key)
        if self.frame_surface is None:
            self.frame_surface = self._render_state_surface(self.state)
            self.frame_cache[key] = self.frame_surface
        self.frame_dirty = False
        self.smoke_result["rendererInitialized"] = True
        self.smoke_result["assetsLoaded"] = True

    def _draw_overlay(self, destination: pygame.Rect) -> None:
        now = time.perf_counter()
        font = pygame.font.Font(None, 24)
        lines: list[str] = []
        if now < self.notice_until:
            lines.append(f"DEV — {self.last_action}")
        if self.hud_enabled:
            mode = "BORDERLESS" if self.fullscreen else "WINDOWED"
            lines.extend((
                f"FPS {self.clock.get_fps():5.1f}",
                f"window {self.screen.get_width()}x{self.screen.get_height()} / logical {self.virtual_size[0]}x{self.virtual_size[1]}",
                f"selected {self.state.selected_id} / action {self.last_action}",
                f"profile {self.last_profile} / maxlevel {self.maxlevel} / {mode}",
            ))
        if not lines:
            return
        rendered = [font.render(line, True, (235, 225, 199)) for line in lines]
        width = max(line.get_width() for line in rendered) + 20
        height = sum(line.get_height() + 3 for line in rendered) + 12
        panel = pygame.Surface((width, height), pygame.SRCALPHA)
        panel.fill((3, 7, 12, 190))
        y = 6
        for line in rendered:
            panel.blit(line, (10, y)); y += line.get_height() + 3
        self.screen.blit(panel, (destination.right - width - 14, destination.top + 14))

    def _draw(self) -> None:
        if self.frame_dirty or self.frame_surface is None:
            self._render_shared_frame()
        self.screen.fill((0, 0, 0))
        destination = _scaled_destination(self.virtual_size, self.screen.get_size())
        if destination.size == self.frame_surface.get_size():
            displayed = self.frame_surface
        else:
            displayed = pygame.transform.smoothscale(self.frame_surface, destination.size)
        self.screen.blit(displayed, destination)
        self._draw_overlay(destination)
        pygame.display.flip()

    def _run_smoke_automation(self, now: float) -> None:
        elapsed = now - self.smoke_started
        if elapsed >= .25 and not self.smoke_navigation_sent:
            self._navigate(ui.InputAction.DOWN)
            self.smoke_result["navigationVerified"] = self.state.selected_id == "load_game"
            self.smoke_navigation_sent = True
        if elapsed >= .80:
            self.running = False

    def run(self) -> int:
        try:
            while self.running:
                now = time.perf_counter()
                self._process_events(now)
                self._update_controller_repeat(now)
                for action in self.repeater.poll(now):
                    self._apply_action(action)
                if self.smoke_test:
                    self._run_smoke_automation(now)
                self._draw()
                self.clock.tick(TARGET_FPS)
            self.smoke_result["cleanShutdown"] = True
            return 0
        finally:
            pygame.quit()
            if self.smoke_report:
                self.smoke_report.parent.mkdir(parents=True, exist_ok=True)
                self.smoke_report.write_text(json.dumps(self.smoke_result, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="render, navigate once, then exit")
    parser.add_argument("--smoke-report", type=pathlib.Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    return MenuHarness(args.smoke_test, args.smoke_report).run()


if __name__ == "__main__":
    raise SystemExit(main())
