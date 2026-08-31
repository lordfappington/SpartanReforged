#!/usr/bin/env python3
"""Build the deterministic Reforged main-menu logo and local review package.

The original decoded logo is read only to measure and trace its silhouette.
The committed master is custom vector geometry; all metallic treatments are
procedural and share that geometry. Review composites stay in an ignored path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
from dataclasses import asdict, dataclass
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = pathlib.Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "assets/reforged/frontend/design-kit/main-menu/logo-reference.png"
SOURCE_TM2 = ROOT / "game-extracted/pak/FE_MAIN/DATA/ENV/FE_MAIN/WORLD/SPARTAN_LOGO.TM2"
TOKENS_PATH = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
LOCALE_PATH = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
ASSET_ROOT = ROOT / "assets/reforged/frontend/main-menu/logo"
SOURCE_ROOT = ASSET_ROOT / "logo_source"
RUNTIME_ROOT = ASSET_ROOT / "logo_runtime"
MASK_ROOT = ASSET_ROOT / "logo_masks"
METADATA_ROOT = ASSET_ROOT / "metadata"
REVIEW_ROOT = ROOT / "assets/reforged/frontend/review/logo"

EXPECTED_REFERENCE_SHA256 = "351e7f5b222011a081201fc64b347acff61009be18015284da11b26946887dae"
EXPECTED_TM2_SHA256 = "755e4dd82ec2d29c1dbc45136f9cbf92a25628a4e6859888ad7c7971b6a3e84c"
MASTER_SIZE = (2520, 840)
SOURCE_SCALE = 12.0
SOURCE_OFFSET = (72.0, 48.0)
TRACE_THRESHOLD = 192
PREFERRED_VARIANT = "A"


class LogoBuildError(ValueError):
    pass


@dataclass(frozen=True)
class Geometry:
    source_size: tuple[int, int]
    visible_alpha_bounds: tuple[int, int, int, int]
    spartan_bounds: tuple[int, int, int, int]
    subtitle_bounds: tuple[int, int, int, int]
    trademark_bounds: tuple[int, int, int, int]
    spartan_baseline: int
    subtitle_baseline: int
    line_gap: int
    spartan_width: int
    subtitle_width: int


VARIANTS: dict[str, dict[str, Any]] = {
    "A": {
        "description": "Faithful restrained aged gold with moderate edge relief and minimal wear.",
        "top": (239, 202, 121), "middle": (171, 125, 57), "bottom": (92, 58, 25),
        "highlight": 0.45, "wear": 0.10, "shadow": 0.30,
    },
    "B": {
        "description": "Aged bronze with darker recesses, stronger tonal irregularity, and visible surface wear.",
        "top": (207, 169, 91), "middle": (139, 91, 40), "bottom": (64, 40, 24),
        "highlight": 0.32, "wear": 0.24, "shadow": 0.40,
    },
    "C": {
        "description": "Cinematic warm gold with stronger upper-edge illumination and restrained wear.",
        "top": (255, 224, 145), "middle": (188, 135, 57), "bottom": (87, 52, 20),
        "highlight": 0.72, "wear": 0.13, "shadow": 0.34,
    },
}


def sha256_path(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_original_layers() -> tuple[Image.Image, Image.Image]:
    """Decode the verified source in memory and return the documented crops."""
    module_path = ROOT / "tools/conversion/tim2_decode.py"
    spec = importlib.util.spec_from_file_location("tim2_decode_logo_build", module_path)
    if not spec or not spec.loader:
        raise LogoBuildError("cannot load validated TIM2 decoder")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    decoded = module.decode_tim2(SOURCE_TM2.read_bytes())
    if (decoded.width, decoded.height) != (512, 512):
        raise LogoBuildError(f"unexpected SPARTAN_LOGO page size {(decoded.width, decoded.height)}")
    page = Image.frombytes("RGBA", (decoded.width, decoded.height), decoded.rgba)
    # FE_MAIN normalized 0..256 declarations resolve to these exact page crops.
    base = page.crop((0, 176, 192, 240))
    flare = page.crop((0, 240, 192, 256))
    return base, flare


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if not len(xs):
        raise LogoBuildError("empty alpha region")
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def measure_geometry(reference: Image.Image) -> Geometry:
    if reference.size != (192, 64):
        raise LogoBuildError(f"expected 192x64 reference, got {reference.size}")
    alpha = np.asarray(reference.getchannel("A"))
    visible = _bbox(alpha > 0)
    spartan = _bbox((alpha > 0) & _region_mask(alpha.shape, (0, 0, 170, 38)))
    subtitle = _bbox((alpha > 0) & _region_mask(alpha.shape, (0, 36, 175, 64)))
    trademark = _bbox((alpha > 0) & _region_mask(alpha.shape, (169, 0, 192, 16)))
    # Baselines are the lower face rows at alpha >= 192, excluding soft glow.
    main_face = _bbox((alpha >= 192) & _region_mask(alpha.shape, (0, 0, 170, 36)))
    subtitle_face = _bbox((alpha >= 192) & _region_mask(alpha.shape, (0, 36, 175, 64)))
    return Geometry(
        source_size=reference.size,
        visible_alpha_bounds=visible,
        spartan_bounds=spartan,
        subtitle_bounds=subtitle,
        trademark_bounds=trademark,
        spartan_baseline=main_face[3] - 1,
        subtitle_baseline=subtitle_face[3] - 1,
        line_gap=max(0, subtitle_face[1] - main_face[3]),
        spartan_width=spartan[2] - spartan[0],
        subtitle_width=subtitle[2] - subtitle[0],
    )


def _region_mask(shape: tuple[int, int], box: tuple[int, int, int, int]) -> np.ndarray:
    result = np.zeros(shape, dtype=bool)
    result[box[1]:box[3], box[0]:box[2]] = True
    return result


def trace_contours(reference: Image.Image) -> tuple[list[np.ndarray], np.ndarray]:
    # Trace a subpixel iso-contour from a high-quality interpolation of the
    # measured alpha field. This removes source-pixel stair steps while keeping
    # the original silhouette and avoids substituting an unrelated font.
    trace_scale = 8
    enlarged = reference.getchannel("A").resize(
        (reference.width * trace_scale, reference.height * trace_scale),
        Image.Resampling.LANCZOS,
    )
    alpha = np.asarray(enlarged)
    binary = (alpha >= TRACE_THRESHOLD).astype(np.uint8) * 255
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None or not contours:
        raise LogoBuildError("no contours found")
    simplified = []
    for contour in contours:
        traced = cv2.approxPolyDP(contour, 1.15, True).astype(np.float64)
        traced /= trace_scale
        simplified.append(traced)
    return simplified, hierarchy[0]


def contour_depth(index: int, hierarchy: np.ndarray) -> int:
    depth, parent = 0, int(hierarchy[index][3])
    while parent >= 0:
        depth += 1
        parent = int(hierarchy[parent][3])
    return depth


def write_geometry_svg(path: pathlib.Path, contours: list[np.ndarray]) -> None:
    parts: list[str] = []
    for contour in contours:
        points = contour[:, 0, :]
        if len(points) < 3:
            continue
        commands = [f"M {points[0,0]:.3f} {points[0,1]:.3f}"]
        commands.extend(f"L {x:.3f} {y:.3f}" for x, y in points[1:])
        commands.append("Z")
        parts.append(" ".join(commands))
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="2520" height="840" '
        'viewBox="-6 -4 210 70">\n'
        '  <title>SpartanReforged main-menu logo geometry</title>\n'
        '  <desc>Custom outline reconstruction traced from the legally owned 192x64 preservation reference; no font dependency.</desc>\n'
        f'  <path d="{" ".join(parts)}" fill="#ffffff" fill-rule="evenodd"/>\n'
        '</svg>\n'
    )
    path.write_text(svg, encoding="utf-8", newline="\n")


def rasterize_contours(contours: list[np.ndarray], hierarchy: np.ndarray) -> Image.Image:
    supersample = 2
    width, height = MASTER_SIZE[0] * supersample, MASTER_SIZE[1] * supersample
    mask = np.zeros((height, width), dtype=np.uint8)
    order = sorted(range(len(contours)), key=lambda i: contour_depth(i, hierarchy))
    for index in order:
        points = contours[index].astype(np.float64)
        points[:, 0, 0] = (points[:, 0, 0] * SOURCE_SCALE + SOURCE_OFFSET[0]) * supersample
        points[:, 0, 1] = (points[:, 0, 1] * SOURCE_SCALE + SOURCE_OFFSET[1]) * supersample
        colour = 255 if contour_depth(index, hierarchy) % 2 == 0 else 0
        cv2.fillPoly(mask, [np.rint(points).astype(np.int32)], colour, lineType=cv2.LINE_AA)
    image = Image.fromarray(mask).resize(MASTER_SIZE, Image.Resampling.LANCZOS)
    return image


def _lerp_colours(stops: tuple[tuple[int, int, int], ...], height: int) -> np.ndarray:
    y = np.linspace(0.0, 1.0, height)[:, None]
    top, middle, bottom = (np.array(colour, dtype=np.float32) for colour in stops)
    result = np.empty((height, 3), dtype=np.float32)
    upper = y[:, 0] <= 0.48
    u = np.clip(y[:, 0] / 0.48, 0, 1)[:, None]
    l = np.clip((y[:, 0] - 0.48) / 0.52, 0, 1)[:, None]
    result[upper] = top * (1 - u[upper]) + middle * u[upper]
    result[~upper] = middle * (1 - l[~upper]) + bottom * l[~upper]
    return result


def material_variant(mask_image: Image.Image, spec: dict[str, Any], seed: int) -> Image.Image:
    alpha = np.asarray(mask_image, dtype=np.float32) / 255.0
    binary = (alpha >= 0.5).astype(np.uint8)
    distance = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    height, width = alpha.shape
    gradient = _lerp_colours((spec["top"], spec["middle"], spec["bottom"]), height)
    rgb = np.broadcast_to(gradient[:, None, :], (height, width, 3)).copy()

    edge = np.exp(-distance / 16.0) * binary
    upper_edge = np.maximum(0.0, edge - np.roll(edge, 8, axis=0))
    rgb += upper_edge[..., None] * (105.0 * float(spec["highlight"]))
    lower_recess = np.maximum(0.0, edge - np.roll(edge, -8, axis=0))
    rgb -= lower_recess[..., None] * 38.0

    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, 1.0, (height, width)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 4.0)
    noise /= max(float(np.std(noise)), 1e-6)
    wear = float(spec["wear"])
    rgb += noise[..., None] * (15.0 * wear)
    pits = (noise < -1.45).astype(np.float32) * wear
    rgb -= pits[..., None] * 38.0

    # Shallow extrusion/self-shadow remains inside the master padding.
    shadow_mask = Image.fromarray(np.uint8(alpha * 255)).filter(ImageFilter.GaussianBlur(5))
    shadow = np.asarray(shadow_mask, dtype=np.float32) / 255.0
    shifted = np.zeros_like(shadow)
    shifted[8:, 7:] = shadow[:-8, :-7]
    shadow = shifted * float(spec["shadow"])
    out_alpha = np.maximum(alpha, shadow * 0.72)
    shadow_rgb = np.zeros_like(rgb) + np.array((24, 14, 8), dtype=np.float32)
    face_weight = alpha[..., None]
    rgb = shadow_rgb * (1.0 - face_weight) + rgb * face_weight
    rgba = np.dstack((np.clip(rgb, 0, 255).astype(np.uint8), np.clip(out_alpha * 255, 0, 255).astype(np.uint8)))
    return Image.fromarray(rgba)


def build_glow(mask: Image.Image) -> Image.Image:
    blurred = mask.filter(ImageFilter.GaussianBlur(18))
    alpha = np.asarray(blurred, dtype=np.float32) * 0.20
    rgba = np.zeros((MASTER_SIZE[1], MASTER_SIZE[0], 4), dtype=np.uint8)
    rgba[:, :, :3] = (218, 164, 74)
    rgba[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(rgba)


def build_glint_mask(mask: Image.Image) -> Image.Image:
    yy, xx = np.mgrid[0:MASTER_SIZE[1], 0:MASTER_SIZE[0]]
    stripe = np.exp(-((xx - 0.62 * MASTER_SIZE[0] + yy * 0.55) / 42.0) ** 2)
    base = np.asarray(mask, dtype=np.float32) / 255.0
    return Image.fromarray(np.uint8(np.clip(stripe * base * 255, 0, 255)))


def build_flare() -> Image.Image:
    width, height = MASTER_SIZE[0], round(MASTER_SIZE[1] * 0.30)
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = width * 0.46, height * 0.5
    core = np.exp(-(((xx - cx) / 350.0) ** 2 + ((yy - cy) / 14.0) ** 2))
    halo = np.exp(-(((xx - cx) / 620.0) ** 2 + ((yy - cy) / 55.0) ** 2)) * 0.28
    alpha = np.clip((core + halo) * 90.0, 0, 90).astype(np.uint8)
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[:, :, :3] = (245, 191, 94)
    rgba[:, :, 3] = alpha
    return Image.fromarray(rgba)


def composite_on(image: Image.Image, background: tuple[int, int, int]) -> Image.Image:
    canvas = Image.new("RGB", image.size, background)
    canvas.paste(image, (0, 0), image)
    return canvas


def _load_ui_module():
    path = ROOT / "tools/reforged/frontend/main_menu_reforged.py"
    spec = importlib.util.spec_from_file_location("main_menu_reforged_logo_build", path)
    if not spec or not spec.loader:
        raise LogoBuildError("cannot load Reforged UI module")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_review_outputs(reference: Image.Image, variants: dict[str, Image.Image], preferred: str) -> None:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    preview_size = (960, 320)
    dark = (8, 14, 24)
    review_font = pathlib.Path(r"C:\Windows\Fonts\arial.ttf")
    font = ImageFont.truetype(str(review_font), 28) if review_font.is_file() else ImageFont.load_default()
    small_font = ImageFont.truetype(str(review_font), 20) if review_font.is_file() else ImageFont.load_default()

    for name, image in variants.items():
        image.resize(preview_size, Image.Resampling.LANCZOS).save(REVIEW_ROOT / f"logo-{name}.png")

    sheet = Image.new("RGB", (1280, 1520), dark)
    draw = ImageDraw.Draw(sheet)
    labels = ("ORIGINAL REFERENCE", "REFORGED A — RESTRAINED", "REFORGED B — AGED BRONZE", "REFORGED C — CINEMATIC")
    images = [reference.resize(preview_size, Image.Resampling.NEAREST)] + [variants[n].resize(preview_size, Image.Resampling.LANCZOS) for n in "ABC"]
    for index, (label, logo) in enumerate(zip(labels, images)):
        y = 24 + index * 370
        draw.text((40, y), label, font=small_font, fill=(205, 184, 126))
        sheet.paste(composite_on(logo, dark), (160, y + 36))
    sheet.save(REVIEW_ROOT / "logo-variants.png")

    compare = Image.new("RGB", (1600, 500), dark)
    d = ImageDraw.Draw(compare)
    d.text((80, 35), "ORIGINAL", font=font, fill=(220, 220, 216))
    d.text((880, 35), f"REFORGED {preferred} — TECHNICAL PREFERENCE", font=font, fill=(220, 220, 216))
    original_size = (630, 210)
    original = reference.resize(original_size, Image.Resampling.NEAREST)
    candidate = variants[preferred].resize(original_size, Image.Resampling.LANCZOS)
    compare.paste(composite_on(original, dark), (80, 130))
    compare.paste(composite_on(candidate, dark), (880, 130))
    compare.save(REVIEW_ROOT / "original-vs-reforged.png")

    scales = Image.new("RGB", (1500, 720), dark)
    sd = ImageDraw.Draw(scales)
    for index, factor in enumerate((1.0, 0.75, 0.5)):
        size = (round(630 * factor), round(210 * factor))
        logo = variants[preferred].resize(size, Image.Resampling.LANCZOS)
        y = 80 + index * 210
        sd.text((40, y), f"{round(factor * 100)}% — {size[0]}x{size[1]}", font=small_font, fill=(205, 184, 126))
        scales.paste(composite_on(logo, dark), (350, y - 30))
    scales.save(REVIEW_ROOT / "logo-scale-evaluation.png")

    transparency = Image.new("RGB", (1920, 720), (0, 0, 0))
    td = ImageDraw.Draw(transparency)
    backgrounds = ((0, 0, 0), (96, 96, 96), (8, 20, 36))
    candidate = variants[preferred].resize((576, 192), Image.Resampling.LANCZOS)
    for i, bg in enumerate(backgrounds):
        x = i * 640
        td.rectangle((x, 0, x + 640, 720), fill=bg)
        transparency.paste(candidate, (x + 32, 250), candidate)
    transparency.save(REVIEW_ROOT / "logo-transparency-validation.png")

    ui = _load_ui_module()
    tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    strings = json.loads(LOCALE_PATH.read_text(encoding="utf-8"))["strings"]
    state = ui.MenuState(ui.build_main_start(maxlevel=0), "new_game")
    for name in "ABC":
        ui.render_wireframe(1920, 1080, state, tokens, strings, logo_image=variants[name]).save(REVIEW_ROOT / f"menu-{name}-1080p.png")
    preferred_image = variants[preferred]
    ui.render_wireframe(2560, 1440, state, tokens, strings, logo_image=preferred_image).save(REVIEW_ROOT / "menu-preferred-1440p.png")
    ui.render_wireframe(3840, 2160, state, tokens, strings, logo_image=preferred_image).save(REVIEW_ROOT / "menu-preferred-4k.png")
    ui.render_wireframe(3440, 1440, state, tokens, strings, logo_image=preferred_image).save(REVIEW_ROOT / "menu-preferred-21x9.png")


def palette_statistics(reference: Image.Image) -> dict[str, list[int]]:
    rgba = np.asarray(reference)
    mask = (rgba[:, :, 3] >= 192) & (rgba[:, :, 0] >= rgba[:, :, 1]) & (rgba[:, :, 0] > 20)
    rgb = rgba[:, :, :3][mask]
    luminance = rgb.astype(np.float32) @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    order = np.argsort(luminance)
    return {
        "darkVisibleMetalP10": rgb[order[round(0.10 * (len(order) - 1))]].tolist(),
        "dominantGoldMedian": np.median(rgb, axis=0).astype(int).tolist(),
        "brightHighlightP99": rgb[order[round(0.99 * (len(order) - 1))]].tolist(),
        "originalFlareReference": [255, 210, 137],
    }


def build() -> dict[str, Any]:
    before = {"reference": sha256_path(REFERENCE), "tm2": sha256_path(SOURCE_TM2)}
    if before["reference"] != EXPECTED_REFERENCE_SHA256 or before["tm2"] != EXPECTED_TM2_SHA256:
        raise LogoBuildError(f"source hash mismatch: {before}")
    reference = Image.open(REFERENCE).convert("RGBA")
    original_base, original_flare = load_original_layers()
    geometry = measure_geometry(original_base)
    contours, hierarchy = trace_contours(original_base)
    for path in (SOURCE_ROOT, RUNTIME_ROOT, MASK_ROOT, METADATA_ROOT, REVIEW_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    write_geometry_svg(SOURCE_ROOT / "logo_geometry.svg", contours)
    mask = rasterize_contours(contours, hierarchy)
    mask.save(MASK_ROOT / "logo-base-mask.png", optimize=False, compress_level=9)
    glow = build_glow(mask); glow.save(MASK_ROOT / "logo-glow.png", optimize=False, compress_level=9)
    glint = build_glint_mask(mask); glint.save(MASK_ROOT / "logo-glint-mask.png", optimize=False, compress_level=9)
    flare = build_flare(); flare.save(MASK_ROOT / "logo-flare.png", optimize=False, compress_level=9)

    variants: dict[str, Image.Image] = {}
    for index, name in enumerate("ABC"):
        image = material_variant(mask, VARIANTS[name], 53393 + index)
        image.save(RUNTIME_ROOT / f"logo-{name}.png", optimize=False, compress_level=9)
        variants[name] = image
    preferred_path = RUNTIME_ROOT / "logo-preferred.png"
    variants[PREFERRED_VARIANT].save(preferred_path, optimize=False, compress_level=9)
    original_base.save(REVIEW_ROOT / "original-base-reference.png")
    original_flare.save(REVIEW_ROOT / "original-flare-reference.png")
    make_review_outputs(reference, variants, PREFERRED_VARIANT)

    after = {"reference": sha256_path(REFERENCE), "tm2": sha256_path(SOURCE_TM2)}
    if after != before:
        raise LogoBuildError("read-only source hashes changed")
    alpha_bounds = variants[PREFERRED_VARIANT].getchannel("A").getbbox()
    metadata = {
        "schemaVersion": 1,
        "source": {
            "referencePath": str(REFERENCE.relative_to(ROOT)).replace("\\", "/"),
            "referenceSha256": before["reference"],
            "tm2Path": str(SOURCE_TM2.relative_to(ROOT)).replace("\\", "/"),
            "tm2Sha256": before["tm2"],
            "displayedDimensions": [192, 64],
            "baseRgbaSha256": hashlib.sha256(original_base.tobytes()).hexdigest(),
            "flareRgbaSha256": hashlib.sha256(original_flare.tobytes()).hexdigest(),
            "baseCropOnDecodedPage": [0, 176, 192, 240],
            "flareCropOnDecodedPage": [0, 240, 192, 256],
        },
        "geometry": asdict(geometry),
        "normalizedGeometry": {
            "visibleAlphaBounds": [v / d for v, d in zip(geometry.visible_alpha_bounds, (192, 64, 192, 64))],
            "spartanBounds": [v / d for v, d in zip(geometry.spartan_bounds, (192, 64, 192, 64))],
            "subtitleBounds": [v / d for v, d in zip(geometry.subtitle_bounds, (192, 64, 192, 64))],
            "trademarkBounds": [v / d for v, d in zip(geometry.trademark_bounds, (192, 64, 192, 64))],
        },
        "master": {
            "dimensions": list(MASTER_SIZE), "canvasAspectRatio": 3.0,
            "format": "SVG custom outlines plus deterministic RGBA PNG derivatives",
            "traceThreshold": TRACE_THRESHOLD, "visibleAlphaBounds": list(alpha_bounds or (0, 0, 0, 0)),
            "colourSpace": "sRGB", "alpha": "straight alpha; masks encode linear coverage",
        },
        "runtime": {
            "format": "PNG RGBA", "dimensions": list(MASTER_SIZE),
            "anchor": "top-left within central 16:9 safe composition",
            "nominalDisplay1080p": [630, 210], "nominalDisplay1440p": [840, 280],
            "nominalDisplay4k": [1260, 420], "filter": "Lanczos downscale",
        },
        "layers": {
            "baseMask": "../logo_masks/logo-base-mask.png", "glow": "../logo_masks/logo-glow.png",
            "glintMask": "../logo_masks/logo-glint-mask.png", "flare": "../logo_masks/logo-flare.png",
        },
        "variants": {name: {**VARIANTS[name], "path": f"../logo_runtime/logo-{name}.png", "sha256": sha256_path(RUNTIME_ROOT / f"logo-{name}.png")} for name in "ABC"},
        "preferredVariant": PREFERRED_VARIANT,
        "preferenceStatus": "TECHNICAL PREFERENCE ONLY — PENDING HUMAN ART REVIEW",
        "paletteReference": palette_statistics(original_base),
        "typography": {
            "method": "custom vector silhouette reconstruction from measured original; no font used",
            "font": None, "fontLicense": None,
            "uncertainty": "The 192x64 source limits subpixel serif detail; no exact typeface attribution is claimed.",
        },
    }
    metadata_path = METADATA_ROOT / "logo.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    metadata = build()
    print(json.dumps({
        "preferredVariant": metadata["preferredVariant"],
        "master": metadata["master"],
        "geometry": metadata["geometry"],
        "reviewPath": str(REVIEW_ROOT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
