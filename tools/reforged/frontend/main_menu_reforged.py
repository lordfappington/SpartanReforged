#!/usr/bin/env python3
"""Deterministic, asset-free foundation for the Reforged main_start view.

The module deliberately has no dependency on extracted game data or the frozen
preservation renderer.  It consumes semantic state and localization, computes a
resolution-independent layout, and can draw development-only wireframes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import dataclass, replace
from enum import Enum, IntEnum
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = pathlib.Path(__file__).resolve().parents[3]
DEFAULT_TOKENS = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
DEFAULT_LOCALE = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
DEFAULT_OUTPUT = ROOT / "temp/reforged/main-menu-wireframes"


class PresentationMode(str, Enum):
    ORIGINAL = "original"
    REFORGED = "reforged"


class MenuAction(str, Enum):
    NEW_GAME = "NEW_GAME"
    LOAD_GAME = "LOAD_GAME"
    OPTIONS = "OPTIONS"
    ARENA_CHALLENGE = "ARENA_CHALLENGE"
    SINGLE_MISSION_REPLAY = "SINGLE_MISSION_REPLAY"
    EXTRAS = "EXTRAS"


class InputAction(str, Enum):
    CONFIRM = "CONFIRM"
    BACK = "BACK"
    UP = "UP"
    DOWN = "DOWN"


class RenderLayer(IntEnum):
    BACKGROUND_ENVIRONMENT = 0
    ATMOSPHERE_BACK = 1
    ORNAMENTAL_FRAME = 2
    FOREGROUND_ENVIRONMENT = 3
    LOGO = 4
    MENU_NAVIGATION = 5
    CONTEXT_DESCRIPTION = 6
    STATUS = 7
    INPUT_PROMPTS = 8
    FRONT_ATMOSPHERE = 9
    TRANSITIONS = 10


INPUT_PROFILES: dict[str, dict[InputAction, str]] = {
    "playstation": {
        InputAction.CONFIRM: "CROSS", InputAction.BACK: "TRIANGLE",
        InputAction.UP: "DPAD_UP", InputAction.DOWN: "DPAD_DOWN",
    },
    "xbox": {
        InputAction.CONFIRM: "A", InputAction.BACK: "B",
        InputAction.UP: "DPAD_UP", InputAction.DOWN: "DPAD_DOWN",
    },
    "keyboard": {
        InputAction.CONFIRM: "ENTER", InputAction.BACK: "ESCAPE",
        InputAction.UP: "ARROW_UP", InputAction.DOWN: "ARROW_DOWN",
    },
}

PLAYSTATION_PROMPT_ASSETS = {
    "TRIANGLE": "glyphTriangle",
    "CIRCLE": "glyphCircle",
    "CROSS": "glyphCross",
    "SQUARE": "glyphSquare",
}


@dataclass(frozen=True)
class MenuItem:
    semantic_id: str
    label_key: str
    heading_key: str
    body_key: str
    action: MenuAction
    enabled: bool = True
    locked: bool = False
    lock_condition: str | None = None
    up_id: str | None = None
    down_id: str | None = None


@dataclass(frozen=True)
class MenuPrompt:
    action: InputAction
    label_key: str


@dataclass(frozen=True)
class MenuScreen:
    semantic_id: str
    items: tuple[MenuItem, ...]
    prompts: tuple[MenuPrompt, ...]


@dataclass(frozen=True)
class AtmosphereEffect:
    semantic_id: str
    layer: RenderLayer
    max_instances: int
    opacity: float
    reduced_motion_instances: int
    excludes_ui_safe_regions: bool = True


def default_atmosphere_effects() -> tuple[AtmosphereEffect, ...]:
    """Return restrained budgets; these are behavior placeholders, not art."""
    return (
        AtmosphereEffect("mist_back", RenderLayer.ATMOSPHERE_BACK, 3, 0.18, 1),
        AtmosphereEffect("smoke_back", RenderLayer.ATMOSPHERE_BACK, 4, 0.14, 1),
        AtmosphereEffect("embers_front", RenderLayer.FRONT_ATMOSPHERE, 24, 0.32, 0),
        AtmosphereEffect("logo_glint", RenderLayer.FRONT_ATMOSPHERE, 1, 0.45, 0),
        AtmosphereEffect("selected_glow", RenderLayer.FRONT_ATMOSPHERE, 1, 0.28, 1),
    )


@dataclass(frozen=True)
class MenuState:
    screen: MenuScreen
    selected_id: str
    presentation: PresentationMode = PresentationMode.REFORGED

    @property
    def selected(self) -> MenuItem:
        return next(item for item in self.screen.items if item.semantic_id == self.selected_id)

    def navigate(self, action: InputAction) -> "MenuState":
        if action not in (InputAction.UP, InputAction.DOWN):
            return self
        target = self.selected.up_id if action is InputAction.UP else self.selected.down_id
        return replace(self, selected_id=target or self.selected_id)

    def confirm(self) -> MenuAction | None:
        item = self.selected
        return item.action if item.enabled and not item.locked else None


@dataclass(frozen=True)
class ViewportLayout:
    output_width: int
    output_height: int
    scale: float
    composition_x: float
    composition_y: float
    composition_width: float
    composition_height: float
    safe_rect: tuple[float, float, float, float]
    background_extension_left: float
    background_extension_right: float

    def point(self, x: float, y: float) -> tuple[float, float]:
        return (self.composition_x + x * self.scale, self.composition_y + y * self.scale)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_main_start(maxlevel: int = 0) -> MenuScreen:
    definitions = (
        ("new_game", MenuAction.NEW_GAME),
        ("load_game", MenuAction.LOAD_GAME),
        ("options", MenuAction.OPTIONS),
        ("arena_challenge", MenuAction.ARENA_CHALLENGE),
        ("single_mission_replay", MenuAction.SINGLE_MISSION_REPLAY),
        ("extras", MenuAction.EXTRAS),
    )
    items: list[MenuItem] = []
    for index, (semantic_id, action) in enumerate(definitions):
        locked = semantic_id == "single_mission_replay" and maxlevel == 0
        items.append(MenuItem(
            semantic_id=semantic_id,
            label_key=f"menu.{semantic_id}.label",
            heading_key=f"menu.{semantic_id}.heading",
            body_key=f"menu.{semantic_id}.body",
            action=action,
            locked=locked,
            lock_condition="maxlevel == 0" if semantic_id == "single_mission_replay" else None,
            up_id=definitions[(index - 1) % len(definitions)][0],
            down_id=definitions[(index + 1) % len(definitions)][0],
        ))
    return MenuScreen(
        semantic_id="main_start",
        items=tuple(items),
        prompts=(
            MenuPrompt(InputAction.BACK, "prompt.back"),
            MenuPrompt(InputAction.CONFIRM, "prompt.confirm"),
        ),
    )


def layout_for_viewport(width: int, height: int, tokens: dict[str, Any]) -> ViewportLayout:
    if width <= 0 or height <= 0:
        raise ValueError("viewport dimensions must be positive")
    design_w = float(tokens["ui"]["designWidth"])
    design_h = float(tokens["ui"]["designHeight"])
    scale = min(width / design_w, height / design_h)
    composition_w, composition_h = design_w * scale, design_h * scale
    x, y = (width - composition_w) / 2.0, (height - composition_h) / 2.0
    inset_x = float(tokens["ui"]["safeArea"]["horizontal"]) * scale
    inset_y = float(tokens["ui"]["safeArea"]["vertical"]) * scale
    safe = (x + inset_x, y + inset_y, x + composition_w - inset_x, y + composition_h - inset_y)
    return ViewportLayout(
        width, height, scale, x, y, composition_w, composition_h, safe,
        max(0.0, x), max(0.0, width - x - composition_w),
    )


def resolve_prompt(profile: str, action: InputAction) -> str:
    try:
        return INPUT_PROFILES[profile][action]
    except KeyError as exc:
        raise ValueError(f"unsupported input profile/action: {profile}/{action.value}") from exc


def resolve_playstation_prompt_asset(glyph: str, tokens: dict[str, Any]) -> pathlib.Path | None:
    asset_id = PLAYSTATION_PROMPT_ASSETS.get(glyph)
    return resolve_asset_path(asset_id, tokens) if asset_id else None


def development_prompt_symbol(profile: str, glyph: str) -> str:
    """Return compact temporary text for non-PlayStation prompt housings."""
    if profile == "keyboard":
        return {"ENTER": "ENT", "ESCAPE": "ESC"}.get(glyph, glyph[:3])
    return glyph[:1]


def render_playstation_prompt_shield(
    target: Image.Image,
    center: tuple[float, float],
    visible_diameter: float,
    glyph: str,
    tokens: dict[str, Any],
) -> dict[str, int | str]:
    """Render one approved shield directly, without a procedural housing."""
    path = resolve_playstation_prompt_asset(glyph, tokens)
    if path is None:
        raise FileNotFoundError(f"approved PlayStation prompt is not configured: {glyph}")
    with Image.open(path) as opened:
        opened.load()
        if opened.format != "PNG" or opened.mode != "RGBA" or opened.size != (448, 448):
            raise ValueError(f"unexpected approved PlayStation prompt: {path}")
        source = opened.copy()
    bounds = source.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"approved PlayStation prompt has no visible pixels: {path}")
    visible = source.crop(bounds)
    scale = visible_diameter / max(visible.size)
    size = (max(1, round(visible.width * scale)), max(1, round(visible.height * scale)))
    rendered = visible.resize(size, Image.Resampling.LANCZOS)
    paste_at = (round(center[0] - size[0] / 2), round(center[1] - size[1] / 2))
    target.paste(rendered, paste_at, rendered)
    return {
        "asset": str(path.relative_to(ROOT)).replace("\\", "/"),
        "renderedWidth": size[0], "renderedHeight": size[1],
        "visibleDiameter": max(size),
    }


def wrap_text(text: str, max_width: float, font: ImageFont.ImageFont) -> list[str]:
    if max_width <= 0:
        raise ValueError("max_width must be positive")
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if probe.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def missing_asset_fallback(asset_id: str, tokens: dict[str, Any]) -> str:
    value = tokens.get("assets", {}).get(asset_id)
    return str(value) if value else f"placeholder:{asset_id}"


def resolve_asset_path(asset_id: str, tokens: dict[str, Any]) -> pathlib.Path | None:
    value = tokens.get("assets", {}).get(asset_id)
    if not value:
        return None
    path = pathlib.Path(str(value))
    if not path.is_absolute():
        path = ROOT / "assets/reforged/frontend/main-menu" / path
    return path if path.is_file() else None


def _colour(tokens: dict[str, Any], name: str) -> str:
    return tokens["colours"][name]


def _font(
    size: int,
    tokens: dict[str, Any] | None = None,
    weight: str = "regular",
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if tokens is not None:
        relative = tokens["typography"]["fontFiles"][weight]
        path = ROOT / "assets/reforged/frontend/main-menu" / relative
        if not path.is_file():
            raise FileNotFoundError(f"configured Reforged font is missing: {path}")
        return ImageFont.truetype(str(path), size=max(8, size))
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=max(8, size))
    except OSError:
        return ImageFont.load_default()


def _scaled_box(layout: ViewportLayout, xyxy: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    p0 = layout.point(xyxy[0], xyxy[1]); p1 = layout.point(xyxy[2], xyxy[3])
    return tuple(round(value) for value in (*p0, *p1))


SELECTED_ILLUMINATION: dict[str, Any] = {
    "container": (103, 45, 5),
    "amberTransition": (231, 151, 32),
    "amberTransitionOpacity": 158,
    "internalLight": (255, 247, 221),
    "internalLightOpacity": 255,
    "hotspot": (255, 253, 235),
    "hotspotOpacity": 255,
    "thinRim": (255, 226, 143),
    "thinRimOpacity": 82,
    "opposingEdge": (92, 38, 4),
    "opposingEdgeOpacity": 24,
    "halo": (239, 157, 39),
    "haloOpacity": 68,
    "haloRadius": 4.0,
    "broadHaloOpacity": 16,
    "broadHaloRadius": 9.5,
    "primaryNoiseFloor": 88,
    "secondaryNoiseFloor": 138,
    "noiseCeiling": 255,
}

MATERIAL_PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "unselected": {
        "top": (255, 252, 237), "upper": (225, 219, 199),
        "centre": (157, 153, 142), "lower": (214, 207, 187),
        "bottom": (105, 105, 100), "highlight": (255, 255, 246),
        "recess": (121, 119, 112), "opposing": (82, 83, 81),
    },
    "locked": {
        "top": (173, 174, 172), "upper": (132, 134, 134),
        "centre": (82, 85, 87), "lower": (117, 119, 119),
        "bottom": (57, 60, 63), "highlight": (190, 190, 184),
        "recess": (71, 74, 76), "opposing": (43, 46, 49),
    },
}


def _shift_mask(mask: Image.Image, dx: int, dy: int) -> Image.Image:
    """Translate an L mask without ImageChops.offset's wraparound."""
    shifted = Image.new("L", mask.size)
    shifted.paste(mask, (dx, dy))
    return shifted


