#!/usr/bin/env python3
"""Bounded, read-only PSQ/BNS character geometry inspector.

The decoder intentionally covers only the record layouts validated for the
rigid-skinned character families studied in Spartan: Total Warrior. It does
not extract archives and never embeds source asset bytes in its JSON output.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import pathlib
import struct
from collections.abc import Sequence


class CharacterFormatError(ValueError):
    """Raised when a PSQ/BNS file does not match the bounded layout."""


@dataclasses.dataclass(frozen=True)
class PsqVertex:
    position: tuple[float, float, float]
    adc: bool
    normal: tuple[float, float, float]
    uv: tuple[float, float]
    bone_id: int


@dataclasses.dataclass(frozen=True)
class PsqMesh:
    vertices: tuple[PsqVertex, ...]
    secondary_range_start: int
    bone_count: int

    @property
    def triangles(self) -> tuple[tuple[int, int, int], ...]:
        faces: list[tuple[int, int, int]] = []
        for index, vertex in enumerate(self.vertices):
            if index < 2 or vertex.adc:
                continue
            face = (index - 2, index - 1, index)
            if index & 1:
                face = (index - 1, index - 2, index)
            faces.append(face)
        return tuple(faces)


@dataclasses.dataclass(frozen=True)
class Bone:
    translation: tuple[float, float, float]
    parent: int


@dataclasses.dataclass(frozen=True)
class Skeleton:
    bones: tuple[Bone, ...]
    trailing_index_count: int
    trailing_indices: tuple[int, ...]

    @property
    def world_translations(self) -> tuple[tuple[float, float, float], ...]:
        result: list[tuple[float, float, float]] = []
        for index, bone in enumerate(self.bones):
            if bone.parent >= index:
                raise CharacterFormatError("BNS parent must precede child")
            parent = result[bone.parent] if bone.parent >= 0 else (0.0, 0.0, 0.0)
            result.append(tuple(bone.translation[axis] + parent[axis] for axis in range(3)))
        return tuple(result)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_psq(data: bytes) -> PsqMesh:
    if len(data) < 12:
        raise CharacterFormatError("PSQ header is truncated")
    record_count, secondary_start, bone_count = struct.unpack_from("<III", data)
    expected_size = 12 + record_count * 48
    if len(data) != expected_size:
        raise CharacterFormatError(f"PSQ size is {len(data)}, expected {expected_size}")
    if secondary_start == 9_999_999:
        secondary_start = record_count
    if not 0 <= secondary_start <= record_count:
        raise CharacterFormatError("PSQ secondary range is outside the record stream")
    if not 0 < bone_count <= 256:
        raise CharacterFormatError("PSQ bone count is implausible")

    vertices: list[PsqVertex] = []
    for index in range(record_count):
        values = struct.unpack_from("<10fII", data, 12 + index * 48)
        position_w = values[3]
        if position_w not in (0.0, 2048.0):
            raise CharacterFormatError(f"PSQ record {index} has unknown ADC value {position_w}")
        if values[7] != 0.0 or values[11] != 0:
            raise CharacterFormatError(f"PSQ record {index} has nonzero reserved fields")
        bone_offset = values[10]
        if bone_offset % 4 or bone_offset // 4 >= bone_count:
            raise CharacterFormatError(f"PSQ record {index} has invalid bone offset")
        vertices.append(PsqVertex(
            position=values[0:3], adc=position_w == 2048.0,
            normal=values[4:7], uv=values[8:10], bone_id=bone_offset // 4,
        ))
    return PsqMesh(tuple(vertices), secondary_start, bone_count)


def parse_bns(data: bytes) -> Skeleton:
    if len(data) < 9 or data[:4] != b"bns2":
        raise CharacterFormatError("BNS magic/header is invalid")
    bone_count = struct.unpack_from("<I", data, 4)[0]
    records_end = 8 + bone_count * 16
    if records_end >= len(data):
        raise CharacterFormatError("BNS bone records are truncated")
    bones = tuple(
        Bone(values[:3], values[3])
        for index in range(bone_count)
        for values in (struct.unpack_from("<3fi", data, 8 + index * 16),)
    )
    tail_count = data[records_end]
    tail_end = records_end + 1 + tail_count
    if tail_end > len(data):
        raise CharacterFormatError("BNS trailing index table is truncated")
    skeleton = Skeleton(bones, tail_count, tuple(data[records_end + 1:tail_end]))
    skeleton.world_translations  # validates parent ordering
    return skeleton


def transformed_positions(mesh: PsqMesh, skeleton: Skeleton) -> tuple[tuple[float, float, float], ...]:
    if mesh.bone_count != len(skeleton.bones):
        raise CharacterFormatError("PSQ and BNS bone counts differ")
    joints = skeleton.world_translations
    return tuple(
        tuple(vertex.position[axis] + joints[vertex.bone_id][axis] for axis in range(3))
        for vertex in mesh.vertices
    )


def bounds(points: Sequence[tuple[float, float, float]]) -> dict[str, list[float]]:
    return {
        "min": [min(point[axis] for point in points) for axis in range(3)],
        "max": [max(point[axis] for point in points) for axis in range(3)],
    }


def mesh_summary(psq_path: pathlib.Path, bns_path: pathlib.Path) -> dict[str, object]:
    mesh = parse_psq(psq_path.read_bytes())
    skeleton = parse_bns(bns_path.read_bytes())
    points = transformed_positions(mesh, skeleton)
    split = mesh.secondary_range_start
    return {
        "psq": {"path": str(psq_path), "size": psq_path.stat().st_size, "sha256": sha256(psq_path)},
        "bns": {"path": str(bns_path), "size": bns_path.stat().st_size, "sha256": sha256(bns_path)},
        "stream_records": len(mesh.vertices),
        "unique_positions": len({vertex.position for vertex in mesh.vertices}),
        "triangles": len(mesh.triangles),
        "primary_range": {"start": 0, "end": split, "triangles": sum(not v.adc for v in mesh.vertices[:split])},
        "secondary_range": {"start": split, "end": len(mesh.vertices), "triangles": sum(not v.adc for v in mesh.vertices[split:])},
        "bone_count": mesh.bone_count,
        "bone_ids_used": sorted({vertex.bone_id for vertex in mesh.vertices}),
        "uv_bounds": {
            "min": [min(v.uv[axis] for v in mesh.vertices) for axis in range(2)],
            "max": [max(v.uv[axis] for v in mesh.vertices) for axis in range(2)],
        },
        "local_position_bounds": bounds([vertex.position for vertex in mesh.vertices]),
        "rest_pose_bounds": bounds(points),
        "parents": [bone.parent for bone in skeleton.bones],
        "local_joint_translations": [list(bone.translation) for bone in skeleton.bones],
        "world_joint_translations": [list(value) for value in skeleton.world_translations],
        "trailing_index_count": skeleton.trailing_index_count,
    }


def export_obj(
    psq_path: pathlib.Path, bns_path: pathlib.Path, output: pathlib.Path,
    texture: pathlib.Path | None = None,
) -> None:
    """Write a private research OBJ; callers must keep it outside Git."""
    mesh = parse_psq(psq_path.read_bytes())
    skeleton = parse_bns(bns_path.read_bytes())
    points = transformed_positions(mesh, skeleton)
    lines = ["# Private preservation reconstruction; do not redistribute"]
    if texture:
        lines.extend((f"mtllib {output.stem}.mtl", "usemtl original_diffuse"))
    lines.extend(f"v {x:.9g} {y:.9g} {z:.9g}" for x, y, z in points)
    lines.extend(f"vt {u:.9g} {1.0 - v:.9g}" for u, v in (item.uv for item in mesh.vertices))
    lines.extend(f"vn {x:.9g} {y:.9g} {z:.9g}" for x, y, z in (item.normal for item in mesh.vertices))
    for a, b, c in mesh.triangles:
        lines.append(f"f {a+1}/{a+1}/{a+1} {b+1}/{b+1}/{b+1} {c+1}/{c+1}/{c+1}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="ascii")
    if texture:
        mtl = output.with_suffix(".mtl")
        mtl.write_text(
            "# Private preservation material; do not redistribute\n"
            "newmtl original_diffuse\nKd 1 1 1\nKa 0 0 0\nKs 0 0 0\n"
            f"map_Kd {texture.resolve().as_posix()}\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("psq", type=pathlib.Path)
    parser.add_argument("bns", type=pathlib.Path)
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--obj", type=pathlib.Path, help="private output; keep outside Git")
    parser.add_argument("--texture", type=pathlib.Path, help="decoded private texture referenced by OBJ MTL")
    args = parser.parse_args()
    report = mesh_summary(args.psq, args.bns)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if args.obj:
        export_obj(args.psq, args.bns, args.obj, args.texture)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
