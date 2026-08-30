#!/usr/bin/env python3
"""Strict, reusable parser for Spartan: Total Warrior MODELS world geometry.

Only structurally confirmed fields are decoded. Input byte strings are never
modified, and no target-format or rendering policy is embedded in this module.
"""

from __future__ import annotations

import hashlib
import math
import pathlib
import struct
from dataclasses import dataclass
from typing import Iterable, Sequence


CANONICAL_HASHES = {
    "MODELS.BIN": "8D091D4104FA556CCFF90D78D3FEB9EA1B656356F2FABC667A8457C1382E4CF3",
    "MODELS.AAB": "CE46A8C58509D74CEEABEDF22D1832DCD365C87D2F8BC583120F1F37797E99D7",
    "MODELS.MTL": "57283516FC3CC8589EEC4817CF8C25DC3FF0CC2185E4FF99E262FA6F3A4A54B2",
}
EXPORTER_VERSION = "1.2.0"


class ModelsFormatError(ValueError):
    """Raised when a MODELS resource violates a required invariant."""


@dataclass(frozen=True)
class Descriptor:
    index: int
    offset: int
    size: int
    secondary_id: int
    material_id: int
    field_0c: int


@dataclass(frozen=True)
class Batch:
    descriptor_id: int
    local_index: int
    global_index: int
    material_id: int
    positions: tuple[tuple[float, float, float], ...]
    controls: tuple[int, ...]
    uv_raw: tuple[tuple[int, int], ...]
    attributes_v4_8: tuple[tuple[int, int, int, int], ...]
    packet_span: int


@dataclass(frozen=True)
class MaterialRecord:
    index: int
    name: str
    resource_stems: tuple[str, ...]
    # Unknown engine property identifiers and their raw little-endian u32
    # payloads. String-bearing child types 0/1 remain represented through
    # resource_stems; no render meaning is assigned here.
    numeric_properties: tuple[tuple[int, tuple[int, ...]], ...] = ()

    def property_values(self, property_type: int) -> tuple[tuple[int, ...], ...]:
        return tuple(value for item_type, value in self.numeric_properties if item_type == property_type)


@dataclass(frozen=True)
class AabData:
    descriptor_refs: frozenset[int]
    descriptor_ref_order: tuple[int, ...]
    node_count: int
    internal_nodes: int
    leaf_nodes: int


@dataclass(frozen=True)
class ModelsData:
    descriptors: tuple[Descriptor, ...]
    batches: tuple[Batch, ...]
    materials: tuple[MaterialRecord, ...]
    aab: AabData
    header_values: tuple[int, ...]

    def batches_for(self, descriptor_id: int) -> tuple[Batch, ...]:
        return tuple(batch for batch in self.batches if batch.descriptor_id == descriptor_id)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def verify_canonical(name: str, data: bytes) -> str:
    actual = sha256(data)
    expected = CANONICAL_HASHES[name]
    if actual != expected:
        raise ModelsFormatError(f"{name} canonical hash mismatch: expected {expected}, got {actual}")
    return actual


def _require_range(data: bytes, offset: int, size: int, label: str) -> None:
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise ModelsFormatError(f"{label} range 0x{offset:X}+0x{size:X} exceeds 0x{len(data):X}")


def _u32(data: bytes, offset: int, label: str = "u32") -> int:
    _require_range(data, offset, 4, label)
    return struct.unpack_from("<I", data, offset)[0]


def _align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def _vif_payload_size(command: int, immediate: int, number_byte: int) -> int:
    count = number_byte or 256
    if 0x60 <= command <= 0x7F:
        widths = (4, 2, 1, 0, 8, 4, 2, 0, 12, 6, 3, 0, 16, 8, 4, 2)
        width = widths[command & 0x0F]
        if width == 0:
            raise ModelsFormatError(f"reserved VIF UNPACK command 0x{command:02X}")
        return _align(width * count, 4)
    if command in (0x00, 0x01, 0x15):
        return 0
    raise ModelsFormatError(f"unsupported VIF command 0x{command:02X}")


