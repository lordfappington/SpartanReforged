#!/usr/bin/env python3
"""Build a deterministic original FE_MAIN main-menu reference design kit.

This tool is intentionally separate from preservation exporters. It reads the
already-extracted FE_MAIN section, reuses the validated TIM2 decoder without
modifying it, and writes reference-only output beneath the Reforged design-kit
directory. Stochastic emitter particles are documented but are not fabricated
into the deterministic still frame.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import struct
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


LOGICAL_WIDTH = 512
LOGICAL_HEIGHT = 448
DISPLAY_ASPECT = (4, 3)
PIXEL_ASPECT = (7, 6)
TARGET_MENU = "main_start"
OUTPUT_RELATIVE = pathlib.Path("assets/reforged/frontend/design-kit/main-menu")

TARGET_PAGE_ROLES = {
    "grab_05.tm2": ("background", "Static overscanned background; RGB modulated 148/128 after titles"),
    "smoke.tm2": ("background-animation", "Source for emitter2/emitter4; procedural particles omitted from static still"),
    "bands.tm2": ("frame", "Four top/bottom border sprites"),
    "spartan_logo.tm2": ("logo", "Small logo plus flare layer"),
    "glows.tm2": ("decorative-animation", "Two logo-area glow emitters; procedural particles omitted from static still"),
    "icons.tm2": ("controller-glyphs", "Cross/Triangle visible; Circle/Square share the same global page"),
    "mission_builder.tm2": ("padlock", "Free-play locked-state padlock"),
    "blackbox.tm2": ("overscan-bars", "PAL bar sprites at/outside logical safe-area boundaries"),
}

TARGET_PAGE_PRESENTATION = {
    "grab_05.tm2": ("normalized full-page crop; scaled to 640x480 at (-64,-16), then viewport-cropped", "RGB 148/128"),
    "smoke.tm2": ("normalized full-page source for two procedural emitters", "emitter colours 26/41/57 and 9/15/21"),
    "bands.tm2": ("normalized 255x16 region; four 512x32 sprites clipped at left/right viewport edges", "neutral"),
    "spartan_logo.tm2": ("two normalized crops displayed 1:1 at 192x64 and 192x16", "neutral"),
    "glows.tm2": ("128x128 normalized quadrant used by two procedural 6x6 emitters", "neutral emitter default"),
    "icons.tm2": ("four normalized quadrants; native/display size 32x32", "neutral"),
    "mission_builder.tm2": ("46x47 padlock crop downscaled to 32x32", "neutral; white flash on rejected confirmation"),
    "blackbox.tm2": ("normalized source stretched to overscan bars outside the 512x448 safe area", "black"),
}

FONT_FILES = ("FONT14", "FONT18", "FONT18G")
INFO_KEYS = {
    "new_game": "info_new_game",
    "load_game": "info_load_game",
    "options": "info_options",
    "arena_mode": "info_arena_mode",
    "replay_mission": "replay_mission_2",
    "bonus": "extras_2",
}
OPTION_KEYS = ("new_game", "load_game", "options", "arena_mode", "replay_mission", "bonus")
OPTION_TEXT_NAMES = {
    "new_game": ("text_new_game", "text_new_game_g"),
    "load_game": ("text_load_game", "text_load_game_g"),
    "options": ("text_options", "text_options_g"),
    "arena_mode": ("text_arena_mode", "text_arena_mode_g"),
    "replay_mission": ("text_replay_mission", "text_replay_mission_g"),
    "bonus": ("text_bonus", "text_bonus_g"),
}


class DesignKitError(ValueError):
    """Raised when source declarations or bounds differ from the known target."""


@dataclass(frozen=True)
class TextureRegion:
    name: str
    page: str
    x: int
    y: int
    width: int
    height: int
    line: int


@dataclass(frozen=True)
class Sprite:
    name: str
    texture: str
    x: int
    y: int
    width: int
    height: int
    rotation: int
    line: int


@dataclass(frozen=True)
class TextObject:
    name: str
    label: str
    x: int
    y: int
    width: int
    height: int
    font_index: int
    layer: int
    line: int


@dataclass(frozen=True)
class Emitter:
    name: str
    texture: str
    values: tuple[int, ...]
    line: int


@dataclass
class ScriptModel:
    pages: dict[str, str]
    fonts: list[str]
    textures: dict[str, TextureRegion]
    sprites: dict[str, Sprite]
    texts: dict[str, TextObject]
    emitters: dict[str, Emitter]
    groups: dict[str, list[str]]
    menus: dict[str, list[str]]
    labels: dict[str, str]
    source_lines: list[str]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_int(value: str, line: int) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise DesignKitError(f"line {line}: expected integer, got {value!r}") from exc


def parse_script(text: str) -> ScriptModel:
    pages: dict[str, str] = {}
    fonts: list[str] = []
    textures: dict[str, TextureRegion] = {}
    sprites: dict[str, Sprite] = {}
    texts: dict[str, TextObject] = {}
    emitters: dict[str, Emitter] = {}
    groups: dict[str, list[str]] = {}
    menus: dict[str, list[str]] = {}
    labels: dict[str, str] = {}
    source_lines = text.splitlines()
    for line_number, raw in enumerate(source_lines, 1):
        parts = raw.strip().split()
        if not parts:
            continue
        kind = parts[0].upper()
        if kind == "TPAGE" and len(parts) >= 3:
            pages[parts[1]] = parts[2]
        elif kind == "FONT" and len(parts) >= 2:
            fonts.append(parts[1])
        elif kind == "TEXTURE" and len(parts) == 7:
            textures[parts[1]] = TextureRegion(
                parts[1], parts[2], *(_parse_int(value, line_number) for value in parts[3:7]), line_number
            )
        elif kind == "SPRITE" and len(parts) >= 7:
            sprites[parts[1]] = Sprite(
                parts[1], parts[2],
                *(_parse_int(value, line_number) for value in parts[3:7]),
                _parse_int(parts[7], line_number) if len(parts) > 7 else 0,
                line_number,
            )
        elif kind == "TEXT" and len(parts) == 9:
            texts[parts[1]] = TextObject(
                parts[1], parts[2], *(_parse_int(value, line_number) for value in parts[3:9]), line_number
            )
        elif kind == "EMITTER" and len(parts) >= 4:
            emitters[parts[1]] = Emitter(
                parts[1], parts[2], tuple(_parse_int(value, line_number) for value in parts[3:]), line_number
            )
        elif kind == "ITEMS" and len(parts) >= 2:
            groups[parts[1]] = parts[2:]
        elif kind == "MENU" and len(parts) >= 2:
            menus[parts[1]] = parts[2:]
        elif kind == "LABEL" and len(parts) >= 3:
            labels[parts[1]] = " ".join(parts[2:])
    if TARGET_MENU not in menus:
        raise DesignKitError(f"target menu {TARGET_MENU!r} is missing")
    return ScriptModel(pages, fonts, textures, sprites, texts, emitters, groups, menus, labels, source_lines)


def parse_localization(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    pattern = re.compile(r"(?ms)^\[([^\]\r\n]+)\]\s*\r?\n\{(.*?)\}\s*$")
    for match in pattern.finditer(text):
        value = match.group(2).replace("\r\n", "\n").replace("\r", "\n").strip()
        entries[match.group(1).casefold()] = value
    return entries


def expand_group(model: ScriptModel, name: str) -> list[str]:
    if name not in model.groups:
        return [name]
    expanded: list[str] = []
    for child in model.groups[name]:
        expanded.extend(expand_group(model, child))
    return expanded


def normalized_crop_box(region: TextureRegion, page_size: tuple[int, int]) -> tuple[int, int, int, int]:
    page_width, page_height = page_size
    values = (
        round(region.x * page_width / 256),
        round(region.y * page_height / 256),
        round((region.x + region.width) * page_width / 256),
        round((region.y + region.height) * page_height / 256),
    )
    left, top, right, bottom = values
    if not (0 <= left < right <= page_width and 0 <= top < bottom <= page_height):
        raise DesignKitError(f"texture region {region.name} exceeds {page_width}x{page_height}: {values}")
    return values


def aspect_mapping(width: int, height: int) -> dict[str, float | int]:
    central_width = round(height * DISPLAY_ASPECT[0] / DISPLAY_ASPECT[1])
    if central_width > width:
        central_width = width
        central_height = round(width * DISPLAY_ASPECT[1] / DISPLAY_ASPECT[0])
        offset_x = 0
        offset_y = (height - central_height) // 2
    else:
        central_height = height
        offset_x = (width - central_width) // 2
        offset_y = 0
    return {
        "outputWidth": width,
        "outputHeight": height,
        "centralWidth": central_width,
        "centralHeight": central_height,
        "offsetX": offset_x,
        "offsetY": offset_y,
        "sideExtensionEach": offset_x,
        "scaleXFromLogical": central_width / LOGICAL_WIDTH,
        "scaleYFromLogical": central_height / LOGICAL_HEIGHT,
    }


def _load_tim2_decoder(project_root: pathlib.Path):
    path = project_root / "tools/conversion/tim2_decode.py"
    spec = importlib.util.spec_from_file_location("spartan_tim2_decode_reference", path)
    if spec is None or spec.loader is None:
        raise DesignKitError("could not load validated TIM2 decoder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rgba_image(decoded) -> Image.Image:
    return Image.frombytes("RGBA", (decoded.width, decoded.height), decoded.rgba)


def _modulate(image: Image.Image, rgb: tuple[int, int, int], alpha: int = 128) -> Image.Image:
    pixels = bytearray(image.convert("RGBA").tobytes())
    for offset in range(0, len(pixels), 4):
        pixels[offset] = min(255, pixels[offset] * rgb[0] // 128)
        pixels[offset + 1] = min(255, pixels[offset + 1] * rgb[1] // 128)
        pixels[offset + 2] = min(255, pixels[offset + 2] * rgb[2] // 128)
        pixels[offset + 3] = min(255, pixels[offset + 3] * alpha // 128)
    return Image.frombytes("RGBA", image.size, bytes(pixels))


def _paste_sprite(
    target: Image.Image,
    sprite: Sprite,
    model: ScriptModel,
    decoded_pages: dict[str, Image.Image],
    modulation: tuple[int, int, int, int] | None = None,
) -> None:
    region = model.textures[sprite.texture]
    page = decoded_pages[region.page]
    crop = page.crop(normalized_crop_box(region, page.size))
    if sprite.rotation:
        raise DesignKitError(f"target sprite rotation is unsupported: {sprite.name}")
    crop = crop.resize((sprite.width, sprite.height), Image.Resampling.NEAREST)
    if modulation:
        crop = _modulate(crop, modulation[:3], modulation[3])
    target.alpha_composite(crop, (sprite.x, sprite.y))


def _font_metrics(dim_data: bytes) -> tuple[int, tuple[int, ...]]:
    if len(dim_data) != 576 or dim_data[1:64] != bytes([0xCD]) * 63:
        raise DesignKitError("unexpected DIM structure")
    return dim_data[0], struct.unpack("<256H", dim_data[64:])


def render_text(
    atlas: Image.Image,
    dim_data: bytes,
    value: str,
    max_width: int,
    max_height: int,
) -> tuple[Image.Image, int]:
    cell_size, advances = _font_metrics(dim_data)
    if atlas.width != cell_size * 16 or atlas.height != cell_size * 16:
        raise DesignKitError("font atlas is not a 16x16 grid matching DIM cell size")
    output = Image.new("RGBA", (max_width, max_height), (0, 0, 0, 0))
    cursor = 0
    for char in value:
        code = ord(char)
        index = code - 32
        if not 0 <= index < 256:
            raise DesignKitError(f"unsupported glyph {char!r} / U+{code:04X}")
        advance = advances[index]
        if advance >= 0x2000:
            raise DesignKitError(f"special DIM value for glyph {char!r}: 0x{advance:04X}")
        glyph = atlas.crop(((index % 16) * cell_size, (index // 16) * cell_size,
                            (index % 16 + 1) * cell_size, (index // 16 + 1) * cell_size))
        if cursor < max_width:
            output.alpha_composite(glyph, (cursor, 0))
        cursor += advance
    return output, cursor


def _render_text_object(
    target: Image.Image,
    obj: TextObject,
    value: str,
    font_pages: dict[int, Image.Image],
    font_dims: dict[int, bytes],
) -> int:
    rendered, advance = render_text(font_pages[obj.font_index], font_dims[obj.font_index], value, obj.width, obj.height)
    target.alpha_composite(rendered, (obj.x, obj.y))
    return advance


def _source_path_for_page(world: pathlib.Path, filename: str) -> pathlib.Path:
    candidates = {path.name.casefold(): path for path in world.glob("*.TM2")}
    if filename.casefold() in candidates:
        return candidates[filename.casefold()]
    raise DesignKitError(f"missing texture page {filename}")


def _save_png(image: Image.Image, path: pathlib.Path) -> dict[str, object]:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False, compress_level=9)
    payload = buffer.getvalue()
    path.write_bytes(payload)
    return {"file": path.name, "width": image.width, "height": image.height, "sha256": sha256(payload), "bytes": len(payload)}


def _visible_text(model: ScriptModel, localization: dict[str, str], selected: str) -> list[tuple[TextObject, str]]:
    result: list[tuple[TextObject, str]] = []
    for key in OPTION_KEYS:
        normal, glow = OPTION_TEXT_NAMES[key]
        obj = model.texts[glow if key == selected else normal]
        localization_key = model.labels[obj.label].casefold()
        result.append((obj, localization[localization_key]))
    info_obj = model.texts["text_info_text"]
    result.append((info_obj, localization[INFO_KEYS[selected].casefold()]))
    for name in ("text_back", "text_ok"):
        obj = model.texts[name]
        result.append((obj, localization[model.labels[obj.label].casefold()]))
    return result


def _render_state(
    model: ScriptModel,
    localization: dict[str, str],
    decoded_pages: dict[str, Image.Image],
    font_pages: dict[int, Image.Image],
    font_dims: dict[int, bytes],
    selected: str,
    locked: bool,
    layer_targets: dict[str, Image.Image] | None = None,
) -> Image.Image:
    canvas = Image.new("RGBA", (LOGICAL_WIDTH, LOGICAL_HEIGHT), (0, 0, 0, 255))
    background = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    chrome = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    text_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    lock_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

    _paste_sprite(background, model.sprites["spr_grab02"], model, decoded_pages, (148, 148, 148, 128))
    for name in ("spr_border_tl", "spr_border_tr", "spr_border_bl", "spr_border_br"):
        _paste_sprite(chrome, model.sprites[name], model, decoded_pages)
    _paste_sprite(chrome, model.sprites["spr_spartan_logo_flare"], model, decoded_pages)
    _paste_sprite(chrome, model.sprites["spr_spartan_logo_small"], model, decoded_pages)

    for obj, value in _visible_text(model, localization, selected):
        _render_text_object(text_layer, obj, value, font_pages, font_dims)
    _paste_sprite(text_layer, model.sprites["spr_button_2"], model, decoded_pages)
    _paste_sprite(text_layer, model.sprites["spr_button_1"], model, decoded_pages)
    if locked:
        _paste_sprite(lock_layer, model.sprites["spr_padlock_freeplay"], model, decoded_pages)

    for layer in (background, chrome, text_layer, lock_layer):
        canvas.alpha_composite(layer)
    if layer_targets is not None:
        layer_targets.update(background=background, chrome=chrome, text=text_layer, lock=lock_layer)
    return canvas


def _glyph_sheet(model: ScriptModel, decoded_pages: dict[str, Image.Image]) -> Image.Image:
    entries = (
        ("spr_button_1", "Cross / CONFIRM"),
        ("spr_button_2", "Triangle / BACK"),
        ("spr_button_3", "Circle / source glyph"),
        ("spr_button_4", "Square / source glyph"),
        ("spr_padlock_freeplay", "Padlock / locked replay"),
    )
    sheet = Image.new("RGBA", (640, len(entries) * 96 + 24), (24, 24, 28, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row, (sprite_name, label) in enumerate(entries):
        sprite = model.sprites[sprite_name]
        region = model.textures[sprite.texture]
        page = decoded_pages[region.page]
        native = page.crop(normalized_crop_box(region, page.size))
        y = 16 + row * 96
        sheet.alpha_composite(native, (16, y))
        enlarged = native.resize((native.width * 2, native.height * 2), Image.Resampling.NEAREST)
        sheet.alpha_composite(enlarged, (96, y))
        draw.text((220, y + 8), f"{label}\n{region.name} / {native.width}x{native.height}\n{sprite_name}", fill=(240, 240, 240, 255), font=font)
    return sheet


def _state_sheet(states: list[tuple[str, Image.Image]]) -> Image.Image:
    scale = 1
    header = 28
    sheet = Image.new("RGBA", (LOGICAL_WIDTH * len(states), LOGICAL_HEIGHT * scale + header), (12, 12, 16, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (label, image) in enumerate(states):
        x = index * LOGICAL_WIDTH
        sheet.alpha_composite(image.resize((LOGICAL_WIDTH, LOGICAL_HEIGHT), Image.Resampling.NEAREST), (x, header))
        draw.text((x + 8, 8), label, fill=(255, 255, 255, 255), font=font)
    return sheet


def _write_json(path: pathlib.Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_csv(path: pathlib.Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise DesignKitError("cannot write empty inventory")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build(project_root: pathlib.Path, output: pathlib.Path) -> dict[str, object]:
    expected_output = (project_root / OUTPUT_RELATIVE).resolve()
    if output.resolve() != expected_output:
        raise DesignKitError(f"output must be the separated design-kit path: {expected_output}")
    fe_root = project_root / "game-extracted/pak/FE_MAIN/DATA/ENV/FE_MAIN"
    world = fe_root / "WORLD"
    text_root = fe_root / "TEXT/ENGLISH"
    script_path = world / "FE_MAIN.TXT"
    localization_path = text_root / "UI.TXT"
    script_data = script_path.read_bytes()
    localization_data = localization_path.read_bytes()
    model = parse_script(script_data.decode("cp1252"))
    localization = parse_localization(localization_data.decode("cp1252"))
    output.mkdir(parents=True, exist_ok=True)

    required_sprite_names = (
        "spr_grab02", "spr_border_tl", "spr_border_tr", "spr_border_bl", "spr_border_br",
        "spr_spartan_logo_flare", "spr_spartan_logo_small", "spr_button_1", "spr_button_2",
        "spr_button_3", "spr_button_4", "spr_padlock_freeplay", "spr_pal_top", "spr_pal_bottom",
    )
    target_pages = {
        model.textures[model.sprites[name].texture].page for name in required_sprite_names
    }
    target_pages.update(
        model.textures[model.emitters[name].texture].page
        for name in ("emitter2", "emitter4", "main_start_particle_01", "main_start_particle_02")
    )
    decoder = _load_tim2_decoder(project_root)
    decoded_pages: dict[str, Image.Image] = {}
    inventory_rows: list[dict[str, object]] = []
    source_hashes: dict[str, str] = {
        str(script_path.relative_to(project_root)).replace("\\", "/"): sha256(script_data),
        str(localization_path.relative_to(project_root)).replace("\\", "/"): sha256(localization_data),
    }
    for page_name in sorted(target_pages):
        filename = model.pages[page_name]
        source = _source_path_for_page(world, filename)
        data = source.read_bytes()
        decoded = decoder.decode_tim2(data)
        image = _rgba_image(decoded)
        decoded_pages[page_name] = image
        alpha = decoded.rgba[3::4]
        source_rel = str(source.relative_to(project_root)).replace("\\", "/")
        source_hashes[source_rel] = sha256(data)
        role, usage = TARGET_PAGE_ROLES[filename.casefold()]
        presentation, colour = TARGET_PAGE_PRESENTATION[filename.casefold()]
        inventory_rows.append({
            "sourcePak": "FE_MAIN.PAK", "internalPath": source_rel.split("pak/FE_MAIN/", 1)[1],
            "filename": source.name, "role": role, "width": decoded.width, "height": decoded.height,
            "imageType": decoded.image_type, "pixelFormat": "PSMT8 / IDTEX8",
            "clutType": decoded.clut_type, "paletteFormat": "RGBA8888 / 256-entry CSM1 CLUT",
            "alphaMin": min(alpha), "alphaMax": max(alpha), "mipCount": decoded.mip_count,
            "usage": usage, "menuStates": "all main_start states", "presentation": presentation,
            "colourModulated": colour, "shared": "yes", "animated": "yes" if "animation" in role else "no",
            "sourceSha256": sha256(data),
        })

    font_pages: dict[int, Image.Image] = {}
    font_dims: dict[int, bytes] = {}
    for index, font_name in enumerate(FONT_FILES):
        tm2 = text_root / f"{font_name}.TM2"
        dim = text_root / f"{font_name}.DIM"
        tm2_data, dim_data = tm2.read_bytes(), dim.read_bytes()
        decoded = decoder.decode_tim2(tm2_data)
        font_pages[index] = _rgba_image(decoded)
        font_dims[index] = dim_data
        for source, data in ((tm2, tm2_data), (dim, dim_data)):
            source_hashes[str(source.relative_to(project_root)).replace("\\", "/")] = sha256(data)
        alpha = decoded.rgba[3::4]
        inventory_rows.append({
            "sourcePak": "FE_MAIN.PAK", "internalPath": str(tm2.relative_to(project_root)).replace("\\", "/").split("pak/FE_MAIN/", 1)[1],
            "filename": tm2.name, "role": "font", "width": decoded.width, "height": decoded.height,
            "imageType": decoded.image_type, "pixelFormat": "PSMT8 / IDTEX8",
            "clutType": decoded.clut_type, "paletteFormat": "RGBA8888 / 256-entry CSM1 CLUT",
            "alphaMin": min(alpha), "alphaMax": max(alpha), "mipCount": decoded.mip_count,
            "usage": ("information and controller-prompt text" if index == 0 else
                      "unselected main-menu labels" if index == 1 else "selected/glow main-menu label"),
            "menuStates": "all main_start states", "presentation": "16x16 glyph grid; per-glyph crop; DIM advances",
            "colourModulated": "neutral", "shared": "yes", "animated": "no", "sourceSha256": sha256(tm2_data),
        })
        inventory_rows.append({
            "sourcePak": "FE_MAIN.PAK", "internalPath": str(dim.relative_to(project_root)).replace("\\", "/").split("pak/FE_MAIN/", 1)[1],
            "filename": dim.name, "role": "font-metrics", "width": "", "height": "",
            "imageType": "", "pixelFormat": "256 little-endian u16 advances after 64-byte prefix",
            "clutType": "", "paletteFormat": "", "alphaMin": "", "alphaMax": "", "mipCount": "",
            "usage": f"metrics paired with {font_name}.TM2", "menuStates": "all main_start states",
            "presentation": "not rendered; supplies horizontal advances", "colourModulated": "n/a",
            "shared": "yes", "animated": "no",
            "sourceSha256": sha256(dim_data),
        })

    before_hashes = dict(source_hashes)
    layers: dict[str, Image.Image] = {}
    original = _render_state(model, localization, decoded_pages, font_pages, font_dims, "new_game", True, layers)
    options = _render_state(model, localization, decoded_pages, font_pages, font_dims, "options", True)
    locked_replay = _render_state(model, localization, decoded_pages, font_pages, font_dims, "replay_mission", True)

    outputs: list[dict[str, object]] = []
    outputs.append(_save_png(original, output / "original-reference.png"))
    outputs.append(_save_png(original.resize((1024, 896), Image.Resampling.NEAREST), output / "original-reference-nearest.png"))
    mapping1080 = aspect_mapping(1920, 1080)
    mapped = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    scaled = original.resize((int(mapping1080["centralWidth"]), int(mapping1080["centralHeight"])), Image.Resampling.NEAREST)
    mapped.alpha_composite(scaled, (int(mapping1080["offsetX"]), int(mapping1080["offsetY"])))
    outputs.append(_save_png(mapped, output / "original-reference-1080p.png"))
    outputs.append(_save_png(_glyph_sheet(model, decoded_pages), output / "glyph-contact-sheet.png"))
    outputs.append(_save_png(_state_sheet([
        ("New Game selected", original), ("Options selected", options), ("Replay locked", locked_replay)
    ]), output / "menu-state-contact-sheet.png"))
    for name, layer in layers.items():
        outputs.append(_save_png(layer, output / f"layer-{name}.png"))

    logo_page = decoded_pages[model.textures["tex_spartan_logo_small"].page]
    logo = Image.new("RGBA", (192, 64), (0, 0, 0, 0))
    for sprite_name in ("spr_spartan_logo_flare", "spr_spartan_logo_small"):
        sprite = model.sprites[sprite_name]
        region = model.textures[sprite.texture]
        crop = logo_page.crop(normalized_crop_box(region, logo_page.size)).resize((sprite.width, sprite.height), Image.Resampling.NEAREST)
        logo.alpha_composite(crop, (sprite.x - 64, sprite.y - 16))
    outputs.append(_save_png(logo, output / "logo-reference.png"))
    padlock_sprite = model.sprites["spr_padlock_freeplay"]
    padlock_region = model.textures[padlock_sprite.texture]
    padlock = decoded_pages[padlock_region.page].crop(normalized_crop_box(padlock_region, decoded_pages[padlock_region.page].size))
    outputs.append(_save_png(padlock, output / "padlock-reference.png"))

    text_measurements: dict[str, object] = {}
    for key in OPTION_KEYS:
        normal_name, glow_name = OPTION_TEXT_NAMES[key]
        label_key = model.labels[model.texts[normal_name].label].casefold()
        value = localization[label_key]
        _, normal_advance = render_text(font_pages[1], font_dims[1], value, 512, 32)
        _, glow_advance = render_text(font_pages[2], font_dims[2], value, 512, 32)
        text_measurements[key] = {"value": value, "normalAdvance": normal_advance, "glowAdvance": glow_advance}

    layout = {
        "screen": {
            "logicalWidth": LOGICAL_WIDTH, "logicalHeight": LOGICAL_HEIGHT,
            "storageAspect": f"{LOGICAL_WIDTH}:{LOGICAL_HEIGHT}", "displayAspect": "4:3",
            "pixelAspect": "7:6", "origin": "top-left", "positiveX": "right", "positiveY": "down",
            "safeArea": {"x": 0, "y": 0, "width": 512, "height": 448},
        },
        "targetMenu": TARGET_MENU,
        "menuDeclarationLine": 3974,
        "drawOrder": model.menus[TARGET_MENU],
        "drawOrderExpanded": [
            child for item in model.menus[TARGET_MENU] for child in expand_group(model, item)
        ],
        "sprites": {name: asdict(model.sprites[name]) for name in required_sprite_names},
        "textures": {name: asdict(model.textures[name]) for name in (
            "tex_grab02", "tex_bands", "tex_spartan_logo_small", "tex_spartan_logo_flare",
            "tex_icons_button_1", "tex_icons_button_2", "tex_icons_button_3", "tex_icons_button_4", "tex_padlock",
        )},
        "menuOptions": {
            key: {
                "normal": asdict(model.texts[OPTION_TEXT_NAMES[key][0]]),
                "selected": asdict(model.texts[OPTION_TEXT_NAMES[key][1]]),
                "localizedText": text_measurements[key]["value"],
                "restPosition": [model.texts[OPTION_TEXT_NAMES[key][0]].x, model.texts[OPTION_TEXT_NAMES[key][0]].y],
            } for key in OPTION_KEYS
        },
        "prompts": {
            "back": {"glyph": "spr_button_2", "text": "text_back", "semanticAction": "BACK"},
            "ok": {"glyph": "spr_button_1", "text": "text_ok", "semanticAction": "CONFIRM"},
        },
        "padlock": {
            "sprite": asdict(model.sprites["spr_padlock_freeplay"]), "nativeCrop": list(normalized_crop_box(padlock_region, decoded_pages[padlock_region.page].size)),
            "condition": "show when maxlevel == 0; hide when maxlevel > 0",
            "activation": "locked replay confirmation plays sfx_locked and flashes colour white then neutral",
        },
        "emitters": {name: asdict(model.emitters[name]) for name in ("emitter2", "emitter4", "main_start_particle_01", "main_start_particle_02")},
        "mapping": {"1920x1080": mapping1080, "2560x1440": aspect_mapping(2560, 1440), "3840x2160": aspect_mapping(3840, 2160)},
        "textMeasurements": text_measurements,
        "limitations": [
            "Emitter particles are stochastic/procedural and are represented in metadata, not fabricated in the deterministic still.",
            "Background RGB 148/128 is inherited from the immediately preceding titles state because main_start does not reset it; runtime capture confirmation is pending.",
            "No runtime capture exists locally, so final pixel-position validation remains pending.",
        ],
    }
    _write_json(output / "layout.json", layout)
    _write_csv(output / "asset-inventory.csv", inventory_rows)
    _write_json(output / "asset-inventory.json", inventory_rows)

    font_notes = """# Main-menu font notes

