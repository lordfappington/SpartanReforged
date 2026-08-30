#!/usr/bin/env python3
"""Build a strict MODELS.MTL property/geometry/texture correlation report.

This probe assigns no native render meaning to the numbered MTL child types.
It preserves raw values, joins them to confirmed MODELS material membership and
decoded texture alpha classes, and reports simple field/value correlations.
Generated reports must be written beneath an ignored ``temp`` directory.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import struct
import sys
from collections import Counter, defaultdict
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "conversion"))

from export_models_gltf import discover_textures, resolve_texture  # noqa: E402
from spartan_models import (  # noqa: E402
    CANONICAL_HASHES,
    ModelsFormatError,
    load_models,
    parse_mtl,
    reconstruct_triangles,
    sha256,
)
from tim2_decode import decode_file  # noqa: E402


def require_range(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ModelsFormatError(f"{label} range 0x{offset:X}+0x{size:X} exceeds 0x{len(data):X}")


def parse_records(data: bytes) -> list[dict[str, Any]]:
    require_range(data, 0, 8, "MTL header")
    record_offset, record_count = struct.unpack_from("<2I", data, 0)
    require_range(data, 8, record_offset - 8, "MTL name table")
    names = [part.decode("ascii") for part in data[8:record_offset].split(b"\0") if part]
    if len(names) != record_count:
        raise ModelsFormatError("MTL name count differs from declared record count")
    result: list[dict[str, Any]] = []
    position = record_offset
    for index, name in enumerate(names):
        require_range(data, position, 16, f"MTL record {index}")
        length, child_count, header_08, header_0c = struct.unpack_from("<4I", data, position)
        require_range(data, position, length, f"MTL record {index}")
        end = position + length
        child_position = position + 16
        children: list[dict[str, Any]] = []
        for child_index in range(child_count):
            require_range(data, child_position, 8, f"MTL record {index} child {child_index}")
            child_length, child_type = struct.unpack_from("<2I", data, child_position)
            if child_length < 8 or child_position + child_length > end:
                raise ModelsFormatError(f"MTL record {index} child {child_index} has invalid bounds")
            payload = data[child_position + 8:child_position + child_length]
            strings = []
            for part in payload.split(b"\0"):
                if part and all(0x20 <= value < 0x7F for value in part):
                    strings.append(part.decode("ascii"))
            words = list(struct.unpack("<" + "I" * (len(payload) // 4), payload)) if len(payload) % 4 == 0 else []
            children.append({
                "childIndex": child_index,
                "offset": child_position,
                "relativeOffset": child_position - position,
                "length": child_length,
                "type": child_type,
                "payloadBytes": len(payload),
                "rawHex": payload.hex().upper(),
                "u32": words,
                "i32": [value if value < 0x80000000 else value - 0x100000000 for value in words],
                "strings": strings,
            })
            child_position += child_length
        if child_position != end:
            raise ModelsFormatError(f"MTL record {index} children do not fill record")
        result.append({
            "index": index,
            "name": name,
            "offset": position,
            "length": length,
            "childCount": child_count,
            "header08": header_08,
            "header0C": header_0c,
            "children": children,
        })
        position = end
    if position != len(data):
        raise ModelsFormatError("MTL record walk does not end at EOF")
    return result


def alpha_class(rgba: bytes) -> tuple[str, list[int], int]:
    values = sorted(set(rgba[3::4]))
    classification = (
        "OPAQUE" if values == [255]
        else "BINARY_ALPHA" if set(values) <= {0, 255}
        else "PARTIAL_ALPHA"
    )
    return classification, [values[0], values[-1]], len(values)


def property_key(child: dict[str, Any]) -> str:
    return f"type_{child['type']:02d}={','.join(f'0x{value:08X}' for value in child['u32'])}"


def confusion(rows: list[dict[str, Any]], predicate: str, key: str) -> dict[str, Any]:
    positive = {"BINARY_ALPHA", "PARTIAL_ALPHA"}
    tp = sum(row["alphaClass"] in positive and key in row["propertyKeys"] for row in rows)
    fp = sum(row["alphaClass"] not in positive and key in row["propertyKeys"] for row in rows)
    fn = sum(row["alphaClass"] in positive and key not in row["propertyKeys"] for row in rows)
    tn = sum(row["alphaClass"] not in positive and key not in row["propertyKeys"] for row in rows)
    return {"predicate": predicate, "key": key, "truePositive": tp, "falsePositive": fp,
            "falseNegative": fn, "trueNegative": tn}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--inventory", type=pathlib.Path)
    args = parser.parse_args()
    if "temp" not in {part.casefold() for part in args.output.resolve().parts}:
        parser.error("output must be beneath an ignored temp directory")

    mtl_path = args.world / "MODELS.MTL"
    mtl_data = mtl_path.read_bytes()
    digest = sha256(mtl_data)
    if len(mtl_data) != 5952 or digest != CANONICAL_HASHES["MODELS.MTL"]:
        raise ModelsFormatError(f"unexpected MODELS.MTL identity: {len(mtl_data)} bytes / {digest}")
    records = parse_records(mtl_data)
    public_records = parse_mtl(mtl_data)
    if len(records) != 55 or [item["name"] for item in records] != [item.name for item in public_records]:
        raise ModelsFormatError("strict and reusable MTL parsers disagree")

    model, identities = load_models(args.world, verify_hashes=True)
    level_root = args.world.parents[3]
    textures, verified_texture_count = discover_textures(level_root, args.inventory)
    descriptor_counts = Counter(item.material_id for item in model.descriptors)
    triangle_counts: Counter[int] = Counter()
    vertex_counts: Counter[int] = Counter()
    for batch in model.batches:
        triangle_counts[batch.material_id] += len(reconstruct_triangles(batch.controls))
        vertex_counts[batch.material_id] += len(batch.positions)

    used_rows: list[dict[str, Any]] = []
    for record, material in zip(records, model.materials):
        record["resourceStems"] = list(material.resource_stems)
        record["numericProperties"] = [
            {"type": item_type, "u32": list(values)} for item_type, values in material.numeric_properties
        ]
        record["descriptorCount"] = descriptor_counts[material.index]
        record["triangleCount"] = triangle_counts[material.index]
        record["streamedVertexCount"] = vertex_counts[material.index]
        if not descriptor_counts[material.index]:
            continue
        texture = resolve_texture(material.name, material.resource_stems, textures)
        alpha = "UNRESOLVED_BINDING"
        alpha_range: list[int] | None = None
        alpha_distinct: int | None = None
        texture_path = texture.relative_path if texture else None
        if texture:
            image, _, decode_report = decode_file(level_root / pathlib.PurePosixPath(texture.relative_path))
            alpha, alpha_range, alpha_distinct = alpha_class(image.rgba)
        numeric = [child for child in record["children"] if child["type"] not in (0, 1)]
        keys = [property_key(child) for child in numeric]
        used_rows.append({
            "mtlIndex": material.index,
            "name": material.name,
            "textureBindingStatus": "TEXTURED_CONFIRMED" if texture else "PLACEHOLDER_UNRESOLVED",
            "texture": texture_path,
            "textureSha256": texture.sha256 if texture else None,
            "alphaClass": alpha,
            "alphaRange": alpha_range,
            "alphaDistinctValues": alpha_distinct,
            "descriptorCount": descriptor_counts[material.index],
            "triangleCount": triangle_counts[material.index],
            "streamedVertexCount": vertex_counts[material.index],
            "propertyKeys": keys,
            "propertyTypes": [child["type"] for child in numeric],
            "singleSidedVisualFailure": "UNKNOWN_PER_MATERIAL; SCENE_LEVEL_FAILURE_CONFIRMED",
            "forcedTwoSidedVisualResult": "UNKNOWN_PER_MATERIAL; SCENE_LEVEL_COHERENCE_CONFIRMED",
            "opaqueAlphaArtifact": (
                "EXPECTED" if alpha in {"BINARY_ALPHA", "PARTIAL_ALPHA"}
                else "CLOUD_OCCLUSION_CONFIRMED_DESPITE_OPAQUE_PIXEL_ALPHA" if material.name == "CLOUD"
                else "NO_PIXEL_ALPHA_INDICATION" if alpha == "OPAQUE"
                else "UNKNOWN_UNRESOLVED_TEXTURE"
            ),
            "sceneRole": "NAME/PRIOR_DIAGNOSTIC_ONLY; NOT_AN_MTL_SEMANTIC",
        })

    frequency: dict[str, dict[str, Any]] = {}
    materials_by_key: dict[str, list[str]] = defaultdict(list)
    for row in used_rows:
        for key in row["propertyKeys"]:
            materials_by_key[key].append(row["name"])
    for key, names in sorted(materials_by_key.items()):
        subset = [row for row in used_rows if key in row["propertyKeys"]]
        frequency[key] = {
            "usedMaterialCount": len(names),
            "materials": names,
            "alphaClasses": dict(Counter(row["alphaClass"] for row in subset)),
            "descriptorCount": sum(row["descriptorCount"] for row in subset),
            "triangleCount": sum(row["triangleCount"] for row in subset),
        }
    type_keys = sorted({f"type_{child['type']:02d}=PRESENT" for record in records for child in record["children"] if child["type"] not in (0, 1)})
    presence_confusions = []
    for present_key in type_keys:
        item_type = int(present_key[5:7])
        transformed = []
        for row in used_rows:
            copy = dict(row)
            copy["propertyKeys"] = [present_key] if item_type in row["propertyTypes"] else []
            transformed.append(copy)
        presence_confusions.append(confusion(transformed, "texture has binary/partial alpha", present_key))

    report = {
        "identity": {"path": str(mtl_path.resolve()), "size": len(mtl_data), "sha256": digest},
        "sourceHashes": identities,
        "recordCount": len(records),
        "recordWalkEndsAtEof": True,
        "reusableParserAgreement": True,
        "geometryUsedRecordCount": len(used_rows),
        "verifiedTim2InventoryCount": verified_texture_count,
        "records": records,
        "usedMaterialBehavior": used_rows,
        "propertyValueFrequency": frequency,
        "alphaPresenceCorrelations": presence_confusions,
        "limitations": [
            "Existing culling diagnostics are scene-level, not per-material controlled observations.",
            "Pixel alpha class does not identify native alpha-test or blend equations.",
            "CLOUD has opaque decoded alpha; standard source-alpha blending alone cannot remove its shell.",
            "Numbered MTL child types remain engine property identifiers with unknown native names.",
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "models_mtl_render_matrix.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
    )
    with (args.output / "models_mtl_used_materials.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["mtlIndex", "name", "textureBindingStatus", "texture", "alphaClass", "alphaRange",
                  "descriptorCount", "triangleCount", "streamedVertexCount", "propertyTypes", "propertyKeys",
                  "singleSidedVisualFailure", "forcedTwoSidedVisualResult", "opaqueAlphaArtifact"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in used_rows:
            writer.writerow({**row, "alphaRange": json.dumps(row["alphaRange"]),
                             "propertyTypes": json.dumps(row["propertyTypes"]),
                             "propertyKeys": json.dumps(row["propertyKeys"])})
    print(json.dumps({
        "recordCount": len(records), "geometryUsedRecordCount": len(used_rows),
        "usedAlphaClasses": dict(Counter(row["alphaClass"] for row in used_rows)),
        "outputs": [str(args.output / "models_mtl_render_matrix.json"),
                    str(args.output / "models_mtl_used_materials.csv")],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
