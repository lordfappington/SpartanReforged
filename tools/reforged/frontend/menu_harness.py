#!/usr/bin/env python3
"""Interactive Windows development harness for the shared Reforged main menu."""

from __future__ import annotations

import argparse
from collections import OrderedDict
import json
import math
import os
import pathlib
import random
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
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


class FacePosition(str, Enum):
    """SDL face-button positions, independent of controller branding."""

    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTH = "north"


class PlayStationFace(str, Enum):
    """PlayStation-equivalent symbols used by Reforged semantics and art."""

    CROSS = "CROSS"
    CIRCLE = "CIRCLE"
    SQUARE = "SQUARE"
    TRIANGLE = "TRIANGLE"


@dataclass(frozen=True)
class FaceButtonMapping:
    position: FacePosition
    playstation_face: PlayStationFace
    menu_action: ui.InputAction | None


FACE_BUTTON_POSITIONS = {
    0: FacePosition.SOUTH,
    1: FacePosition.EAST,
    2: FacePosition.WEST,
    3: FacePosition.NORTH,
}
PLAYSTATION_EQUIVALENTS = {
    FacePosition.SOUTH: PlayStationFace.CROSS,
    FacePosition.EAST: PlayStationFace.CIRCLE,
    FacePosition.WEST: PlayStationFace.SQUARE,
    FacePosition.NORTH: PlayStationFace.TRIANGLE,
}
CURRENT_MENU_FACE_ACTIONS = {
    FacePosition.SOUTH: ui.InputAction.CONFIRM,
    FacePosition.NORTH: ui.InputAction.BACK,
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
    if is_playstation:
        return "playstation"
    xbox_terms = ("xbox", "xinput")
    return "xbox" if any(term in normalized for term in xbox_terms) else "generic"


def controller_face_mapping(button: int) -> FaceButtonMapping | None:
    """Map an SDL face-button index through position, glyph, and menu meaning."""
    position = FACE_BUTTON_POSITIONS.get(button)
    if position is None:
        return None
    return FaceButtonMapping(
        position,
        PLAYSTATION_EQUIVALENTS[position],
        CURRENT_MENU_FACE_ACTIONS.get(position),
    )


def prompt_profile_for_input_profile(profile: str) -> str:
    """All controllers use approved PlayStation shield presentation."""
    return "keyboard" if profile == "keyboard" else "playstation"


def controller_button_action(profile: str, button: int) -> ui.InputAction | None:
    # The profile is deliberately presentation/diagnostic metadata only. Face
    # semantics follow physical position identically across controller brands.
    del profile
    face = controller_face_mapping(button)
    if face is not None:
        return face.menu_action
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


def ease_out_cubic(progress: float) -> float:
    clamped = max(0.0, min(1.0, progress))
    return 1.0 - (1.0 - clamped) ** 3


def particle_emission_bounds(selected_index: int, tokens: dict) -> tuple[float, float, float, float]:
    """Return the soft selected-row concentration region in design pixels."""
    effects = tokens["selectionEffects"]
    menu_x, menu_y = tokens["menu"]["position"]
    centre_x = menu_x + 165
    centre_y = menu_y + selected_index * tokens["menu"]["itemSpacing"] + 34
    return (
        centre_x - effects["particleHorizontalRadius"],
        centre_y - effects["particleVerticalRadius"],
        centre_x + effects["particleHorizontalRadius"],
        centre_y + effects["particleVerticalRadius"],
    )


@dataclass
class SelectionParticle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    age: float
    lifetime: float
    peak_alpha: int
    colour: tuple[int, int, int]


class AnimatedSelectionEffects:
    """Small dynamic overlay; the expensive menu composition remains cached."""

    def __init__(self, tokens: dict, strings: dict[str, str], reduced_motion: bool = False) -> None:
        self.tokens = tokens
        self.strings = strings
        self.reduced_motion = reduced_motion
        self.rng = random.Random(0x53504152)
        self.particles: list[SelectionParticle] = []
        self.spawn_accumulator = 0.0
        self.last_update: float | None = None
        self.transition_start = 0.0
        self.pointer_from: tuple[float, float] | None = None
        self.pointer_to: tuple[float, float] | None = None
        self.previous_selected_id: str | None = None
        self.text_cache: OrderedDict[tuple, tuple[pygame.Surface, tuple[int, int]]] = OrderedDict()
        self.pointer_cache: dict[tuple[int, int], pygame.Surface] = {}
        self.last_frame_ms = 0.0

    def clear_resolution_cache(self) -> None:
        self.text_cache.clear()
        self.pointer_cache.clear()

    def _layout(self, virtual_size: tuple[int, int]) -> ui.ViewportLayout:
        return ui.layout_for_viewport(*virtual_size, self.tokens)

    def _tip_for_id(self, selected_id: str, virtual_size: tuple[int, int], screen: ui.MenuScreen) -> tuple[float, float]:
        state = ui.MenuState(screen, selected_id)
        return ui.selected_pointer_tip_for_state(self._layout(virtual_size), state, self.tokens)

    def pointer_tip(self, now: float) -> tuple[float, float] | None:
        if self.pointer_to is None:
            return None
        if self.reduced_motion or self.pointer_from is None:
            return self.pointer_to
        duration = self.tokens["menu"]["transitionDurationMs"] / 1000.0
        progress = ease_out_cubic((now - self.transition_start) / duration)
        return (
            self.pointer_from[0] + (self.pointer_to[0] - self.pointer_from[0]) * progress,
            self.pointer_from[1] + (self.pointer_to[1] - self.pointer_from[1]) * progress,
        )

    def set_initial_selection(self, state: ui.MenuState, virtual_size: tuple[int, int], now: float) -> None:
        self.pointer_to = self._tip_for_id(state.selected_id, virtual_size, state.screen)
        self.pointer_from = self.pointer_to
        self.transition_start = now

    def selection_changed(
        self, previous_id: str, state: ui.MenuState, virtual_size: tuple[int, int], now: float
    ) -> None:
        current = self.pointer_tip(now)
        self.pointer_from = current or self._tip_for_id(previous_id, virtual_size, state.screen)
        self.pointer_to = self._tip_for_id(state.selected_id, virtual_size, state.screen)
        self.transition_start = now
        self.previous_selected_id = previous_id

    def _spawn_particle(self, state: ui.MenuState) -> None:
        index = next(i for i, item in enumerate(state.screen.items) if item.semantic_id == state.selected_id)
        left, top, right, bottom = particle_emission_bounds(index, self.tokens)
        effects = self.tokens["selectionEffects"]
        # Triangular distributions naturally concentrate the cloud at the row.
        x = self.rng.triangular(left, right, (left + right) / 2)
        y = self.rng.triangular(top, bottom, (top + bottom) / 2)
        life_min, life_max = effects["particleLifetimeSeconds"]
        drift_min, drift_max = effects["particleDriftPerSecond"]
        rise_min, rise_max = effects["particleRisePerSecond"]
        radius_min, radius_max = effects["particleRadius"]
        alpha_min, alpha_max = effects["particleAlpha"]
        warmth = self.rng.random()
        self.particles.append(SelectionParticle(
            x=x, y=y,
            vx=self.rng.uniform(drift_min, drift_max),
            vy=-self.rng.uniform(rise_min, rise_max),
            radius=self.rng.uniform(radius_min, radius_max),
            age=0.0, lifetime=self.rng.uniform(life_min, life_max),
            peak_alpha=round(self.rng.uniform(alpha_min, alpha_max)),
            colour=(255, round(188 + warmth * 49), round(83 + warmth * 91)),
        ))

    def update(self, state: ui.MenuState, now: float) -> None:
        if self.last_update is None:
            self.last_update = now
            return
        dt = min(.05, max(0.0, now - self.last_update))
        self.last_update = now
        for particle in self.particles:
            particle.age += dt
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
        self.particles = [particle for particle in self.particles if particle.age < particle.lifetime]
        if self.reduced_motion:
            self.particles.clear()
            return
        effects = self.tokens["selectionEffects"]
        self.spawn_accumulator += dt * effects["particleSpawnRate"]
        maximum = effects["particleMaximum"]
        while self.spawn_accumulator >= 1.0 and len(self.particles) < maximum:
            self._spawn_particle(state)
            self.spawn_accumulator -= 1.0

    def _text_surface(
        self, item: ui.MenuItem, virtual_size: tuple[int, int], effect_time: float
    ) -> tuple[pygame.Surface, tuple[int, int]]:
        layout = self._layout(virtual_size)
        fps = self.tokens["selectionEffects"]["textFrameRate"]
        quantized = 0.0 if self.reduced_motion else math.floor(effect_time * fps) / fps
        key = (virtual_size, item.semantic_id, quantized, self.reduced_motion)
        cached = self.text_cache.get(key)
        if cached is not None:
            self.text_cache.move_to_end(key)
            return cached
        font = ui._font(
            round(self.tokens["typography"]["MenuPrimarySelected"] * layout.scale),
            self.tokens, "bold",
        )
        tile, offset = ui.render_selected_text_tile(
            self.strings[item.label_key], font, layout.scale, quantized, self.reduced_motion
        )
        surface = pygame.image.frombytes(tile.tobytes(), tile.size, "RGBA").convert_alpha()
        result = (surface, offset)
        self.text_cache[key] = result
        maximum = self.tokens["selectionEffects"]["textCacheFrames"]
        while len(self.text_cache) > maximum:
            self.text_cache.popitem(last=False)
        return result

    def _pointer_surface(self, virtual_size: tuple[int, int]) -> pygame.Surface:
        cached = self.pointer_cache.get(virtual_size)
        if cached is not None:
            return cached
        layout = self._layout(virtual_size)
        path = ui.resolve_asset_path("selectionMarker", self.tokens)
        if path is None:
            raise FileNotFoundError("approved selection pointer is unavailable")
        source = pygame.image.load(str(path)).convert_alpha()
        width, height = self.tokens["menu"]["markerSize"]
        size = (max(1, round(width * layout.scale)), max(1, round(height * layout.scale)))
        rendered = pygame.transform.smoothscale(source, size)
        self.pointer_cache[virtual_size] = rendered
        return rendered

    @staticmethod
    def _map_point(point: tuple[float, float], destination: pygame.Rect, virtual_size: tuple[int, int]) -> tuple[float, float]:
        return (
            destination.x + point[0] * destination.width / virtual_size[0],
            destination.y + point[1] * destination.height / virtual_size[1],
        )

    def draw(
        self, target: pygame.Surface, destination: pygame.Rect,
        state: ui.MenuState, virtual_size: tuple[int, int], now: float,
    ) -> None:
        started = time.perf_counter()
        self.update(state, now)
        layout = self._layout(virtual_size)
        bounds_top_left = self._map_point(layout.point(35, 270), destination, virtual_size)
        bounds_bottom_right = self._map_point(layout.point(920, 850), destination, virtual_size)
        overlay_rect = pygame.Rect(
            math.floor(bounds_top_left[0]), math.floor(bounds_top_left[1]),
            max(1, math.ceil(bounds_bottom_right[0] - bounds_top_left[0])),
            max(1, math.ceil(bounds_bottom_right[1] - bounds_top_left[1])),
        )
        overlay = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
        for particle in self.particles:
            progress = particle.age / particle.lifetime
            alpha = round(particle.peak_alpha * math.sin(math.pi * progress))
            centre = self._map_point(layout.point(particle.x, particle.y), destination, virtual_size)
            scale = destination.width / virtual_size[0] * layout.scale
            radius = max(1, round(particle.radius * scale))
            pygame.draw.circle(
                overlay, (*particle.colour, alpha),
                (round(centre[0] - overlay_rect.x), round(centre[1] - overlay_rect.y)), radius,
            )

        def blit_selected(item: ui.MenuItem, opacity: float) -> None:
            if item.locked or opacity <= 0:
                return
            tile, offset = self._text_surface(item, virtual_size, now)
            index = next(i for i, candidate in enumerate(state.screen.items) if candidate.semantic_id == item.semantic_id)
            menu_x, menu_y = self.tokens["menu"]["position"]
            virtual_position = layout.point(menu_x, menu_y + index * self.tokens["menu"]["itemSpacing"])
            virtual_position = (virtual_position[0] + offset[0], virtual_position[1] + offset[1])
            mapped = self._map_point(virtual_position, destination, virtual_size)
            ratio = destination.width / virtual_size[0]
            displayed = tile.copy() if abs(ratio - 1.0) < 1e-6 else pygame.transform.smoothscale(
                tile, (max(1, round(tile.width * ratio)), max(1, round(tile.height * ratio)))
            )
            displayed.set_alpha(round(255 * max(0.0, min(1.0, opacity))))
            overlay.blit(displayed, (round(mapped[0] - overlay_rect.x), round(mapped[1] - overlay_rect.y)))

        selected = state.selected
        fade_duration = self.tokens["selectionEffects"]["textFadeInMs"] / 1000.0
        fade = 1.0 if self.reduced_motion else min(1.0, (now - self.transition_start) / fade_duration)
        fade = ease_out_cubic(fade)
        if self.previous_selected_id and fade < 1.0:
            previous = next(
                item for item in state.screen.items if item.semantic_id == self.previous_selected_id
            )
            blit_selected(previous, 1.0 - fade)
        blit_selected(selected, fade)

        tip = self.pointer_tip(now)
        if tip is not None:
            mapped_tip = self._map_point(tip, destination, virtual_size)
            pointer = self._pointer_surface(virtual_size)
            ratio = destination.width / virtual_size[0]
            displayed_pointer = pointer if abs(ratio - 1.0) < 1e-6 else pygame.transform.smoothscale(
                pointer, (max(1, round(pointer.width * ratio)), max(1, round(pointer.height * ratio)))
            )
            overlay.blit(
                displayed_pointer,
                (round(mapped_tip[0] - displayed_pointer.width - overlay_rect.x),
                 round(mapped_tip[1] - displayed_pointer.height / 2 - overlay_rect.y)),
            )
        target.blit(overlay, overlay_rect.topleft)
        self.last_frame_ms = (time.perf_counter() - started) * 1000.0


class MenuHarness:
    def __init__(
        self, smoke_test: bool = False, smoke_report: pathlib.Path | None = None,
        reduced_motion: bool = False,
    ) -> None:
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
        self.effects = AnimatedSelectionEffects(self.tokens, self.strings, reduced_motion)
        self.running = True
        self.smoke_test = smoke_test
        self.smoke_report = smoke_report
        self.smoke_started = 0.0
        self.smoke_navigation_step = 0
        self.smoke_result = {"windowInitialized": True, "rendererInitialized": False, "assetsLoaded": False, "navigationVerified": False, "cleanShutdown": False}
        self.effect_frame_samples: list[float] = []
        self._discover_joysticks()
        self.effects.set_initial_selection(self.state, self.virtual_size, time.perf_counter())
        self._prewarm_current_context()
        self.smoke_started = time.perf_counter()

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
            self.effects.selection_changed(previous, self.state, self.virtual_size, time.perf_counter())
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
        self.effects.clear_resolution_cache()
        self.effects.set_initial_selection(self.state, self.virtual_size, time.perf_counter())
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
                profile = controller_profile(joystick.get_name()) if joystick else "generic"
                face = controller_face_mapping(event.button)
                action = controller_button_action(profile, event.button)
                if face is not None or action in (ui.InputAction.UP, ui.InputAction.DOWN):
                    self.last_profile = profile
                    self.frame_dirty = True
                if action in (ui.InputAction.CONFIRM, ui.InputAction.BACK):
                    self._apply_action(action)

    def _frame_key(self, state: ui.MenuState) -> tuple[tuple[int, int], int, str, str]:
        prompt_profile = prompt_profile_for_input_profile(self.last_profile)
        return self.virtual_size, self.maxlevel, prompt_profile, state.selected_id

    def _render_state_surface(self, state: ui.MenuState) -> pygame.Surface:
        frame = ui.render_wireframe(
            *self.virtual_size, state, self.tokens, self.strings,
            profile=prompt_profile_for_input_profile(self.last_profile),
            include_selected_effects=False,
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
                f"selection effects {self.effects.last_frame_ms:5.2f} ms / reduced motion {self.effects.reduced_motion}",
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
        self.effects.draw(self.screen, destination, self.state, self.virtual_size, time.perf_counter())
        self.effect_frame_samples.append(self.effects.last_frame_ms)
        if len(self.effect_frame_samples) > 600:
            del self.effect_frame_samples[:300]
        self._draw_overlay(destination)
        pygame.display.flip()

    def _run_smoke_automation(self, now: float) -> None:
        elapsed = now - self.smoke_started
        sequence = (
            (.25, ui.InputAction.DOWN, "load_game"),
            (.42, ui.InputAction.DOWN, "options"),
            (.59, ui.InputAction.UP, "load_game"),
            (.76, ui.InputAction.DOWN, "options"),
        )
        while self.smoke_navigation_step < len(sequence):
            due, action, expected = sequence[self.smoke_navigation_step]
            if elapsed < due:
                break
            self._navigate(action)
            self.smoke_result["navigationVerified"] = self.state.selected_id == expected
            self.smoke_navigation_step += 1
        if elapsed >= 1.20:
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
            if self.effect_frame_samples:
                ordered = sorted(self.effect_frame_samples)
                self.smoke_result["selectionEffectsAverageMs"] = round(
                    sum(ordered) / len(ordered), 3
                )
                self.smoke_result["selectionEffectsP95Ms"] = round(
                    ordered[min(len(ordered) - 1, round((len(ordered) - 1) * .95))], 3
                )
                self.smoke_result["selectionEffectsMaximumMs"] = round(ordered[-1], 3)
            if self.smoke_report:
                self.smoke_report.parent.mkdir(parents=True, exist_ok=True)
                self.smoke_report.write_text(json.dumps(self.smoke_result, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="render, navigate once, then exit")
    parser.add_argument("--smoke-report", type=pathlib.Path)
    parser.add_argument("--reduced-motion", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    return MenuHarness(args.smoke_test, args.smoke_report, args.reduced_motion).run()


if __name__ == "__main__":
    raise SystemExit(main())
