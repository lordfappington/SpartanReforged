#!/usr/bin/env python3
"""Read-only structural probe for Spartan's LEVEL00 MODELS family.

This is deliberately a research probe, not a format parser or asset exporter. It
validates container extents, PS2 VIF stream structure, MTL record organization,
and AAB spatial references without modifying any input file.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import math
import pathlib
import re
import struct
from dataclasses import dataclass


FAMILY_NAMES = (
    "MODELS.BIN",
    "MODELS.AAB",
    "MODELS.MTL",
    "MODELS.STL",
    "MODELS.FLP",
    "MODELS.MVR",
    "MODELS.INS",
)


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    size = len(data)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def hex_sample(data: bytes) -> str:
    return " ".join(f"{value:02X}" for value in data)


@dataclass(frozen=True)
class Descriptor:
    offset: int
    size: int
    packed_ids: int
    field_0c: int

    @property
    def material_id(self) -> int:
        return self.packed_ids >> 16

    @property
    def secondary_id(self) -> int:
        return self.packed_ids & 0xFFFF


@dataclass(frozen=True)
class VifBatch:
    vertex_count: int
    packet_span: int
    adc_clear: int
    adc_set: int
    position_min: tuple[float, float, float]
    position_max: tuple[float, float, float]
    uv_min: tuple[int, int]
    uv_max: tuple[int, int]
    packed_w: tuple[int, ...]


def vif_payload_size(command: int, immediate: int, number: int) -> int:
    count = number or 256
    if 0x60 <= command <= 0x7F:
        widths = (4, 2, 1, 0, 8, 4, 2, 0, 12, 6, 3, 0, 16, 8, 4, 2)
        width = widths[command & 0x0F]
        if not width:
            raise ValueError(f"reserved VIF UNPACK format 0x{command:02X}")
        return align(width * count, 4)
    if command == 0x20:  # STMASK
        return 4
    if command in (0x30, 0x31):  # STROW/STCOL
        return 16
    if command == 0x4A:  # MPG
        return count * 8
    if command in (0x50, 0x51):  # DIRECT/DIRECTHL
        return immediate * 16
    if command in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
                   0x10, 0x11, 0x13, 0x14, 0x15, 0x17):
        return 0
    raise ValueError(f"unsupported VIF command 0x{command:02X}")


def parse_vif_block(data: bytes, descriptor: Descriptor) -> tuple[list[VifBatch], list[int]]:
    position = descriptor.offset + 16
    end = descriptor.offset + descriptor.size
    batches: list[VifBatch] = []
    commands: list[int] = []
    pending_vertex_count: int | None = None
    pending_packet_span = 0
    pending_adc: tuple[int, int] | None = None
    pending_position_min: tuple[float, float, float] | None = None
    pending_position_max: tuple[float, float, float] | None = None
    pending_uv_min: tuple[int, int] | None = None
    pending_uv_max: tuple[int, int] | None = None

    while position < end:
        word = u32(data, position)
        immediate = word & 0xFFFF
        number = (word >> 16) & 0xFF
        command = (word >> 24) & 0x7F
        commands.append(command)
        position += 4
        payload_size = vif_payload_size(command, immediate, number)
        payload = data[position:position + payload_size]
        if len(payload) != payload_size:
            raise ValueError("VIF payload exceeds descriptor extent")

        if command == 0x6C and immediate == 0x8000 and (number or 256) == 2:
            values = struct.unpack("<8I", payload)
            if values[:4] != values[4:]:
                raise ValueError("VIF batch preamble vectors differ")
            if values[2:] != (0x8000, 0, values[0], values[1], 0x8000, 0):
                raise ValueError("unexpected VIF batch preamble fields")
            pending_packet_span = values[0]
        elif command == 0x6C and immediate == 0x8002:
            pending_vertex_count = number or 256
            flags = [u32(payload, index * 16 + 12) for index in range(pending_vertex_count)]
            pending_adc = (flags.count(0), flags.count(0x8000))
            if set(flags) - {0, 0x8000}:
                raise ValueError("unexpected position-W control values")
            positions = [struct.unpack_from("<3f", payload, index * 16)
                         for index in range(pending_vertex_count)]
            pending_position_min = tuple(min(row[axis] for row in positions) for axis in range(3))
            pending_position_max = tuple(max(row[axis] for row in positions) for axis in range(3))
        elif command == 0x65 and pending_vertex_count is not None:
            if (number or 256) != pending_vertex_count:
                raise ValueError("VIF V2-16 count does not agree with positions")
            uv = [struct.unpack_from("<2h", payload, index * 4)
                  for index in range(pending_vertex_count)]
            pending_uv_min = tuple(min(row[axis] for row in uv) for axis in range(2))
            pending_uv_max = tuple(max(row[axis] for row in uv) for axis in range(2))
        elif command == 0x6E and pending_vertex_count is not None:
            if ((number or 256) != pending_vertex_count or pending_adc is None
                    or pending_position_min is None or pending_position_max is None
                    or pending_uv_min is None or pending_uv_max is None):
                raise ValueError("VIF attribute counts do not agree")
            packed_w = tuple(sorted({payload[index * 4 + 3] for index in range(pending_vertex_count)}))
            batches.append(VifBatch(
                vertex_count=pending_vertex_count,
                packet_span=pending_packet_span,
                adc_clear=pending_adc[0],
                adc_set=pending_adc[1],
                position_min=pending_position_min,
                position_max=pending_position_max,
                uv_min=pending_uv_min,
                uv_max=pending_uv_max,
                packed_w=packed_w,
            ))
            pending_vertex_count = None
            pending_adc = None

        position += payload_size

    if position != end:
        raise ValueError("VIF commands do not end at descriptor boundary")
    return batches, commands


def parse_mtl(data: bytes) -> tuple[list[str], list[dict[str, object]]]:
    record_offset, record_count = struct.unpack_from("<2I", data, 0)
    names = [part.decode("ascii") for part in data[8:record_offset].split(b"\0") if part]
    if len(names) != record_count:
        raise ValueError("MTL name count does not match header")
    records: list[dict[str, object]] = []
    position = record_offset
    for index, name in enumerate(names):
        record_length, child_count = struct.unpack_from("<2I", data, position)
        child_position = position + 16
        children = []
        for _ in range(child_count):
            child_length, child_type = struct.unpack_from("<2I", data, child_position)
            payload = data[child_position + 8:child_position + child_length]
            strings = [
                part.decode("ascii") for part in payload.split(b"\0")
                if part and all(0x20 <= value < 0x7F for value in part)
            ]
            numeric = list(struct.unpack("<" + "I" * (len(payload) // 4), payload))
            children.append({
                "length": child_length,
                "type": child_type,
                "strings": strings,
                "numeric": numeric,
            })
            child_position += child_length
        if child_position != position + record_length:
            raise ValueError(f"MTL record {index} child lengths do not fill record")
        records.append({
            "index": index,
            "offset": position,
            "length": record_length,
            "name": name,
            "children": children,
        })
        position += record_length
    if position != len(data):
        raise ValueError("MTL record walk does not end at EOF")
    return names, records


def parse_aab(data: bytes) -> dict[str, object]:
    file_size, declared_nodes, field_08, box_size, root_count = struct.unpack_from("<5I", data, 0)
    if file_size != len(data):
        raise ValueError("AAB declared size does not match file size")

    visited: set[int] = set()
    internal: list[tuple[int, int, int]] = []
    leaves: list[int] = []
    depths: collections.Counter[int] = collections.Counter()

    def walk(pointer_table: int, depth: int) -> None:
        if pointer_table in visited:
            raise ValueError("AAB tree contains a repeated/cyclic node")
        visited.add(pointer_table)
        depths[depth] += 1
        bounds_pointer, *children = struct.unpack_from("<5I", data, pointer_table)
        if any(children):
            if not all(children) or bounds_pointer != pointer_table + 0x30:
                raise ValueError("AAB internal-node layout is inconsistent")
            internal.append((pointer_table, bounds_pointer, depth))
            for child in children:
                walk(child, depth + 1)
        else:
            if bounds_pointer:
                raise ValueError("AAB leaf has a bounds pointer but no children")
            leaves.append(pointer_table)

    walk(0x20, 0)
    if len(visited) != declared_nodes:
        raise ValueError("AAB traversed node count does not match header")

    occupied_ranges = [(0, 0x50)]
    occupied_ranges += [(offset, offset + 0x30) for offset, _, _ in internal if offset != 0x20]
    occupied_ranges += [(bounds, bounds + 0x80) for _, bounds, _ in internal]
    occupied_ranges += [(offset, offset + 0x30) for offset in leaves]
    occupied_ranges.sort()
    merged: list[tuple[int, int]] = []
    for start, end in occupied_ranges:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    gaps: list[tuple[int, int]] = []
    cursor = 0
    for start, end in merged:
        if cursor < start:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < len(data):
        gaps.append((cursor, len(data)))

    descriptor_refs: list[int] = []
    for start, end in gaps:
        count = u32(data, start)
        if start + 4 + count * 4 > end:
            raise ValueError("AAB leaf reference list exceeds its region")
        descriptor_refs.extend(struct.unpack_from("<" + "I" * count, data, start + 4))

    return {
        "file_size": file_size,
        "declared_nodes": declared_nodes,
        "field_08": field_08,
        "box_size": box_size,
        "root_count": root_count,
        "name": data[0x14:0x20].split(b"\0", 1)[0].decode("ascii"),
        "top_offsets": struct.unpack_from("<5I", data, 0x20),
        "node_depths": dict(sorted(depths.items())),
        "internal_nodes": len(internal),
        "leaf_nodes": len(leaves),
        "reference_regions": len(gaps),
        "descriptor_refs": descriptor_refs,
    }


def strict_ascii_strings(data: bytes) -> list[tuple[int, str]]:
    result = []
    for match in re.finditer(rb"[A-Za-z_][A-Za-z0-9_./\\:-]{5,}\x00", data):
        value = match.group()[:-1].decode("ascii")
        if any(marker in value for marker in ("_", ".", "/", "\\", ":")):
            result.append((match.start(), value))
    return result


def make_report(world: pathlib.Path) -> str:
    blobs = {name: (world / name).read_bytes() for name in FAMILY_NAMES}
    lines: list[str] = []
    add = lines.append
    add("MODELS FAMILY READ-ONLY STRUCTURAL PROBE")
    add("")
    add("IDENTITY")
    for name in FAMILY_NAMES:
        add(f"{name}: size={len(blobs[name])} sha256={sha256(blobs[name])}")

    bin_data = blobs["MODELS.BIN"]
    header = struct.unpack_from("<8I", bin_data, 0)
    descriptor_count = header[2]
    descriptors = [Descriptor(*struct.unpack_from("<4I", bin_data, 0x20 + index * 16))
                   for index in range(descriptor_count)]
    table_end = 0x20 + descriptor_count * 16
    contiguous = all(
        left.offset + left.size == right.offset
        for left, right in zip(descriptors, descriptors[1:])
    )
    all_batches: list[VifBatch] = []
    command_counts: collections.Counter[int] = collections.Counter()
    block_batch_mismatches = 0
    for descriptor in descriptors:
        batches, commands = parse_vif_block(bin_data, descriptor)
        all_batches.extend(batches)
        command_counts.update(commands)
        if u32(bin_data, descriptor.offset) != len(batches):
            block_batch_mismatches += 1

    add("")
    add("MODELS.BIN")
    add("header_u32=" + ",".join(f"0x{value:X}" for value in header))
    add(f"head_0x100={hex_sample(bin_data[:0x100])}")
    add(f"tail_0x100={hex_sample(bin_data[-0x100:])}")
    add(f"descriptor_count={descriptor_count} descriptor_table=0x20-0x{table_end:X}")
    add(f"payload=0x{descriptors[0].offset:X}-0x{len(bin_data):X}")
    add(f"descriptors_contiguous={contiguous} first_matches_table_end={descriptors[0].offset == table_end}")
    add(f"last_matches_eof={descriptors[-1].offset + descriptors[-1].size == len(bin_data)}")
    add(f"descriptor_size_range={min(item.size for item in descriptors)}-{max(item.size for item in descriptors)}")
    add(f"material_ids={','.join(map(str, sorted({item.material_id for item in descriptors})))}")
    add(f"secondary_id_ffff={sum(item.secondary_id == 0xFFFF for item in descriptors)}")
    add(f"field_0c_counts={dict(sorted(collections.Counter(item.field_0c for item in descriptors).items()))}")
    add(f"vif_blocks={len(descriptors)} vif_batches={len(all_batches)} block_batch_mismatches={block_batch_mismatches}")
    add(f"streamed_vertices={sum(item.vertex_count for item in all_batches)}")
    add(f"batch_vertex_range={min(item.vertex_count for item in all_batches)}-{max(item.vertex_count for item in all_batches)}")
    add(f"position_w_adc_clear={sum(item.adc_clear for item in all_batches)}")
    add(f"position_w_adc_set={sum(item.adc_set for item in all_batches)}")
    add("vif_commands=" + ",".join(f"0x{key:02X}:{value}" for key, value in sorted(command_counts.items())))
    add(f"candidate_delimited_ascii_runs={strict_ascii_strings(bin_data)}")
    window_entropies = [
        (offset, entropy(bin_data[offset:offset + 0x1000]))
        for offset in range(0, len(bin_data), 0x1000)
    ]
    add(f"entropy_header={entropy(bin_data[:0x20]):.4f}")
    add(f"entropy_descriptor_table={entropy(bin_data[0x20:table_end]):.4f}")
    add(f"entropy_payload={entropy(bin_data[table_end:]):.4f}")
    add(f"entropy_windows_min={min(window_entropies, key=lambda item: item[1])}")
    add(f"entropy_windows_max={max(window_entropies, key=lambda item: item[1])}")

    mtl_names, mtl_records = parse_mtl(blobs["MODELS.MTL"])
    exact_mtl_names = [name for name in mtl_names if name.encode("ascii") in bin_data]
    add(f"exact_mtl_names_in_bin={exact_mtl_names}")
    position_min = tuple(min(batch.position_min[axis] for batch in all_batches) for axis in range(3))
    position_max = tuple(max(batch.position_max[axis] for batch in all_batches) for axis in range(3))
    uv_min = tuple(min(batch.uv_min[axis] for batch in all_batches) for axis in range(2))
    uv_max = tuple(max(batch.uv_max[axis] for batch in all_batches) for axis in range(2))
    add(f"position_xyz_range={position_min}..{position_max}")
    add(f"signed_v2_16_range={uv_min}..{uv_max}")
    add(f"unsigned_v4_8_w_values={sorted({value for batch in all_batches for value in batch.packed_w})}")
    zero_runs = [(match.start(), len(match.group())) for match in re.finditer(b"\0{64,}", bin_data)]
    add(f"zero_runs_ge_64=count:{len(zero_runs)} total:{sum(size for _, size in zero_runs)} max:{max(size for _, size in zero_runs)}")
    material_counts = collections.Counter(item.material_id for item in descriptors)
    add("")
    add("MODELS.MTL ORDERED RECORDS")
    for record in mtl_records:
        children = record["children"]
        lengths = ",".join(str(child["length"]) for child in children)
        types = ",".join(str(child["type"]) for child in children)
        values = ";".join(
            "/".join(child["strings"]) or ",".join(f"0x{value:X}" for value in child["numeric"][:2])
            for child in children
        )
        index = int(record["index"])
        add(
            f"{index:02d} off=0x{int(record['offset']):04X} len={int(record['length'])} "
            f"name={record['name']} children={len(children)} child_lengths={lengths} "
            f"child_types={types} values={values} bin_descriptors={material_counts[index]}"
        )

    aab = parse_aab(blobs["MODELS.AAB"])
    refs = list(aab["descriptor_refs"])
    add("")
    add("MODELS.AAB")
    for key in ("file_size", "declared_nodes", "field_08", "box_size", "root_count", "name",
                "top_offsets", "node_depths", "internal_nodes", "leaf_nodes", "reference_regions"):
        add(f"{key}={aab[key]}")
    add(f"descriptor_refs={len(refs)} unique={len(set(refs))} range={min(refs)}-{max(refs)}")
    add(f"descriptor_refs_exact_114_1337={set(refs) == set(range(114, 1338)) and len(refs) == 1224}")

    stl = blobs["MODELS.STL"]
    stl_header = struct.unpack_from("<2I", stl, 0)
    stl_ids = struct.unpack_from("<32i", stl, 8)
    add("")
    add("COMPANIONS")
    add(f"STL_header={stl_header} active_ids={[(index, value) for index, value in enumerate(stl_ids) if value >= 0]}")
    flp = blobs["MODELS.FLP"]
    flp_size, flp_count = struct.unpack_from("<2I", flp, 0)
    flp_records = [flp[16 + index * 80:16 + (index + 1) * 80] for index in range(flp_count)]
    add(f"FLP_size={flp_size} count={flp_count} record_size=80 exact_formula={16 + flp_count * 80 == len(flp)}")
    mvr = blobs["MODELS.MVR"]
    mvr_header = struct.unpack_from("<4I", mvr, 0)
    mvr_paths = strict_ascii_strings(mvr)
    flp_matches = [index for index, record in enumerate(flp_records) if mvr.find(record) >= 0]
    add(f"MVR_header={mvr_header} fixed_record_size={(len(mvr) - 16) // mvr_header[2]} paths={mvr_paths}")
    add(f"FLP_record_indices_found_exactly_in_MVR={flp_matches}")
    add(f"INS_u32={struct.unpack('<8I', blobs['MODELS.INS'])}")

    add("")
    add("CROSS-FILE")
    add(f"MTL_records={len(mtl_names)} BIN_material_id_max={max(item.material_id for item in descriptors)}")
    add(f"AAB_refs_match_BIN_static_partition={set(refs) == set(range(114, len(descriptors)))}")
    add(f"BIN_unindexed_partition=0-113 bytes=0x{descriptors[114].offset - table_end:X}")
    add(f"BIN_aab_partition=114-1337 bytes=0x{len(bin_data) - descriptors[114].offset:X}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("world_dir", type=pathlib.Path, help="directory containing the MODELS family")
    parser.add_argument("--output", type=pathlib.Path, help="optional text-report destination")
    args = parser.parse_args()
    report = make_report(args.world_dir)
    if args.output:
        allowed_parts = {part.lower() for part in args.output.resolve().parts}
        if not allowed_parts.intersection({"logs", "temp", "tmp"}):
            parser.error("--output must be beneath a logs or temporary directory")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
