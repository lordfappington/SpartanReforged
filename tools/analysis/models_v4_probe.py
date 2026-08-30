#!/usr/bin/env python3
"""Deterministic aggregate survey of LEVEL00 MODELS V4-8 attributes.

The source files are read only. Reports contain aggregate statistics and are
restricted to an ignored ``temp`` directory; no raw vertex stream is emitted.
No RGBA, normal, or render-state meaning is assigned by the parser.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Iterable


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "conversion"))

from export_models_gltf import discover_textures, resolve_texture  # noqa: E402
from spartan_models import (  # noqa: E402
    CANONICAL_HASHES,
    Batch,
    ModelsFormatError,
    decode_uv,
    load_models,
    reconstruct_triangles,
    sha256,
)
from tim2_decode import decode_file  # noqa: E402


def signed8(value: int) -> int:
    return value if value < 0x80 else value - 0x100


def percentile(values: list[int | float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ModelsFormatError("cannot summarize an empty channel")
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return float(ordered[lower] * (upper - position) + ordered[upper] * (position - lower))


def summarize(values: list[int]) -> dict[str, Any]:
    counts = Counter(values)
    return {
        "minimum": min(values),
        "maximum": max(values),
        "uniqueCount": len(counts),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "q05": percentile(values, 0.05),
        "q95": percentile(values, 0.95),
        "zeroCount": counts[0],
        "value80Count": counts[0x80],
        "valueFFCount": counts[0xFF],
        "common": [{"value": value, "count": count} for value, count in counts.most_common(16)],
        "frequency": {str(value): counts[value] for value in sorted(counts)},
    }


def pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    left_ss = sum((value - left_mean) ** 2 for value in left)
    right_ss = sum((value - right_mean) ** 2 for value in right)
    denominator = math.sqrt(left_ss * right_ss)
    return numerator / denominator if denominator else None


def material_alpha(model, material_id: int, level_root: pathlib.Path, textures) -> tuple[str, str | None]:
    material = model.materials[material_id]
    texture = resolve_texture(material.name, material.resource_stems, textures)
    if texture is None:
        return "UNRESOLVED_BINDING", None
    image, _, _ = decode_file(level_root / pathlib.PurePosixPath(texture.relative_path))
    values = set(image.rgba[3::4])
    classification = (
        "OPAQUE" if values == {255}
        else "BINARY_ALPHA" if values <= {0, 255}
        else "PARTIAL_ALPHA"
    )
    return classification, texture.relative_path


def rows_for_batches(batches: Iterable[Batch]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for batch in batches:
        if not (len(batch.positions) == len(batch.uv_raw) == len(batch.attributes_v4_8)):
            raise ModelsFormatError(f"batch {batch.global_index} V4 cardinality disagreement")
        for local_index, (position, uv_raw, attribute) in enumerate(
            zip(batch.positions, batch.uv_raw, batch.attributes_v4_8)
        ):
            rows.append({
                "descriptor": batch.descriptor_id,
                "batch": batch.global_index,
                "localIndex": local_index,
                "position": position,
                "uv": decode_uv(uv_raw, "source"),
                "attribute": attribute,
            })
    return rows


def group_batches_by_material(batches: Iterable[Batch]) -> dict[int, tuple[Batch, ...]]:
    grouped: dict[int, list[Batch]] = defaultdict(list)
    for batch in batches:
        grouped[batch.material_id].append(batch)
    return {material_id: tuple(values) for material_id, values in sorted(grouped.items())}


def channel_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    unsigned = [[row["attribute"][axis] for row in rows] for axis in range(4)]
    signed = [[signed8(value) for value in channel] for channel in unsigned]
    return {
        "recordCount": len(rows),
        "unsigned": [summarize(channel) for channel in unsigned],
        "signed": [summarize(channel) for channel in signed],
        "constantTuple": len({row["attribute"] for row in rows}) == 1,
        "uniqueTupleCount": len({row["attribute"] for row in rows}),
        "allFirstThreeAtOrBelow80": all(value <= 0x80 for channel in unsigned[:3] for value in channel),
        "firstThreeAbove80Count": sum(value > 0x80 for channel in unsigned[:3] for value in channel),
        "firstThreeEqualCount": sum(a == b == c for a, b, c, _ in (row["attribute"] for row in rows)),
    }


def cloud_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tuples = Counter(row["attribute"] for row in rows)
    positions = [[float(row["position"][axis]) for row in rows] for axis in range(3)]
    uvs = [[float(row["uv"][axis]) for row in rows] for axis in range(2)]
    center = [statistics.fmean(channel) for channel in positions]
    radial_xz = [math.hypot(row["position"][0] - center[0], row["position"][2] - center[2]) for row in rows]
    radial_3d = [math.sqrt(sum((row["position"][axis] - center[axis]) ** 2 for axis in range(3))) for row in rows]
    uv_min = [min(channel) for channel in uvs]
    uv_max = [max(channel) for channel in uvs]
    uv_edge = []
    for row in rows:
        normalized = []
        for axis in range(2):
            span = uv_max[axis] - uv_min[axis]
            normalized.append((row["uv"][axis] - uv_min[axis]) / span if span else 0.0)
        uv_edge.append(min(normalized[0], 1.0 - normalized[0], normalized[1], 1.0 - normalized[1]))

    independent = {
        "x": positions[0], "y": positions[1], "z": positions[2],
        "u": uvs[0], "v": uvs[1], "radialXZ": radial_xz,
        "radial3D": radial_3d, "uvEdgeDistance": uv_edge,
        "localVertexIndex": [float(row["localIndex"]) for row in rows],
        "batchIndex": [float(row["batch"]) for row in rows],
    }
    correlations: dict[str, dict[str, float | None]] = {}
    for channel in range(4):
        values = [float(row["attribute"][channel]) for row in rows]
        correlations[f"byte{channel}"] = {name: pearson(values, vector) for name, vector in independent.items()}

    by_tuple = []
    for attribute, count in tuples.most_common():
        subset = [row for row in rows if row["attribute"] == attribute]
        by_tuple.append({
            "tuple": list(attribute), "count": count,
            "positionMin": [min(row["position"][axis] for row in subset) for axis in range(3)],
            "positionMax": [max(row["position"][axis] for row in subset) for axis in range(3)],
            "uvMin": [min(row["uv"][axis] for row in subset) for axis in range(2)],
            "uvMax": [max(row["uv"][axis] for row in subset) for axis in range(2)],
        })

    by_batch: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_batch[row["batch"]].append(row)
    batch_summaries = [{
        "batch": batch,
        "recordCount": len(values),
        "uniqueTupleCount": len({row["attribute"] for row in values}),
        "tupleTransitionCount": sum(
            values[index - 1]["attribute"] != values[index]["attribute"] for index in range(1, len(values))
        ),
    } for batch, values in sorted(by_batch.items())]

    repeated_positions: dict[tuple[float, float, float], set[tuple[int, int, int, int]]] = defaultdict(set)
    repeated_position_uv: dict[tuple[float, float, float, float, float], set[tuple[int, int, int, int]]] = defaultdict(set)
    for row in rows:
        repeated_positions[tuple(row["position"])].add(row["attribute"])
        repeated_position_uv[tuple(row["position"]) + tuple(row["uv"])].add(row["attribute"])
    return {
        "uniqueTuples": by_tuple,
        "correlations": correlations,
        "center": center,
        "batchSummaries": batch_summaries,
        "repeatedPositionGroupCount": sum(len(values) > 1 for values in repeated_positions.values()),
        "repeatedPositionUvGroupCount": sum(len(values) > 1 for values in repeated_position_uv.values()),
        "samePositionDifferentAttributeGroups": sum(len(values) > 1 for values in repeated_positions.values()),
        "samePositionUvDifferentAttributeGroups": sum(len(values) > 1 for values in repeated_position_uv.values()),
    }


def normal_plausibility(rows: list[dict[str, Any]]) -> dict[str, Any]:
    signed_lengths = []
    biased_lengths = []
    for row in rows:
        first = row["attribute"][:3]
        signed = [signed8(value) / 127.0 for value in first]
        biased = [(value - 128.0) / 127.0 for value in first]
        signed_lengths.append(math.sqrt(sum(value * value for value in signed)))
        biased_lengths.append(math.sqrt(sum(value * value for value in biased)))
    return {
        "signedUnitLengthMean": statistics.fmean(signed_lengths),
        "signedWithinTenPercentOfUnitFraction": sum(0.9 <= value <= 1.1 for value in signed_lengths) / len(rows),
        "biasedUnitLengthMean": statistics.fmean(biased_lengths),
        "biasedWithinTenPercentOfUnitFraction": sum(0.9 <= value <= 1.1 for value in biased_lengths) / len(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--inventory", type=pathlib.Path)
    args = parser.parse_args()
    if "temp" not in {part.casefold() for part in args.output.resolve().parts}:
        parser.error("output must be beneath an ignored temp directory")

    bin_data = (args.world / "MODELS.BIN").read_bytes()
    mtl_data = (args.world / "MODELS.MTL").read_bytes()
    if sha256(bin_data) != CANONICAL_HASHES["MODELS.BIN"] or sha256(mtl_data) != CANONICAL_HASHES["MODELS.MTL"]:
        raise ModelsFormatError("canonical MODELS input hash mismatch")
    model, hashes = load_models(args.world, verify_hashes=True)
    rows = rows_for_batches(model.batches)
    if len(rows) != 88314:
        raise ModelsFormatError(f"expected 88,314 V4 records, got {len(rows)}")
    if any(row["attribute"][3] != 0x80 for row in rows):
        raise ModelsFormatError("V4 byte 3 is not globally 0x80")

    level_root = args.world.parents[3]
    textures, verified_textures = discover_textures(level_root, args.inventory)
    descriptors = Counter(item.material_id for item in model.descriptors)
    triangles: Counter[int] = Counter()
    material_batches = group_batches_by_material(model.batches)
    for batch in model.batches:
        triangles[batch.material_id] += len(reconstruct_triangles(batch.controls))

    materials = []
    for material_id in sorted(material_batches):
        material = model.materials[material_id]
        material_rows = rows_for_batches(material_batches[material_id])
        type2 = material.property_values(2)
        alpha, texture = material_alpha(model, material_id, level_root, textures)
        materials.append({
            "mtlIndex": material_id, "name": material.name,
            "type2": [list(value) for value in type2],
            "textureAlphaClass": alpha, "texture": texture,
            "descriptorCount": descriptors[material_id], "triangleCount": triangles[material_id],
            "statistics": channel_matrix(material_rows),
            "normalPlausibility": normal_plausibility(material_rows),
        })

    type2_groups: dict[str, list[Batch]] = defaultdict(list)
    for material_id, batches in material_batches.items():
        values = model.materials[material_id].property_values(2)
        key = str(values[0][0]) if values else "ABSENT"
        type2_groups[key].extend(batches)
    grouped = {key: channel_matrix(rows_for_batches(batches)) for key, batches in sorted(type2_groups.items())}
    grouped_materials = {
        key: sorted({model.materials[batch.material_id].name for batch in batches})
        for key, batches in sorted(type2_groups.items())
    }

    cloud_material = next((item for item in model.materials if item.name == "CLOUD"), None)
    if cloud_material is None or cloud_material.index != 31 or cloud_material.property_values(2) != ((5, 0),):
        raise ModelsFormatError("CLOUD material binding/property changed")
    cloud_batches = material_batches[31]
    cloud_descriptors = sorted({batch.descriptor_id for batch in cloud_batches})
    if cloud_descriptors != [48] or triangles[31] != 1728:
        raise ModelsFormatError("CLOUD descriptor/topology identity changed")
    cloud_rows = rows_for_batches(cloud_batches)

    report = {
        "sourceHashes": hashes,
        "v4RecordCount": len(rows),
        "positionUvV4CardinalityOneToOne": True,
        "byte3Globally80": True,
        "verifiedTim2InventoryCount": verified_textures,
        "global": channel_matrix(rows),
        "globalNormalPlausibility": normal_plausibility(rows),
        "materials": materials,
        "type2Groups": grouped,
        "type2GroupMaterials": grouped_materials,
        "cloud": {
            "mtlIndex": 31, "descriptorIds": cloud_descriptors,
            "recordCount": len(cloud_rows), "triangleCount": triangles[31],
            "statistics": channel_matrix(cloud_rows),
            "normalPlausibility": normal_plausibility(cloud_rows),
            "deep": cloud_analysis(cloud_rows),
            "standardPs2VertexAlphaIfByte3": 1.0,
            "textureAlpha": 1.0,
            "standardTextureTimesVertexAlpha": 1.0,
        },
        "limitations": [
            "The V4-8 destination VU addresses and later VU-to-GS routing are not present in the archive data.",
            "Correlation cannot assign RGBA, normal, lighting, or control semantics by itself.",
            "MTL type-2 values are engine properties, not proven packed GS ALPHA registers.",
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "models_v4_probe.json"
    target.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "v4RecordCount": len(rows),
        "globalUnsigned": [
            {key: item[key] for key in ("minimum", "maximum", "uniqueCount", "mean", "median")}
            for item in report["global"]["unsigned"]
        ],
        "cloudUniqueTupleCount": report["cloud"]["statistics"]["uniqueTupleCount"],
        "output": str(target),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