def _scaled_alpha(mask: Image.Image, opacity: int) -> Image.Image:
    return mask.point(lambda value: value * opacity // 255)


def build_material_text_layers(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    state: str,
    scale: float = 1.0,
) -> tuple[dict[str, Image.Image], tuple[int, int]]:
    """Build deterministic internal metal/bevel masks for one text run."""
    if state not in ("selected", *MATERIAL_PALETTES):
        raise ValueError(f"unsupported typography material state: {state}")
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    bbox = probe.textbbox((0, 0), text, font=font)
    bevel = max(1, round(1.5 * scale))
    pad = max(6, round(7 * scale))
    size = (max(1, bbox[2] - bbox[0] + pad * 2), max(1, bbox[3] - bbox[1] + pad * 2))
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=255)
    eroded_1 = mask.filter(ImageFilter.MinFilter(bevel * 2 + 1))
    deep_width = bevel * 2 + 1
    eroded_2 = eroded_1.filter(ImageFilter.MinFilter(deep_width * 2 + 1))
    layers = {
        "glyph": mask,
        "light_bevel": ImageChops.subtract(mask, _shift_mask(mask, bevel, bevel)),
        "opposing_bevel": ImageChops.subtract(mask, _shift_mask(mask, -bevel, -bevel)),
        "inset": ImageChops.subtract(eroded_1, eroded_2),
        "face": eroded_1,
    }
    return layers, (bbox[0] - pad, bbox[1] - pad)


