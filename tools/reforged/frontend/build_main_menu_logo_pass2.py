#!/usr/bin/env python3
"""Build clean-geometry Pass 2 Reforged logo candidates and diagnostics.

No raster contour is traced. Letterforms are intentional reusable path
definitions made from exact line segments and cubic Bezier curves, positioned
to the measured original composition. A signed-distance bevel provides actual
directional surface shading before restrained material variation is applied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = pathlib.Path(__file__).resolve().parents[3]
LOGO_ROOT = ROOT / "assets/reforged/frontend/main-menu/logo"
PASS1_ROOT = LOGO_ROOT
PASS2_ROOT = LOGO_ROOT / "pass2"
SOURCE_ROOT = PASS2_ROOT / "logo_source"
RUNTIME_ROOT = PASS2_ROOT / "logo_runtime"
MASK_ROOT = PASS2_ROOT / "logo_masks"
METADATA_ROOT = PASS2_ROOT / "metadata"
REVIEW_ROOT = ROOT / "assets/reforged/frontend/review/logo"
TOKENS_PATH = ROOT / "assets/reforged/frontend/main-menu/main_menu_tokens.json"
LOCALE_PATH = ROOT / "assets/reforged/frontend/main-menu/locales/en.json"
PASS1_MODULE = ROOT / "tools/reforged/frontend/build_main_menu_logo.py"
UI_MODULE = ROOT / "tools/reforged/frontend/main_menu_reforged.py"

MASTER_SIZE = (2520, 840)
SOURCE_SCALE = 12.0
SOURCE_OFFSET = (72.0, 48.0)
PREFERRED = "2A"
EXPECTED_TM2_SHA256 = "755e4dd82ec2d29c1dbc45136f9cbf92a25628a4e6859888ad7c7971b6a3e84c"


class Pass2Error(ValueError):
    pass


Command = tuple[Any, ...]


@dataclass(frozen=True)
class Contour:
    commands: tuple[Command, ...]
    hole: bool = False


@dataclass(frozen=True)
class Glyph:
    name: str
    advance: float
    contours: tuple[Contour, ...]
    construction: tuple[str, ...]


@dataclass(frozen=True)
class Placement:
    glyph: str
    occurrence: int
    line: str
    tx: float
    ty: float
    sx: float
    sy: float


def path(*commands: Command, hole: bool = False) -> Contour:
    return Contour(tuple(commands), hole)


def poly(points: Iterable[tuple[float, float]], hole: bool = False) -> Contour:
    pts = list(points)
    commands: list[Command] = [("M", *pts[0])]
    commands.extend(("L", *point) for point in pts[1:])
    commands.append(("Z",))
    return Contour(tuple(commands), hole)


def _ellipse(cx: float, cy: float, rx: float, ry: float, hole: bool = False) -> Contour:
    k = 0.5522847498
    return path(
        ("M", cx + rx, cy),
        ("C", cx + rx, cy - k * ry, cx + k * rx, cy - ry, cx, cy - ry),
        ("C", cx - k * rx, cy - ry, cx - rx, cy - k * ry, cx - rx, cy),
        ("C", cx - rx, cy + k * ry, cx - k * rx, cy + ry, cx, cy + ry),
        ("C", cx + k * rx, cy + ry, cx + rx, cy + k * ry, cx + rx, cy),
        ("Z",), hole=hole,
    )


def glyphs() -> dict[str, Glyph]:
    serif_top = lambda x0, x1: poly(((x0, 20), (x1, 20), (x1 - 20, 105), (x0 + 20, 105)))
    serif_bottom = lambda x0, x1: poly(((x0 + 15, 900), (x1 - 15, 900), (x1, 985), (x0, 985)))
    stem = lambda x0, x1: poly(((x0, 70), (x1, 70), (x1, 940), (x0, 940)))

    s = path(
        ("M", 835, 120),
        ("C", 705, 20, 315, -5, 130, 145),
        ("C", -10, 260, 35, 430, 330, 520),
        ("C", 565, 592, 720, 610, 685, 735),
        ("C", 650, 865, 390, 900, 125, 750),
        ("L", 65, 895),
        ("C", 315, 1050, 715, 1035, 858, 810),
        ("C", 1005, 578, 885, 420, 558, 335),
        ("C", 350, 282, 220, 255, 260, 180),
        ("C", 305, 98, 535, 112, 780, 255),
        ("Z",),
    )

    p_outer = path(
        ("M", 270, 70), ("L", 535, 70),
        ("C", 795, 70, 905, 190, 905, 355),
        ("C", 905, 525, 770, 595, 300, 595),
        ("L", 300, 455), ("L", 510, 455),
        ("C", 660, 455, 720, 410, 720, 335),
        ("C", 720, 245, 650, 210, 300, 210),
        ("Z",),
    )
    p = Glyph("P", 870, (stem(125, 305), serif_top(65, 370), serif_bottom(65, 385), p_outer),
              ("straight vertical stem", "cubic symmetric bowl", "consistent wedge serifs"))

    a_contours = (
        poly(((55, 940), (415, 25), (555, 25), (925, 940), (730, 940), (630, 675), (328, 675), (235, 940))),
        poly(((350, 570), (610, 570), (650, 685), (310, 685))),
        poly(((427, 250), (487, 105), (550, 250), (610, 490), (355, 490)), hole=True),
        serif_bottom(25, 300), serif_bottom(680, 955),
    )
    a = Glyph("A", 930, a_contours, ("mirrored straight diagonals", "horizontal crossbar", "symmetric apex/counter", "consistent foot serifs"))

    r_leg = poly(((455, 510), (610, 475), (940, 930), (890, 985), (730, 950), (430, 555)))
    r = Glyph("R", 930, (*p.contours, r_leg, serif_bottom(710, 965)),
              ("shared P stem and cubic bowl", "straight diagonal leg", "consistent wedge serifs"))

    t = Glyph("T", 900, (
        poly(((45, 20), (855, 20), (825, 150), (525, 125), (525, 920), (610, 985), (290, 985), (375, 920), (375, 125), (75, 150))),
    ), ("mathematically horizontal crown", "straight central stem", "symmetric crown/foot serifs"))

    n = Glyph("N", 960, (
        stem(100, 275), stem(700, 875),
        poly(((220, 80), (390, 80), (770, 835), (770, 965), (615, 965), (235, 210))),
        serif_top(45, 335), serif_top(640, 930), serif_bottom(45, 335), serif_bottom(640, 930),
    ), ("parallel straight stems", "straight diagonal", "matched four stem serifs"))

    o = Glyph("O", 920, (
        _ellipse(460, 505, 420, 485),
        _ellipse(460, 505, 255, 345, hole=True),
    ), ("four deliberate cubic outer arcs", "concentric cubic counter", "vertical stress"))

    l = Glyph("L", 760, (
        stem(120, 300), serif_top(55, 365),
        poly(((120, 900), (650, 900), (720, 790), (690, 985), (55, 985))),
    ), ("straight stem", "horizontal foot", "wedge terminal"))

    w = Glyph("W", 1120, (
        poly(((35, 45), (225, 45), (405, 790), (505, 430), (610, 790), (815, 45), (1005, 45), (715, 980), (570, 980), (505, 655), (440, 980), (295, 980))),
        serif_top(10, 260), serif_top(780, 1040),
    ), ("four straight diagonals", "symmetric central valley", "matched upper serifs"))

    i = Glyph("I", 420, (
        stem(145, 275), serif_top(55, 365), serif_bottom(55, 365),
    ), ("straight stem", "matched horizontal serifs"))

    m = Glyph("M", 1080, (
        stem(75, 245), stem(835, 1005),
        poly(((205, 80), (355, 80), (540, 600), (725, 80), (875, 80), (610, 850), (470, 850))),
        serif_top(20, 300), serif_top(780, 1060), serif_bottom(20, 300), serif_bottom(780, 1060),
    ), ("parallel straight stems", "symmetric straight inner diagonals", "matched serifs"))

    return {
        "S": Glyph("S", 880, (s,), ("deliberate cubic spine", "smooth opposing curves", "tapered terminals")),
        "P": p, "A": a, "R": r, "T": t, "N": n, "O": o, "L": l, "W": w, "I": i, "M": m,
    }


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise Pass2Error(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def layout_word(text: str, line: str, box: tuple[float, float, float, float], library: dict[str, Glyph], tracking: float) -> list[Placement]:
    tokens = [character for character in text]
    natural = sum((540 if char == " " else library[char].advance) for char in tokens)
    natural += tracking * max(0, len(tokens) - 1)
    x0, y0, x1, y1 = box
    sx = (x1 - x0) / natural
    sy = (y1 - y0) / 1000.0
    cursor = x0
    counts: dict[str, int] = {}
    placements: list[Placement] = []
    for char in tokens:
        if char == " ":
            cursor += (540 + tracking) * sx
            continue
        occurrence = counts.get(char, 0)
        counts[char] = occurrence + 1
        placements.append(Placement(char, occurrence, line, cursor, y0, sx, sy))
        cursor += (library[char].advance + tracking) * sx
    return placements


def all_placements(library: dict[str, Glyph]) -> list[Placement]:
    # Boxes are the measured original base composition in 192x64 logical units.
    title = layout_word("SPARTAN", "SPARTAN", (2, 1, 170, 36), library, 55)
    subtitle = layout_word("TOTAL WARRIOR", "TOTAL_WARRIOR", (2, 41, 171, 64), library, 54)
    trademark = layout_word("TM", "TM", (169, 2, 184, 12), library, 12)
    return title + subtitle + trademark


def transform_command(command: Command, placement: Placement, pixel_scale: float = 1.0) -> Command:
    kind = command[0]
    if kind == "Z":
        return command
    values = list(command[1:])
    result: list[float] = []
    for index in range(0, len(values), 2):
        source_x = placement.tx + values[index] * placement.sx
        source_y = placement.ty + values[index + 1] * placement.sy
        result.extend(((source_x * SOURCE_SCALE + SOURCE_OFFSET[0]) * pixel_scale,
                       (source_y * SOURCE_SCALE + SOURCE_OFFSET[1]) * pixel_scale))
    return (kind, *result)


def sample_contour(contour: Contour, placement: Placement, pixel_scale: float) -> np.ndarray:
    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    for raw in contour.commands:
        command = transform_command(raw, placement, pixel_scale)
        if command[0] == "M":
            current = (command[1], command[2]); points.append(current)
        elif command[0] == "L":
            current = (command[1], command[2]); points.append(current)
        elif command[0] == "C":
            p0 = current; p1 = (command[1], command[2]); p2 = (command[3], command[4]); p3 = (command[5], command[6])
            for step in range(1, 25):
                t = step / 24.0; u = 1.0 - t
                points.append((
                    u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1],
                ))
            current = p3
    return np.rint(np.array(points)).astype(np.int32)


def rasterize(library: dict[str, Glyph], placements: list[Placement]) -> Image.Image:
    supersample = 2
    mask = np.zeros((MASTER_SIZE[1] * supersample, MASTER_SIZE[0] * supersample), dtype=np.uint8)
    for placement in placements:
        glyph = library[placement.glyph]
        for contour in (c for c in glyph.contours if not c.hole):
            cv2.fillPoly(mask, [sample_contour(contour, placement, supersample)], 255, lineType=cv2.LINE_AA)
        for contour in (c for c in glyph.contours if c.hole):
            cv2.fillPoly(mask, [sample_contour(contour, placement, supersample)], 0, lineType=cv2.LINE_AA)
    return Image.fromarray(mask).resize(MASTER_SIZE, Image.Resampling.LANCZOS)


def command_svg(command: Command) -> str:
    if command[0] == "Z":
        return "Z"
    return f"{command[0]} " + " ".join(f"{float(value):.4f}" for value in command[1:])


def write_svg(path: pathlib.Path, library: dict[str, Glyph], placements: list[Placement]) -> None:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="2520" height="840" viewBox="0 0 2520 840">',
        '  <title>SpartanReforged main-menu logo Pass 2 clean geometry</title>',
        '  <desc>Intentional reusable line and cubic-Bezier glyph construction; no raster contour trace and no font dependency.</desc>',
        '  <defs>',
    ]
    for name, glyph in library.items():
        lines.append(f'    <mask id="mask-{name}" maskUnits="userSpaceOnUse" x="-100" y="-100" width="1300" height="1200">')
        for contour in glyph.contours:
            data = " ".join(command_svg(command) for command in contour.commands)
            colour = "black" if contour.hole else "white"
            lines.append(f'      <path d="{data}" fill="{colour}"/>')
        lines.append('    </mask>')
        lines.append(f'    <g id="glyph-{name}"><rect x="-100" y="-100" width="1300" height="1200" fill="white" mask="url(#mask-{name})"/></g>')
    lines.append('  </defs>')
    for placement in placements:
        a = placement.sx * SOURCE_SCALE; d = placement.sy * SOURCE_SCALE
        e = placement.tx * SOURCE_SCALE + SOURCE_OFFSET[0]; f = placement.ty * SOURCE_SCALE + SOURCE_OFFSET[1]
        lines.append(f'  <use href="#glyph-{placement.glyph}" data-line="{placement.line}" data-occurrence="{placement.occurrence}" transform="matrix({a:.8f} 0 0 {d:.8f} {e:.4f} {f:.4f})"/>')
    lines.append('</svg>')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


VARIANTS: dict[str, dict[str, Any]] = {
    "2A": {"description": "Faithful bevel: restrained Pass-1A gold with original-like directional edge separation.", "face": (178, 129, 59), "bevel_dark": (52, 30, 15), "bevel_light": (248, 210, 126), "specular": 0.55, "roughness": 0.62, "wear": 0.025},
    "2B": {"description": "Modern metallic: identical geometry/profile with smoother bronze-gold response and tighter specular.", "face": (185, 134, 62), "bevel_dark": (47, 28, 14), "bevel_light": (245, 207, 124), "specular": 0.72, "roughness": 0.48, "wear": 0.018},
    "2C": {"description": "Cinematic: identical geometry/profile with stronger controlled upper-left edge illumination.", "face": (190, 139, 64), "bevel_dark": (45, 27, 13), "bevel_light": (255, 225, 148), "specular": 0.90, "roughness": 0.42, "wear": 0.022},
}


def shifted(array: np.ndarray, dx: int, dy: int) -> np.ndarray:
    result = np.zeros_like(array)
    ys = slice(max(0, dy), array.shape[0] + min(0, dy)); src_y = slice(max(0, -dy), array.shape[0] - max(0, dy))
    xs = slice(max(0, dx), array.shape[1] + min(0, dx)); src_x = slice(max(0, -dx), array.shape[1] - max(0, dx))
    result[ys, xs] = array[src_y, src_x]
    return result


def bevel_material(mask_image: Image.Image, spec: dict[str, Any], seed: int) -> Image.Image:
    alpha = np.asarray(mask_image, dtype=np.float32) / 255.0
    binary = (alpha >= 0.5).astype(np.uint8)
    distance = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    bevel_width = 20.0
    bevel_t = np.clip(distance / bevel_width, 0.0, 1.0)
    gy, gx = np.gradient(distance)
    length = np.maximum(np.sqrt(gx * gx + gy * gy), 1e-5)
    # Height rises from perimeter to face. Surface normal opposes gradient.
    nx, ny = -gx / length, -gy / length
    nz = np.full_like(nx, 0.72)
    normal_length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= normal_length; ny /= normal_length; nz /= normal_length
    light = np.array((-0.48, -0.72, 0.50), dtype=np.float32)
    light /= np.linalg.norm(light)
    ndotl = np.clip(nx * light[0] + ny * light[1] + nz * light[2], -1.0, 1.0)
    edge_light = np.clip((ndotl + 0.30) / 1.15, 0.0, 1.0)

    dark = np.array(spec["bevel_dark"], dtype=np.float32)
    bright = np.array(spec["bevel_light"], dtype=np.float32)
    face = np.array(spec["face"], dtype=np.float32)
    bevel_rgb = dark + edge_light[..., None] * (bright - dark)
    # A restrained face gradient follows inferred upper-left illumination.
    yy, xx = np.mgrid[0:alpha.shape[0], 0:alpha.shape[1]]
    directional = np.clip(1.10 - 0.18 * yy / alpha.shape[0] - 0.05 * xx / alpha.shape[1], 0.82, 1.10)
    face_rgb = face[None, None, :] * directional[..., None]
    rgb = bevel_rgb * (1.0 - bevel_t[..., None]) + face_rgb * bevel_t[..., None]

    # Directional specular is restricted to the actual bevel surface.
    half_vec = light + np.array((0.0, 0.0, 1.0), dtype=np.float32); half_vec /= np.linalg.norm(half_vec)
    ndoth = np.clip(nx * half_vec[0] + ny * half_vec[1] + nz * half_vec[2], 0.0, 1.0)
    exponent = 12.0 + 30.0 * (1.0 - float(spec["roughness"]))
    specular = np.power(ndoth, exponent) * (1.0 - bevel_t) * 150.0 * float(spec["specular"])
    rgb += specular[..., None]

    # Tiny material variation is added last and cannot change geometry/profile.
    rng = np.random.default_rng(seed)
    noise = cv2.GaussianBlur(rng.normal(0, 1, alpha.shape).astype(np.float32), (0, 0), 6.0)
    noise /= max(float(noise.std()), 1e-5)
    rgb += noise[..., None] * (255.0 * float(spec["wear"])) * bevel_t[..., None]

    shadow = np.asarray(mask_image.filter(ImageFilter.GaussianBlur(4)), dtype=np.float32) / 255.0
    shadow = shifted(shadow, 6, 7) * 0.30
    out_alpha = np.maximum(alpha, shadow)
    shadow_colour = np.array((22, 13, 8), dtype=np.float32)
    rgb = shadow_colour + alpha[..., None] * (rgb - shadow_colour)
    rgba = np.dstack((np.clip(rgb, 0, 255).astype(np.uint8), np.uint8(np.clip(out_alpha * 255, 0, 255))))
    return Image.fromarray(rgba)


def build_glow(mask: Image.Image) -> Image.Image:
    alpha = np.asarray(mask.filter(ImageFilter.GaussianBlur(16)), dtype=np.float32) * 0.13
    rgba = np.zeros((MASTER_SIZE[1], MASTER_SIZE[0], 4), dtype=np.uint8)
    rgba[:, :, :3] = (218, 169, 83); rgba[:, :, 3] = np.uint8(np.clip(alpha, 0, 255))
    return Image.fromarray(rgba)


def build_glint(mask: Image.Image) -> Image.Image:
    yy, xx = np.mgrid[0:MASTER_SIZE[1], 0:MASTER_SIZE[0]]
    stripe = np.exp(-((xx - 0.58 * MASTER_SIZE[0] + yy * 0.42) / 34.0) ** 2)
    return Image.fromarray(np.uint8(stripe * (np.asarray(mask) / 255.0) * 255))


def build_blue_flare() -> Image.Image:
    width, height = MASTER_SIZE[0], round(MASTER_SIZE[1] * 0.30)
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = width * 0.49, height * 0.52
    core = np.exp(-(((xx - cx) / 170.0) ** 2 + ((yy - cy) / 8.0) ** 2))
    beam = np.exp(-(((xx - cx) / 660.0) ** 2 + ((yy - cy) / 20.0) ** 2)) * 0.55
    bloom = np.exp(-(((xx - cx) / 330.0) ** 2 + ((yy - cy) / 72.0) ** 2)) * 0.28
    intensity = np.clip(core + beam + bloom, 0, 1)
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgb = np.zeros((height, width, 3), dtype=np.float32)
    rgb[:, :, 0] = 155 + 100 * core; rgb[:, :, 1] = 195 + 60 * core; rgb[:, :, 2] = 255
    rgba[:, :, :3] = np.uint8(np.clip(rgb, 0, 255)); rgba[:, :, 3] = np.uint8(intensity * 150)
    return Image.fromarray(rgba)


def original_colour_study(base: Image.Image, flare: Image.Image) -> dict[str, Any]:
    rgba = np.asarray(base)
    valid = (rgba[:, :, 3] >= 192) & (rgba[:, :, :3].max(axis=2) > 20)
    rgb = rgba[:, :, :3][valid]
    lum = rgb.astype(np.float32) @ np.array((0.2126, 0.7152, 0.0722), dtype=np.float32)
    order = np.argsort(lum)
    sample = lambda q: rgb[order[round(q * (len(order) - 1))]].tolist()
    f = np.asarray(flare); fm = f[:, :, 3] > 0; frgb = f[:, :, :3][fm]
    return {
        "deepestShadowP02": sample(0.02), "darkBevelP15": sample(0.15),
        "mainFaceMedian": sample(0.50), "lightBevelP85": sample(0.85),
        "brightHighlightP99": sample(0.99), "flareBrightestRgb": frgb[np.argmax(frgb.sum(axis=1))].tolist(),
        "inferredLightDirection": "upper-left/front; repeated bright upper/left edges oppose dark lower/right edges",
    }


def compose_logo(material: Image.Image, flare: Image.Image) -> Image.Image:
    result = Image.new("RGBA", MASTER_SIZE, (0, 0, 0, 0))
    # Original 192x16 flare sits around logical y=32..48; retain that identity.
    flare_y = round((32 * SOURCE_SCALE + SOURCE_OFFSET[1]) - flare.height / 2)
    result.alpha_composite(flare, (0, flare_y))
    result.alpha_composite(material)
    return result


def review_font(size: int):
    path = pathlib.Path(r"C:\Windows\Fonts\arial.ttf")
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def on_bg(image: Image.Image, size: tuple[int, int], bg=(7, 13, 22), resample=Image.Resampling.LANCZOS) -> Image.Image:
    rendered = image.resize(size, resample)
    canvas = Image.new("RGB", size, bg); canvas.paste(rendered, (0, 0), rendered); return canvas


def build_geometry_diagnostic(base: Image.Image, pass1_mask: Image.Image, pass2_mask: Image.Image) -> None:
    dark = (7, 13, 22); sheet = Image.new("RGB", (1800, 1950), dark); draw = ImageDraw.Draw(sheet)
    font = review_font(25); small = review_font(18)
    original_mask = base.getchannel("A")
    downsample = pass2_mask.resize((192, 64), Image.Resampling.LANCZOS)
    rows = [
        ("ORIGINAL RASTER COVERAGE", original_mask.resize((960, 320), Image.Resampling.NEAREST)),
        ("PASS 1 VECTOR SILHOUETTE", pass1_mask.resize((960, 320), Image.Resampling.LANCZOS)),
        ("PASS 2 CLEAN VECTOR", pass2_mask.resize((960, 320), Image.Resampling.LANCZOS)),
        ("PASS 2 DOWNSAMPLED TO 192x64", downsample.resize((960, 320), Image.Resampling.NEAREST)),
    ]
    for i, (label, item) in enumerate(rows):
        y = 30 + i * 300; draw.text((30, y), label, font=font, fill=(215, 190, 126)); sheet.paste(Image.merge("RGB", (item, item, item)), (500, y + 5))
    # Edge overlay: source red, Pass 2 cyan after both are reduced to 192x64.
    source_edge = cv2.Canny(np.asarray(original_mask), 40, 100) > 0
    pass2_edge = cv2.Canny(np.asarray(downsample), 40, 100) > 0
    overlay = np.zeros((64, 192, 3), dtype=np.uint8); overlay[source_edge] = (235, 70, 80); overlay[pass2_edge] = np.maximum(overlay[pass2_edge], (60, 210, 235))
    edge = Image.fromarray(overlay).resize((960, 320), Image.Resampling.NEAREST)
    draw.text((30, 1250), "EDGE OVERLAY: ORIGINAL RED / PASS 2 CYAN", font=small, fill=(215, 190, 126)); sheet.paste(edge, (500, 1180))
    draw.text((30, 1530), "ENLARGED TITLE EDGE DETAILS — ORIGINAL / PASS 2", font=font, fill=(215,190,126))
    logical_pass2 = downsample
    ranges = (("S", 2, 24), ("P", 24, 47), ("R", 70, 96), ("A", 112, 142), ("N", 139, 171))
    for index, (name, x0, x1) in enumerate(ranges):
        x = 40 + index * 345
        draw.text((x, 1580), name, font=font, fill=(220,220,215))
        original_crop = original_mask.crop((x0, 0, x1, 38)).resize((150, 285), Image.Resampling.NEAREST)
        pass2_crop = logical_pass2.crop((x0, 0, x1, 38)).resize((150, 285), Image.Resampling.NEAREST)
        sheet.paste(Image.merge("RGB", (original_crop, original_crop, original_crop)), (x + 35, 1620))
        cyan = Image.new("RGB", pass2_crop.size, (0,0,0)); ca=np.array(cyan); pm=np.asarray(pass2_crop)>32; ca[pm]=(60,210,235); cyan=Image.fromarray(ca)
        sheet.paste(cyan, (x + 185, 1620))
    sheet.save(REVIEW_ROOT / "logo-geometry-comparison.png")


def build_bevel_diagnostic(base: Image.Image, pass2: Image.Image, colour_study: dict[str, Any]) -> None:
    sheet = Image.new("RGB", (1800, 1050), (7, 13, 22)); draw = ImageDraw.Draw(sheet); font = review_font(25); small = review_font(18)
    draw.text((40, 30), "ORIGINAL BEVEL EVIDENCE", font=font, fill=(215, 190, 126))
    source = base.resize((1152, 384), Image.Resampling.NEAREST); sheet.paste(on_bg(source, source.size, resample=Image.Resampling.NEAREST), (40, 80))
    draw.line((1250, 150, 1050, 330), fill=(255, 235, 170), width=6); draw.polygon(((1050,330),(1080,320),(1065,295)), fill=(255,235,170))
    draw.text((1260, 130), "INFERRED LIGHT\nUPPER-LEFT / FRONT", font=small, fill=(220, 220, 215))
    labels = ["brightHighlightP99", "lightBevelP85", "mainFaceMedian", "darkBevelP15", "deepestShadowP02"]
    for i, label in enumerate(labels):
        colour = tuple(colour_study[label]); y = 500 + i * 70
        draw.rectangle((50, y, 120, y + 45), fill=colour); draw.text((145, y + 10), f"{label}: {colour}", font=small, fill=(220,220,215))
    draw.text((650, 500), "PASS 2A DIRECTIONAL DISTANCE-FIELD BEVEL", font=font, fill=(215,190,126))
    candidate = pass2.resize((1008, 336), Image.Resampling.LANCZOS); sheet.paste(on_bg(candidate, candidate.size), (650, 560))
    draw.text((650, 920), "Outer edge → directional bevel slope → raised face → counter bevel", font=small, fill=(220,220,215))
    sheet.save(REVIEW_ROOT / "logo-bevel-analysis.png")


def create_reviews(base: Image.Image, pass1a: Image.Image, candidates: dict[str, Image.Image], pass1_mask: Image.Image, pass2_mask: Image.Image, colour_study: dict[str, Any]) -> None:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True); dark=(7,13,22); font=review_font(22)
    original_composite = Image.open(PASS1_ROOT.parent.parent / "design-kit/main-menu/logo-reference.png").convert("RGBA")
    rows = [("ORIGINAL", original_composite), ("PASS 1 A — REJECTED GEOMETRY", pass1a), *[(f"PASS {n}", candidates[n]) for n in ("2A","2B","2C")]]
    sheet = Image.new("RGB", (1400, 1830), dark); draw=ImageDraw.Draw(sheet)
    for i,(label,image) in enumerate(rows):
        y=25+i*350; draw.text((35,y),label,font=font,fill=(215,190,126)); sheet.paste(on_bg(image,(1008,336)),(330,y))
    sheet.save(REVIEW_ROOT / "logo-pass2-variants.png")
    build_geometry_diagnostic(base, pass1_mask, pass2_mask)
    build_bevel_diagnostic(base, candidates[PREFERRED], colour_study)

    compare=Image.new("RGB",(1700,800),dark); d=ImageDraw.Draw(compare); d.text((60,30),"ORIGINAL",font=font,fill=(220,220,215)); d.text((880,30),f"PASS {PREFERRED} — TECHNICAL PREFERENCE",font=font,fill=(220,220,215))
    compare.paste(on_bg(original_composite,(630,210),resample=Image.Resampling.NEAREST),(60,100)); compare.paste(on_bg(candidates[PREFERRED],(630,210)),(880,100))
    compare.paste(on_bg(original_composite,(768,256),resample=Image.Resampling.NEAREST),(30,420)); compare.paste(on_bg(candidates[PREFERRED],(768,256)),(870,420)); compare.save(REVIEW_ROOT / "original-vs-reforged-pass2.png")

    ui=load_module("main_menu_reforged_pass2",UI_MODULE); tokens=json.loads(TOKENS_PATH.read_text(encoding="utf-8")); strings=json.loads(LOCALE_PATH.read_text(encoding="utf-8"))["strings"]; state=ui.MenuState(ui.build_main_start(0),"new_game")
    for name,image in candidates.items(): ui.render_wireframe(1920,1080,state,tokens,strings,logo_image=image).save(REVIEW_ROOT/f"menu-logo-pass{name}-1080p.png")
    preferred=candidates[PREFERRED]
    ui.render_wireframe(2560,1440,state,tokens,strings,logo_image=preferred).save(REVIEW_ROOT/f"menu-logo-pass{PREFERRED}-1440p.png")
    ui.render_wireframe(3840,2160,state,tokens,strings,logo_image=preferred).save(REVIEW_ROOT/f"menu-logo-pass{PREFERRED}-4k.png")
    ui.render_wireframe(3440,1440,state,tokens,strings,logo_image=preferred).save(REVIEW_ROOT/f"menu-logo-pass{PREFERRED}-21x9.png")


def build() -> dict[str, Any]:
    pass1=load_module("main_menu_logo_pass1_for_pass2",PASS1_MODULE)
    if pass1.sha256_path(pass1.SOURCE_TM2) != EXPECTED_TM2_SHA256:
        raise Pass2Error("original logo hash mismatch")
    original_base, original_flare=pass1.load_original_layers(); original_hash=pass1.sha256_path(pass1.SOURCE_TM2)
    pass1_required=[PASS1_ROOT/"logo_source/logo_geometry.svg",PASS1_ROOT/"logo_runtime/logo-A.png",PASS1_ROOT/"metadata/logo.json"]
    if not all(path.is_file() for path in pass1_required): raise Pass2Error("Pass 1 must remain present")
    library=glyphs(); placements=all_placements(library)
    for directory in (SOURCE_ROOT,RUNTIME_ROOT,MASK_ROOT,METADATA_ROOT,REVIEW_ROOT): directory.mkdir(parents=True,exist_ok=True)
    write_svg(SOURCE_ROOT/"logo_clean_geometry.svg",library,placements)
    mask=rasterize(library,placements); mask.save(MASK_ROOT/"logo-clean-mask.png",optimize=False,compress_level=9)
    glow=build_glow(mask); glow.save(MASK_ROOT/"logo-glow.png",optimize=False,compress_level=9)
    glint=build_glint(mask); glint.save(MASK_ROOT/"logo-glint-mask.png",optimize=False,compress_level=9)
    flare=build_blue_flare(); flare.save(MASK_ROOT/"logo-blue-flare.png",optimize=False,compress_level=9)
    candidates:dict[str,Image.Image]={}; materials:dict[str,Image.Image]={}
    for i,name in enumerate(("2A","2B","2C")):
        material=bevel_material(mask,VARIANTS[name],53393+i); material.save(RUNTIME_ROOT/f"logo-pass{name}.png",optimize=False,compress_level=9); materials[name]=material
        candidates[name]=compose_logo(material,flare)
    materials[PREFERRED].save(RUNTIME_ROOT/"logo-pass2-preferred.png",optimize=False,compress_level=9)
    colour_study=original_colour_study(original_base,original_flare)
    create_reviews(original_base,Image.open(PASS1_ROOT/"logo_runtime/logo-A.png").convert("RGBA"),candidates,Image.open(PASS1_ROOT/"logo_masks/logo-base-mask.png").convert("L"),mask,colour_study)
    if pass1.sha256_path(pass1.SOURCE_TM2)!=original_hash: raise Pass2Error("original source changed")
    uses:dict[str,int]={}
    for placement in placements: uses[placement.glyph]=uses.get(placement.glyph,0)+1
    original_binary=np.asarray(original_base.getchannel("A"))>=192
    downsample_binary=np.asarray(mask.resize((192,64),Image.Resampling.LANCZOS))>=128
    intersection=int(np.logical_and(original_binary,downsample_binary).sum()); union=int(np.logical_or(original_binary,downsample_binary).sum())
    metadata={
        "schemaVersion":2,"pass":"Pass 2","approval":"PENDING HUMAN APPROVAL","pass1Retained":True,
        "source":{"tm2Sha256":original_hash,"measuredComposition":asdict_safe(pass1.measure_geometry(original_base))},
        "geometry":{"method":"intentional reusable line/cubic-Bezier glyph construction; no raster contour tracing","masterDimensions":list(MASTER_SIZE),"glyphUses":uses,"placements":[placement.__dict__ for placement in placements],"glyphConstruction":{name:list(glyph.construction) for name,glyph in library.items()},"straightStrokePolicy":"all intended stems, bars, diagonals and serif edges use exact line segments","curvePolicy":"S and bowls/counters use deliberate cubic Bezier segments","repeatedGlyphPolicy":"every occurrence references the same glyph definition"},
        "downsample":{"target":[192,64],"filter":"Lanczos","objective":"plausible correspondence without reproducing PS2 pixel stair steps","thresholdedInteriorIou":intersection/union,"assessment":"composition, line hierarchy and glyph identities correspond; deliberate clean strokes differ from low-resolution bevel/coverage boundaries"},
        "bevel":{"profile":"20-master-pixel signed-distance rise from outer/counter edge to raised face","lightDirection":[-0.48,-0.72,0.50],"inferredDirection":colour_study["inferredLightDirection"],"widthAt1080pPixels":5.0,"colourStudy":colour_study},
        "flare":{"separate":True,"path":"../logo_masks/logo-blue-flare.png","description":"cool blue-white core, restrained horizontal beam and bloom"},
        "variants":{name:{**VARIANTS[name],"runtimePath":f"../logo_runtime/logo-pass{name}.png","sha256":sha256(RUNTIME_ROOT/f"logo-pass{name}.png")} for name in ("2A","2B","2C")},
        "preferred":PREFERRED,"preferenceStatus":"TECHNICAL PREFERENCE ONLY — PENDING HUMAN ART REVIEW",
        "runtime":{"format":"straight-alpha sRGB PNG","dimensions":list(MASTER_SIZE),"nominal1080p":[630,210],"nominal1440p":[840,280],"nominal4k":[1260,420]},
    }
    (METADATA_ROOT/"logo-pass2.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8",newline="\n")
    return metadata


def asdict_safe(value: Any) -> dict[str, Any]:
    return {name:getattr(value,name) for name in value.__dataclass_fields__}


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(); metadata=build(); print(json.dumps({"preferred":metadata["preferred"],"geometry":metadata["geometry"]["method"],"bevel":metadata["bevel"],"review":str(REVIEW_ROOT)},indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
