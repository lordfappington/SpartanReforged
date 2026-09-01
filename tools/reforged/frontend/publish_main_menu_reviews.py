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
TOKENS_PATH = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
LOCALE_PATH = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
EXPECTED_LOGO_SHA256 = "b57304192c2b811a8f49b3b235617082ab8b5d4319a2867d08b2df671cd1d42d"
EXPECTED_LOGO_SIZE = (2172, 724)
TARGETS = {
    "main-menu-1080p.png": (1920, 1080),
    "main-menu-1440p.png": (2560, 1440),
    "main-menu-4k.png": (3840, 2160),
    "main-menu-21x9.png": (2560, 1080),
}


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


def render_reviews() -> dict[str, dict[str, object]]:
    ui = load_ui_module()
    logo = validate_logo()
    tokens = ui.load_json(TOKENS_PATH)
    if tokens["assets"]["logo"] != "logo/approved/runtime/spartan-logo-approved.png":
        raise ValueError("menu tokens are not bound to the approved runtime logo")
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
            "provenance": "project-created Reforged menu renderer and approved Reforged logo",
        }
    return manifest


def main() -> int:
    print(json.dumps(render_reviews(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
