#!/usr/bin/env python3
"""Export confirmed LEVEL00 MODELS geometry to traceable glTF 2.0.

The exporter writes only beneath a temp directory. It never modifies input
resources or invents normals. V4-8 is omitted by default and has an explicit
diagnostic color mode. Optional texture decoding creates native-resolution
derived PNGs beside the ignored export.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import struct
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from tim2_decode import decode_file

from spartan_models import (
    Batch,
    Descriptor,
    ModelsData,
    ModelsFormatError,
    bounds,
    decode_uv,
    load_models,
    reconstruct_triangles,
    select_descriptors,
    sha256,
    transform_position,
)


ARRAY_BUFFER = 34962
ELEMENT_ARRAY_BUFFER = 34963
FLOAT = 5126
UNSIGNED_SHORT = 5123
UNSIGNED_INT = 5125
TRIANGLES = 4
REPEAT = 10497
MIRRORED_REPEAT = 33648
VALIDATED_MODERN_V_MODE = "source"
EXPORTER_VERSION = "1.5.0"


def decode_v4_color(value: tuple[int, int, int, int]) -> tuple[float, float, float, float]:
    """Map PS2-range color to legal glTF COLOR_0; retain raw bytes in the model."""
    return tuple(min(component / 128.0, 1.0) for component in value)


@dataclass(frozen=True)
class TextureReference:
    relative_path: str
    sha256: str


@dataclass(frozen=True)
class TextureImageInfo:
    uri: str
    width: int
    height: int
    alpha_classification: str
    png_sha256: str
    rgba_sha256: str


COORDINATE_METADATA = {
    "source": ("(X,Y,Z)->(X,Y,Z)", 1),
    "gltf": ("(X,Y,Z)->(X,Y,-Z)", -1),
    "x_z_neg_y": ("(X,Y,Z)->(X,Z,-Y)", 1),
    "x_z_y": ("(X,Y,Z)->(X,Z,Y)", -1),
}


class BufferBuilder:
    def __init__(self) -> None:
        self.data = bytearray()
        self.views: list[dict[str, Any]] = []
        self.accessors: list[dict[str, Any]] = []

    def add(self, payload: bytes, target: int | None = None) -> int:
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        self.data.extend(payload)
        view: dict[str, Any] = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
        if target is not None:
            view["target"] = target
        self.views.append(view)
        return len(self.views) - 1

    def accessor(
        self,
        view: int,
        component_type: int,
        count: int,
        accessor_type: str,
        minimum: Iterable[float | int] | None = None,
        maximum: Iterable[float | int] | None = None,
    ) -> int:
        item: dict[str, Any] = {
            "bufferView": view,
            "byteOffset": 0,
            "componentType": component_type,
            "count": count,
            "type": accessor_type,
        }
        if minimum is not None:
            item["min"] = list(minimum)
        if maximum is not None:
            item["max"] = list(maximum)
        self.accessors.append(item)
        return len(self.accessors) - 1


def _allowed_output(path: pathlib.Path) -> bool:
    return "temp" in {part.casefold() for part in path.resolve().parts}


def _pack_floats(rows: Iterable[Iterable[float]]) -> bytes:
    values = [float(value) for row in rows for value in row]
    if not all(math.isfinite(value) for value in values):
        raise ModelsFormatError("export payload contains NaN/Inf")
    return struct.pack(f"<{len(values)}f", *values)


def _pack_indices(values: list[int], component_type: int) -> bytes:
    if not values or min(values) < 0:
        raise ModelsFormatError("index payload is empty or contains a negative value")
    code = "H" if component_type == UNSIGNED_SHORT else "I"
    limit = 0xFFFF if component_type == UNSIGNED_SHORT else 0xFFFFFFFF
    if max(values) > limit:
        raise ModelsFormatError("index value exceeds selected component type")
    return struct.pack(f"<{len(values)}{code}", *values)


def _tri_area2(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> float:
    ab = tuple(b[i] - a[i] for i in range(3))
    ac = tuple(c[i] - a[i] for i in range(3))
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return math.sqrt(sum(value * value for value in cross))


def _uv_area2(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))


def _git_commit(project_root: pathlib.Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=project_root, check=True,
            capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def discover_textures(level_root: pathlib.Path, inventory_path: pathlib.Path | None) -> tuple[dict[str, list[TextureReference]], int]:
    inventory: dict[str, str] = {}
    if inventory_path:
        entries = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory = {
            entry["relative_path"].replace("\\", "/").casefold(): entry["sha256"].upper()
            for entry in entries if entry.get("extension", "").casefold() == ".tm2"
        }
    by_stem: dict[str, list[TextureReference]] = {}
    verified = 0
    for path in sorted(level_root.rglob("*.TM2")):
        relative = path.relative_to(level_root).as_posix()
        digest = sha256(path.read_bytes())
        if inventory:
            expected = inventory.get(relative.casefold())
            if expected is None or expected != digest:
                raise ModelsFormatError(f"TIM2 inventory mismatch: {relative}")
            verified += 1
        by_stem.setdefault(path.stem.casefold(), []).append(TextureReference(relative, digest))
    if inventory and verified != len(inventory):
        raise ModelsFormatError(f"TIM2 inventory coverage mismatch: verified {verified}, expected {len(inventory)}")
    return by_stem, verified


def resolve_texture(material_name: str, resource_stems: tuple[str, ...], textures: dict[str, list[TextureReference]]) -> TextureReference | None:
    candidates: list[TextureReference] = []
    for stem in resource_stems or (material_name,):
        candidates.extend(textures.get(stem.casefold(), ()))
    unique = {(item.relative_path, item.sha256): item for item in candidates}
    return next(iter(unique.values())) if len(unique) == 1 else None


def decode_bound_textures(
    model: ModelsData,
    selected: tuple[Descriptor, ...],
    level_root: pathlib.Path,
    textures: dict[str, list[TextureReference]],
    output: pathlib.Path,
) -> tuple[dict[str, TextureImageInfo], dict[str, Any]]:
    """Decode each unique strongly resolved selected texture exactly once."""
    output_dir = output.parent / "textures"
    images: dict[str, TextureImageInfo] = {}
    decoded_sources: set[str] = set()
    cached = written = 0
    for material_id in sorted({item.material_id for item in selected}):
        material = model.materials[material_id]
        reference = resolve_texture(material.name, material.resource_stems, textures)
        if reference is None:
            continue
        source_key = reference.relative_path.casefold()
        if source_key in decoded_sources:
            continue
        decoded_sources.add(source_key)
        source = level_root / pathlib.PurePosixPath(reference.relative_path)
        image, png, report = decode_file(source)
        target = output_dir / f"{source.stem}.png"
        if target.is_file() and target.read_bytes() == png:
            cached += 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(png)
            written += 1
        alpha_values = set(image.rgba[3::4])
        alpha_classification = (
            "FULLY_OPAQUE" if alpha_values == {255}
            else "BINARY_ALPHA" if alpha_values <= {0, 255}
            else "PARTIAL_ALPHA"
        )
        stem = source.stem.casefold()
        if stem in images:
            raise ModelsFormatError(f"decoded texture basename collision: {source.stem}")
        images[stem] = TextureImageInfo(
            target.relative_to(output.parent).as_posix(), image.width, image.height,
            alpha_classification, str(report["pngSha256"]), str(report["rgbaSha256"]),
        )
    return images, {
        "uniqueDecodedTextureCount": len(images),
        "cachedDecodeCount": cached,
        "writtenDecodeCount": written,
        "decodedPngBytes": sum((output.parent / item.uri).stat().st_size for item in images.values()),
    }


def build_gltf(
    model: ModelsData,
    selected: tuple[Descriptor, ...],
    buffer_uri: str,
    identities: dict[str, str],
    texture_map: dict[str, list[TextureReference]],
    coords: str,
    winding: str,
    v_mode: str,
    texture_images: dict[str, str | TextureImageInfo] | None = None,
    sampler_mode: str = "repeat",
    mtl_render_semantics: str = "raw",
    v4_color: str = "omitted",
) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    sampler_values = {"repeat": REPEAT, "mirrored-repeat": MIRRORED_REPEAT}
    if sampler_mode not in sampler_values:
        raise ModelsFormatError(f"unsupported sampler mode {sampler_mode!r}")
    if mtl_render_semantics not in {"raw", "experimental"}:
        raise ModelsFormatError(f"unsupported MTL render semantics mode {mtl_render_semantics!r}")
    if v4_color not in {"omitted", "ps2-rgba"}:
        raise ModelsFormatError(f"unsupported V4 color mode {v4_color!r}")
    reverse = winding == "reverse"
    selected_ids = {item.index for item in selected}
    batches_by_descriptor: dict[int, list[Batch]] = {item.index: [] for item in selected}
    for batch in model.batches:
        if batch.descriptor_id in selected_ids:
            batches_by_descriptor[batch.descriptor_id].append(batch)

    material_ids = sorted({item.material_id for item in selected})
    material_map = {source_id: export_id for export_id, source_id in enumerate(material_ids)}
    texture_images = texture_images or {}
    materials: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    gltf_textures: list[dict[str, Any]] = []
    texture_slots_by_source: dict[str, tuple[int, int]] = {}
    material_reports: list[dict[str, Any]] = []
    bound_textures = 0
    for material_id in material_ids:
        source = model.materials[material_id]
        texture = resolve_texture(source.name, source.resource_stems, texture_map)
        extras: dict[str, Any] = {
            "sourceMtlIndex": material_id,
            "resourceStems": list(source.resource_stems),
            "placeholderOnly": True,
        }
        material_item: dict[str, Any] = {
            "name": f"UNRESOLVED_{source.name}",
            "extras": extras,
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.5, 0.5, 0.5, 1.0],
                "metallicFactor": 0.0,
            },
            "extensions": {"KHR_materials_unlit": {}},
        }
        mapping: dict[str, Any] = {
            "mtlIndex": material_id,
            "mtlName": source.name,
            "bindingStatus": "PLACEHOLDER_UNRESOLVED",
            "placeholder": True,
        }
        if texture:
            bound_textures += 1
            extras["sourceTextureReference"] = texture.relative_path
            extras["sourceTextureSha256"] = texture.sha256
            material_item["name"] = f"mtl_{material_id:02d}_{source.name}"
            mapping.update({
                "bindingStatus": "TEXTURE_REFERENCE_ONLY",
                "sourceTim2": texture.relative_path,
                "sourceTim2Sha256": texture.sha256,
            })
            image_value = texture_images.get(pathlib.PurePosixPath(texture.relative_path).stem.casefold())
            if image_value:
                image_info = image_value if isinstance(image_value, TextureImageInfo) else TextureImageInfo(
                    image_value, 0, 0, "UNKNOWN", "UNKNOWN", "UNKNOWN",
                )
                source_key = texture.relative_path.casefold()
                if source_key in texture_slots_by_source:
                    image_index, texture_index = texture_slots_by_source[source_key]
                else:
                    image_index = len(images)
                    image_item: dict[str, Any] = {
                        "name": pathlib.PurePosixPath(texture.relative_path).stem,
                        "uri": image_info.uri,
                    }
                    if image_info.width and image_info.height:
                        image_item["extras"] = {
                            "sourceWidth": image_info.width,
                            "sourceHeight": image_info.height,
                            "pngSha256": image_info.png_sha256,
                            "rgbaSha256": image_info.rgba_sha256,
                        }
                    images.append(image_item)
                    texture_index = len(gltf_textures)
                    gltf_textures.append({"source": image_index, "sampler": 0})
                    texture_slots_by_source[source_key] = (image_index, texture_index)
                material_item["pbrMetallicRoughness"] = {
                    "baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                    "baseColorTexture": {"index": texture_index},
                    "metallicFactor": 0.0,
                }
                extras["placeholderOnly"] = False
                extras["renderSemantics"] = "GENERATED_UNLIT_VALIDATION_MATERIAL"
                extras["samplerWrapS"] = sampler_mode.upper().replace("-", "_")
                extras["samplerWrapT"] = sampler_mode.upper().replace("-", "_")
                extras["sourceAlphaClassification"] = image_info.alpha_classification
                extras["alphaPolicy"] = "OPAQUE_MATERIAL; SOURCE_ALPHA_RETAINED_IN_PNG"
                mapping.update({
                    "bindingStatus": "TEXTURED_CONFIRMED",
                    "decodedPng": image_info.uri,
                    "width": image_info.width,
                    "height": image_info.height,
                    "alphaClassification": image_info.alpha_classification,
                    "alphaMode": "OPAQUE",
                    "samplerMode": sampler_mode,
                    "placeholder": False,
                })
        property_2_values = source.property_values(2)
        extras["sourceMtlNumericProperties"] = [
            {"type": property_type, "u32": list(values)}
            for property_type, values in source.numeric_properties
        ]
        extras["mtlRenderSemanticsMode"] = mtl_render_semantics.upper()
        if mtl_render_semantics == "experimental":
            # The PS2 GS primitive state has no face-culling selector. Keeping
            # all submitted triangles visible is therefore the least lossy GS
            # rasterization approximation, while remaining opt-in because
            # Spartan could still cull earlier in its CPU/VU pipeline.
            material_item["doubleSided"] = True
            extras["doubleSidedEvidence"] = "GENERIC_PS2_GS_NO_CULL_BIT; SPARTAN_PRE_GS_CULLING_UNKNOWN"
            alpha_classification = mapping.get("alphaClassification")
            # Type 2 is present on every geometry material whose bound texture
            # has binary/partial alpha (9/9), but also on three opaque textures.
            # BLEND is only a glTF validation approximation: it avoids an
            # invented alpha-test threshold and does not claim the native GS
            # equation. Opaque type-2 textures, including CLOUD, remain OPAQUE.
            if property_2_values and alpha_classification in {"BINARY_ALPHA", "PARTIAL_ALPHA"}:
                material_item["alphaMode"] = "BLEND"
                extras["alphaPolicy"] = "EXPERIMENTAL_GLTF_BLEND_FROM_MTL_TYPE_2_AND_SOURCE_PIXEL_ALPHA"
                mapping["alphaMode"] = "BLEND"
                mapping["sourceMtlType2"] = [list(values) for values in property_2_values]
            else:
                mapping["alphaMode"] = "OPAQUE"
            mapping["doubleSided"] = True
        else:
            mapping["doubleSided"] = False
        materials.append(material_item)
        material_reports.append(mapping)

    builder = BufferBuilder()
    meshes: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    selected_batches = selected_vertices = selected_triangles = 0
    referenced_vertices = 0
    geometric_degenerates = uv_degenerates = 0
    all_source_positions: list[tuple[float, float, float]] = []
    all_output_positions: list[tuple[float, float, float]] = []
    all_source_uv: list[tuple[float, float]] = []
    all_output_uv: list[tuple[float, float]] = []
    descriptor_reports: list[dict[str, Any]] = []

    for descriptor in selected:
        descriptor_batches = batches_by_descriptor[descriptor.index]
        if not descriptor_batches:
            raise ModelsFormatError(f"selected descriptor {descriptor.index} has no parsed batches")
        positions: list[tuple[float, float, float]] = []
        output_positions: list[tuple[float, float, float]] = []
        source_uv: list[tuple[float, float]] = []
        output_uv: list[tuple[float, float]] = []
        output_colors: list[tuple[float, float, float, float]] = []
        indices: list[int] = []
        batch_ranges: list[dict[str, int]] = []
        for batch in descriptor_batches:
            vertex_start = len(positions)
            index_start = len(indices)
            batch_positions = list(batch.positions)
            batch_output_positions = [transform_position(value, coords) for value in batch.positions]
            batch_source_uv = [decode_uv(value, "source") for value in batch.uv_raw]
            batch_output_uv = [decode_uv(value, v_mode) for value in batch.uv_raw]
            batch_output_colors = [decode_v4_color(value) for value in batch.attributes_v4_8]
            batch_triangles = reconstruct_triangles(batch.controls, reverse=reverse)
            for triangle in batch_triangles:
                indices.extend(vertex_start + value for value in triangle)
                geometric_degenerates += _tri_area2(*(batch_positions[value] for value in triangle)) == 0
                uv_degenerates += _uv_area2(*(batch_source_uv[value] for value in triangle)) == 0
            positions.extend(batch_positions)
            output_positions.extend(batch_output_positions)
            source_uv.extend(batch_source_uv)
            output_uv.extend(batch_output_uv)
            output_colors.extend(batch_output_colors)
            batch_ranges.append({
                "globalBatch": batch.global_index,
                "localBatch": batch.local_index,
                "firstVertex": vertex_start,
                "vertexCount": len(batch.positions),
                "firstIndex": index_start,
                "indexCount": len(batch_triangles) * 3,
            })

        position_min, position_max = bounds(output_positions, 3)
        uv_min, uv_max = bounds(output_uv, 2)
        source_position_min, source_position_max = bounds(positions, 3)
        source_uv_min, source_uv_max = bounds(source_uv, 2)
        position_view = builder.add(_pack_floats(output_positions), ARRAY_BUFFER)
        uv_view = builder.add(_pack_floats(output_uv), ARRAY_BUFFER)
        color_accessor = None
        if v4_color == "ps2-rgba":
            color_min, color_max = bounds(output_colors, 4)
            color_view = builder.add(_pack_floats(output_colors), ARRAY_BUFFER)
            color_accessor = builder.accessor(color_view, FLOAT, len(output_colors), "VEC4", color_min, color_max)
        component_type = UNSIGNED_SHORT if len(positions) <= 0xFFFF else UNSIGNED_INT
        index_view = builder.add(_pack_indices(indices, component_type), ELEMENT_ARRAY_BUFFER)
        position_accessor = builder.accessor(position_view, FLOAT, len(positions), "VEC3", position_min, position_max)
        uv_accessor = builder.accessor(uv_view, FLOAT, len(output_uv), "VEC2", uv_min, uv_max)
        index_accessor = builder.accessor(index_view, component_type, len(indices), "SCALAR", [min(indices)], [max(indices)])
        material = model.materials[descriptor.material_id]
        name = f"descriptor_{descriptor.index:04d}_mtl_{descriptor.material_id:02d}_{material.name}"
        primitive_attributes = {"POSITION": position_accessor, "TEXCOORD_0": uv_accessor}
        if color_accessor is not None:
            primitive_attributes["COLOR_0"] = color_accessor
        primitive = {
            "attributes": primitive_attributes,
            "indices": index_accessor,
            "material": material_map[descriptor.material_id],
            "mode": TRIANGLES,
            "extras": {
                "sourceDescriptorId": descriptor.index,
                "sourceMaterialId": descriptor.material_id,
                "batchRanges": batch_ranges,
                "v4ColorMode": v4_color,
            },
        }
        meshes.append({"name": name, "primitives": [primitive]})
        nodes.append({
            "name": name,
            "mesh": len(meshes) - 1,
            "extras": {
                "sourceDescriptorId": descriptor.index,
                "sourceMaterialId": descriptor.material_id,
                "sourceSecondaryId": descriptor.secondary_id,
                "aabIndexed": descriptor.index in model.aab.descriptor_refs,
            },
        })
        triangle_count = len(indices) // 3
        selected_batches += len(descriptor_batches)
        selected_vertices += len(positions)
        selected_triangles += triangle_count
        referenced_vertices += len(set(indices))
        all_source_positions.extend(positions)
        all_output_positions.extend(output_positions)
        all_source_uv.extend(source_uv)
        all_output_uv.extend(output_uv)
        descriptor_reports.append({
            "descriptorId": descriptor.index,
            "materialId": descriptor.material_id,
            "materialName": material.name,
            "batchCount": len(descriptor_batches),
            "vertexCount": len(positions),
            "triangleCount": triangle_count,
            "sourceBounds": {"min": source_position_min, "max": source_position_max},
            "outputBounds": {"min": position_min, "max": position_max},
            "sourceUvRange": {"min": source_uv_min, "max": source_uv_max},
            "outputUvRange": {"min": uv_min, "max": uv_max},
            "textureBindingStatus": material_reports[material_map[descriptor.material_id]]["bindingStatus"],
            "sourceTim2": material_reports[material_map[descriptor.material_id]].get("sourceTim2"),
            "decodedPng": material_reports[material_map[descriptor.material_id]].get("decodedPng"),
            "placeholder": material_reports[material_map[descriptor.material_id]]["placeholder"],
        })

    source_min, source_max = bounds(all_source_positions, 3)
    output_min, output_max = bounds(all_output_positions, 3)
    source_uv_min, source_uv_max = bounds(all_source_uv, 2)
    output_uv_min, output_uv_max = bounds(all_output_uv, 2)
    document: dict[str, Any] = {
        "asset": {
            "version": "2.0",
            "generator": f"SpartanReforged export_models_gltf.py {EXPORTER_VERSION}",
            "extras": {
                "sourceHashes": identities,
                "coords": coords,
                "coordinateTransform": COORDINATE_METADATA[coords][0],
                "winding": winding,
                "vMode": v_mode,
                "validatedModernVMode": VALIDATED_MODERN_V_MODE,
                "samplerMode": sampler_mode,
                "mtlRenderSemantics": mtl_render_semantics,
                "v4ColorMode": v4_color,
                "v4ColorFormula": "min(float(component) / 128.0, 1.0)" if v4_color == "ps2-rgba" else "OMITTED",
                "normals": "OMITTED",
                "textures": "LOCAL_NATIVE_TIM2_DECODES_ATTACHED" if images else "REFERENCED_IN_EXTRAS_ONLY_NOT_CONVERTED",
            },
        },
        "scene": 0,
        "scenes": [{"name": "LEVEL00_MODELS", "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "buffers": [{"uri": buffer_uri, "byteLength": len(builder.data)}],
        "bufferViews": builder.views,
        "accessors": builder.accessors,
    }
    if materials:
        document["extensionsUsed"] = ["KHR_materials_unlit"]
    if images:
        document["images"] = images
        document["textures"] = gltf_textures
        document["samplers"] = [{"wrapS": sampler_values[sampler_mode], "wrapT": sampler_values[sampler_mode]}]
    report = {
        "exporterVersion": EXPORTER_VERSION,
        "descriptorCount": len(selected),
        "batchCount": selected_batches,
        "streamedPositionCount": selected_vertices,
        "referencedPositionCount": referenced_vertices,
        "unreferencedStreamedPositionCount": selected_vertices - referenced_vertices,
        "triangleCount": selected_triangles,
        "materialCount": len(materials),
        "meshCount": len(meshes),
        "nodeCount": len(nodes),
        "boundTextureReferenceCount": bound_textures,
        "coordinateMode": coords,
        "coordinateTransform": COORDINATE_METADATA[coords][0],
        "coordinateTransformDeterminant": COORDINATE_METADATA[coords][1],
        "windingMode": winding,
        "vMode": v_mode,
        "validatedModernVMode": VALIDATED_MODERN_V_MODE,
        "samplerMode": sampler_mode,
        "mtlRenderSemantics": mtl_render_semantics,
        "v4ColorMode": v4_color,
        "doubleSidedMaterialCount": sum(bool(item.get("doubleSided")) for item in materials),
        "alphaModeCounts": dict(sorted(Counter(
            item.get("alphaMode", "OPAQUE") for item in materials
        ).items())),
        "normalsGenerated": False,
        "texturesConverted": bool(images),
        "textureImageCount": len(images),
        "texturedMaterialCount": sum(item["bindingStatus"] == "TEXTURED_CONFIRMED" for item in material_reports),
        "unresolvedPlaceholderMaterialCount": sum(item["bindingStatus"] == "PLACEHOLDER_UNRESOLVED" for item in material_reports),
        "materialMappings": material_reports,
        "attachedTextureImages": [item["uri"] for item in images],
        "attachedSourceTextures": [
            {
                "relativePath": item["extras"]["sourceTextureReference"],
                "sha256": item["extras"]["sourceTextureSha256"],
            }
            for item in materials if "sourceTextureReference" in item["extras"] and "pbrMetallicRoughness" in item
        ],
        "sourceBounds": {"min": source_min, "max": source_max},
        "outputBounds": {"min": output_min, "max": output_max},
        "sourceUvRange": {"min": source_uv_min, "max": source_uv_max},
        "outputUvRange": {"min": output_uv_min, "max": output_uv_max},
        "geometricDegenerateTriangles": geometric_degenerates,
        "collapsedUvTriangles": uv_degenerates,
        "descriptors": descriptor_reports,
    }
    return document, bytes(builder.data), report


def validate_gltf(document: dict[str, Any], buffer_data: bytes) -> dict[str, Any]:
    if document.get("asset", {}).get("version") != "2.0":
        raise ModelsFormatError("glTF asset version is not 2.0")
    buffers = document.get("buffers", [])
    if len(buffers) != 1 or buffers[0].get("byteLength") != len(buffer_data):
        raise ModelsFormatError("glTF buffer length mismatch")
    views = document.get("bufferViews", [])
    accessors = document.get("accessors", [])
    materials = document.get("materials", [])
    images = document.get("images", [])
    textures = document.get("textures", [])
    samplers = document.get("samplers", [])
    for index, texture in enumerate(textures):
        if texture.get("source", -1) not in range(len(images)) or texture.get("sampler", -1) not in range(len(samplers)):
            raise ModelsFormatError(f"glTF texture {index} has invalid image/sampler linkage")
    for index, material in enumerate(materials):
        texture_info = material.get("pbrMetallicRoughness", {}).get("baseColorTexture")
        if texture_info and texture_info.get("index", -1) not in range(len(textures)):
            raise ModelsFormatError(f"glTF material {index} has invalid base-color texture")
    component_sizes = {FLOAT: 4, UNSIGNED_SHORT: 2, UNSIGNED_INT: 4}
    type_widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    for index, view in enumerate(views):
        start = view.get("byteOffset", 0)
        length = view["byteLength"]
        if start < 0 or length < 0 or start + length > len(buffer_data):
            raise ModelsFormatError(f"glTF bufferView {index} exceeds buffer")
    for index, accessor in enumerate(accessors):
        view_index = accessor["bufferView"]
        if view_index < 0 or view_index >= len(views):
            raise ModelsFormatError(f"glTF accessor {index} has invalid bufferView")
        component_size = component_sizes.get(accessor["componentType"])
        type_width = type_widths.get(accessor["type"])
        if component_size is None or type_width is None or accessor["count"] < 1:
            raise ModelsFormatError(f"glTF accessor {index} has unsupported layout")
        required = accessor.get("byteOffset", 0) + accessor["count"] * component_size * type_width
        if required > views[view_index]["byteLength"]:
            raise ModelsFormatError(f"glTF accessor {index} exceeds its bufferView")
        values = _read_accessor(document, buffer_data, index)
        if any(isinstance(value, float) and not math.isfinite(value) for row in values for value in row):
            raise ModelsFormatError(f"glTF accessor {index} contains NaN/Inf")
        actual_min = [min(row[axis] for row in values) for axis in range(type_width)]
        actual_max = [max(row[axis] for row in values) for axis in range(type_width)]
        if "min" in accessor and accessor["min"] != actual_min:
            raise ModelsFormatError(f"glTF accessor {index} minimum metadata mismatch")
        if "max" in accessor and accessor["max"] != actual_max:
            raise ModelsFormatError(f"glTF accessor {index} maximum metadata mismatch")

    total_indices = total_positions = total_uvs = 0
    for mesh_index, mesh in enumerate(document.get("meshes", [])):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode") != TRIANGLES:
                raise ModelsFormatError(f"mesh {mesh_index} primitive is not TRIANGLES")
            material = primitive.get("material")
            if material is None or material < 0 or material >= len(materials):
                raise ModelsFormatError(f"mesh {mesh_index} has invalid material")
            position_accessor = accessors[primitive["attributes"]["POSITION"]]
            uv_accessor = accessors[primitive["attributes"]["TEXCOORD_0"]]
            index_accessor = accessors[primitive["indices"]]
            if position_accessor["type"] != "VEC3" or uv_accessor["type"] != "VEC2":
                raise ModelsFormatError(f"mesh {mesh_index} has invalid vertex accessor types")
            if position_accessor["count"] != uv_accessor["count"]:
                raise ModelsFormatError(f"mesh {mesh_index} position/UV counts differ")
            color_index = primitive["attributes"].get("COLOR_0")
            if color_index is not None:
                color_accessor = accessors[color_index]
                if color_accessor["type"] != "VEC4" or color_accessor["count"] != position_accessor["count"]:
                    raise ModelsFormatError(f"mesh {mesh_index} COLOR_0 layout/count differs")
                if any(value < 0.0 or value > 1.0 for item in _read_accessor(document, buffer_data, color_index) for value in item):
                    raise ModelsFormatError(f"mesh {mesh_index} COLOR_0 is outside glTF [0,1]")
            if index_accessor["type"] != "SCALAR" or index_accessor["count"] % 3:
                raise ModelsFormatError(f"mesh {mesh_index} index count is not triangular")
            actual_indices = [value[0] for value in _read_accessor(document, buffer_data, primitive["indices"])]
            if max(actual_indices) >= position_accessor["count"]:
                raise ModelsFormatError(f"mesh {mesh_index} index exceeds vertex count")
            total_positions += position_accessor["count"]
            total_uvs += uv_accessor["count"]
            total_indices += index_accessor["count"]
    if total_positions != total_uvs:
        raise ModelsFormatError("aggregate glTF position/UV counts differ")
    # JSON round trip rejects non-standard NaN/Inf when allow_nan is disabled.
    json.dumps(document, allow_nan=False)
    return {
        "valid": True,
        "bufferLength": len(buffer_data),
        "bufferViewCount": len(views),
        "accessorCount": len(accessors),
        "positionCount": total_positions,
        "uvCount": total_uvs,
        "indexCount": total_indices,
        "triangleCount": total_indices // 3,
        "materialCount": len(materials),
        "imageCount": len(images),
        "textureCount": len(textures),
        "meshCount": len(document.get("meshes", [])),
        "nodeCount": len(document.get("nodes", [])),
    }


def validate_external_images(document: dict[str, Any], gltf_path: pathlib.Path) -> dict[str, Any]:
    """Validate every external PNG link and any recorded source dimensions."""
    missing: list[str] = []
    broken: list[str] = []
    dimensions: dict[str, list[int]] = {}
    for item in document.get("images", []):
        uri = item.get("uri")
        if not isinstance(uri, str):
            broken.append(str(uri))
            continue
        path = gltf_path.parent / pathlib.PurePosixPath(uri)
        if not path.is_file():
            missing.append(uri)
            continue
        data = path.read_bytes()
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            broken.append(uri)
            continue
        width, height = struct.unpack_from(">II", data, 16)
        dimensions[uri] = [width, height]
        extras = item.get("extras", {})
        expected = (extras.get("sourceWidth"), extras.get("sourceHeight"))
        if all(isinstance(value, int) for value in expected) and expected != (width, height):
            broken.append(uri)
    if missing or broken:
        raise ModelsFormatError(f"external image validation failed: missing={missing}, broken={broken}")
    return {
        "valid": True,
        "imageCount": len(document.get("images", [])),
        "missingImageCount": 0,
        "brokenImageCount": 0,
        "dimensions": dimensions,
    }


def _read_accessor(document: dict[str, Any], buffer_data: bytes, accessor_index: int) -> list[tuple[float | int, ...]]:
    accessor = document["accessors"][accessor_index]
    view = document["bufferViews"][accessor["bufferView"]]
    widths = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    formats = {FLOAT: "f", UNSIGNED_SHORT: "H", UNSIGNED_INT: "I"}
    width = widths[accessor["type"]]
    code = formats[accessor["componentType"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = struct.calcsize("<" + code * width)
    return [
        struct.unpack_from("<" + code * width, buffer_data, start + row * stride)
        for row in range(accessor["count"])
    ]


def validate_consistency(
    document: dict[str, Any],
    buffer_data: bytes,
    model: ModelsData,
    selected: tuple[Descriptor, ...],
    coords: str,
    winding: str,
    v_mode: str,
    v4_color: str = "omitted",
) -> dict[str, Any]:
    if len(document["meshes"]) != len(selected) or len(document["nodes"]) != len(selected):
        raise ModelsFormatError("round-trip mesh/node count differs from descriptor selection")
    by_descriptor: dict[int, list[Batch]] = {item.index: [] for item in selected}
    for batch in model.batches:
        if batch.descriptor_id in by_descriptor:
            by_descriptor[batch.descriptor_id].append(batch)
    checked_vertices = checked_triangles = 0
    seen: set[int] = set()
    for descriptor, mesh, node in zip(selected, document["meshes"], document["nodes"]):
        primitive = mesh["primitives"][0]
        descriptor_id = primitive["extras"]["sourceDescriptorId"]
        if descriptor_id != descriptor.index or node["extras"]["sourceDescriptorId"] != descriptor.index:
            raise ModelsFormatError("round-trip descriptor provenance mismatch")
        if descriptor_id in seen:
            raise ModelsFormatError("round-trip duplicated descriptor")
        seen.add(descriptor_id)
        gltf_material = document["materials"][primitive["material"]]["extras"]["sourceMtlIndex"]
        if gltf_material != descriptor.material_id:
            raise ModelsFormatError(f"descriptor {descriptor.index} material membership changed")
        expected_positions: list[tuple[float, float, float]] = []
        expected_uv: list[tuple[float, float]] = []
        expected_indices: list[int] = []
        expected_colors: list[tuple[float, float, float, float]] = []
        for batch in by_descriptor[descriptor.index]:
            base = len(expected_positions)
            expected_positions.extend(transform_position(value, coords) for value in batch.positions)
            expected_uv.extend(decode_uv(value, v_mode) for value in batch.uv_raw)
            expected_colors.extend(decode_v4_color(value) for value in batch.attributes_v4_8)
            for triangle in reconstruct_triangles(batch.controls, reverse=winding == "reverse"):
                expected_indices.extend(base + value for value in triangle)
        actual_positions = _read_accessor(document, buffer_data, primitive["attributes"]["POSITION"])
        actual_uv = _read_accessor(document, buffer_data, primitive["attributes"]["TEXCOORD_0"])
        actual_indices = [value[0] for value in _read_accessor(document, buffer_data, primitive["indices"])]
        if actual_positions != expected_positions:
            raise ModelsFormatError(f"descriptor {descriptor.index} position round-trip mismatch")
        if actual_uv != expected_uv:
            raise ModelsFormatError(f"descriptor {descriptor.index} UV round-trip mismatch")
        if actual_indices != expected_indices:
            raise ModelsFormatError(f"descriptor {descriptor.index} index round-trip mismatch")
        color_index = primitive["attributes"].get("COLOR_0")
        if v4_color == "ps2-rgba":
            if color_index is None or _read_accessor(document, buffer_data, color_index) != expected_colors:
                raise ModelsFormatError(f"descriptor {descriptor.index} V4 color round-trip mismatch")
        elif color_index is not None:
            raise ModelsFormatError(f"descriptor {descriptor.index} unexpectedly exports V4 color")
        checked_vertices += len(expected_positions)
        checked_triangles += len(expected_indices) // 3
    if seen != {item.index for item in selected}:
        raise ModelsFormatError("round-trip descriptor membership is incomplete")
    return {
        "valid": True,
        "descriptorMembershipMatches": True,
        "materialMembershipMatches": True,
        "positionsMatchExactly": True,
        "q4_12UvValuesMatchExactly": True,
        "topologyIndicesMatchExactly": True,
        "v4ColorMatchesExactly": v4_color == "ps2-rgba",
        "descriptorCount": len(seen),
        "vertexCount": checked_vertices,
        "triangleCount": checked_triangles,
    }


def write_export(output: pathlib.Path, document: dict[str, Any], buffer_data: bytes) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    binary_path = output.with_suffix(".bin")
    document["buffers"][0]["uri"] = binary_path.name
    binary_path.write_bytes(buffer_data)
    output.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world", type=pathlib.Path, help="existing LEVEL00 WORLD directory")
    parser.add_argument("output", type=pathlib.Path, help="output .gltf path beneath temp")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--static-only", action="store_true")
    scope.add_argument("--special-only", action="store_true")
    scope.add_argument("--all", action="store_true")
    parser.add_argument("--descriptor", type=int, action="append", default=[])
    parser.add_argument("--material", type=int, action="append", default=[])
    parser.add_argument("--coords", choices=tuple(COORDINATE_METADATA), default="source")
    parser.add_argument("--winding", choices=("source", "reverse"), default="source")
    parser.add_argument(
        "--v-mode", choices=("source", "flip"), default=VALIDATED_MODERN_V_MODE,
        help="V convention; source is validated for modern glTF/Blender output",
    )
    parser.add_argument(
        "--sampler", choices=("repeat", "mirrored-repeat"), default="repeat",
        help="explicit validation sampler; native MTL semantics remain unresolved",
    )
    parser.add_argument(
        "--mtl-render-semantics", choices=("raw", "experimental"), default="raw",
        help="opt-in culling/alpha validation mapping; raw preserves conservative prior behavior",
    )
    parser.add_argument(
        "--v4-color", choices=("omitted", "ps2-rgba"), default="omitted",
        help="opt-in V4-8 COLOR_0 diagnostic using min(component/128, 1); omitted preserves prior output",
    )
    parser.add_argument("--report", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--inventory", type=pathlib.Path, help="existing LEVEL00 inventory JSON")
    parser.add_argument(
        "--texture-image", type=pathlib.Path, action="append", default=[],
        help="native decoded PNG beside the output glTF; matched to a TM2 by basename",
    )
    parser.add_argument(
        "--decode-bound-textures", action="store_true",
        help="decode all strongly resolved selected TIM2 files to native PNGs under the ignored export directory",
    )
    args = parser.parse_args()
    paths = [args.output] + [value for value in (args.report, args.manifest) if value] + args.texture_image
    if args.output.suffix.casefold() != ".gltf" or any(not _allowed_output(path) for path in paths):
        parser.error("all generated outputs must be .gltf/JSON beneath a temp directory")
    texture_images: dict[str, str | TextureImageInfo] = {}
    for image_path in args.texture_image:
        if image_path.suffix.casefold() != ".png" or not image_path.is_file():
            parser.error(f"texture image does not exist or is not PNG: {image_path}")
        if image_path.resolve().parent != args.output.resolve().parent:
            parser.error("texture images must be beside the output glTF")
        stem = image_path.stem.casefold()
        if stem.endswith("_native"):
            stem = stem[:-7]
        if stem in texture_images:
            parser.error(f"duplicate texture image stem: {stem}")
        texture_images[stem] = image_path.name

    model, identities = load_models(args.world, verify_hashes=True)
    level_root = args.world.parents[3]
    textures, verified_textures = discover_textures(level_root, args.inventory)
    scope_value = "static" if args.static_only else "special" if args.special_only else "all"
    selected = select_descriptors(
        model,
        scope=scope_value,
        descriptor_ids=set(args.descriptor) or None,
        material_ids=set(args.material) or None,
    )
    decode_summary: dict[str, Any] = {
        "uniqueDecodedTextureCount": 0,
        "cachedDecodeCount": 0,
        "writtenDecodeCount": 0,
        "decodedPngBytes": 0,
    }
    if args.decode_bound_textures:
        if texture_images:
            parser.error("--decode-bound-textures cannot be combined with --texture-image")
        texture_images, decode_summary = decode_bound_textures(
            model, selected, level_root, textures, args.output,
        )
    document, buffer_data, report = build_gltf(
        model, selected, args.output.with_suffix(".bin").name, identities, textures,
        args.coords, args.winding, args.v_mode, texture_images, args.sampler,
        args.mtl_render_semantics, args.v4_color,
    )
    validation = validate_gltf(document, buffer_data)
    report["gltfValidation"] = validation
    report["roundTripConsistency"] = validate_consistency(
        document, buffer_data, model, selected, args.coords, args.winding, args.v_mode, args.v4_color
    )
    report["sourceHashes"] = identities
    report["verifiedTim2InventoryCount"] = verified_textures
    report["textureDecode"] = decode_summary
    report["outputGltf"] = str(args.output.resolve())
    report["outputBuffer"] = str(args.output.with_suffix(".bin").resolve())
    write_export(args.output, document, buffer_data)
    # Reload the written files to validate actual serialization, not just memory state.
    written_document = json.loads(args.output.read_text(encoding="utf-8"))
    written_buffer = args.output.with_suffix(".bin").read_bytes()
    report["writtenGltfValidation"] = validate_gltf(written_document, written_buffer)
    report["writtenRoundTripConsistency"] = validate_consistency(
        written_document, written_buffer, model, selected, args.coords, args.winding, args.v_mode, args.v4_color
    )
    report["externalImageValidation"] = validate_external_images(written_document, args.output)
    report["outputGltfBytes"] = args.output.stat().st_size
    report["outputBufferBytes"] = args.output.with_suffix(".bin").stat().st_size

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    if args.manifest:
        warnings = [
            "V4-8 attributes are retained by the parser but not exported or interpreted.",
            "Seven unresolved bindings remain explicit neutral placeholders.",
            "REPEAT is an explicit conservative validation sampler, not a confirmed native MTL state.",
            (
                "Experimental render semantics make submitted triangles double-sided and map nonopaque type-2 materials to standard glTF BLEND; this is not a decoded native GS blend equation."
                if args.mtl_render_semantics == "experimental" else
                "Raw render semantics retain conservative single-sided OPAQUE glTF materials."
            ),
            "No MTL alpha-test threshold was identified; MASK/alphaCutoff are never invented.",
            "CLOUD has opaque decoded alpha, so standard glTF source-alpha blending cannot resolve its native effect semantics.",
            (
                "V4-8 is exported experimentally as legal glTF COLOR_0 using min(component/128, 1); raw values above 128 remain only in the parser."
                if args.v4_color == "ps2-rgba" else
                "V4-8 remains omitted from glTF vertex attributes."
            ),
            (
                "Explicit local native PNG decodes were attached; source TIM2 resources were not modified or embedded."
                if report["textureImageCount"] else
                "TIM2 resources are hash-referenced only and were not converted or embedded."
            ),
            "Source coordinates, winding, and V are validated for modern glTF; raw alternatives remain explicit.",
            f"Retained {report['geometricDegenerateTriangles']} exact geometric degenerates.",
            f"Retained {report['collapsedUvTriangles']} collapsed-UV triangles.",
            f"Retained {report['unreferencedStreamedPositionCount']} streamed vertices not referenced by emitted triangles; importers may omit them.",
        ]
        project_root = pathlib.Path(__file__).resolve().parents[2]
        manifest = {
            "canonicalSourceHashes": identities,
            "exporterVersion": EXPORTER_VERSION,
            "exporterGitCommit": _git_commit(project_root),
            "timestampUtc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "descriptorCount": report["descriptorCount"],
            "batchCount": report["batchCount"],
            "streamedPositionCount": report["streamedPositionCount"],
            "referencedPositionCount": report["referencedPositionCount"],
            "unreferencedStreamedPositionCount": report["unreferencedStreamedPositionCount"],
            "triangleCount": report["triangleCount"],
            "materialCount": report["materialCount"],
            "texturedMaterialCount": report["texturedMaterialCount"],
            "unresolvedPlaceholderMaterialCount": report["unresolvedPlaceholderMaterialCount"],
            "uniqueTextureImageCount": report["textureImageCount"],
            "materialMappings": report["materialMappings"],
            "descriptors": report["descriptors"],
            "coordinateConversion": report["coordinateTransform"],
            "windingOption": args.winding,
            "vOption": args.v_mode,
            "samplerOption": args.sampler,
            "mtlRenderSemantics": args.mtl_render_semantics,
            "v4ColorMode": args.v4_color,
            "doubleSidedMaterialCount": report["doubleSidedMaterialCount"],
            "alphaModeCounts": report["alphaModeCounts"],
            "normalsGenerated": False,
            "texturesConverted": report["texturesConverted"],
            "attachedTextureImages": report["attachedTextureImages"],
            "attachedSourceTextures": report["attachedSourceTextures"],
            "verifiedTim2InventoryCount": verified_textures,
            "textureDecode": decode_summary,
            "gltfValidation": report["writtenGltfValidation"],
            "roundTripConsistency": report["writtenRoundTripConsistency"],
            "externalImageValidation": report["externalImageValidation"],
            "outputGltfBytes": report["outputGltfBytes"],
            "outputBufferBytes": report["outputBufferBytes"],
            "warnings": warnings,
        }
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps({key: report[key] for key in (
        "descriptorCount", "batchCount", "streamedPositionCount", "triangleCount",
        "materialCount", "meshCount", "sourceBounds", "outputBounds", "gltfValidation",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModelsFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
