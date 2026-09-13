"""Compose private Roman Grunt V1 review and comparison boards.

Only the script is public-safe. Output boards default to ``temp/`` and may
include private preservation references, so they must never be committed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RENDER_ROOT = ROOT / "temp" / "roman-reforged-v1" / "renders"
DEFAULT_PS2 = ROOT / "temp" / "roman-research" / "turnaround" / "roman-standard-turnaround.png"
DEFAULT_CONCEPT = ROOT / "assets" / "Concept" / "Characters" / "Roman-Grunt" / "roman-grunt-reforged-concept-v1-approved.png"


def font(size: int, bold: bool = False):
    choices = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in choices:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def fit(image: Image.Image, box: tuple[int, int], background=(18, 20, 23)) -> Image.Image:
    copy = image.convert("RGB")
    copy.thumbnail(box, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", box, background)
    canvas.paste(copy, ((box[0] - copy.width) // 2, (box[1] - copy.height) // 2))
    return canvas


def contact_sheet(render_root: Path, output: Path) -> None:
    views = [
        ("FRONT", "front"),
        ("FRONT THREE-QUARTER", "front-three-quarter"),
        ("SIDE", "side"),
        ("REAR THREE-QUARTER", "rear-three-quarter"),
        ("REAR", "rear"),
        ("HEAD / HELMET", "closeup-head-helmet"),
        ("TORSO ARMOUR", "closeup-torso-armour"),
        ("SKIRT CONSTRUCTION", "closeup-skirt"),
        ("SHIELD FRONT", "closeup-shield-front"),
        ("SHIELD REAR", "closeup-shield-rear"),
        ("SWORD / HAND SCALE", "closeup-sword"),
    ]
    width, height = 3600, 2400
    board = Image.new("RGB", (width, height), (11, 13, 16))
    draw = ImageDraw.Draw(board)
    draw.text((80, 42), "ROMAN GRUNT REFORGED V1 — REVIEW", font=font(54, True), fill=(230, 214, 183))
    draw.text((80, 108), "STATIC FORM / MATERIAL BLOCKOUT — AWAITING HUMAN VISUAL APPROVAL", font=font(25), fill=(160, 164, 170))
    margin, gap, top = 70, 24, 170
    cell_w = (width - 2 * margin - 4 * gap) // 5
    cell_h = 1010
    for index, (label, slug) in enumerate(views[:5]):
        image = Image.open(render_root / f"roman-grunt-reforged-v1-{slug}.png")
        x = margin + index * (cell_w + gap)
        board.paste(fit(image, (cell_w, cell_h)), (x, top))
        draw.text((x, top + cell_h + 14), label, font=font(22, True), fill=(208, 194, 168))
    close_top = 1280
    close_w = (width - 2 * margin - 5 * gap) // 6
    close_h = 870
    for index, (label, slug) in enumerate(views[5:]):
        image = Image.open(render_root / f"roman-grunt-reforged-v1-{slug}.png")
        x = margin + index * (close_w + gap)
        board.paste(fit(image, (close_w, close_h)), (x, close_top))
        draw.text((x, close_top + close_h + 14), label, font=font(18, True), fill=(208, 194, 168))
    draw.text((80, 2315), "Newly authored review geometry. No recovered vertices or original texture pixels used.", font=font(22), fill=(135, 142, 150))
    board.save(output, optimize=True)


def comparison_board(ps2: Path, concept: Path, review: Path, output: Path) -> None:
    width, height = 3600, 2200
    board = Image.new("RGB", (width, height), (10, 12, 15))
    draw = ImageDraw.Draw(board)
    draw.text((70, 38), "ROMAN GRUNT V1 — OBJECTIVE REFERENCE COMPARISON", font=font(48, True), fill=(230, 214, 183))
    columns = [
        ("ORIGINAL PS2 RECONSTRUCTION — PRIVATE", Image.open(ps2)),
        ("APPROVED REFORGED CONCEPT", Image.open(concept)),
        ("BLENDER V1 — AWAITING REVIEW", Image.open(review)),
    ]
    margin, gap, top = 60, 30, 125
    cell_w = (width - 2 * margin - 2 * gap) // 3
    cell_h = 1930
    for index, (label, image) in enumerate(columns):
        x = margin + index * (cell_w + gap)
        draw.text((x, top), label, font=font(23, True), fill=(205, 190, 164))
        board.paste(fit(image, (cell_w, cell_h - 55)), (x, top + 45))
    board.save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-root", type=Path, default=DEFAULT_RENDER_ROOT)
    parser.add_argument("--ps2-reference", type=Path, default=DEFAULT_PS2)
    parser.add_argument("--concept", type=Path, default=DEFAULT_CONCEPT)
    args = parser.parse_args()
    review = args.render_root / "roman-grunt-reforged-v1-review.png"
    comparison = args.render_root / "roman-grunt-reforged-v1-comparison.png"
    contact_sheet(args.render_root, review)
    comparison_board(args.ps2_reference, args.concept, review, comparison)
    print(review)
    print(comparison)


if __name__ == "__main__":
    main()
