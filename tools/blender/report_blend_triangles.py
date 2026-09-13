"""Write a deterministic evaluated per-object triangle report for a Blender scene.

Invoke after the blend path so Blender opens the target scene first::

    blender --background scene.blend --python report_blend_triangles.py -- --output report.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import bpy


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--include-studio", action="store_true")
    return parser.parse_args(argv)


def category(name: str) -> str:
    lowered = name.lower()
    for token, label in (
        ("shield", "shield"),
        ("skirt", "skirt"),
        ("helmet", "helmet"),
        ("head", "head"),
        ("eye", "head"),
        ("mouth", "head"),
        ("brow", "head"),
        ("torso", "torso"),
        ("shoulder", "shoulders"),
        ("arm", "arms_hands"),
        ("hand", "arms_hands"),
        ("wrist", "arms_hands"),
        ("sword", "sword"),
        ("thigh", "legs_feet"),
        ("calf", "legs_feet"),
        ("foot", "legs_feet"),
        ("sandal", "legs_feet"),
    ):
        if token in lowered:
            return label
    return "other"


def main() -> None:
    args = parse_args()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if not args.include_studio and obj.name.startswith("Studio_"):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        triangles = len(mesh.loop_triangles)
        evaluated.to_mesh_clear()
        rows.append({"object": obj.name, "category": category(obj.name), "triangles": triangles})
    rows.sort(key=lambda row: (-row["triangles"], row["object"]))
    total = sum(row["triangles"] for row in rows)
    for row in rows:
        row["percentage"] = round((row["triangles"] * 100.0 / total) if total else 0.0, 4)
    by_category: dict[str, int] = {}
    for row in rows:
        by_category[row["category"]] = by_category.get(row["category"], 0) + row["triangles"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("object", "category", "triangles", "percentage"))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "blend": bpy.data.filepath,
        "total_triangles": total,
        "object_count": len(rows),
        "by_category": dict(sorted(by_category.items(), key=lambda item: (-item[1], item[0]))),
        "top_20": rows[:20],
    }
    args.output.with_suffix(".json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
