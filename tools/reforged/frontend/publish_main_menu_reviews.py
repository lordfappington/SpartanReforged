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

from PIL import Image


ROOT = pathlib.Path(__file__).resolve().parents[3]
OUTPUT_ROOT = ROOT / "assets/reforged/frontend/review/main-menu/current"
LOGO_PATH = ROOT / "assets/reforged/frontend/main-menu/logo/approved/runtime/spartan-logo-approved.png"
BACKGROUND_PATH = ROOT / "assets/reforged/frontend/main-menu/background/approved/runtime/spartan-background-approved.jpg"
TOKENS_PATH = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
LOCALE_PATH = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
EXPECTED_LOGO_SHA256 = "b57304192c2b811a8f49b3b235617082ab8b5d4319a2867d08b2df671cd1d42d"
EXPECTED_LOGO_SIZE = (2172, 724)
EXPECTED_BACKGROUND_SHA256 = "76ceaa4eb1a68f85824205e70df86b068196d6b378b8eee802cc531a14c7fad5"
EXPECTED_BACKGROUND_SIZE = (1280, 720)
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
DIAGNOSTIC_SIZE = (1600, 720)


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


def validate_fonts() -> None:
    for path, expected in FONT_FILES.items():
        if not path.is_file() or sha256_path(path) != expected:
            raise ValueError(f"configured Cinzel font is missing or changed: {path}")


def render_reviews() -> dict[str, dict[str, object]]:
    ui = load_ui_module()
    logo = validate_logo()
    validate_background()
    validate_fonts()
    tokens = ui.load_json(TOKENS_PATH)
    if tokens["assets"]["logo"] != "logo/approved/runtime/spartan-logo-approved.png":
        raise ValueError("menu tokens are not bound to the approved runtime logo")
    if tokens["assets"]["background"] != "background/approved/runtime/spartan-background-approved.jpg":
        raise ValueError("menu tokens are not bound to the approved runtime background")
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
            "provenance": "project-created Reforged menu renderer, approved background, and approved logo",
        }
    diagnostic = Image.new("RGB", DIAGNOSTIC_SIZE, (7, 13, 23))
    regular_normal = ui._font(52, tokens, "regular")
    bold_normal = ui._font(56, tokens, "bold")
    bold_enlarged = ui._font(160, tokens, "bold")
    samples = (
        ("NEW GAME", bold_normal, "selected", (100, 62), 1.0, "selected-normal"),
        ("LOAD GAME", regular_normal, "unselected", (620, 65), 1.0, "unselected-normal"),
        ("NEW GAME", bold_enlarged, "selected", (100, 275), 160 / 56, "selected-enlarged"),
    )
    layer_stats: dict[str, dict[str, int]] = {}
    for text, font, state_name, position, scale, sample_name in samples:
        layer_stats[sample_name] = ui.render_material_text(
            diagnostic, position, text, font, state_name, scale=scale
        )
    diagnostic_path = OUTPUT_ROOT / DIAGNOSTIC_NAME
    diagnostic.save(diagnostic_path, "PNG", optimize=False, compress_level=9)
    manifest[DIAGNOSTIC_NAME] = {
        "dimensions": list(DIAGNOSTIC_SIZE),
        "mode": diagnostic.mode,
        "sha256": sha256_path(diagnostic_path),
        "bytes": diagnostic_path.stat().st_size,
        "fontFamily": "Cinzel",
        "samples": [
            "selected NEW GAME at 56 px", "selected NEW GAME enlarged to 160 px",
            "unselected LOAD GAME at 52 px",
        ],
        "materialLayers": layer_stats,
        "provenance": "project-created deterministic typography material diagnostic",
    }
    return manifest


def main() -> int:
    print(json.dumps(render_reviews(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
