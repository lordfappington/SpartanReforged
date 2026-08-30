#!/usr/bin/env python3
"""Deterministic, read-only topology probe for LEVEL00 MODELS.BIN.

This research tool reconstructs candidate triangles in memory only. It never
exports geometry and restricts generated reports to logs/temporary directories.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import math
import pathlib
import statistics
import struct
from dataclasses import dataclass

from models_family_probe import Descriptor, align, parse_mtl, u32, vif_payload_size


EXPECTED_HASHES = {
    "MODELS.BIN": "8D091D4104FA556CCFF90D78D3FEB9EA1B656356F2FABC667A8457C1382E4CF3",
    "MODELS.AAB": "CE46A8C58509D74CEEABEDF22D1832DCD365C87D2F8BC583120F1F37797E99D7",
    "MODELS.MTL": "57283516FC3CC8589EEC4817CF8C25DC3FF0CC2185E4FF99E262FA6F3A4A54B2",
}


@dataclass(frozen=True)
class Batch:
    descriptor: int
    local_index: int
    global_index: int
    material: int
    static: bool
    positions: tuple[tuple[float, float, float], ...]
    controls: tuple[int, ...]
    uv: tuple[tuple[int, int], ...]
    attr: tuple[tuple[int, int, int, int], ...]


@dataclass(frozen=True)
class Triangle:
    batch: Batch
    source_index: int
    indices: tuple[int, int, int]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def allowed_output(path: pathlib.Path) -> bool:
    return bool({part.lower() for part in path.resolve().parts} & {"logs", "temp", "tmp"})


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    point = fraction * (len(ordered) - 1)
    low = int(point)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (point - low)


def vec_sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a: tuple[float, float, float]) -> float:
    return math.sqrt(dot(a, a))


def decode_bin(data: bytes) -> tuple[list[Descriptor], list[Batch]]:
    count = u32(data, 8)
    descriptors = [Descriptor(*struct.unpack_from("<4I", data, 0x20 + i * 16)) for i in range(count)]
    batches: list[Batch] = []
    global_index = 0
    for descriptor_index, descriptor in enumerate(descriptors):
        position = descriptor.offset + 16
        end = descriptor.offset + descriptor.size
        local_index = 0
        positions = controls = uv = None
        while position < end:
            word = u32(data, position)
            immediate = word & 0xFFFF
            number = ((word >> 16) & 0xFF) or 256
            command = (word >> 24) & 0x7F
            position += 4
            size = vif_payload_size(command, immediate, (word >> 16) & 0xFF)
            payload = data[position:position + size]
            if len(payload) != size:
                raise ValueError("VIF payload exceeds descriptor")
            if command == 0x6C and immediate == 0x8002:
                positions = tuple(struct.unpack_from("<3f", payload, i * 16) for i in range(number))
                controls = tuple(u32(payload, i * 16 + 12) for i in range(number))
            elif command == 0x65 and positions is not None:
                if number != len(positions):
                    raise ValueError("UV count mismatch")
                uv = tuple(struct.unpack_from("<2h", payload, i * 4) for i in range(number))
            elif command == 0x6E and positions is not None and controls is not None and uv is not None:
                if number != len(positions):
                    raise ValueError("attribute count mismatch")
                attrs = tuple(struct.unpack_from("<4B", payload, i * 4) for i in range(number))
                batches.append(Batch(
                    descriptor=descriptor_index,
                    local_index=local_index,
                    global_index=global_index,
                    material=descriptor.material_id,
                    static=descriptor_index >= 114,
                    positions=positions,
                    controls=controls,
                    uv=uv,
                    attr=attrs,
                ))
                local_index += 1
                global_index += 1
                positions = controls = uv = None
            position += size
        if position != end:
            raise ValueError("descriptor did not parse to its declared end")
        if local_index != u32(data, descriptor.offset):
            raise ValueError("descriptor batch count mismatch")
    return descriptors, batches


def internal_runs(batch: Batch) -> list[int]:
    runs: list[int] = []
    run = 0
    for value in batch.controls[2:]:
        if value == 0x8000:
            run += 1
        elif run:
            runs.append(run)
            run = 0
    if run:
        runs.append(run)
    return runs


def pattern_class(batch: Batch) -> str:
    runs = internal_runs(batch)
    if not runs:
        return "initial-only"
    isolated = any(value == 1 for value in runs)
    consecutive = any(value >= 2 for value in runs)
    if isolated and consecutive:
        return "mixed-isolated-and-consecutive"
    if consecutive:
        return "consecutive-only"
    return "isolated-only"


def rle_controls(batch: Batch) -> str:
    names = {0: "D", 0x8000: "A"}
    result: list[str] = []
    for value, group in __import__("itertools").groupby(batch.controls):
        count = sum(1 for _ in group)
        result.append(f"{names[value]}{count}")
    return " ".join(result)


def triangles(batch: Batch, model: str) -> list[Triangle]:
    result: list[Triangle] = []
    if model == "A":
        for i in range(2, len(batch.positions)):
            indices = (i - 2, i - 1, i) if i % 2 == 0 else (i - 1, i - 2, i)
            result.append(Triangle(batch, i, indices))
        return result
    if model in {"B", "D", "E"}:
        emitted = 0
        parity_after_adc = 0
        for i, control in enumerate(batch.controls):
            if control == 0x8000:
                parity_after_adc = 0
                continue
            if i < 2:
                continue
            if model == "D":
                parity = i & 1
            elif model == "B":
                parity = emitted & 1
            else:
                parity = parity_after_adc & 1
            indices = (i - 2, i - 1, i) if parity == 0 else (i - 1, i - 2, i)
            result.append(Triangle(batch, i, indices))
            emitted += 1
            parity_after_adc += 1
        return result
    if model == "C":
        history: list[int] = []
        local_triangle = 0
        for i, control in enumerate(batch.controls):
            if control == 0x8000:
                history.clear()
                local_triangle = 0
                continue
            history.append(i)
            if len(history) >= 3:
                a, b, c = history[-3:]
                indices = (a, b, c) if local_triangle % 2 == 0 else (b, a, c)
                result.append(Triangle(batch, i, indices))
                local_triangle += 1
        return result
    raise ValueError(f"unknown model {model}")


def tri_geometry(triangle: Triangle) -> tuple[float, list[float], float]:
    p = [triangle.batch.positions[i] for i in triangle.indices]
    edges = [norm(vec_sub(p[1], p[0])), norm(vec_sub(p[2], p[1])), norm(vec_sub(p[0], p[2]))]
    area2 = norm(cross(vec_sub(p[1], p[0]), vec_sub(p[2], p[0])))
    aspect = math.inf if area2 == 0 else max(edges) ** 2 / area2
    return area2, edges, aspect


def triangle_metrics(items: list[Triangle]) -> dict[str, object]:
    area2_values: list[float] = []
    edges: list[float] = []
    aspects: list[float] = []
    duplicate_xyz = collections.Counter()
    uv_zero = 0
    exact_zero = 0
    near_zero = 0
    bad = 0
    repeated_indices = 0
    winding_dots: list[float] = []
    previous: Triangle | None = None
    for triangle in items:
        if any(i < 0 or i >= len(triangle.batch.positions) for i in triangle.indices):
            bad += 1
            continue
        repeated_indices += len(set(triangle.indices)) != 3
        area2, tri_edges, aspect = tri_geometry(triangle)
        area2_values.append(area2)
        edges.extend(tri_edges)
        if math.isfinite(aspect):
            aspects.append(aspect)
        exact_zero += area2 <= 1e-12
        near_zero += area2 <= 1e-6
        xyz_key = tuple(sorted(triangle.batch.positions[i] for i in triangle.indices))
        duplicate_xyz[xyz_key] += 1
        uv = [triangle.batch.uv[i] for i in triangle.indices]
        uv_area2 = (uv[1][0] - uv[0][0]) * (uv[2][1] - uv[0][1]) - (uv[1][1] - uv[0][1]) * (uv[2][0] - uv[0][0])
        uv_zero += uv_area2 == 0
        if (previous is not None
                and previous.batch.global_index == triangle.batch.global_index
                and triangle.source_index == previous.source_index + 1
                and len(set(previous.indices) & set(triangle.indices)) == 2):
            pp = [previous.batch.positions[i] for i in previous.indices]
            pcross = cross(vec_sub(pp[1], pp[0]), vec_sub(pp[2], pp[0]))
            plen = norm(pcross)
            tp = [triangle.batch.positions[i] for i in triangle.indices]
            tcross = cross(vec_sub(tp[1], tp[0]), vec_sub(tp[2], tp[0]))
            tlen = norm(tcross)
            if plen > 1e-12 and tlen > 1e-12:
                winding_dots.append(dot(pcross, tcross) / (plen * tlen))
        previous = triangle
    return {
        "triangles": len(items), "bad_refs": bad, "repeated_indices": repeated_indices,
        "exact_zero_area": exact_zero, "near_zero_area_le_1e-6": near_zero,
        "duplicate_xyz_occurrences": sum(value - 1 for value in duplicate_xyz.values() if value > 1),
        "uv_zero_area": uv_zero,
        "area2_p50": percentile(area2_values, .5), "area2_p99": percentile(area2_values, .99),
        "edge_p50": percentile(edges, .5), "edge_p99": percentile(edges, .99), "edge_max": max(edges, default=math.nan),
        "aspect_p50": percentile(aspects, .5), "aspect_p99": percentile(aspects, .99), "aspect_max": max(aspects, default=math.nan),
        "adjacent_face_pairs": len(winding_dots), "adjacent_face_dot_mean": statistics.fmean(winding_dots) if winding_dots else math.nan,
        "adjacent_face_dot_positive": sum(value > 0 for value in winding_dots),
        "adjacent_face_dot_negative": sum(value < 0 for value in winding_dots),
    }


def anomaly_rows(items: list[Triangle]) -> tuple[list[tuple[object, ...]], list[tuple[object, ...]]]:
    near: list[tuple[object, ...]] = []
    longest: list[tuple[float, tuple[object, ...]]] = []
    for triangle in items:
        area2, edges, aspect = tri_geometry(triangle)
        row = (triangle.batch.global_index, triangle.batch.descriptor, triangle.source_index,
               triangle.batch.material, area2, tuple(edges), aspect)
        if area2 <= 1e-6:
            near.append(row)
        longest.append((max(edges), row))
    return near, [row for _, row in sorted(longest, reverse=True)[:10]]


def attr_metrics(batches: list[Batch], spec_triangles: list[Triangle]) -> dict[str, object]:
    attrs = [value for batch in batches for value in batch.attr]
    signed = [tuple(component - 256 if component >= 128 else component for component in value[:3]) for value in attrs]
    biased = [tuple(component - 128 for component in value[:3]) for value in attrs]
    signed_mag = [norm(value) / 127.0 for value in signed]
    biased_mag = [norm(value) / 127.0 for value in biased]
    dots: dict[str, list[float]] = {"signed": [], "biased": []}
    for triangle in spec_triangles:
        points = [triangle.batch.positions[i] for i in triangle.indices]
        face = cross(vec_sub(points[1], points[0]), vec_sub(points[2], points[0]))
        face_length = norm(face)
        if face_length <= 1e-12:
            continue
        face = tuple(value / face_length for value in face)
        for name, decoded in (("signed", signed), ("biased", biased)):
            # Locate attributes directly; the global arrays above are only for magnitudes.
            vectors = []
            for i in triangle.indices:
                raw = triangle.batch.attr[i][:3]
                vector = tuple((x - 256 if x >= 128 else x) for x in raw) if name == "signed" else tuple(x - 128 for x in raw)
                vectors.append(vector)
            average = tuple(sum(v[axis] for v in vectors) / 3.0 for axis in range(3))
            length = norm(average)
            if length:
                dots[name].append(dot(face, tuple(value / length for value in average)))
    return {
        "component_ranges": tuple((min(value[i] for value in attrs), max(value[i] for value in attrs)) for i in range(4)),
        "fourth_values": sorted({value[3] for value in attrs}),
        "signed_mag_mean": statistics.fmean(signed_mag), "signed_mag_p50": percentile(signed_mag, .5),
        "signed_mag_near_unit_075_125": sum(.75 <= value <= 1.25 for value in signed_mag),
        "biased_mag_mean": statistics.fmean(biased_mag), "biased_mag_p50": percentile(biased_mag, .5),
        "biased_mag_near_unit_075_125": sum(.75 <= value <= 1.25 for value in biased_mag),
        "signed_dot_mean": statistics.fmean(dots["signed"]),
        "signed_dot_positive": sum(value > 0 for value in dots["signed"]),
        "biased_dot_mean": statistics.fmean(dots["biased"]),
        "biased_dot_positive": sum(value > 0 for value in dots["biased"]),
        "dot_samples": len(dots["signed"]),
    }


def duplication_metrics(batches: list[Batch]) -> dict[str, int]:
    adjacent = previous2 = around_internal = 0
    boundary_same_order = boundary_reverse = descriptor_boundary_same = 0
    repeated_position_different_uv = 0
    for batch in batches:
        seen: dict[tuple[float, float, float], set[tuple[int, int]]] = collections.defaultdict(set)
        for i, position in enumerate(batch.positions):
            if i and position == batch.positions[i - 1]:
                adjacent += 1
            if i >= 2 and position == batch.positions[i - 2]:
                previous2 += 1
            if i >= 2 and batch.controls[i] == 0x8000 and position in batch.positions[max(0, i - 2):i]:
                around_internal += 1
            seen[position].add(batch.uv[i])
        repeated_position_different_uv += sum(len(values) - 1 for values in seen.values() if len(values) > 1)
    for left, right in zip(batches, batches[1:]):
        if left.descriptor == right.descriptor:
            boundary_same_order += left.positions[-2:] == right.positions[:2]
            boundary_reverse += left.positions[-2:] == tuple(reversed(right.positions[:2]))
        elif left.positions[-2:] == right.positions[:2]:
            descriptor_boundary_same += 1
    return {
        "adjacent_equal_positions": adjacent, "equal_position_i_minus_2": previous2,
        "internal_adc_equal_recent_position": around_internal,
        "repeated_position_distinct_uv_extra": repeated_position_different_uv,
        "within_descriptor_batch_tail2_equals_next_head2": boundary_same_order,
        "within_descriptor_batch_tail2_equals_next_head2_reversed": boundary_reverse,
        "descriptor_boundary_tail2_equals_next_head2": descriptor_boundary_same,
    }


def aab_cells(data: bytes) -> list[tuple[tuple[float, ...], tuple[int, ...]]]:
    occupied: list[tuple[int, int]] = [(0, 0x50)]
    leaves: list[int] = []
    leaf_bounds: dict[int, tuple[float, ...]] = {}

    def walk(offset: int) -> None:
        bounds, *children = struct.unpack_from("<5I", data, offset)
        if any(children):
            occupied.append((offset, offset + 0x30))
            occupied.append((bounds, bounds + 0x80))
            for index, child in enumerate(children):
                leaf_bounds[child] = struct.unpack_from("<8f", data, bounds + index * 0x20)
                walk(child)
        else:
            leaves.append(offset)
            occupied.append((offset, offset + 0x30))

    walk(0x20)
    starts = sorted({start for start, _ in occupied} | {len(data)})
    cells = []
    for leaf in leaves:
        start = leaf + 0x30
        end = min(value for value in starts if value >= start)
        if end > start:
            count = u32(data, start)
            if start + 4 + count * 4 <= end and count:
                refs = struct.unpack_from("<" + "I" * count, data, start + 4)
                cells.append((leaf_bounds[leaf], refs))
    return cells


def aab_validation(aab: bytes, descriptors: list[Descriptor], batches: list[Batch]) -> dict[str, object]:
    by_descriptor: dict[int, list[tuple[float, float, float]]] = collections.defaultdict(list)
    for batch in batches:
        by_descriptor[batch.descriptor].extend(batch.positions)
    cells = aab_cells(aab)
    contained = 0
    tested = 0
    examples = []
    for bounds, refs in cells:
        origin = bounds[:3]
        extent = bounds[4:7]
        low = tuple(min(origin[i], origin[i] + extent[i]) for i in range(3))
        high = tuple(max(origin[i], origin[i] + extent[i]) for i in range(3))
        for ref in refs:
            points = by_descriptor[ref]
            ok = all(low[i] - 1e-4 <= point[i] <= high[i] + 1e-4 for point in points for i in range(3))
            contained += ok
            tested += 1
            if len(examples) < 8:
                pmin = tuple(min(point[i] for point in points) for i in range(3))
                pmax = tuple(max(point[i] for point in points) for i in range(3))
                examples.append((ref, low, high, pmin, pmax, ok))
    return {"cells": len(cells), "refs_tested": tested, "fully_contained": contained, "examples": examples}


def representatives(batches: list[Batch]) -> list[Batch]:
    chosen: dict[int, Batch] = {}
    def add(batch: Batch) -> None:
        chosen.setdefault(batch.global_index, batch)
    ordered = sorted(batches, key=lambda value: (len(value.positions), value.global_index))
    add(ordered[0]); add(ordered[len(ordered) // 2]); add(ordered[-1])
    for name in sorted({pattern_class(batch) for batch in batches}):
        add(next(batch for batch in batches if pattern_class(batch) == name))
    add(next(batch for batch in batches if not batch.static))
    add(next(batch for batch in batches if batch.static))
    max_run = max(max(internal_runs(batch), default=0) for batch in batches)
    add(next(batch for batch in batches if max(internal_runs(batch), default=0) == max_run))
    # Add deterministic examples until at least six material IDs are represented.
    materials = {batch.material for batch in chosen.values()}
    for batch in batches:
        if batch.material not in materials:
            add(batch); materials.add(batch.material)
        if len(materials) >= 6:
            break
    return list(chosen.values())


def make_reports(world: pathlib.Path) -> tuple[str, str]:
    blobs = {name: (world / name).read_bytes() for name in EXPECTED_HASHES}
    identities = {name: (len(data), sha256(data)) for name, data in blobs.items()}
    for name, (_, digest) in identities.items():
        if digest != EXPECTED_HASHES[name]:
            raise ValueError(f"{name} hash differs from canonical input")
    descriptors, batches = decode_bin(blobs["MODELS.BIN"])
    mtl_names, _ = parse_mtl(blobs["MODELS.MTL"])
    if len(batches) != 2128:
        raise ValueError("unexpected batch count")

    control_counts = collections.Counter(value for batch in batches for value in batch.controls)
    pattern_classes = collections.Counter(pattern_class(batch) for batch in batches)
    exact_patterns = collections.Counter(rle_controls(batch) for batch in batches)
    run_counts = collections.Counter(run for batch in batches for run in internal_runs(batch))
    initial_ok = sum(batch.controls[:2] == (0x8000, 0x8000) for batch in batches)
    internal_positions = collections.Counter(i for batch in batches for i, value in enumerate(batch.controls[2:], 2) if value == 0x8000)
    model_triangles = {model: [tri for batch in batches for tri in triangles(batch, model)] for model in "ABCDE"}
    model_metrics = {model: triangle_metrics(value) for model, value in model_triangles.items()}
    attrs = attr_metrics(batches, model_triangles["D"])
    duplicates = duplication_metrics(batches)
    aab = aab_validation(blobs["MODELS.AAB"], descriptors, batches)
    samples = representatives(batches)
    near_rows, longest_rows = anomaly_rows(model_triangles["D"])

    uv_all = [value for batch in batches for value in batch.uv]
    uv_deltas_adc = []
    uv_deltas_draw = []
    for batch in batches:
        for i in range(1, len(batch.uv)):
            delta = abs(batch.uv[i][0] - batch.uv[i - 1][0]) + abs(batch.uv[i][1] - batch.uv[i - 1][1])
            (uv_deltas_adc if batch.controls[i] == 0x8000 else uv_deltas_draw).append(delta)

    lines: list[str] = []
    add = lines.append
    add("MODELS.BIN READ-ONLY TOPOLOGY PROBE")
    add("")
    add("IDENTITY")
    for name, (size, digest) in identities.items():
        add(f"{name}: size={size} sha256={digest}")
    add("")
    add("SCOPE")
    add(f"descriptors={len(descriptors)} batches={len(batches)} vertices={sum(len(b.positions) for b in batches)}")
    add(f"static_batches={sum(b.static for b in batches)} unindexed_batches={sum(not b.static for b in batches)}")
    add(f"materials_used={len({b.material for b in batches})} mtl_records={len(mtl_names)}")
    add("")
    add("CONTROL CLASSIFICATION")
    add(f"control_counts={dict(sorted(control_counts.items()))}")
    add(f"all_first_two_adc={initial_ok}/{len(batches)}")
    add(f"pattern_classes={dict(sorted(pattern_classes.items()))}")
    add(f"unique_rle_patterns={len(exact_patterns)}")
    add(f"internal_adc_run_lengths={dict(sorted(run_counts.items()))}")
    add(f"max_internal_adc_run={max(run_counts, default=0)}")
    add(f"internal_adc_position_top20={internal_positions.most_common(20)}")
    add("rle_pattern_counts:")
    for pattern, count in sorted(exact_patterns.items(), key=lambda item: (-item[1], item[0])):
        add(f"  {count:4d} {pattern}")
    add("")
    add("CANDIDATE MODELS")
    add("A=ordinary strip, every source vertex i>=2 emits; parity follows source index")
    add("B=ADC suppresses emission, history continues, parity follows emitted-triangle count")
    add("C=ADC clears history/restarts; only runs of three clear vertices emit")
    add("D=GS/ADC model: ADC suppresses current primitive, history and source-index parity continue")
    add("E=ADC suppresses, history continues, but parity resets after each ADC")
    for model in "ABCDE":
        add(f"model_{model}={model_metrics[model]}")
    add(f"model_D_static={triangle_metrics([t for t in model_triangles['D'] if t.batch.static])}")
    add(f"model_D_unindexed={triangle_metrics([t for t in model_triangles['D'] if not t.batch.static])}")
    add(f"model_D_triangle_count_equals_w_zero={len(model_triangles['D']) == control_counts[0]} ({len(model_triangles['D'])}={control_counts[0]})")
    add(f"A_vs_D_suppressed={len(model_triangles['A']) - len(model_triangles['D'])}")
    add(f"D_vs_B_index_order_diff={sum(a.indices != b.indices for a,b in zip(model_triangles['D'], model_triangles['B']))}")
    add(f"D_vs_E_index_order_diff={sum(a.indices != b.indices for a,b in zip(model_triangles['D'], model_triangles['E']))}")
    add(f"model_D_near_zero_rows={near_rows}")
    add(f"model_D_longest_edge_rows={longest_rows}")
    add("")
    add("ATTRIBUTES")
    add(f"uv_count={len(uv_all)} position_count={sum(len(b.positions) for b in batches)} one_to_one={len(uv_all) == sum(len(b.positions) for b in batches)}")
    add(f"uv_ranges=({min(v[0] for v in uv_all)},{max(v[0] for v in uv_all)})..({min(v[1] for v in uv_all)},{max(v[1] for v in uv_all)})")
    add(f"uv_l1_delta_adc_mean={statistics.fmean(uv_deltas_adc):.6f} uv_l1_delta_draw_mean={statistics.fmean(uv_deltas_draw):.6f}")
    add(f"v4_8={attrs}")
    add("")
    add("POSITION DUPLICATION AND BOUNDARIES")
    for key, value in duplicates.items(): add(f"{key}={value}")
    add("")
    add("AAB VALIDATION (TOPOLOGY-INDEPENDENT)")
    for key in ("cells", "refs_tested", "fully_contained"): add(f"{key}={aab[key]}")
    for example in aab["examples"]: add(f"example={example}")
    add("")
    add("REPRESENTATIVE BATCHES")
    for batch in samples:
        add(f"batch={batch.global_index} descriptor={batch.descriptor} local={batch.local_index} static={batch.static} material={batch.material}:{mtl_names[batch.material]} vertices={len(batch.positions)} class={pattern_class(batch)} pattern={rle_controls(batch)}")

    csv_buffer = io.StringIO(newline="")
    writer = csv.writer(csv_buffer, lineterminator="\n")
    writer.writerow(["global_batch", "descriptor", "local_batch", "partition", "material_id", "material_name", "vertices", "adc", "draw", "class", "max_internal_run", "rle", "tri_A", "tri_B", "tri_C", "tri_D", "tri_E"])
    for batch in batches:
        writer.writerow([
            batch.global_index, batch.descriptor, batch.local_index, "static" if batch.static else "unindexed",
            batch.material, mtl_names[batch.material], len(batch.positions), batch.controls.count(0x8000), batch.controls.count(0),
            pattern_class(batch), max(internal_runs(batch), default=0), rle_controls(batch),
            *(len(triangles(batch, model)) for model in "ABCDE"),
        ])
    return "\n".join(lines) + "\n", csv_buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world_dir", type=pathlib.Path)
    parser.add_argument("--model", choices=list("ABCDE"), default="D", help="candidate model highlighted by callers; all models are always compared")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--details", type=pathlib.Path, help="per-batch CSV destination")
    args = parser.parse_args()
    for path in (args.output, args.details):
        if path and not allowed_output(path):
            parser.error("generated outputs must be beneath logs/temp/tmp")
    report, details = make_reports(args.world_dir)
    report = report.replace("SCOPE\n", f"SCOPE\nselected_model={args.model}\n", 1)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
    else:
        print(report, end="")
    if args.details:
        args.details.parent.mkdir(parents=True, exist_ok=True)
        args.details.write_text(details, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
