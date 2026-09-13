"""Compose private review boards for Roman Grunt — Human Base Build 1."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "temp" / "roman-human-base-build1"
RENDERS = BUILD / "renders"
CONCEPT = ROOT / "assets" / "Concept" / "Characters" / "Roman-Grunt" / "roman-grunt-reforged-concept-v1-approved.png"
ORIGINAL = ROOT / "temp" / "roman-research" / "turnaround" / "roman-standard-front-three-quarter.png"


def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


BG = (16, 19, 23)
PANEL = (28, 32, 38)
TEXT = (230, 225, 214)
MUTED = (155, 164, 176)
GOLD = (205, 158, 76)


def fit(image, size, background=PANEL):
    return ImageOps.pad(image.convert("RGB"), size, method=Image.Resampling.LANCZOS, color=background, centering=(0.5, 0.5))


def label(draw, xy, text, size=28, color=TEXT, bold=False):
    draw.text(xy, text, font=font(size, bold), fill=color)


def load(name):
    return Image.open(RENDERS / name)


def compose_human():
    board = Image.new("RGB", (3600, 2300), BG)
    draw = ImageDraw.Draw(board)
    label(draw, (90, 55), "ROMAN GRUNT — HUMAN FOUNDATION / ANATOMY GATE", 48, GOLD, True)
    label(draw, (90, 120), "Official Blender CC0 continuous realistic male base; neutral studio form review", 26, MUTED)
    top = [
        ("human-front.png", "FRONT"), ("human-front-three-quarter.png", "FRONT 3/4"),
        ("human-side.png", "SIDE"), ("human-rear-three-quarter.png", "REAR 3/4"), ("human-rear.png", "REAR"),
    ]
    x, y, w, h, gap = 90, 190, 650, 1120, 40
    for name, title in top:
        board.paste(fit(load(name), (w, h)), (x, y))
        label(draw, (x, y+h+14), title, 26, TEXT, True)
        x += w + gap
    bottom = [
        ("human-head-neck.png", "HEAD / NECK"), ("human-torso-shoulder.png", "TORSO / SHOULDER"),
        ("human-arm-elbow-hand.png", "ARM / ELBOW / HAND"), ("human-leg-knee-foot.png", "LEG / KNEE / FOOT"),
    ]
    x, y, w, h, gap = 90, 1400, 810, 760, 55
    for name, title in bottom:
        board.paste(fit(load(name), (w, h)), (x, y))
        label(draw, (x, y+h+12), title, 25, TEXT, True)
        x += w + gap
    path = RENDERS / "human-base-review.png"
    board.save(path, optimize=True)
    return path


def compose_roman():
    board = Image.new("RGB", (4200, 2500), BG)
    draw = ImageDraw.Draw(board)
    label(draw, (90, 55), "ROMAN GRUNT — HUMAN BASE BUILD 1", 50, GOLD, True)
    label(draw, (90, 122), "Major-form equipment review — AWAITING HUMAN VISUAL APPROVAL", 27, MUTED)
    top = [
        ("roman-build1-front.png", "FRONT"), ("roman-build1-front-three-quarter.png", "FRONT 3/4"),
        ("roman-build1-side.png", "SIDE"), ("roman-build1-rear-three-quarter.png", "REAR 3/4"), ("roman-build1-rear.png", "REAR"),
    ]
    x, y, w, h, gap = 80, 190, 760, 1320, 50
    for name, title in top:
        board.paste(fit(load(name), (w, h)), (x, y))
        label(draw, (x, y+h+12), title, 25, TEXT, True)
        x += w + gap
    details = [
        ("roman-build1-head-helmet.png", "HELMET"), ("roman-build1-torso-armour.png", "TORSO ARMOUR"),
        ("roman-build1-skirt.png", "PTERUGES"), ("roman-build1-shield-front.png", "SHIELD / EAGLE"),
        ("roman-build1-sword.png", "GLADIUS"), ("roman-build1-footwear.png", "FOOTWEAR"),
    ]
    x, y, w, h, gap = 80, 1625, 635, 700, 55
    for name, title in details:
        board.paste(fit(load(name), (w, h)), (x, y))
        label(draw, (x, y+h+10), title, 23, TEXT, True)
        x += w + gap
    path = RENDERS / "roman-build1-review.png"
    board.save(path, optimize=True)
    return path


def compose_comparison():
    board = Image.new("RGB", (4200, 1900), BG)
    draw = ImageDraw.Draw(board)
    label(draw, (80, 48), "ROMAN GRUNT — STRUCTURAL / ART-DIRECTION COMPARISON", 48, GOLD, True)
    panels = [
        (Image.open(ORIGINAL), "ORIGINAL PS2 RECONSTRUCTION", "Canonical structural/gameplay identity"),
        (Image.open(CONCEPT), "APPROVED REFORGED CONCEPT", "Human-approved visual target"),
        (load("roman-build1-front-three-quarter.png"), "HUMAN-BASE BUILD 1", "Current major-form implementation"),
    ]
    x, y, w, h, gap = 80, 145, 1300, 1580, 70
    for image, title, subtitle in panels:
        board.paste(fit(image, (w, h)), (x, y))
        label(draw, (x, y+h+14), title, 27, TEXT, True)
        label(draw, (x, y+h+54), subtitle, 22, MUTED)
        x += w + gap
    path = RENDERS / "roman-build1-reference-comparison.png"
    board.save(path, optimize=True)
    return path


def main():
    RENDERS.mkdir(parents=True, exist_ok=True)
    for path in (compose_human(), compose_roman(), compose_comparison()):
        print(path)


if __name__ == "__main__":
    main()