def _vertical_material_gradient(size: tuple[int, int], palette: dict[str, tuple[int, int, int]]) -> Image.Image:
    stops = (
        (0.00, palette["top"]), (0.17, palette["upper"]),
        (0.48, palette["centre"]), (0.68, palette["lower"]),
        (1.00, palette["bottom"]),
    )
    gradient = Image.new("RGBA", size)
    pixels = gradient.load()
    height = max(1, size[1] - 1)
    for y in range(size[1]):
        t = y / height
        left, right = stops[0], stops[-1]
        for index in range(len(stops) - 1):
            if stops[index][0] <= t <= stops[index + 1][0]:
                left, right = stops[index], stops[index + 1]
                break
        span = max(1e-9, right[0] - left[0])
        local = (t - left[0]) / span
        colour = tuple(round(left[1][c] * (1 - local) + right[1][c] * local) for c in range(3))
        for x in range(size[0]):
            pixels[x, y] = (*colour, 255)
    return gradient


def build_selected_illumination_masks(
    glyph: Image.Image, scale: float, text: str = ""
) -> dict[str, Image.Image]:
    """Derive organic, label-stable light contained inside selected glyphs."""
    core = glyph.filter(ImageFilter.MinFilter(3))
    interior = ImageChops.multiply(
        glyph,
        core.filter(ImageFilter.GaussianBlur(max(1.0, 1.5 * scale))),
    )
    thin_edge = ImageChops.subtract(glyph, core)

    seed = hashlib.sha256(("SpartanReforged:selected:" + text).encode("utf-8")).digest()

    def field(label: bytes, cell_x: float, cell_y: float, floor: int) -> Image.Image:
        coarse_w = max(3, round(glyph.width / max(1, cell_x * scale)))
        coarse_h = max(3, round(glyph.height / max(1, cell_y * scale)))
        values: list[int] = []
        counter = 0
        while len(values) < coarse_w * coarse_h:
            values.extend(hashlib.sha256(seed + label + counter.to_bytes(4, "little")).digest())
            counter += 1
        result = Image.new("L", (coarse_w, coarse_h))
        ceiling = SELECTED_ILLUMINATION["noiseCeiling"]
        result.putdata([
            floor + value * (ceiling - floor) // 255
            for value in values[:coarse_w * coarse_h]
        ])
        return result.resize(glyph.size, Image.Resampling.BICUBIC)

    primary = field(b"broad", 31, 21, SELECTED_ILLUMINATION["primaryNoiseFloor"])
    secondary = field(b"medium", 14, 11, SELECTED_ILLUMINATION["secondaryNoiseFloor"])
    noise = Image.blend(primary, secondary, .34).filter(
        ImageFilter.GaussianBlur(max(.75, 1.1 * scale))
    ).point(lambda value: max(42, min(255, round(128 + (value - 128) * 1.72))))
    internal = ImageChops.multiply(interior, noise)

    hotspot_field = Image.new("L", glyph.size)
    hotspot_draw = ImageDraw.Draw(hotspot_field)
    count = 3 + seed[0] % 3
    for index in range(count):
        base = 1 + index * 5
        centre_x = glyph.width * (.10 + seed[base] / 255 * .80)
        centre_y = glyph.height * (.22 + seed[base + 1] / 255 * .56)
        radius_x = glyph.width * (.055 + seed[base + 2] / 255 * .095)
        radius_y = glyph.height * (.14 + seed[base + 3] / 255 * .19)
        intensity = 190 + seed[base + 4] % 66
        hotspot_draw.ellipse(
            (centre_x - radius_x, centre_y - radius_y,
             centre_x + radius_x, centre_y + radius_y),
            fill=intensity,
        )
    hotspots = ImageChops.multiply(
        interior,
        hotspot_field.filter(ImageFilter.GaussianBlur(max(1.5, 3.0 * scale))),
    ).point(lambda value: min(255, round(value * 1.55)))
    return {
        "interior": interior, "internal_light": internal,
        "thin_edge": thin_edge, "hotspots": hotspots,
    }