- English main-menu labels come from `UI.TXT` keys referenced through script `LABEL` declarations.
- Unselected options use `FONT18.TM2` and selected options swap to `FONT18G.TM2`.
- Both atlases use 32x32 cells in a 16x16 grid and share identical 256-entry DIM advances.
- Information/footer and controller-prompt text uses `FONT14`, with 16x16 cells.
- Character index is `codepoint - 32` for the target ASCII strings. DIM stores one little-endian u16 advance per glyph after its 64-byte prefix.
- No independent kerning table was found. The target strings use advances only.
- The selected glow is baked into `FONT18G`; there is no replacement font, generated outline, or added shadow in the reference.
"""
    (output / "font-notes.md").write_text(font_notes, encoding="utf-8", newline="\n")
    state_notes = """# Main-menu state notes

- Entry resets selected text colour, starts main-menu music, enables four procedural emitters, applies padlock state, and selects New Game.
- Selection hides the normal text object for one option and shows its matching FONT18G object at the same coordinates.
- A selection event runs `icon_shaker`: +16 then -16 logical X over ten ticks, followed by a position reset. It is not a persistent selection-bar animation.
- Confirmation flashes the selected text between bright and transparent three times before transitioning.
- Single Mission Replay shows a padlock while `maxlevel == 0`. Confirming it plays the locked sound and flashes the lock from white back to neutral; no transition occurs.
- Smoke and logo glows are script emitters. The deterministic still deliberately represents the zero-particle static composition rather than inventing a runtime particle frame.
- `ATTRACT.PSS`/`ATTRACT_PAL.PSS` belong to the preceding title-screen idle flow and are not part of `main_start`.
"""
    (output / "state-notes.md").write_text(state_notes, encoding="utf-8", newline="\n")

    after_hashes = {
        path: sha256((project_root / path).read_bytes()) for path in source_hashes
    }
    if before_hashes != after_hashes:
        raise DesignKitError("a source asset changed while building the design kit")
    manifest = {
        "schemaVersion": 1,
        "generator": "tools/reforged/frontend/main_menu_design_kit.py",
        "sourcePak": "FE_MAIN.PAK",
        "targetMenu": TARGET_MENU,
        "sourceHashes": source_hashes,
        "sourceUnchanged": True,
        "contributingTexturePages": len(target_pages) + len(FONT_FILES),
        "inventoryRecords": len(inventory_rows),
        "directSpriteDeclarations": 12,
        "proceduralEmitters": 4,
        "visibleTextObjectsPerState": 9,
        "outputs": outputs,
        "runtimeCaptureValidation": "PENDING: no existing local main-menu capture found",
        "referencePolicy": "Original dimensions/alpha/colour; nearest-neighbour only; no replacement art",
    }
    _write_json(output / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output = args.output.resolve() if args.output else root / OUTPUT_RELATIVE
    manifest = build(root, output)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
