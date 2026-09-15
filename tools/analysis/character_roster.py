#!/usr/bin/env python3
"""Inventory character assets across extracted Spartan section directories.

The tool is read-only with respect to extracted game data.  Its JSON output
contains paths, hashes, dimensions, decoded fingerprints, and bounded PSQ/BNS
statistics only; it never copies proprietary payloads into the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.analysis.psq_character import CharacterFormatError, parse_bns  # noqa: E402
from tools.conversion.tim2_decode import Tim2FormatError, decode_tim2  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _float_token(value: float) -> str:
    return struct.pack("<f", value).hex()


def decoded_psq_fingerprint(data: bytes) -> tuple[str, dict[str, object]]:
    """Hash the common 48-byte PSQ mesh independently of strip ordering.

    Some families use the final record word for per-vertex rendering data while
    the bounded Roman decoder requires it to be zero.  It does not affect the
    geometry fingerprint and is deliberately excluded here.
    """
    if len(data) < 12:
        raise CharacterFormatError("PSQ header is truncated")
    record_count, secondary_start, bone_count = struct.unpack_from("<III", data)
    if len(data) != 12 + record_count * 48:
        raise CharacterFormatError("not the common 48-byte PSQ record layout")
    if secondary_start == 9_999_999:
        secondary_start = record_count
    records = []
    adc = []
    positions = []
    final_words = set()
    for index in range(record_count):
        values = struct.unpack_from("<10fII", data, 12 + index * 48)
        if values[3] not in (0.0, 2048.0) or values[7] != 0.0:
            raise CharacterFormatError(f"PSQ record {index} is outside the common layout")
        if values[10] % 4 or values[10] // 4 >= bone_count:
            raise CharacterFormatError(f"PSQ record {index} has an invalid bone offset")
        positions.append(values[0:3])
        adc.append(values[3] == 2048.0)
        final_words.add(values[11])
        records.append((
            *(_float_token(value) for value in values[0:3]),
            *(_float_token(value) for value in values[4:7]),
            *(_float_token(value) for value in values[8:10]),
            str(values[10] // 4),
        ))
    record_text = [",".join(record) for record in records]
    triangle_indices = []
    for index in range(2, record_count):
        if not adc[index]:
            triangle_indices.append((index - 2, index - 1, index))
    triangles = sorted("|".join(sorted((record_text[a], record_text[b], record_text[c]))) for a, b, c in triangle_indices)
    payload = "\n".join(triangles).encode("ascii")
    return digest(payload), {
        "stream_records": record_count,
        "unique_positions": len(set(positions)),
        "triangles": len(triangle_indices),
        "bone_count": bone_count,
        "secondary_start": secondary_start,
        "final_record_word_values": len(final_words),
    }


def parse_names(path: pathlib.Path) -> list[dict[str, object]]:
    result = []
    pattern = re.compile(r"^\s*(\d+)\s+CHARACTER_TYPE_([A-Z0-9_]+)")
    for line in path.read_text(encoding="latin-1").splitlines():
        match = pattern.match(line)
        if match:
            result.append({"id": len(result), "category_code": int(match.group(1)), "name": match.group(2)})
    return result


def inventory(root: pathlib.Path) -> dict[str, object]:
    sections = sorted(path for path in root.iterdir() if path.is_dir())
    names_paths = sorted(root.glob("*/DATA/TEXT/ENGLISH/NAMES.TXT"))
    if not names_paths:
        raise ValueError("no English NAMES.TXT found beneath extracted root")
    gameplay_types = parse_names(names_paths[0])
    type_presence: dict[int, list[str]] = defaultdict(list)
    family_presence: dict[str, list[str]] = defaultdict(list)
    assets: dict[str, list[tuple[str, pathlib.Path]]] = defaultdict(list)

    for section in sections:
        char_types = next(section.glob("DATA/ENV/*/ENTITIES/CHAR_TYPES.BIN"), None)
        if char_types:
            data = char_types.read_bytes()
            if len(data) % 4:
                raise ValueError(f"unaligned CHAR_TYPES table: {char_types}")
            for offset in range(0, len(data), 4):
                type_presence[struct.unpack_from("<I", data, offset)[0]].append(section.name)
        character_root = section / "DATA" / "CHR_MDLS"
        if not character_root.is_dir():
            continue
        for family in sorted(path for path in character_root.iterdir() if path.is_dir()):
            family_presence[family.name].append(section.name)
            for path in family.rglob("*"):
                if path.is_file():
                    logical = path.relative_to(character_root).as_posix()
                    assets[logical].append((section.name, path))

    asset_rows = []
    for logical, copies in sorted(assets.items()):
        variants: dict[str, dict[str, object]] = {}
        for section, path in copies:
            data = path.read_bytes()
            sha = digest(data)
            variant = variants.setdefault(sha, {"sha256": sha, "size": len(data), "sections": []})
            variant["sections"].append(section)
            suffix = path.suffix.casefold()
            if suffix == ".psq" and "psq" not in variant:
                try:
                    fingerprint, summary = decoded_psq_fingerprint(data)
                    variant["psq"] = {"decoded_mesh_sha256": fingerprint, **summary}
                except CharacterFormatError as exc:
                    variant["psq_error"] = str(exc)
            elif suffix == ".bns" and "bns" not in variant:
                try:
                    skeleton = parse_bns(data)
                    variant["bns"] = {
                        "bone_count": len(skeleton.bones),
                        "parents": [bone.parent for bone in skeleton.bones],
                    }
                except CharacterFormatError as exc:
                    variant["bns_error"] = str(exc)
            elif suffix == ".tm2" and "tm2" not in variant:
                try:
                    image = decode_tim2(data)
                    variant["tm2"] = {
                        "width": image.width,
                        "height": image.height,
                        "mip_count": image.mip_count,
                        "image_type": image.image_type,
                        "clut_type": image.clut_type,
                        "rgba_sha256": digest(image.rgba),
                        "alpha_range": [min(image.rgba[3::4]), max(image.rgba[3::4])],
                    }
                except Tim2FormatError as exc:
                    variant["tm2_error"] = str(exc)
        asset_rows.append({
            "logical_path": logical,
            "family": logical.split("/", 1)[0],
            "extension": pathlib.PurePosixPath(logical).suffix.casefold(),
            "variants": list(variants.values()),
        })

    used_ids = set(type_presence)
    for item in gameplay_types:
        item["sections"] = sorted(type_presence.get(int(item["id"]), []))
        item["packaged"] = int(item["id"]) in used_ids

    return {
        "schema_version": 1,
        "extracted_root": str(root.resolve()),
        "section_count": len(sections),
        "sections": [path.name for path in sections],
        "gameplay_types": gameplay_types,
        "gameplay_type_count": len(gameplay_types),
        "packaged_type_count": len(used_ids),
        "unpackaged_type_count": len(gameplay_types) - len(used_ids),
        "family_presence": {key: sorted(value) for key, value in sorted(family_presence.items())},
        "top_level_family_count": len(family_presence),
        "assets": asset_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extracted_root", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report = inventory(args.extracted_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({
        "output": str(args.output.resolve()),
        "gameplay_types": report["gameplay_type_count"],
        "packaged_types": report["packaged_type_count"],
        "top_level_families": report["top_level_family_count"],
        "logical_assets": len(report["assets"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