def _composite_selected_illumination(
    tile: Image.Image,
    layers: dict[str, Image.Image],
    scale: float,
    text: str,
) -> dict[str, Image.Image]:
    settings = SELECTED_ILLUMINATION
    illumination = build_selected_illumination_masks(layers["glyph"], scale, text=text)
    light_source = ImageChops.lighter(
        illumination["internal_light"], illumination["hotspots"]
    )
    halo_mask = light_source.filter(
        ImageFilter.GaussianBlur(max(2.0, settings["haloRadius"] * scale))
    )
    broad_halo_mask = light_source.filter(
        ImageFilter.GaussianBlur(max(4.0, settings["broadHaloRadius"] * scale))
    )
    broad_halo = Image.new("RGBA", tile.size, (*settings["halo"], 0))
    broad_halo.putalpha(_scaled_alpha(broad_halo_mask, settings["broadHaloOpacity"]))
    tile.alpha_composite(broad_halo)
    halo = Image.new("RGBA", tile.size, (*settings["halo"], 0))
    halo.putalpha(_scaled_alpha(halo_mask, settings["haloOpacity"]))
    tile.alpha_composite(halo)
    container = Image.new("RGBA", tile.size, (*settings["container"], 0))
    container.putalpha(layers["glyph"])
    tile.alpha_composite(container)
    transition = Image.new("RGBA", tile.size, (*settings["amberTransition"], 0))
    transition.putalpha(_scaled_alpha(illumination["interior"], settings["amberTransitionOpacity"]))
    tile.alpha_composite(transition)
    internal = Image.new("RGBA", tile.size, (*settings["internalLight"], 0))
    internal.putalpha(_scaled_alpha(illumination["internal_light"], settings["internalLightOpacity"]))
    tile.alpha_composite(internal)
    hotspots = Image.new("RGBA", tile.size, (*settings["hotspot"], 0))
    hotspots.putalpha(_scaled_alpha(illumination["hotspots"], settings["hotspotOpacity"]))
    tile.alpha_composite(hotspots)
    opposing = Image.new("RGBA", tile.size, (*settings["opposingEdge"], 0))
    opposing.putalpha(_scaled_alpha(layers["opposing_bevel"], settings["opposingEdgeOpacity"]))
    tile.alpha_composite(opposing)
    edge = Image.new("RGBA", tile.size, (*settings["thinRim"], 0))
    edge.putalpha(_scaled_alpha(illumination["thin_edge"], settings["thinRimOpacity"]))
    tile.alpha_composite(edge)
    return illumination


