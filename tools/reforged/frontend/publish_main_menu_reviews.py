#!/usr/bin/env python3
"""Publish deterministic, Reforged-only main-menu review renders.

The outputs contain the project-created menu wireframe/placeholders and the
human-approved Reforged logo. Original game captures and extracted assets are
neither read nor accepted by this publisher.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

from PIL import Image, ImageDraw


ROOT = pathlib.Path(__file__).resolve().parents[3]
OUTPUT_ROOT = ROOT / "assets/reforged/frontend/review/main-menu/current"
LOGO_PATH = ROOT / "assets/reforged/frontend/main-menu/logo/approved/runtime/spartan-logo-approved.png"
BACKGROUND_PATH = ROOT / "assets/reforged/frontend/main-menu/background/approved/runtime/spartan-background-approved.jpg"
POINTER_SOURCE_PATH = ROOT / "assets/reforged/frontend/main-menu/pointer/approved/source/spartan-selection-pointer-approved.jpg"
POINTER_RUNTIME_PATH = ROOT / "assets/reforged/frontend/main-menu/pointer/approved/runtime/spartan-selection-pointer-approved.png"
PROMPT_SOURCE_PATH = ROOT / "assets/reforged/frontend/main-menu/prompts/playstation/approved/source/spartan-playstation-shields-approved.jpg"
PADLOCK_SOURCE_PATH = ROOT / "assets/reforged/frontend/main-menu/padlock/approved/source/spartan-padlock-approved.jpg"
PADLOCK_RUNTIME_PATH = ROOT / "assets/reforged/frontend/main-menu/padlock/approved/runtime/spartan-padlock-approved.png"
TOKENS_PATH = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
LOCALE_PATH = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
EXPECTED_LOGO_SHA256 = "b57304192c2b811a8f49b3b235617082ab8b5d4319a2867d08b2df671cd1d42d"
EXPECTED_LOGO_SIZE = (2172, 724)
EXPECTED_BACKGROUND_SHA256 = "76ceaa4eb1a68f85824205e70df86b068196d6b378b8eee802cc531a14c7fad5"
EXPECTED_BACKGROUND_SIZE = (1280, 720)
EXPECTED_POINTER_SOURCE_SHA256 = "8938fde3105960d2db38b86c8914ea90e79474ad950e556b818d6059d4752833"
EXPECTED_POINTER_RUNTIME_SHA256 = "c3c174f1fe035bb02d7c39eb43917c0c4ecbdb80056bd16ae8862631a1077425"
EXPECTED_PROMPT_SOURCE_SHA256 = "0ad9b4e09f91602617516cd48e992d0e421bb1a39ff86ca680441f384fbb8af6"
EXPECTED_PROMPT_RUNTIME_SHA256 = {
    "TRIANGLE": "83fb48f84a6cec78b2bac5bc2d9c5a8cd06749fe08a11dcd490deef746d3d35c",
    "CIRCLE": "f70305a12930d273708e62995c0b8086d051d90c4fc7e60deb7fe680d5622662",
    "CROSS": "6cb1178304bc5e027fc0c3f1c8ec4ae9719af904f3d7ab59cd659bd2dfa1d97e",
    "SQUARE": "f3760801744438327e3bda04e828ba4eca062c2c98435636628b8599363ed342",
}
EXPECTED_PADLOCK_SOURCE_SHA256 = "5cd5b57030d9f37eaec89b3fabddbf5a6e746eea7dc1dd58d002d302e013a04a"
EXPECTED_PADLOCK_RUNTIME_SHA256 = "bfa98d9838ba6e15a5b72a7456ebbe4d0f02de3a03f372b1800e16c4a769933f"
FONT_FILES = {
    ROOT / "assets/reforged/frontend/main-menu/fonts/cinzel/Cinzel-Regular.ttf": "af0031129f27dc752e8629a80b793d27abea94027faa27cc660c3fc33f607a1f",
    ROOT / "assets/reforged/frontend/main-menu/fonts/cinzel/Cinzel-Bold.ttf": "0c23ec565db45c5508ee95889c60ad87debd167ca07167a43a5d68572b4e2eac",
}
TARGETS = {
    "main-menu-1080p.png": (1920, 1080),
    "main-menu-1440p.png": (2560, 1440),
    "main-menu-4k.png": (3840, 2160),
    "main-menu-21x9.png": (2560, 1080),
}
DIAGNOSTIC_NAME = "menu-typography-material-diagnostic.png"
DIAGNOSTIC_SIZE = (1920, 1080)
POINTER_DIAGNOSTIC_NAME = "selection-pointer-diagnostic.png"
POINTER_DIAGNOSTIC_SIZE = (1600, 700)
PROMPT_DIAGNOSTIC_NAME = "playstation-shield-prompts-diagnostic.png"
PROMPT_DIAGNOSTIC_SIZE = (1600, 900)
PADLOCK_DIAGNOSTIC_NAME = "locked-padlock-diagnostic.png"
PADLOCK_DIAGNOSTIC_SIZE = (1400, 800)


def sha256_path(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_ui_module():
    module_path = ROOT / "tools/reforged/frontend/main_menu_reforged.py"
    spec = importlib.util.spec_from_file_location("main_menu_public_review", module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load menu renderer: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_logo() -> Image.Image:
    if not LOGO_PATH.is_file():
        raise FileNotFoundError(f"approved runtime logo is missing: {LOGO_PATH}")
    digest = sha256_path(LOGO_PATH)
    if digest != EXPECTED_LOGO_SHA256:
        raise ValueError(f"approved runtime logo hash mismatch: {digest}")
    with Image.open(LOGO_PATH) as source:
        source.load()
        if source.format != "PNG" or source.mode != "RGBA" or source.size != EXPECTED_LOGO_SIZE:
            raise ValueError(
                f"unexpected approved runtime logo: {source.format}/{source.mode}/{source.size}"
            )
        return source.copy()


def validate_background() -> None:
    if not BACKGROUND_PATH.is_file():
        raise FileNotFoundError(f"approved runtime background is missing: {BACKGROUND_PATH}")
    digest = sha256_path(BACKGROUND_PATH)
    if digest != EXPECTED_BACKGROUND_SHA256:
        raise ValueError(f"approved runtime background hash mismatch: {digest}")
    with Image.open(BACKGROUND_PATH) as source:
        source.load()
        if source.format != "JPEG" or source.mode != "RGB" or source.size != EXPECTED_BACKGROUND_SIZE:
            raise ValueError(
                f"unexpected approved runtime background: {source.format}/{source.mode}/{source.size}"
            )


def validate_pointer() -> None:
    if sha256_path(POINTER_SOURCE_PATH) != EXPECTED_POINTER_SOURCE_SHA256:
        raise ValueError("approved pointer source hash mismatch")
    if sha256_path(POINTER_RUNTIME_PATH) != EXPECTED_POINTER_RUNTIME_SHA256:
        raise ValueError("approved pointer runtime hash mismatch")
    with Image.open(POINTER_SOURCE_PATH) as source:
        if source.format != "JPEG" or source.mode != "RGB" or source.size != (1280, 427):
            raise ValueError("unexpected approved pointer source metadata")
    with Image.open(POINTER_RUNTIME_PATH) as runtime:
        if runtime.format != "PNG" or runtime.mode != "RGBA" or runtime.size != (1228, 282):
            raise ValueError("unexpected approved pointer runtime metadata")


def validate_playstation_prompts(tokens: dict[str, object]) -> None:
    if sha256_path(PROMPT_SOURCE_PATH) != EXPECTED_PROMPT_SOURCE_SHA256:
        raise ValueError("approved PlayStation prompt source hash mismatch")
    for glyph, expected in EXPECTED_PROMPT_RUNTIME_SHA256.items():
        asset_id = {"TRIANGLE": "glyphTriangle", "CIRCLE": "glyphCircle", "CROSS": "glyphCross", "SQUARE": "glyphSquare"}[glyph]
        relative = tokens["assets"][asset_id]  # type: ignore[index]
        path = ROOT / "assets/reforged/frontend/main-menu" / str(relative)
        if sha256_path(path) != expected:
            raise ValueError(f"approved PlayStation prompt hash mismatch: {glyph}")
        with Image.open(path) as prompt:
            if prompt.format != "PNG" or prompt.mode != "RGBA" or prompt.size != (448, 448):
                raise ValueError(f"unexpected approved PlayStation prompt metadata: {glyph}")


def validate_padlock() -> None:
    if sha256_path(PADLOCK_SOURCE_PATH) != EXPECTED_PADLOCK_SOURCE_SHA256:
        raise ValueError("approved padlock source hash mismatch")
    if sha256_path(PADLOCK_RUNTIME_PATH) != EXPECTED_PADLOCK_RUNTIME_SHA256:
        raise ValueError("approved padlock runtime hash mismatch")
    with Image.open(PADLOCK_SOURCE_PATH) as source:
        if source.format != "JPEG" or source.mode != "RGB" or source.size != (1280, 1260):
            raise ValueError("unexpected approved padlock source metadata")
    with Image.open(PADLOCK_RUNTIME_PATH) as runtime:
        if runtime.format != "PNG" or runtime.mode != "RGBA" or runtime.size != (520, 724):
            raise ValueError("unexpected approved padlock runtime metadata")


def validate_fonts() -> None:
    for path, expected in FONT_FILES.items():
        if not path.is_file() or sha256_path(path) != expected:
            raise ValueError(f"configured Cinzel font is missing or changed: {path}")


def render_reviews() -> dict[str, dict[str, object]]:
    ui = load_ui_module()
    logo = validate_logo()
    validate_background()
    validate_pointer()
    validate_fonts()
    tokens = ui.load_json(TOKENS_PATH)
    validate_playstation_prompts(tokens)
    validate_padlock()
    if tokens["assets"]["logo"] != "logo/approved/runtime/spartan-logo-approved.png":
        raise ValueError("menu tokens are not bound to the approved runtime logo")
    if tokens["assets"]["background"] != "background/approved/runtime/spartan-background-approved.jpg":
        raise ValueError("menu tokens are not bound to the approved runtime background")
    if tokens["assets"]["selectionMarker"] != "pointer/approved/runtime/spartan-selection-pointer-approved.png":
        raise ValueError("menu tokens are not bound to the approved runtime pointer")
    if tokens["assets"]["padlock"] != "padlock/approved/runtime/spartan-padlock-approved.png":
        raise ValueError("menu tokens are not bound to the approved runtime padlock")
    if not tokens["background"].get("approvedPlateIncludesOrnamentBands"):
        raise ValueError("approved background must suppress duplicate ornament overlays")
    strings = ui.load_json(LOCALE_PATH)["strings"]
    state = ui.MenuState(ui.build_main_start(maxlevel=0), "new_game")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, object]] = {}
    for filename, dimensions in TARGETS.items():
        image = ui.render_wireframe(*dimensions, state, tokens, strings, logo_image=logo)
        if image.mode != "RGB" or image.size != dimensions:
            raise RuntimeError(f"unexpected review render metadata: {filename}")
        output = OUTPUT_ROOT / filename
        image.save(output, "PNG", optimize=False, compress_level=9)
        manifest[filename] = {
            "dimensions": list(dimensions),
            "mode": image.mode,
            "sha256": sha256_path(output),
            "bytes": output.stat().st_size,
            "approvedLogo": str(LOGO_PATH.relative_to(ROOT)).replace("\\", "/"),
            "approvedBackground": str(BACKGROUND_PATH.relative_to(ROOT)).replace("\\", "/"),
            "fontFamily": "Cinzel",
            "approvedPointer": str(POINTER_RUNTIME_PATH.relative_to(ROOT)).replace("\\", "/"),
            "approvedPromptSheet": str(PROMPT_SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "approvedPadlock": str(PADLOCK_RUNTIME_PATH.relative_to(ROOT)).replace("\\", "/"),
            "provenance": "project-created Reforged menu renderer with approved background, logo, selection pointer, PlayStation prompts, and padlock",
        }
    diagnostic = Image.new("RGB", DIAGNOSTIC_SIZE, (7, 13, 23))
    regular_normal = ui._font(52, tokens, "regular")
    bold_normal = ui._font(56, tokens, "bold")
    bold_enlarged = ui._font(160, tokens, "bold")
    samples = (
        ("NEW GAME", bold_normal, "selected", (190, 64), 1.0, "new-selected-normal"),
        ("LOAD GAME", bold_normal, "selected", (950, 64), 1.0, "load-selected-normal"),
        ("LOAD GAME", regular_normal, "unselected", (1450, 68), 1.0, "load-unselected-normal"),
        ("NEW GAME", bold_enlarged, "selected", (300, 310), 160 / 56, "new-selected-enlarged"),
        ("LOAD GAME", bold_enlarged, "selected", (1050, 620), 160 / 56, "load-selected-enlarged"),
    )
    layer_stats: dict[str, dict[str, int]] = {}
    for text, font, state_name, position, scale, sample_name in samples:
        layer_stats[sample_name] = ui.render_material_text(
            diagnostic, position, text, font, state_name, scale=scale
        )
    pointer_stats = {
        "normal-beside-new": ui.render_selection_pointer(
            diagnostic, (173, 99), 96, 22
        ),
        "normal-beside-load": ui.render_selection_pointer(
            diagnostic, (933, 99), 96, 22
        ),
        "enlarged-beside-new": ui.render_selection_pointer(
            diagnostic, (251, 410), round(96 * 160 / 56), round(22 * 160 / 56)
        ),
        "enlarged-beside-load": ui.render_selection_pointer(
            diagnostic, (1001, 720), round(96 * 160 / 56), round(22 * 160 / 56)
        ),
        "enlarged-isolated": ui.render_selection_pointer(
            diagnostic, (680, 940), 384, 88
        ),
    }
    diagnostic_path = OUTPUT_ROOT / DIAGNOSTIC_NAME
    diagnostic.save(diagnostic_path, "PNG", optimize=False, compress_level=9)
    manifest[DIAGNOSTIC_NAME] = {
        "dimensions": list(DIAGNOSTIC_SIZE),
        "mode": diagnostic.mode,
        "sha256": sha256_path(diagnostic_path),
        "bytes": diagnostic_path.stat().st_size,
        "fontFamily": "Cinzel",
        "samples": [
            "selected NEW GAME at 56 px with approved 96x22 pointer",
            "selected LOAD GAME at 56 px with approved 96x22 pointer",
            "unselected LOAD GAME at 52 px", "selected NEW GAME enlarged to 160 px",
            "selected LOAD GAME enlarged to 160 px", "approved pointer enlarged to 384x88",
        ],
        "materialLayers": layer_stats,
        "pointerLayers": pointer_stats,
        "provenance": "project-created deterministic typography diagnostic using approved pointer art",
    }

    pointer_diagnostic = Image.new("RGB", POINTER_DIAGNOSTIC_SIZE, (7, 13, 23))
    pointer_draw = ImageDraw.Draw(pointer_diagnostic)
    heading_font = ui._font(22, tokens, "regular")
    pointer_draw.text((40, 30), "HUMAN-APPROVED SELECTION POINTER — RUNTIME INTEGRATION", font=heading_font, fill=(240, 233, 217))
    pointer_draw.text((40, 62), f"source 1280x427 JPEG  {EXPECTED_POINTER_SOURCE_SHA256}", font=heading_font, fill=(176, 179, 178))
    pointer_draw.text((40, 92), f"runtime 1228x282 RGBA  {EXPECTED_POINTER_RUNTIME_SHA256}", font=heading_font, fill=(176, 179, 178))
    diagnostic_stats = {
        "enlarged": ui.render_selection_pointer(pointer_diagnostic, (610, 205), 540, 124),
        "menu-scale-new": ui.render_selection_pointer(pointer_diagnostic, (180, 360), 96, 22),
        "menu-scale-load": ui.render_selection_pointer(pointer_diagnostic, (180, 460), 96, 22),
    }
    selected_font = ui._font(56, tokens, "bold")
    ui.render_material_text(pointer_diagnostic, (197, 325), "NEW GAME", selected_font, "selected")
    ui.render_material_text(pointer_diagnostic, (197, 425), "LOAD GAME", selected_font, "selected")
    pointer_draw.rectangle((70, 349, 166, 371), outline=(92, 148, 178), width=1)
    pointer_draw.text((40, 520), "Visible design bounds: 96x22 px at 1920x1080; right edge anchored 17 px left of selected label.", font=heading_font, fill=(216, 212, 200))
    pointer_diagnostic_path = OUTPUT_ROOT / POINTER_DIAGNOSTIC_NAME
    pointer_diagnostic.save(pointer_diagnostic_path, "PNG", optimize=False, compress_level=9)
    manifest[POINTER_DIAGNOSTIC_NAME] = {
        "dimensions": list(POINTER_DIAGNOSTIC_SIZE),
        "mode": pointer_diagnostic.mode,
        "sha256": sha256_path(pointer_diagnostic_path),
        "bytes": pointer_diagnostic_path.stat().st_size,
        "sourceSha256": EXPECTED_POINTER_SOURCE_SHA256,
        "runtimeSha256": EXPECTED_POINTER_RUNTIME_SHA256,
        "samples": diagnostic_stats,
        "provenance": "public-safe project diagnostic using locked approved Reforged pointer artwork",
    }

    prompt_diagnostic = Image.new("RGB", PROMPT_DIAGNOSTIC_SIZE, (7, 13, 23))
    prompt_draw = ImageDraw.Draw(prompt_diagnostic)
    prompt_heading = ui._font(22, tokens, "regular")
    prompt_draw.text((40, 28), "HUMAN-APPROVED PLAYSTATION SHIELD PROMPTS", font=prompt_heading, fill=(240, 233, 217))
    prompt_draw.text((40, 60), f"source 1280x853 JPEG  {EXPECTED_PROMPT_SOURCE_SHA256}", font=prompt_heading, fill=(176, 179, 178))
    glyphs = ("TRIANGLE", "CIRCLE", "CROSS", "SQUARE")
    centres = (220, 610, 1000, 1390)
    hash_font = ui._font(16, tokens, "regular")
    prompt_stats: dict[str, dict[str, int | str]] = {}
    for glyph, x in zip(glyphs, centres):
        prompt_stats[f"{glyph.lower()}-enlarged"] = ui.render_playstation_prompt_shield(
            prompt_diagnostic, (x, 265), 280, glyph, tokens
        )
        prompt_stats[f"{glyph.lower()}-ui"] = ui.render_playstation_prompt_shield(
            prompt_diagnostic, (x, 570), 52, glyph, tokens
        )
        prompt_draw.rectangle((x - 26, 544, x + 26, 596), outline=(92, 148, 178), width=1)
        label = f"{glyph} — 52 px"
        width = prompt_draw.textlength(label, font=prompt_heading)
        prompt_draw.text((x - width / 2, 625), label, font=prompt_heading, fill=(216, 212, 200))
    for index, glyph in enumerate(glyphs):
        x = 40 if index % 2 == 0 else 810
        y = 690 + (index // 2) * 34
        prompt_draw.text((x, y), f"{glyph}: {EXPECTED_PROMPT_RUNTIME_SHA256[glyph]}", font=hash_font, fill=(176, 179, 178))
    prompt_draw.text((40, 820), "Normalized canvas: 448x448 RGBA. Visible diameter: 416 runtime pixels; 52 design pixels at 1920x1080.", font=prompt_heading, fill=(176, 179, 178))
    prompt_diagnostic_path = OUTPUT_ROOT / PROMPT_DIAGNOSTIC_NAME
    prompt_diagnostic.save(prompt_diagnostic_path, "PNG", optimize=False, compress_level=9)
    manifest[PROMPT_DIAGNOSTIC_NAME] = {
        "dimensions": list(PROMPT_DIAGNOSTIC_SIZE), "mode": prompt_diagnostic.mode,
        "sha256": sha256_path(prompt_diagnostic_path),
        "bytes": prompt_diagnostic_path.stat().st_size,
        "sourceSha256": EXPECTED_PROMPT_SOURCE_SHA256,
        "runtimeSha256": EXPECTED_PROMPT_RUNTIME_SHA256,
        "samples": prompt_stats,
        "provenance": "public-safe project diagnostic using locked approved Reforged PlayStation shield artwork",
    }

    padlock_diagnostic = Image.new("RGB", PADLOCK_DIAGNOSTIC_SIZE, (7, 13, 23))
    padlock_draw = ImageDraw.Draw(padlock_diagnostic)
    padlock_heading = ui._font(22, tokens, "regular")
    padlock_draw.text((40, 28), "HUMAN-APPROVED LOCKED-STATE PADLOCK", font=padlock_heading, fill=(240, 233, 217))
    padlock_draw.text((40, 60), f"source 1280x1260 JPEG  {EXPECTED_PADLOCK_SOURCE_SHA256}", font=padlock_heading, fill=(176, 179, 178))
    padlock_draw.text((40, 92), f"runtime 520x724 RGBA  {EXPECTED_PADLOCK_RUNTIME_SHA256}", font=padlock_heading, fill=(176, 179, 178))
    enlarged = ui.render_locked_padlock(padlock_diagnostic, (165, 375), 420, PADLOCK_RUNTIME_PATH)
    locked_font = ui._font(52, tokens, "regular")
    label_position = (680.0, 330.0)
    ui.render_material_text(padlock_diagnostic, label_position, "SINGLE MISSION REPLAY", locked_font, "locked")
    layout = ui.layout_for_viewport(1920, 1080, tokens)
    anchor, text_bounds = ui.locked_padlock_placement(layout, label_position, "SINGLE MISSION REPLAY", locked_font, tokens)
    menu_scale = ui.render_locked_padlock(padlock_diagnostic, anchor, tokens["padlock"]["visibleHeight"], PADLOCK_RUNTIME_PATH)
    padlock_draw.rectangle(text_bounds, outline=(92, 148, 178), width=1)
    padlock_draw.rectangle((menu_scale["pasteX"], menu_scale["pasteY"], menu_scale["pasteX"] + menu_scale["renderedWidth"], menu_scale["pasteY"] + menu_scale["renderedHeight"]), outline=(92, 148, 178), width=1)
    padlock_draw.text((40, 720), "Runtime alpha bounds: 520x724. UI visible size: 22x30 px. Label gap: 12 px.", font=padlock_heading, fill=(216, 212, 200))
    padlock_diagnostic_path = OUTPUT_ROOT / PADLOCK_DIAGNOSTIC_NAME
    padlock_diagnostic.save(padlock_diagnostic_path, "PNG", optimize=False, compress_level=9)
    manifest[PADLOCK_DIAGNOSTIC_NAME] = {
        "dimensions": list(PADLOCK_DIAGNOSTIC_SIZE), "mode": padlock_diagnostic.mode,
        "sha256": sha256_path(padlock_diagnostic_path), "bytes": padlock_diagnostic_path.stat().st_size,
        "sourceSha256": EXPECTED_PADLOCK_SOURCE_SHA256, "runtimeSha256": EXPECTED_PADLOCK_RUNTIME_SHA256,
        "samples": {"enlarged": enlarged, "menuScale": menu_scale, "textBounds": list(text_bounds)},
        "provenance": "public-safe project diagnostic using locked approved Reforged padlock artwork",
    }
    return manifest


def main() -> int:
    print(json.dumps(render_reviews(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
