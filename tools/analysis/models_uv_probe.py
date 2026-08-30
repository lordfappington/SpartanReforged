#!/usr/bin/env python3
"""Read-only V2-16/TIM2 correlation probe for LEVEL00 MODELS.BIN.

The tool reconstructs confirmed triangle indices in memory for UV statistics but
never exports vertices, triangles, textures, or images. Reports are restricted
to logs and temporary directories.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import itertools
import math
import pathlib
import statistics
import struct
from dataclasses import dataclass

from models_family_probe import parse_mtl
from models_topology_probe import Batch, decode_bin, percentile, triangles


EXPECTED = {
    "MODELS.BIN": "8D091D4104FA556CCFF90D78D3FEB9EA1B656356F2FABC667A8457C1382E4CF3",
    "MODELS.MTL": "57283516FC3CC8589EEC4817CF8C25DC3FF0CC2185E4FF99E262FA6F3A4A54B2",
}
SCALES = (16, 32, 64, 128, 256, 512, 1024, 4096)


@dataclass(frozen=True)
class Texture:
    path: pathlib.Path
    relative_path: str
    stem: str
    width: int
    height: int
    mipmaps: int
    image_type: int
    clut_type: int
    sha256: str


@dataclass(frozen=True)
class Binding:
    material: int
    name: str
    resource_stems: tuple[str, ...]
    confidence: str
    texture: Texture | None


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def allowed_output(path: pathlib.Path) -> bool:
    return bool({part.lower() for part in path.resolve().parts} & {"logs", "temp", "tmp"})


def parse_tim2(path: pathlib.Path, root: pathlib.Path) -> Texture:
    data = path.read_bytes()
    if len(data) < 0x40 or data[:4] != b"TIM2" or struct.unpack_from("<H", data, 6)[0] != 1:
        raise ValueError(f"unsupported TIM2 metadata layout: {path}")
    picture = 0x10
    header_size = struct.unpack_from("<H", data, picture + 0x0C)[0]
    if header_size < 0x30:
        raise ValueError(f"short TIM2 picture header: {path}")
    width, height = struct.unpack_from("<2H", data, picture + 0x14)
    return Texture(
        path=path,
        relative_path=path.relative_to(root).as_posix(),
        stem=path.stem.casefold(),
        width=width,
        height=height,
        mipmaps=data[picture + 0x11],
        image_type=data[picture + 0x13],
        clut_type=data[picture + 0x12],
        sha256=digest(data),
    )


def normalize_stem(value: str) -> str:
    value = value.strip().replace("\\", "/").rsplit("/", 1)[-1]
    return pathlib.PurePosixPath(value).stem.casefold()


def build_bindings(root: pathlib.Path, mtl_data: bytes, used: set[int]) -> tuple[list[Binding], list[Texture]]:
    textures = [parse_tim2(path, root) for path in sorted(root.rglob("*.TM2"))]
    by_stem: dict[str, list[Texture]] = collections.defaultdict(list)
    for texture in textures:
        by_stem[texture.stem].append(texture)
    names, records = parse_mtl(mtl_data)
    result: list[Binding] = []
    for material in sorted(used):
        record = records[material]
        explicit = []
        for child in record["children"]:
            if child["type"] == 0:
                explicit.extend(normalize_stem(value) for value in child["strings"])
        stems = tuple(dict.fromkeys(value for value in explicit if value))
        candidates: list[Texture] = []
        for stem in stems:
            candidates.extend(by_stem.get(stem, ()))
        candidates = list(dict.fromkeys(candidates))
        if len(candidates) == 1:
            texture = candidates[0]
            confidence = "CONFIRMED_DIRECT" if normalize_stem(names[material]) == texture.stem else "CONFIRMED_ALIAS"
        elif not candidates and len(by_stem.get(normalize_stem(names[material]), ())) == 1:
            texture = by_stem[normalize_stem(names[material])][0]
            confidence = "LIKELY_NAME_MATCH"
        else:
            texture = None
            confidence = "UNKNOWN"
        result.append(Binding(material, names[material], stems, confidence, texture))
    return result, textures


def common(counter: collections.Counter[int], count: int = 16) -> list[tuple[int, int]]:
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:count]


def raw_axis(values: list[int]) -> dict[str, object]:
    counter = collections.Counter(values)
    unsigned = [value & 0xFFFF for value in values]
    return {
        "count": len(values),
        "signed_range": (min(values), max(values)),
        "unsigned_range": (min(unsigned), max(unsigned)),
        "negative": sum(value < 0 for value in values),
        "zero": counter[0],
        "near_zero_abs_le_16": sum(abs(value) <= 16 for value in values),
        "common_signed": common(counter),
        "common_unsigned": common(collections.Counter(unsigned)),
        "residue_mod_16": dict(sorted(collections.Counter(value % 16 for value in values).items())),
        "multiples": {factor: sum(value % factor == 0 for value in values) for factor in (16, 32, 64, 128, 256)},
        "power_of_two_exact": {
            power: sum(value in {power, -power} for value in values)
            for power in (16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384)
        },
    }


def binding_map(bindings: list[Binding]) -> dict[int, Binding]:
    return {binding.material: binding for binding in bindings}


def material_vertices(batches: list[Batch]) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    for batch in batches:
        result[batch.material].extend(batch.uv)
    return result


def material_triangles(batches: list[Batch]) -> dict[int, list[object]]:
    result: dict[int, list[object]] = collections.defaultdict(list)
    for batch in batches:
        result[batch.material].extend(triangles(batch, "D"))
    return result


def seam_pairs(batches: list[Batch], bindings: dict[int, Binding], scale: int) -> tuple[int, int, int]:
    differing = periodic = one_axis_periodic = 0
    for batch in batches:
        binding = bindings[batch.material]
        if not binding.texture:
            continue
        grouped: dict[tuple[float, float, float], set[tuple[int, int]]] = collections.defaultdict(set)
        for position, uv in zip(batch.positions, batch.uv):
            grouped[position].add(uv)
        up = binding.texture.width * scale
        vp = binding.texture.height * scale
        for values in grouped.values():
            for left, right in itertools.combinations(sorted(values), 2):
                differing += 1
                du, dv = right[0] - left[0], right[1] - left[1]
                u_periodic = du % up == 0
                v_periodic = dv % vp == 0
                periodic += u_periodic and v_periodic
                one_axis_periodic += (u_periodic or v_periodic) and not (u_periodic and v_periodic)
    return differing, periodic, one_axis_periodic


def scale_metrics(scale: int, batches: list[Batch], bindings: dict[int, Binding]) -> dict[str, object]:
    vertices = triangles_total = triangles_outside = 0
    u_out = v_out = 0
    edge_hits = half_texel = integer_texel = 0
    areas: list[float] = []
    spans: list[float] = []
    stretch: list[float] = []
    zero_area = near_area = 0
    for batch in batches:
        binding = bindings[batch.material]
        if not binding.texture:
            continue
        width, height = binding.texture.width, binding.texture.height
        for u, v in batch.uv:
            vertices += 1
            u_out += u < 0 or u > width * scale
            v_out += v < 0 or v > height * scale
            edge_hits += (u % (width * scale) == 0) + (v % (height * scale) == 0)
            integer_texel += (u % scale == 0) + (v % scale == 0)
            if scale % 2 == 0:
                half_texel += (u % scale == scale // 2) + (v % scale == scale // 2)
        for triangle in triangles(batch, "D"):
            triangles_total += 1
            uv = [batch.uv[index] for index in triangle.indices]
            decoded = [(u / (scale * width), v / (scale * height)) for u, v in uv]
            triangles_outside += any(u < 0 or u > 1 or v < 0 or v > 1 for u, v in decoded)
            area2 = abs(
                (decoded[1][0] - decoded[0][0]) * (decoded[2][1] - decoded[0][1])
                - (decoded[1][1] - decoded[0][1]) * (decoded[2][0] - decoded[0][0])
            )
            areas.append(area2)
            zero_area += area2 == 0
            near_area += area2 <= 1e-8
            spans.append(max(max(value[axis] for value in decoded) - min(value[axis] for value in decoded) for axis in (0, 1)))
            p = [batch.positions[index] for index in triangle.indices]
            ab = tuple(p[1][i] - p[0][i] for i in range(3))
            ac = tuple(p[2][i] - p[0][i] for i in range(3))
            world_area2 = math.sqrt(sum(value * value for value in (
                ab[1] * ac[2] - ab[2] * ac[1],
                ab[2] * ac[0] - ab[0] * ac[2],
                ab[0] * ac[1] - ab[1] * ac[0],
            )))
            if area2 > 0:
                stretch.append(world_area2 / area2)
    differing, periodic, one_axis = seam_pairs(batches, bindings, scale)
    return {
        "bound_vertices": vertices,
        "u_outside_single_extent": u_out,
        "v_outside_single_extent": v_out,
        "bound_triangles": triangles_total,
        "triangles_outside_single_extent": triangles_outside,
        "edge_period_hits": edge_hits,
        "integer_texel_residue_hits": integer_texel,
        "half_texel_residue_hits": half_texel,
        "uv_zero_area": zero_area,
        "uv_near_area_le_1e-8": near_area,
        "normalized_area_p50": percentile(areas, .5),
        "normalized_area_p99": percentile(areas, .99),
        "triangle_span_p50": percentile(spans, .5),
        "triangle_span_p99": percentile(spans, .99),
        "stretch_p50": percentile(stretch, .5),
        "stretch_p99": percentile(stretch, .99),
        "differing_uv_seam_pairs": differing,
        "two_axis_periodic_seams": periodic,
        "one_axis_only_periodic_seams": one_axis,
    }


def normalized_scale_metrics(scale: int, batches: list[Batch], bindings: dict[int, Binding]) -> dict[str, object]:
    vertices = triangles_total = triangles_outside = zero_area = near_area = 0
    u_out = v_out = edge_hits = texel_grid = half_texel_grid = 0
    areas: list[float] = []
    spans: list[float] = []
    seam_pairs_total = seam_periodic = 0
    for batch in batches:
        binding = bindings[batch.material]
        if not binding.texture:
            continue
        width, height = binding.texture.width, binding.texture.height
        grouped: dict[tuple[float, float, float], set[tuple[int, int]]] = collections.defaultdict(set)
        for position, (u, v) in zip(batch.positions, batch.uv):
            vertices += 1
            grouped[position].add((u, v))
            u_out += u < 0 or u > scale
            v_out += v < 0 or v > scale
            edge_hits += (u % scale == 0) + (v % scale == 0)
            texel_grid += ((u * width) % scale == 0) + ((v * height) % scale == 0)
            if scale % 2 == 0:
                half_texel_grid += ((u * width - scale // 2) % scale == 0) + ((v * height - scale // 2) % scale == 0)
        for values in grouped.values():
            for left, right in itertools.combinations(sorted(values), 2):
                seam_pairs_total += 1
                seam_periodic += ((right[0] - left[0]) % scale == 0 and (right[1] - left[1]) % scale == 0)
        for triangle in triangles(batch, "D"):
            triangles_total += 1
            decoded = [(batch.uv[index][0] / scale, batch.uv[index][1] / scale) for index in triangle.indices]
            triangles_outside += any(u < 0 or u > 1 or v < 0 or v > 1 for u, v in decoded)
            area2 = abs(
                (decoded[1][0] - decoded[0][0]) * (decoded[2][1] - decoded[0][1])
                - (decoded[1][1] - decoded[0][1]) * (decoded[2][0] - decoded[0][0])
            )
            areas.append(area2)
            zero_area += area2 == 0
            near_area += area2 <= 1e-8
            spans.append(max(max(value[axis] for value in decoded) - min(value[axis] for value in decoded) for axis in (0, 1)))
    return {
        "bound_vertices": vertices,
        "u_outside_0_1": u_out,
        "v_outside_0_1": v_out,
        "bound_triangles": triangles_total,
        "triangles_outside_0_1": triangles_outside,
        "integer_uv_boundary_hits": edge_hits,
        "exact_texel_grid_hits": texel_grid,
        "half_texel_grid_hits": half_texel_grid,
        "uv_zero_area": zero_area,
        "uv_near_area_le_1e-8": near_area,
        "normalized_area_p50": percentile(areas, .5),
        "normalized_area_p99": percentile(areas, .99),
        "triangle_span_p50": percentile(spans, .5),
        "triangle_span_p99": percentile(spans, .99),
        "differing_uv_seam_pairs": seam_pairs_total,
        "integer_period_seams": seam_periodic,
    }


def all_triangle_metrics(batches: list[Batch], scale: int = 4096) -> dict[str, object]:
    """Dimension-independent quality statistics for every decoded UV triangle."""
    areas: list[float] = []
    spans: list[float] = []
    outside = zero_area = near_area = 0
    for batch in batches:
        for triangle in triangles(batch, "D"):
            decoded = [
                (batch.uv[index][0] / scale, batch.uv[index][1] / scale)
                for index in triangle.indices
            ]
            outside += any(u < 0 or u > 1 or v < 0 or v > 1 for u, v in decoded)
            area2 = abs(
                (decoded[1][0] - decoded[0][0]) * (decoded[2][1] - decoded[0][1])
                - (decoded[1][1] - decoded[0][1]) * (decoded[2][0] - decoded[0][0])
            )
            areas.append(area2)
            zero_area += area2 == 0
            near_area += area2 <= 1e-8
            spans.append(
                max(
                    max(value[axis] for value in decoded) - min(value[axis] for value in decoded)
                    for axis in (0, 1)
                )
            )
    return {
        "triangles": len(areas),
        "triangles_outside_0_1": outside,
        "uv_zero_area": zero_area,
        "uv_near_area_le_1e-8": near_area,
        "normalized_area_p50": percentile(areas, .5),
        "normalized_area_p99": percentile(areas, .99),
        "triangle_span_p50": percentile(spans, .5),
        "triangle_span_p99": percentile(spans, .99),
    }


def signedness_metrics(batches: list[Batch]) -> dict[str, object]:
    signed_deltas: list[int] = []
    unsigned_deltas: list[int] = []
    masked_deltas: list[int] = []
    modular14_deltas: list[int] = []
    sign_crossings = 0
    mask_crossings = 0
    for batch in batches:
        for triangle in triangles(batch, "D"):
            for left, right in ((0, 1), (1, 2), (2, 0)):
                for axis in (0, 1):
                    a = batch.uv[triangle.indices[left]][axis]
                    b = batch.uv[triangle.indices[right]][axis]
                    signed_deltas.append(abs(b - a))
                    au, bu = a & 0xFFFF, b & 0xFFFF
                    unsigned_deltas.append(abs(bu - au))
                    am, bm = a & 0x3FFF, b & 0x3FFF
                    masked_deltas.append(abs(bm - am))
                    modular14_deltas.append(min(abs(bm - am), 0x4000 - abs(bm - am)))
                    sign_crossings += (a < 0) != (b < 0)
                    mask_crossings += abs(am - bm) > 0x2000
    return {
        "signed_delta_p50_p99": (percentile(signed_deltas, .5), percentile(signed_deltas, .99)),
        "unsigned16_delta_p50_p99": (percentile(unsigned_deltas, .5), percentile(unsigned_deltas, .99)),
        "masked14_delta_p50_p99": (percentile(masked_deltas, .5), percentile(masked_deltas, .99)),
        "masked14_shortest_delta_p50_p99": (percentile(modular14_deltas, .5), percentile(modular14_deltas, .99)),
        "signed_edge_axis_crossings": sign_crossings,
        "masked14_wrap_axis_crossings": mask_crossings,
    }


def material_row(material: int, values: list[tuple[int, int]], tris: list[object], binding: Binding) -> dict[str, object]:
    u = [value[0] for value in values]
    v = [value[1] for value in values]
    texture = binding.texture
    row: dict[str, object] = {
        "material": material, "name": binding.name, "vertices": len(values), "triangles": len(tris),
        "binding": binding.confidence, "resource_stems": ";".join(binding.resource_stems),
        "texture": texture.relative_path if texture else "", "width": texture.width if texture else "",
        "height": texture.height if texture else "", "sha256": texture.sha256 if texture else "",
        "u_min": min(u), "u_max": max(u), "v_min": min(v), "v_max": max(v),
        "u_negative": sum(value < 0 for value in u), "v_negative": sum(value < 0 for value in v),
    }
    if texture:
        row.update({
            "u_texel_min": min(u) * texture.width / 4096, "u_texel_max": max(u) * texture.width / 4096,
            "v_texel_min": min(v) * texture.height / 4096, "v_texel_max": max(v) * texture.height / 4096,
            "u_normalized_min": min(u) / 4096, "u_normalized_max": max(u) / 4096,
            "v_normalized_min": min(v) / 4096, "v_normalized_max": max(v) / 4096,
            "u_outside": sum(value < 0 or value > 4096 for value in u),
            "v_outside": sum(value < 0 or value > 4096 for value in v),
        })
    return row


def aggregate_batches(groups: dict[object, list[Batch]], bindings: dict[int, Binding]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key in sorted(groups, key=str):
        selected = groups[key]
        values = [uv for batch in selected for uv in batch.uv]
        materials = sorted({batch.material for batch in selected})
        textures = sorted({bindings[value].texture.relative_path for value in materials if bindings[value].texture})
        rows.append({
            "group": key,
            "batches": len(selected),
            "vertices": len(values),
            "triangles": sum(len(triangles(batch, "D")) for batch in selected),
            "materials": materials,
            "textures": textures,
            "u_range": (min(value[0] for value in values), max(value[0] for value in values)),
            "v_range": (min(value[1] for value in values), max(value[1] for value in values)),
        })
    return rows


def make_reports(root: pathlib.Path, scale: int) -> tuple[str, str]:
    world = root / "DATA" / "ENV" / "LEVEL00" / "WORLD"
    bin_data = (world / "MODELS.BIN").read_bytes()
    mtl_data = (world / "MODELS.MTL").read_bytes()
    identities = {"MODELS.BIN": digest(bin_data), "MODELS.MTL": digest(mtl_data)}
    for name, expected in EXPECTED.items():
        if identities[name] != expected:
            raise ValueError(f"{name} differs from canonical hash")
    _, batches = decode_bin(bin_data)
    used = {batch.material for batch in batches}
    bindings, textures = build_bindings(root, mtl_data, used)
    by_binding = binding_map(bindings)
    vertices = material_vertices(batches)
    tris = material_triangles(batches)
    rows = [material_row(material, vertices[material], tris[material], by_binding[material]) for material in sorted(used)]
    all_uv = [value for batch in batches for value in batch.uv]
    us = [value[0] for value in all_uv]
    vs = [value[1] for value in all_uv]
    scale_results = {candidate: scale_metrics(candidate, batches, by_binding) for candidate in SCALES}
    normalized_results = {candidate: normalized_scale_metrics(candidate, batches, by_binding) for candidate in SCALES}
    by_descriptor: dict[int, list[Batch]] = collections.defaultdict(list)
    by_texture: dict[str, list[Batch]] = collections.defaultdict(list)
    for batch in batches:
        by_descriptor[batch.descriptor].append(batch)
        texture = by_binding[batch.material].texture
        by_texture[texture.relative_path if texture else "<UNRESOLVED>"].append(batch)

    lines: list[str] = []
    add = lines.append
    add("MODELS.BIN V2-16 / TIM2 READ-ONLY UV PROBE")
    add("")
    add("IDENTITY")
    add(f"MODELS.BIN sha256={identities['MODELS.BIN']}")
    add(f"MODELS.MTL sha256={identities['MODELS.MTL']}")
    add(f"selected_scale={scale}")
    add("")
    add("SCOPE")
    add(f"batches={len(batches)} records={len(all_uv)} materials={len(used)} level00_tim2={len(textures)}")
    add(f"bindings={dict(sorted(collections.Counter(binding.confidence for binding in bindings).items()))}")
    add(f"bound_texture_dimensions={dict(sorted(collections.Counter((b.texture.width,b.texture.height) for b in bindings if b.texture).items()))}")
    add("")
    add("RAW AXES")
    add(f"U={raw_axis(us)}")
    add(f"V={raw_axis(vs)}")
    add(f"signedness={signedness_metrics(batches)}")
    add(f"all_triangle_q4_12={all_triangle_metrics(batches)}")
    add("")
    add("FIXED-TEXEL CANDIDATES: raw / scale / texture_dimension")
    for candidate in SCALES:
        add(f"scale_{candidate}={scale_results[candidate]}")
    add("")
    add("FIXED-NORMALIZED CANDIDATES: raw / scale")
    for candidate in SCALES:
        add(f"normalized_scale_{candidate}={normalized_results[candidate]}")
    add("")
    add("MATERIALS")
    for row in rows:
        add(str(row))
    add("")
    add("TEXTURE GROUPS")
    for row in aggregate_batches(by_texture, by_binding):
        add(str(row))
    add("")
    add("DESCRIPTOR GROUPS")
    for row in aggregate_batches(by_descriptor, by_binding):
        add(str(row))
    add("")
    add("BOUND TIM2 IDENTITIES")
    for binding in bindings:
        if binding.texture:
            add(f"material={binding.material} name={binding.name} confidence={binding.confidence} texture={binding.texture.relative_path} dimensions={binding.texture.width}x{binding.texture.height} sha256={binding.texture.sha256}")

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return "\n".join(lines) + "\n", csv_buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level00_root", type=pathlib.Path, help="root of the isolated LEVEL00 extraction")
    parser.add_argument("--scale", type=int, choices=SCALES, default=4096)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--materials", type=pathlib.Path, help="aggregate per-material CSV")
    args = parser.parse_args()
    for path in (args.output, args.materials):
        if path and not allowed_output(path):
            parser.error("generated outputs must be beneath logs/temp/tmp")
    report, materials = make_reports(args.level00_root, args.scale)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
    else:
        print(report, end="")
    if args.materials:
        args.materials.parent.mkdir(parents=True, exist_ok=True)
        args.materials.write_text(materials, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