def render_material_text(
    target: Image.Image,
    position: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    state: str,
    scale: float = 1.0,
) -> dict[str, int]:
    """Composite internally bevelled Cinzel text and return layer statistics."""
    layers, offset = build_material_text_layers(text, font, state, scale)
    tile = Image.new("RGBA", layers["glyph"].size)
    shadow_mask = layers["glyph"].filter(ImageFilter.GaussianBlur(max(.65, 1.0 * scale)))
    shadow = Image.new("RGBA", tile.size, (2, 5, 9, 0))
    shadow.putalpha(_scaled_alpha(_shift_mask(shadow_mask, max(1, round(scale)), max(1, round(2 * scale))), 76))
    tile.alpha_composite(shadow)
    if state == "selected":
        illumination = _composite_selected_illumination(tile, layers, scale, text)
        paste_at = (round(position[0] + offset[0]), round(position[1] + offset[1]))
        target.paste(tile, paste_at, tile)
        combined = {
            "glyph": layers["glyph"],
            "opposing_bevel": layers["opposing_bevel"],
            **illumination,
        }
        return {name: sum(1 for value in layer.getdata() if value) for name, layer in combined.items()}
    palette = MATERIAL_PALETTES[state]
    base = _vertical_material_gradient(tile.size, palette)
    base.putalpha(layers["glyph"])
    tile.alpha_composite(base)
    inset = Image.new("RGBA", tile.size, (*palette["recess"], 0))
    inset.putalpha(_scaled_alpha(layers["inset"], 150 if state == "selected" else 105))
    tile.alpha_composite(inset)
    opposing = Image.new("RGBA", tile.size, (*palette["opposing"], 0))
    opposing.putalpha(_scaled_alpha(layers["opposing_bevel"], 220 if state == "selected" else 155))
    tile.alpha_composite(opposing)
    highlight = Image.new("RGBA", tile.size, (*palette["highlight"], 0))
    highlight.putalpha(_scaled_alpha(layers["light_bevel"], 230 if state == "selected" else (135 if state == "unselected" else 78)))
    tile.alpha_composite(highlight)
    paste_at = (round(position[0] + offset[0]), round(position[1] + offset[1]))
    target.paste(tile, paste_at, tile)
    return {name: sum(1 for value in layer.getdata() if value) for name, layer in layers.items()}


def selected_pointer_tip(
    layout: ViewportLayout, menu_x: float, item_y: float, marker_gap: float
) -> tuple[float, float]:
    """Return the pointer tip anchored to the selected label's optical centre."""
    return layout.point(menu_x - marker_gap, item_y + 35)


def selected_pointer_tip_for_state(
    layout: ViewportLayout, state: MenuState, tokens: dict[str, Any]
) -> tuple[float, float]:
    index = next(
        index for index, item in enumerate(state.screen.items)
        if item.semantic_id == state.selected_id
    )
    menu_x, menu_y = tokens["menu"]["position"]
    item_y = menu_y + index * tokens["menu"]["itemSpacing"]
    return selected_pointer_tip(layout, menu_x, item_y, tokens["menu"]["markerGap"])


