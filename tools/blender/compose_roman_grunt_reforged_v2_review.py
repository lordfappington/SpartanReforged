"""Compose private V2 review, reference, and V1-to-V2 comparison boards."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import compose_roman_grunt_reforged_v1_review as common


ROOT = Path(__file__).resolve().parents[2]
V2_ROOT = ROOT / "temp" / "roman-reforged-v2" / "renders"
V1_ROOT = ROOT / "temp" / "roman-reforged-v1" / "renders"
PS2 = ROOT / "temp" / "roman-research" / "turnaround" / "roman-standard-turnaround.png"
CONCEPT = ROOT / "assets" / "Concept" / "Characters" / "Roman-Grunt" / "roman-grunt-reforged-concept-v1-approved.png"


def contact_sheet(output: Path) -> None:
    views = [
        ("FRONT", "front"), ("FRONT THREE-QUARTER", "front-three-quarter"),
        ("SIDE", "side"), ("REAR THREE-QUARTER", "rear-three-quarter"), ("REAR", "rear"),
        ("HEAD / HELMET", "closeup-head-helmet"), ("TORSO ARMOUR", "closeup-torso-armour"),
        ("SKIRT CONSTRUCTION", "closeup-skirt"), ("SHIELD FRONT", "closeup-shield-front"),
        ("SHIELD REAR", "closeup-shield-rear"), ("SWORD / HAND SCALE", "closeup-sword"),
    ]
    width, height = 3600, 2400
    board = Image.new("RGB", (width, height), (11, 13, 16))
    draw = ImageDraw.Draw(board)
    draw.text((80, 42), "ROMAN GRUNT REFORGED V2 — TARGETED FORM PASS", font=common.font(52, True), fill=(230, 214, 183))
    draw.text((80, 108), "STATIC REVIEW BUILD — AWAITING HUMAN VISUAL APPROVAL", font=common.font(25), fill=(160, 164, 170))
    margin, gap, top = 70, 24, 170
    cell_w, cell_h = (width - 2 * margin - 4 * gap) // 5, 1010
    for index, (label, slug) in enumerate(views[:5]):
        image = Image.open(V2_ROOT / f"roman-grunt-reforged-v2-{slug}.png")
        x = margin + index * (cell_w + gap)
        board.paste(common.fit(image, (cell_w, cell_h)), (x, top))
        draw.text((x, top + cell_h + 14), label, font=common.font(22, True), fill=(208, 194, 168))
    close_top = 1280
    close_w, close_h = (width - 2 * margin - 5 * gap) // 6, 870
    for index, (label, slug) in enumerate(views[5:]):
        image = Image.open(V2_ROOT / f"roman-grunt-reforged-v2-{slug}.png")
        x = margin + index * (close_w + gap)
        board.paste(common.fit(image, (close_w, close_h)), (x, close_top))
        draw.text((x, close_top + close_h + 14), label, font=common.font(18, True), fill=(208, 194, 168))
    draw.text((80, 2315), "Newly authored V2 geometry. No recovered vertices or original texture pixels used.", font=common.font(22), fill=(135, 142, 150))
    board.save(output, optimize=True)


def three_way(v2_review: Path, output: Path) -> None:
    width, height = 3600, 2200
    board = Image.new("RGB", (width, height), (10, 12, 15))
    draw = ImageDraw.Draw(board)
    draw.text((70, 38), "ROMAN GRUNT V2 — REFERENCE COMPARISON", font=common.font(48, True), fill=(230, 214, 183))
    columns = [
        ("ORIGINAL PS2 RECONSTRUCTION — PRIVATE", Image.open(PS2)),
        ("APPROVED REFORGED CONCEPT", Image.open(CONCEPT)),
        ("BLENDER V2 — AWAITING REVIEW", Image.open(v2_review)),
    ]
    margin, gap, top = 60, 30, 125
    cell_w, cell_h = (width - 2 * margin - 2 * gap) // 3, 1930
    for index, (label, image) in enumerate(columns):
        x = margin + index * (cell_w + gap)
        draw.text((x, top), label, font=common.font(23, True), fill=(205, 190, 164))
        board.paste(common.fit(image, (cell_w, cell_h - 55)), (x, top + 45))
    board.save(output, optimize=True)


def v1_v2(output: Path) -> None:
    width, height = 3600, 2200
    board = Image.new("RGB", (width, height), (10, 12, 15))
    draw = ImageDraw.Draw(board)
    draw.text((70, 38), "ROMAN GRUNT — V1 TO V2 FORM CORRECTION", font=common.font(48, True), fill=(230, 214, 183))
    columns = [
        ("V1 — PIPELINE PROOF", Image.open(V1_ROOT / "roman-grunt-reforged-v1-review.png")),
        ("V2 — TARGETED FORM PASS", Image.open(V2_ROOT / "roman-grunt-reforged-v2-review.png")),
    ]
    margin, gap, top = 70, 40, 125
    cell_w, cell_h = (width - 2 * margin - gap) // 2, 1950
    for index, (label, image) in enumerate(columns):
        x = margin + index * (cell_w + gap)
        draw.text((x, top), label, font=common.font(25, True), fill=(205, 190, 164))
        board.paste(common.fit(image, (cell_w, cell_h - 55)), (x, top + 45))
    board.save(output, optimize=True)


def main() -> None:
    review = V2_ROOT / "roman-grunt-reforged-v2-review.png"
    comparison = V2_ROOT / "roman-grunt-reforged-v2-comparison.png"
    delta = V2_ROOT / "roman-grunt-reforged-v1-v2-comparison.png"
    contact_sheet(review)
    three_way(review, comparison)
    v1_v2(delta)
    print(review)
    print(comparison)
    print(delta)


if __name__ == "__main__":
    main()
