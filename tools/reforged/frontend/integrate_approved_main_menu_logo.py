#!/usr/bin/env python3
"""Integrate the human-approved Reforged main-menu logo without redesign.

The approved PNG is copied byte-for-byte into archival and runtime locations.
This tool intentionally performs no vectorisation, colour correction, alpha
cleanup, sharpening, or layer extraction. Review renders are local/ignored.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys
from collections import Counter
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = pathlib.Path(__file__).resolve().parents[3]
INCOMING = ROOT / "assets/reforged/frontend/incoming/spartan-logo-approved.png"
APPROVED_ROOT = ROOT / "assets/reforged/frontend/main-menu/logo/approved"
SOURCE_PATH = APPROVED_ROOT / "source/spartan-logo-approved.png"
RUNTIME_PATH = APPROVED_ROOT / "runtime/spartan-logo-approved.png"
METADATA_PATH = APPROVED_ROOT / "metadata/spartan-logo-approved.json"
REVIEW_ROOT = ROOT / "assets/reforged/frontend/review/logo/approved"
TOKENS_PATH = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
LOCALE_PATH = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
EXPECTED_SOURCE_SHA256 = "b57304192c2b811a8f49b3b235617082ab8b5d4319a2867d08b2df671cd1d42d"
EXPECTED_SIZE = (2172, 724)


def sha256_path(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_source(path: pathlib.Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"approved artwork is missing: {path}")
    digest = sha256_path(path)
    if digest != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"approved artwork hash mismatch: {digest}")
    with Image.open(path) as image:
        image.load()
        if image.format != "PNG" or image.mode != "RGBA" or image.size != EXPECTED_SIZE:
            raise ValueError(
                f"unexpected approved artwork metadata: {image.format}/{image.mode}/{image.size}"
            )
        alpha = image.getchannel("A")
        counts = Counter(alpha.getdata())
        bbox = alpha.getbbox()
        return {
            "filename": path.name,
            "sha256": digest,
            "fileSize": path.stat().st_size,
            "format": image.format,
            "mode": image.mode,
            "dimensions": list(image.size),
            "aspectRatio": image.width / image.height,
            "alpha": {
                "convention": "straight alpha",
                "present": alpha.getextrema()[0] < 255,
                "range": list(alpha.getextrema()),
                "uniqueValues": len(counts),
                "transparentPixels": counts[0],
                "opaquePixels": counts[255],
                "partialPixels": sum(value for level, value in counts.items() if 0 < level < 255),
                "visibleBounds": list(bbox) if bbox else None,
            },
        }


def copy_exact(source: pathlib.Path, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    if source.read_bytes() != target.read_bytes():
        raise RuntimeError(f"byte-exact copy validation failed: {target}")


def load_ui_module():
    module_path = ROOT / "tools/reforged/frontend/main_menu_reforged.py"
    spec = importlib.util.spec_from_file_location("main_menu_reforged_approved", module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load menu renderer: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def approved_tokens(tokens: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(tokens))
    result["assets"]["logo"] = "logo/approved/runtime/spartan-logo-approved.png"
    # Divider and flare remain baked into the approved raster. Do not overlay
    # rejected experimental layers on top of approved art.
    result["assets"]["logoFlare"] = None
    result["assets"]["logoGlintMask"] = None
    return result


def render_reviews(source: pathlib.Path) -> list[str]:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    ui = load_ui_module()
    tokens = approved_tokens(ui.load_json(TOKENS_PATH))
    strings = ui.load_json(LOCALE_PATH)["strings"]
    logo = Image.open(source).convert("RGBA")
    state = ui.MenuState(ui.build_main_start(maxlevel=0), "new_game")
    targets = {
        "menu-approved-logo-1080p.png": (1920, 1080),
        "menu-approved-logo-1440p.png": (2560, 1440),
        "menu-approved-logo-4k.png": (3840, 2160),
        "menu-approved-logo-21x9.png": (2560, 1080),
    }
    outputs: list[pathlib.Path] = []
    rendered: dict[str, Image.Image] = {}
    for name, size in targets.items():
        image = ui.render_wireframe(*size, state, tokens, strings, logo_image=logo)
        path = REVIEW_ROOT / name
        image.save(path, "PNG", optimize=False, compress_level=9)
        rendered[name] = image
        outputs.append(path)

    dark = Image.new("RGB", (1600, 620), "#070c15")
    fitted = logo.copy()
    fitted.thumbnail((1480, 520), Image.Resampling.LANCZOS)
    dark.paste(fitted, ((dark.width - fitted.width) // 2, (dark.height - fitted.height) // 2), fitted)
    dark_path = REVIEW_ROOT / "approved-logo-dark-background.png"
    dark.save(dark_path, "PNG", optimize=False, compress_level=9)
    outputs.append(dark_path)

    # Design-evolution review remains ignored because it contains original PS2 imagery.
    candidates = [
        ("ORIGINAL PS2", ROOT / "assets/reforged/frontend/design-kit/main-menu/logo-reference.png"),
        ("REJECTED PASS 1A", ROOT / "assets/reforged/frontend/main-menu/logo/logo_runtime/logo-A.png"),
        ("REJECTED PASS 2A", ROOT / "assets/reforged/frontend/main-menu/logo/pass2/logo_runtime/logo-pass2A.png"),
        ("HUMAN-APPROVED", source),
    ]
    sheet = Image.new("RGB", (1920, 1900), "#070c15")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 30)
    except OSError:
        font = ImageFont.load_default()
    y = 35
    for label, path in candidates:
        draw.text((55, y), label, fill="#d8d6cf", font=font)
        candidate = Image.open(path).convert("RGBA")
        candidate.thumbnail((1500, 300), Image.Resampling.LANCZOS)
        sheet.paste(candidate, (320, y), candidate)
        y += 340
    draw.text((55, y), "APPROVED — ACTUAL 1080P MENU PRESENTATION", fill="#d8d6cf", font=font)
    menu = rendered["menu-approved-logo-1080p.png"]
    menu.thumbnail((1500, 844), Image.Resampling.LANCZOS)
    sheet.paste(menu, (320, y))
    review_path = REVIEW_ROOT / "logo-final-review.png"
    sheet.save(review_path, "PNG", optimize=False, compress_level=9)
    outputs.append(review_path)
    return [str(path.relative_to(ROOT)).replace("\\", "/") for path in outputs]


def integrate(source: pathlib.Path) -> dict[str, Any]:
    source_info = inspect_source(source)
    copy_exact(source, SOURCE_PATH)
    copy_exact(source, RUNTIME_PATH)
    reviews = render_reviews(RUNTIME_PATH)
    metadata = {
        "schemaVersion": 1,
        "approvalStatus": "HUMAN APPROVED",
        "source": {
            **source_info,
            "incomingPath": str(source.relative_to(ROOT)).replace("\\", "/"),
            "archivalPath": str(SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "processing": {
            "visualDesignAltered": False,
            "vectorisationAttempted": False,
            "cleanupRequired": False,
            "cleanupPerformed": False,
            "resizePerformed": False,
            "sourceAndRuntimeByteIdentical": True,
        },
        "layers": {
            "dividerExtractionAttempted": False,
            "dividerExtractionSuccessful": False,
            "flareExtractionAttempted": False,
            "flareExtractionSuccessful": False,
            "decision": "Use the complete approved raster; destructive layer separation was not justified.",
        },
        "runtime": {
            "path": str(RUNTIME_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_path(RUNTIME_PATH),
            "dimensions": list(EXPECTED_SIZE),
            "format": "PNG RGBA",
            "colourSpace": "sRGB (PNG has no embedded profile)",
            "alphaConvention": "straight alpha",
            "anchor": "top-left in the central 1920x1080 composition",
            "designPosition": [130, 90],
            "designBounds": [650, 210],
            "nominalDisplay1080p": [630, 210],
            "nominalDisplay1440p": [840, 280],
            "nominalDisplay4k": [1260, 420],
            "ultrawidePolicy": "central 16:9 composition; environment-only side extension",
        },
        "reviews": reviews,
        "retainedResearch": {
            "pass1": "assets/reforged/frontend/main-menu/logo",
            "pass2": "assets/reforged/frontend/main-menu/logo/pass2",
            "pass2BevelResearchRetained": True,
        },
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, default=INCOMING)
    args = parser.parse_args()
    metadata = integrate(args.source.resolve())
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