def render_selection_pointer(
    target: Image.Image,
    tip: tuple[float, float],
    width: float,
    height: float,
    pointer_path: pathlib.Path | None = None,
) -> dict[str, int | str]:
    """Scale and place the locked approved pointer raster by its visible bounds."""
    if pointer_path is None:
        pointer_path = resolve_asset_path("selectionMarker", load_json(DEFAULT_TOKENS))
    if pointer_path is None:
        raise FileNotFoundError("approved Reforged selection pointer is not configured")
    with Image.open(pointer_path) as opened:
        opened.load()
        if opened.format != "PNG" or opened.mode != "RGBA":
            raise ValueError(f"unexpected approved pointer runtime: {opened.format}/{opened.mode}")
        source = opened.copy()
    alpha_bounds = source.getchannel("A").getbbox()
    if alpha_bounds is None:
        raise ValueError("approved pointer runtime has no visible pixels")
    source = source.crop(alpha_bounds)
    requested_w, requested_h = max(1, round(width)), max(1, round(height))
    ratio = min(requested_w / source.width, requested_h / source.height)
    output_w = max(1, round(source.width * ratio))
    output_h = max(1, round(source.height * ratio))
    rendered = source.resize((output_w, output_h), Image.Resampling.LANCZOS)
    paste_at = (round(tip[0] - output_w), round(tip[1] - output_h / 2))
    target.paste(rendered, paste_at, rendered)
    return {
        "asset": str(pointer_path.relative_to(ROOT)).replace("\\", "/"),
        "sourceWidth": source.width,
        "sourceHeight": source.height,
        "renderedWidth": output_w,
        "renderedHeight": output_h,
        "visiblePixels": sum(1 for value in rendered.getchannel("A").getdata() if value),
    }


def locked_padlock_placement(
    layout: ViewportLayout,
    text_position: tuple[float, float],
    label: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    tokens: dict[str, Any],
) -> tuple[tuple[float, float], tuple[int, int, int, int]]:
    """Anchor the approved padlock to the visible bounds of the locked label."""
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    bounds = probe.textbbox(text_position, label, font=font)
    gap = float(tokens["padlock"]["labelGap"]) * layout.scale
    offset_y = float(tokens["padlock"]["opticalOffsetY"]) * layout.scale
    return (
        (bounds[2] + gap, (bounds[1] + bounds[3]) / 2 + offset_y),
        bounds,
    )


def render_locked_padlock(
    target: Image.Image,
    left_center: tuple[float, float],
    visible_height: float,
    padlock_path: pathlib.Path | None = None,
) -> dict[str, int | str]:
    """Render the approved raster by alpha-visible bounds with no added effects."""
    if padlock_path is None:
        padlock_path = resolve_asset_path("padlock", load_json(DEFAULT_TOKENS))
    if padlock_path is None:
        raise FileNotFoundError("approved Reforged padlock is not configured")
    with Image.open(padlock_path) as opened:
        opened.load()
        if opened.format != "PNG" or opened.mode != "RGBA":
            raise ValueError(f"unexpected approved padlock runtime: {opened.format}/{opened.mode}")
        source = opened.copy()
    alpha_bounds = source.getchannel("A").getbbox()
    if alpha_bounds is None:
        raise ValueError("approved padlock runtime has no visible pixels")
    visible = source.crop(alpha_bounds)
    ratio = max(1.0 / visible.height, visible_height / visible.height)
    size = (max(1, round(visible.width * ratio)), max(1, round(visible.height * ratio)))
    rendered = visible.resize(size, Image.Resampling.LANCZOS)
    paste_at = (round(left_center[0]), round(left_center[1] - size[1] / 2))
    target.paste(rendered, paste_at, rendered)
    return {
        "asset": str(padlock_path.relative_to(ROOT)).replace("\\", "/"),
        "sourceWidth": visible.width, "sourceHeight": visible.height,
        "renderedWidth": size[0], "renderedHeight": size[1],
        "pasteX": paste_at[0], "pasteY": paste_at[1],
    }