def _read_vif_word(data: bytes, position: int, end: int, label: str) -> tuple[int, int, int, int, int]:
    if position + 4 > end:
        raise ModelsFormatError(f"{label}: truncated VIF word")
    word = _u32(data, position, label)
    immediate = word & 0xFFFF
    number_byte = (word >> 16) & 0xFF
    command = (word >> 24) & 0x7F
    payload_size = _vif_payload_size(command, immediate, number_byte)
    if position + 4 + payload_size > end:
        raise ModelsFormatError(f"{label}: VIF payload exceeds descriptor")
    return word, command, immediate, number_byte, payload_size


def _expect_command(
    data: bytes,
    position: int,
    end: int,
    command: int,
    immediate: int,
    label: str,
) -> tuple[bytes, int, int]:
    _, actual_command, actual_immediate, number_byte, payload_size = _read_vif_word(data, position, end, label)
    if actual_command != command or actual_immediate != immediate:
        raise ModelsFormatError(
            f"{label}: expected command 0x{command:02X}/imm 0x{immediate:04X}, "
            f"got 0x{actual_command:02X}/0x{actual_immediate:04X}"
        )
    start = position + 4
    return data[start:start + payload_size], number_byte or 256, start + payload_size


def parse_mtl(data: bytes) -> tuple[MaterialRecord, ...]:
    _require_range(data, 0, 8, "MTL header")
    record_offset, record_count = struct.unpack_from("<2I", data, 0)
    if record_offset < 8 or record_offset > len(data):
        raise ModelsFormatError("MTL record offset is outside file")
    raw_names = data[8:record_offset].split(b"\0")
    try:
        names = [part.decode("ascii") for part in raw_names if part]
    except UnicodeDecodeError as exc:
        raise ModelsFormatError("MTL name table is not ASCII") from exc
    if len(names) != record_count:
        raise ModelsFormatError("MTL name count does not match header")

    records: list[MaterialRecord] = []
    position = record_offset
    for index, name in enumerate(names):
        _require_range(data, position, 16, f"MTL record {index}")
        record_length, child_count = struct.unpack_from("<2I", data, position)
        if record_length < 16:
            raise ModelsFormatError(f"MTL record {index} is too short")
        record_end = position + record_length
        _require_range(data, position, record_length, f"MTL record {index}")
        child_position = position + 16
        stems: list[str] = []
        numeric_properties: list[tuple[int, tuple[int, ...]]] = []
        for child_index in range(child_count):
            _require_range(data, child_position, 8, f"MTL record {index} child {child_index}")
            child_length, child_type = struct.unpack_from("<2I", data, child_position)
            if child_length < 8 or child_position + child_length > record_end:
                raise ModelsFormatError(f"MTL record {index} child {child_index} has invalid length")
            payload = data[child_position + 8:child_position + child_length]
            if child_type == 0:
                for part in payload.split(b"\0"):
                    if not part:
                        continue
                    try:
                        value = part.decode("ascii")
                    except UnicodeDecodeError:
                        continue
                    if all(0x20 <= byte < 0x7F for byte in part):
                        stem = pathlib.PureWindowsPath(value).stem
                        if stem and stem.casefold() not in {item.casefold() for item in stems}:
                            stems.append(stem)
            elif child_type not in (0, 1):
                if len(payload) % 4:
                    raise ModelsFormatError(
                        f"MTL record {index} child {child_index} numeric payload is not u32-aligned"
                    )
                numeric_properties.append((
                    child_type,
                    struct.unpack("<" + "I" * (len(payload) // 4), payload),
                ))
            child_position += child_length
        if child_position != record_end:
            raise ModelsFormatError(f"MTL record {index} children do not fill record")
        records.append(MaterialRecord(index, name, tuple(stems), tuple(numeric_properties)))
        position = record_end
    if position != len(data):
        raise ModelsFormatError("MTL records do not end at EOF")
    return tuple(records)


def parse_aab(data: bytes) -> AabData:
    _require_range(data, 0, 0x50, "AAB header/root")
    file_size, declared_nodes = struct.unpack_from("<2I", data, 0)
    if file_size != len(data):
        raise ModelsFormatError("AAB declared size does not match physical size")

    visited: set[int] = set()
    internal: list[tuple[int, int]] = []
    leaves: list[int] = []

    def walk(offset: int) -> None:
        _require_range(data, offset, 0x30, "AAB node")
        if offset in visited:
            raise ModelsFormatError("AAB contains a repeated or cyclic node")
        visited.add(offset)
        bounds_pointer, *children = struct.unpack_from("<5I", data, offset)
        if any(children):
            if not all(children) or bounds_pointer != offset + 0x30:
                raise ModelsFormatError("AAB internal-node layout is inconsistent")
            _require_range(data, bounds_pointer, 0x80, "AAB child bounds")
            internal.append((offset, bounds_pointer))
            for child in children:
                walk(child)
        else:
            if bounds_pointer != 0:
                raise ModelsFormatError("AAB leaf unexpectedly has bounds pointer")
            leaves.append(offset)

    walk(0x20)
    if len(visited) != declared_nodes:
        raise ModelsFormatError("AAB visited node count does not match header")

    occupied = [(0, 0x50)]
    occupied.extend((offset, offset + 0x30) for offset, _ in internal if offset != 0x20)
    occupied.extend((bounds, bounds + 0x80) for _, bounds in internal)
    occupied.extend((offset, offset + 0x30) for offset in leaves)
    occupied.sort()
    merged: list[tuple[int, int]] = []
    for start, end in occupied:
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

    refs: list[int] = []
    for start, end in gaps:
        _require_range(data, start, 4, "AAB reference count")
        count = _u32(data, start, "AAB reference count")
        size = 4 + count * 4
        if start + size > end:
            raise ModelsFormatError("AAB descriptor-reference list exceeds its gap")
        if count:
            refs.extend(struct.unpack_from(f"<{count}I", data, start + 4))
    if len(refs) != len(set(refs)):
        raise ModelsFormatError("AAB contains duplicate descriptor references")
    return AabData(frozenset(refs), tuple(refs), len(visited), len(internal), len(leaves))


def parse_models_bin(data: bytes, material_count: int) -> tuple[tuple[int, ...], tuple[Descriptor, ...], tuple[Batch, ...]]:
    _require_range(data, 0, 0x20, "MODELS.BIN header")
    header = struct.unpack_from("<8I", data, 0)
    if header[0] != len(data):
        raise ModelsFormatError("MODELS.BIN declared size does not match physical size")
    descriptor_count = header[2]
    if descriptor_count == 0:
        raise ModelsFormatError("MODELS.BIN has no descriptors")
    table_end = 0x20 + descriptor_count * 16
    _require_range(data, 0x20, descriptor_count * 16, "MODELS.BIN descriptor table")

    descriptors: list[Descriptor] = []
    for index in range(descriptor_count):
        offset, size, packed_ids, field_0c = struct.unpack_from("<4I", data, 0x20 + index * 16)
        material_id = packed_ids >> 16
        secondary_id = packed_ids & 0xFFFF
        if offset % 16 or size % 16 or size < 16:
            raise ModelsFormatError(f"descriptor {index} extent is not a valid 16-byte-aligned block")
        _require_range(data, offset, size, f"descriptor {index}")
        if material_id >= material_count:
            raise ModelsFormatError(f"descriptor {index} material {material_id} is outside MTL table")
        descriptors.append(Descriptor(index, offset, size, secondary_id, material_id, field_0c))

    if descriptors[0].offset != table_end:
        raise ModelsFormatError("first descriptor does not begin at descriptor-table end")
    for left, right in zip(descriptors, descriptors[1:]):
        if left.offset + left.size != right.offset:
            raise ModelsFormatError(f"descriptor payloads are not contiguous at {left.index}/{right.index}")
    if descriptors[-1].offset + descriptors[-1].size != len(data):
        raise ModelsFormatError("descriptor payload partition does not end at EOF")

    batches: list[Batch] = []
    global_batch = 0
    for descriptor in descriptors:
        batch_count, block_flag, constant_a, constant_b = struct.unpack_from("<4I", data, descriptor.offset)
        if batch_count == 0:
            raise ModelsFormatError(f"descriptor {descriptor.index} declares zero batches")
        if block_flag not in (0, 0x00010000) or constant_a != 0x45 or constant_b != 0x45:
            raise ModelsFormatError(f"descriptor {descriptor.index} has unexpected block wrapper")
        position = descriptor.offset + 16
        end = descriptor.offset + descriptor.size
        for local_batch in range(batch_count):
            label = f"descriptor {descriptor.index} batch {local_batch}"
            _, count, position = _expect_command(data, position, end, 0x01, 0x0101, label + " STCYCL")
            if count != 256:  # NUM byte is zero for non-UNPACK commands.
                raise ModelsFormatError(f"{label}: unexpected STCYCL NUM")

            preamble, preamble_count, position = _expect_command(
                data, position, end, 0x6C, 0x8000, label + " preamble"
            )
            if preamble_count != 2 or len(preamble) != 32:
                raise ModelsFormatError(f"{label}: invalid preamble cardinality")
            controls_a = struct.unpack("<4I", preamble[:16])
            controls_b = struct.unpack("<4I", preamble[16:])
            if controls_a != controls_b or controls_a[2:] != (0x8000, 0):
                raise ModelsFormatError(f"{label}: preamble control vectors differ")
            packet_span, preamble_vertices = controls_a[:2]

            position_payload, vertex_count, position = _expect_command(
                data, position, end, 0x6C, 0x8002, label + " positions"
            )
            if vertex_count < 3 or vertex_count != preamble_vertices or len(position_payload) != vertex_count * 16:
                raise ModelsFormatError(f"{label}: position cardinality does not match preamble")
            positions: list[tuple[float, float, float]] = []
            controls: list[int] = []
            for vertex in range(vertex_count):
                xyz = struct.unpack_from("<3f", position_payload, vertex * 16)
                if not all(math.isfinite(value) for value in xyz):
                    raise ModelsFormatError(f"{label}: position {vertex} contains NaN/Inf")
                control = struct.unpack_from("<I", position_payload, vertex * 16 + 12)[0]
                if control not in (0, 0x8000):
                    raise ModelsFormatError(f"{label}: position {vertex} has unknown control 0x{control:X}")
                positions.append(xyz)
                controls.append(control)
            if controls[:2] != [0x8000, 0x8000]:
                raise ModelsFormatError(f"{label}: first two vertices are not suppressed")

            uv_payload, uv_count, position = _expect_command(
                data, position, end, 0x65, 0x8000 | (vertex_count + 2), label + " UV"
            )
            if uv_count != vertex_count or len(uv_payload) != vertex_count * 4:
                raise ModelsFormatError(f"{label}: UV cardinality mismatch")
            uv_raw = tuple(struct.unpack_from("<2h", uv_payload, vertex * 4) for vertex in range(vertex_count))

            attr_payload, attr_count, position = _expect_command(
                data, position, end, 0x6E, 0xC000 | (vertex_count * 2 + 2), label + " V4-8"
            )
            if attr_count != vertex_count or len(attr_payload) != vertex_count * 4:
                raise ModelsFormatError(f"{label}: V4-8 cardinality mismatch")
            attributes = tuple(struct.unpack_from("<4B", attr_payload, vertex * 4) for vertex in range(vertex_count))

            _, mscal_count, position = _expect_command(
                data, position, end, 0x15, 0x0000, label + " MSCALF"
            )
            if mscal_count != 256:
                raise ModelsFormatError(f"{label}: unexpected MSCALF NUM")

            while position < end and _u32(data, position, label + " padding") == 0:
                position += 4
            batch = Batch(
                descriptor.index,
                local_batch,
                global_batch,
                descriptor.material_id,
                tuple(positions),
                tuple(controls),
                uv_raw,
                attributes,
                packet_span,
            )
            # Validate topology indices immediately.
            reconstruct_triangles(batch.controls)
            batches.append(batch)
            global_batch += 1
        if position != end:
            raise ModelsFormatError(f"descriptor {descriptor.index} did not parse to its declared end")
    return tuple(header), tuple(descriptors), tuple(batches)


def reconstruct_triangles(controls: Sequence[int], reverse: bool = False) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for index, control in enumerate(controls):
        if control not in (0, 0x8000):
            raise ModelsFormatError(f"unknown ADC control 0x{control:X} at vertex {index}")
        if index < 2 or control == 0x8000:
            continue
        triangle = (index - 2, index - 1, index) if index % 2 == 0 else (index - 1, index - 2, index)
        if reverse:
            triangle = (triangle[0], triangle[2], triangle[1])
        if min(triangle) < 0 or max(triangle) >= len(controls):
            raise ModelsFormatError("reconstructed topology index is outside source stream")
        triangles.append(triangle)
    return tuple(triangles)


def decode_uv(raw: tuple[int, int], v_mode: str = "source") -> tuple[float, float]:
    if v_mode not in ("source", "flip"):
        raise ValueError(f"unsupported V mode {v_mode!r}")
    u = raw[0] / 4096.0
    v = raw[1] / 4096.0
    return (u, v if v_mode == "source" else 1.0 - v)


def transform_position(position: tuple[float, float, float], coords: str = "source") -> tuple[float, float, float]:
    if coords == "source":
        return position
    if coords == "gltf":
        # Explicit reflection across Z; determinant -1. No semantic relabeling.
        return position[0], position[1], -position[2]
    if coords == "x_z_neg_y":
        # Proper +90-degree rotation about X: source Y becomes target Z.
        return position[0], position[2], -position[1]
    if coords == "x_z_y":
        # Axis exchange with determinant -1; retained as an explicit validation mode.
        return position[0], position[2], position[1]
    raise ValueError(f"unsupported coordinate mode {coords!r}")


def bounds(values: Iterable[Sequence[float]], dimensions: int) -> tuple[tuple[float, ...], tuple[float, ...]]:
    rows = list(values)
    if not rows:
        raise ValueError("cannot calculate bounds of an empty sequence")
    if any(len(row) != dimensions or not all(math.isfinite(value) for value in row) for row in rows):
        raise ValueError("invalid value in bounds input")
    return (
        tuple(min(row[axis] for row in rows) for axis in range(dimensions)),
        tuple(max(row[axis] for row in rows) for axis in range(dimensions)),
    )


def select_descriptors(
    model: ModelsData,
    scope: str = "all",
    descriptor_ids: set[int] | None = None,
    material_ids: set[int] | None = None,
) -> tuple[Descriptor, ...]:
    if scope not in ("all", "static", "special"):
        raise ValueError(f"unsupported descriptor scope {scope!r}")
    descriptors = list(model.descriptors)
    if scope == "static":
        descriptors = [item for item in descriptors if item.index in model.aab.descriptor_refs]
    elif scope == "special":
        descriptors = [item for item in descriptors if item.index not in model.aab.descriptor_refs]
    if descriptor_ids:
        missing = descriptor_ids - {item.index for item in model.descriptors}
        if missing:
            raise ModelsFormatError(f"unknown descriptor IDs: {sorted(missing)}")
        descriptors = [item for item in descriptors if item.index in descriptor_ids]
    if material_ids:
        missing = material_ids - {item.index for item in model.materials}
        if missing:
            raise ModelsFormatError(f"unknown material IDs: {sorted(missing)}")
        descriptors = [item for item in descriptors if item.material_id in material_ids]
    if not descriptors:
        raise ModelsFormatError("descriptor selection is empty")
    return tuple(descriptors)


def load_models(world: pathlib.Path, verify_hashes: bool = True) -> tuple[ModelsData, dict[str, str]]:
    blobs = {name: (world / name).read_bytes() for name in CANONICAL_HASHES}
    identities = {
        name: verify_canonical(name, data) if verify_hashes else sha256(data)
        for name, data in blobs.items()
    }
    materials = parse_mtl(blobs["MODELS.MTL"])
    aab = parse_aab(blobs["MODELS.AAB"])
    header, descriptors, batches = parse_models_bin(blobs["MODELS.BIN"], len(materials))
    if any(reference >= len(descriptors) for reference in aab.descriptor_refs):
        raise ModelsFormatError("AAB references a descriptor outside MODELS.BIN")
    if aab.descriptor_refs != frozenset(range(114, len(descriptors))):
        raise ModelsFormatError("canonical static AAB descriptor partition is unexpected")
    model = ModelsData(descriptors, batches, materials, aab, header)
    return model, identities