def render_wireframe(
    width: int,
    height: int,
    state: MenuState,
    tokens: dict[str, Any],
    strings: dict[str, str],
    profile: str = "playstation",
    logo_image: Image.Image | None = None,
) -> Image.Image:
    if state.presentation is not PresentationMode.REFORGED:
        raise ValueError("wireframe renderer accepts only Reforged presentation state")
    layout = layout_for_viewport(width, height, tokens)
    image = Image.new("RGB", (width, height), _colour(tokens, "backgroundDark"))
    draw = ImageDraw.Draw(image, "RGBA")

    background_path = resolve_asset_path("background", tokens)
    if background_path:
        with Image.open(background_path) as background_source:
            background = background_source.convert("RGB")
        composition_size = (round(layout.composition_width), round(layout.composition_height))
        rendered_background = background.resize(composition_size, Image.Resampling.LANCZOS)
        image.paste(rendered_background, (round(layout.composition_x), round(layout.composition_y)))
    else:
        # Project-created fallback zones remain available when approved artwork is absent.
        if layout.background_extension_left:
            draw.rectangle((0, 0, round(layout.composition_x), height), fill=(10, 20, 31, 255))
            draw.rectangle((round(layout.composition_x + layout.composition_width), 0, width, height), fill=(10, 20, 31, 255))
        draw.rectangle(_scaled_box(layout, (0, 0, 1920, 1080)), fill=_colour(tokens, "backgroundMid"))
        draw.rectangle(_scaled_box(layout, (960, 0, 1920, 1080)), fill=_colour(tokens, "environmentGuide"))
        draw.polygon([
            layout.point(1260, 1080), layout.point(1510, 360), layout.point(1920, 250), layout.point(1920, 1080)
        ], fill=(*ImageColor_getrgb(_colour(tokens, "foregroundGuide")), 220))
        safe = tuple(round(v) for v in layout.safe_rect)
        draw.rectangle(safe, outline=_colour(tokens, "safeAreaGuide"), width=max(1, round(2 * layout.scale)))

    ornament_h = tokens["ornament"]["height"]
    bands_baked_in = bool(tokens["background"].get("approvedPlateIncludesOrnamentBands"))
    if not (background_path and bands_baked_in):
        for y in (0, 1080 - ornament_h):
            box = _scaled_box(layout, (0, y, 1920, y + ornament_h))
            draw.rectangle(box, fill=(*ImageColor_getrgb(_colour(tokens, "ornamentNeutral")), 180))
            step = max(8, round(tokens["ornament"]["tileWidth"] * layout.scale))
            for x in range(box[0], box[2], step):
                draw.line((x, box[1], min(box[2], x + step // 2), box[3]), fill=(195, 172, 112, 140), width=2)

    # Replaceable logo component. A missing asset remains a labelled fallback.
    lx, ly = tokens["logo"]["position"]
    lw, lh = tokens["logo"]["maxWidth"], tokens["logo"]["height"]
    logo_box = _scaled_box(layout, (lx, ly, lx + lw, ly + lh))
    if logo_image is None:
        logo_path = resolve_asset_path("logo", tokens)
        if logo_path:
            logo_image = Image.open(logo_path).convert("RGBA")
    if logo_image is not None:
        target_w, target_h = logo_box[2] - logo_box[0], logo_box[3] - logo_box[1]
        ratio = min(target_w / logo_image.width, target_h / logo_image.height)
        size = (max(1, round(logo_image.width * ratio)), max(1, round(logo_image.height * ratio)))
        rendered_logo = logo_image.resize(size, Image.Resampling.LANCZOS)
        image.paste(rendered_logo, (logo_box[0], logo_box[1]), rendered_logo)
    else:
        draw.rounded_rectangle(logo_box, radius=round(12 * layout.scale), outline=_colour(tokens, "selectedGold"), width=max(2, round(3 * layout.scale)))
        logo_font = _font(round(46 * layout.scale), tokens, "bold")
        draw.text(layout.point(lx + 24, ly + 54), "SPARTAN / TOTAL WARRIOR", font=logo_font, fill=_colour(tokens, "selectedGold"))
        draw.text(layout.point(lx + 24, ly + 124), "REPLACEABLE LOGO + GLINT LAYERS", font=_font(round(18 * layout.scale), tokens), fill=_colour(tokens, "textSecondary"))

    mx, my = tokens["menu"]["position"]
    spacing = tokens["menu"]["itemSpacing"]
    marker_w, marker_h = tokens["menu"]["markerSize"]
    marker_gap = tokens["menu"]["markerGap"]
    pointer_path = resolve_asset_path("selectionMarker", tokens)
    padlock_path = resolve_asset_path("padlock", tokens)
    for index, item in enumerate(state.screen.items):
        y = my + index * spacing
        selected = item.semantic_id == state.selected_id
        size_key = "MenuPrimarySelected" if selected else "MenuPrimary"
        font = _font(
            round(tokens["typography"][size_key] * layout.scale),
            tokens,
            "bold" if selected else "regular",
        )
        if selected:
            tip = selected_pointer_tip_for_state(layout, state, tokens)
            render_selection_pointer(
                image, tip, marker_w * layout.scale, marker_h * layout.scale,
                pointer_path=pointer_path,
            )
        text_position = layout.point(mx, y)
        material_state = "locked" if item.locked else ("selected" if selected else "unselected")
        render_material_text(image, text_position, strings[item.label_key], font, material_state, layout.scale)
        if item.locked:
            padlock_anchor, _ = locked_padlock_placement(
                layout, text_position, strings[item.label_key], font, tokens
            )
            render_locked_padlock(
                image, padlock_anchor,
                tokens["padlock"]["visibleHeight"] * layout.scale,
                padlock_path=padlock_path,
            )

    selected = state.selected
    cx, cy = tokens["context"]["position"]
    max_width = tokens["context"]["maxWidth"] * layout.scale
    heading_font = _font(round(tokens["typography"]["ContextHeading"] * layout.scale), tokens, "bold")
    body_font = _font(round(tokens["typography"]["ContextBody"] * layout.scale), tokens)
    heading_position = layout.point(cx, cy)
    draw.text(
        (heading_position[0] + max(1, round(layout.scale)), heading_position[1] + max(1, round(layout.scale))),
        strings[selected.heading_key],
        font=heading_font,
        fill=(3, 7, 12, 190),
    )
    draw.text(heading_position, strings[selected.heading_key], font=heading_font, fill=_colour(tokens, "contextHeading"))
    body_y = cy + tokens["typography"]["ContextHeading"] + tokens["context"]["headingBodyGap"]
    for line in wrap_text(strings[selected.body_key], max_width, body_font):
        body_position = layout.point(cx, body_y)
        draw.text(
            body_position,
            line,
            font=body_font,
            fill=_colour(tokens, "contextBody"),
            stroke_width=max(1, round(layout.scale)),
            stroke_fill=(3, 7, 12, 180),
        )
        body_y += tokens["typography"]["ContextBody"] * 1.35

    # Bottom-right semantic prompts; PlayStation uses the approved shield artwork directly.
    px, py = tokens["prompt"]["position"]
    prompt_font = _font(round(tokens["typography"]["PromptLabel"] * layout.scale), tokens)
    cursor = px
    for prompt in reversed(state.screen.prompts):
        glyph = resolve_prompt(profile, prompt.action)
        label = strings[prompt.label_key]
        label_width = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(label, font=prompt_font) / layout.scale
        glyph_label_gap = tokens["prompt"]["glyphLabelGap"]
        group_width = tokens["prompt"]["glyphSize"] + glyph_label_gap + label_width
        cursor -= group_width
        center = layout.point(cursor + tokens["prompt"]["glyphSize"] / 2, py)
        radius = tokens["prompt"]["glyphSize"] * layout.scale / 2
        if profile == "playstation":
            render_playstation_prompt_shield(
                image, center, tokens["prompt"]["glyphSize"] * layout.scale,
                glyph, tokens,
            )
        else:
            draw.ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=(20, 23, 29, 255), outline=_colour(tokens, "ornamentNeutral"), width=max(1, round(3 * layout.scale)))
            symbol = development_prompt_symbol(profile, glyph)
            symbol_font = _font(round((13 if profile == "keyboard" else 20) * layout.scale))
            symbol_bounds = draw.textbbox((0, 0), symbol, font=symbol_font)
            symbol_position = (
                center[0] - (symbol_bounds[2] - symbol_bounds[0]) / 2 - symbol_bounds[0],
                center[1] - (symbol_bounds[3] - symbol_bounds[1]) / 2 - symbol_bounds[1],
            )
            draw.text(symbol_position, symbol, font=symbol_font, fill=_colour(tokens, "textPrimary"))
        prompt_position = layout.point(cursor + tokens["prompt"]["glyphSize"] + glyph_label_gap, py - 13)
        draw.text(
            prompt_position,
            label,
            font=prompt_font,
            fill=_colour(tokens, "textPrimary"),
            stroke_width=max(1, round(layout.scale)),
            stroke_fill=(3, 7, 12, 200),
        )
        cursor -= tokens["prompt"]["itemGap"]

    if not background_path:
        # Development labels apply only to the project-created fallback treatment.
        note_font = _font(round(15 * layout.scale))
        draw.text(layout.point(1040, 100), "BACKGROUND ENVIRONMENT / ATMOSPHERE", font=note_font, fill=(175, 195, 211, 210))
        draw.text(layout.point(1360, 720), "FOREGROUND ENVIRONMENT", font=note_font, fill=(175, 195, 211, 210))
        draw.text(layout.point(1040, 130), "wireframe only — no final art", font=note_font, fill=(155, 101, 119, 240))
    return image


def ImageColor_getrgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"expected #RRGGBB colour, got {value!r}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def write_wireframes(output_dir: pathlib.Path, tokens: dict[str, Any], strings: dict[str, str]) -> dict[str, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    state = MenuState(build_main_start(maxlevel=0), "new_game")
    targets = {
        "1920x1080": (1920, 1080),
        "2560x1440": (2560, 1440),
        "3840x2160": (3840, 2160),
        "2560x1080-21x9": (2560, 1080),
    }
    manifest: dict[str, dict[str, Any]] = {}
    for name, (width, height) in targets.items():
        image = render_wireframe(width, height, state, tokens, strings)
        path = output_dir / f"main-start-wireframe-{name}.png"
        image.save(path, format="PNG", optimize=False, compress_level=9)
        layout = layout_for_viewport(width, height, tokens)
        manifest[name] = {
            "path": str(path), "width": width, "height": height,
            "scale": layout.scale, "safeRect": layout.safe_rect,
            "backgroundExtension": [layout.background_extension_left, layout.background_extension_right],
        }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokens", type=pathlib.Path, default=DEFAULT_TOKENS)
    parser.add_argument("--locale", type=pathlib.Path, default=DEFAULT_LOCALE)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    tokens = load_json(args.tokens)
    strings = load_json(args.locale)["strings"]
    manifest = write_wireframes(args.output_dir, tokens, strings)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
