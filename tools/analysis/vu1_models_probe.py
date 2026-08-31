#!/usr/bin/env python3
"""Bounded, read-only probe for the resident MODELS VU1 render path.

The probe reconstructs only the canonical VIF1 MPG upload, validates the
small instruction landmarks used by the MODELS vertex-layout path, and
decodes its GIFtag/PRIM template.  It is not a VU emulator or a general VU
disassembler, and it never emits raw microprogram bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
from dataclasses import asdict, dataclass
from typing import Any


EXECUTABLE_SHA256 = "55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d"
ELF_VADDR_BIAS = 0x001FFF00
MPG_COMMAND_VADDR = 0x0050488C
EXPECTED_PROGRAM_INSTRUCTIONS = 1603
EXPECTED_PROGRAM_EXTENT = 0x643


class Vu1ProbeError(ValueError):
    """Canonical source or bounded VU structure did not match expectations."""


@dataclass(frozen=True)
class MpgBlock:
    source_command: int
    destination: int
    count: int


@dataclass(frozen=True)
class PrimState:
    raw: int
    primitive: int
    iip: int
    tme: int
    fge: int
    abe: int
    aa1: int
    fst: int
    ctxt: int
    fix: int


@dataclass(frozen=True)
class GifTagState:
    nloop: int
    eop: int
    pre: int
    prim: PrimState
    flg: int
    nreg: int
    registers: tuple[int, ...]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_offset(vaddr: int, size: int, data: bytes) -> int:
    offset = vaddr - ELF_VADDR_BIAS
    if offset < 0 or size < 0 or offset > len(data) or size > len(data) - offset:
        raise Vu1ProbeError(f"virtual range 0x{vaddr:08x}+0x{size:x} is outside the ELF image")
    return offset


def u32_vaddr(data: bytes, vaddr: int) -> int:
    return struct.unpack_from("<I", data, file_offset(vaddr, 4, data))[0]


def extract_mpg_program(data: bytes) -> tuple[tuple[MpgBlock, ...], tuple[tuple[int, int], ...]]:
    """Reconstruct the seven bounded VIF MPG blocks beginning at 0x50488c."""
    cursor = MPG_COMMAND_VADDR
    program: list[tuple[int, int] | None] = [None] * 0x800
    blocks: list[MpgBlock] = []
    loaded = 0
    while loaded < EXPECTED_PROGRAM_INSTRUCTIONS:
        command = u32_vaddr(data, cursor)
        while command == 0:
            cursor += 4
            command = u32_vaddr(data, cursor)
        if ((command >> 24) & 0x7F) != 0x4A:
            raise Vu1ProbeError(f"expected MPG at 0x{cursor:08x}, found 0x{command:08x}")
        count = (command >> 16) & 0xFF
        count = count or 256
        destination = command & 0x7FF
        if destination + count > len(program):
            raise Vu1ProbeError("MPG block exceeds VU1 micro memory")
        blocks.append(MpgBlock(cursor, destination, count))
        cursor += 4
        for index in range(count):
            lower = u32_vaddr(data, cursor)
            upper = u32_vaddr(data, cursor + 4)
            if program[destination + index] is not None:
                raise Vu1ProbeError("overlapping canonical MPG blocks")
            program[destination + index] = (lower, upper)
            cursor += 8
            loaded += 1
    if loaded != EXPECTED_PROGRAM_INSTRUCTIONS or len(blocks) != 7:
        raise Vu1ProbeError("unexpected resident VU1 program size/block count")
    extent = max(index for index, pair in enumerate(program) if pair is not None) + 1
    if extent != EXPECTED_PROGRAM_EXTENT or any(pair is None for pair in program[:extent]):
        raise Vu1ProbeError("resident VU1 program is not the documented contiguous extent")
    return tuple(blocks), tuple(pair for pair in program[:extent] if pair is not None)


def decode_prim(raw: int) -> PrimState:
    if raw & ~0x7FF:
        raise Vu1ProbeError(f"PRIM has bits outside its 11-bit field: 0x{raw:x}")
    return PrimState(
        raw=raw,
        primitive=raw & 0x7,
        iip=(raw >> 3) & 1,
        tme=(raw >> 4) & 1,
        fge=(raw >> 5) & 1,
        abe=(raw >> 6) & 1,
        aa1=(raw >> 7) & 1,
        fst=(raw >> 8) & 1,
        ctxt=(raw >> 9) & 1,
        fix=(raw >> 10) & 1,
    )


def decode_giftag(tag0: int, tag1: int, registers: int) -> GifTagState:
    nreg_raw = (tag1 >> 28) & 0xF
    nreg = nreg_raw or 16
    return GifTagState(
        nloop=tag0 & 0x7FFF,
        eop=(tag0 >> 15) & 1,
        pre=(tag1 >> 14) & 1,
        prim=decode_prim((tag1 >> 15) & 0x7FF),
        flg=(tag1 >> 26) & 0x3,
        nreg=nreg,
        registers=tuple((registers >> (4 * index)) & 0xF for index in range(nreg)),
    )


def validate_models_landmarks(program: tuple[tuple[int, int], ...]) -> dict[str, int]:
    """Validate only the entry-0 instructions needed for the MODELS conclusion."""
    # Lower words are stable canonical instruction encodings.  Keeping this
    # bounded set catches selection of a neighboring VU renderer path without
    # embedding or dumping the complete copyrighted microprogram.
    expected_lower = {
        0x000: 0x800106BC,  # XTOP vi1 (startup/entry zero)
        0x014: 0x800706BC,  # XTOP vi7 (batch dispatch)
        0x073: 0x5006009C,  # layout selector branch to 0x110
        0x110: 0x804F63FC,  # VIF control z -> vi15
        0x114: 0x01FD0008,  # load blended/fog-disabled tag template
        0x115: 0x5800780A,  # negative 0x8000 control retains that template
        0x120: 0x11082000,  # NLOOP plus EOP construction (first half)
        0x121: 0x11084000,  # NLOOP plus EOP construction (second half)
        0x122: 0x811D43FD,  # insert dynamic loop/tag word
        0x128: 0x81E5EB7D,  # emit GIFtag
        0x12C: 0x81F21B7C,  # load V4-8-expanded qword
        0x141: 0x81E5937D,  # emit that qword unchanged in the vertex triplet
    }
    for pc, lower in expected_lower.items():
        if pc >= len(program) or program[pc][0] != lower:
            raise Vu1ProbeError(f"MODELS VU landmark mismatch at micro-address 0x{pc:03x}")
    return {name: pc for name, pc in {
        "entry": 0x000,
        "dispatch": 0x014,
        "models_layout": 0x110,
        "tag_emit": 0x128,
        "v4_load": 0x12C,
        "v4_emit": 0x141,
    }.items()}


def probe(executable: bytes) -> dict[str, Any]:
    digest = sha256(executable)
    if digest != EXECUTABLE_SHA256:
        raise Vu1ProbeError(f"canonical executable hash mismatch: {digest}")
    if executable[:4] != b"\x7fELF" or executable[4:6] != b"\x01\x01":
        raise Vu1ProbeError("input is not a little-endian ELF32 executable")
    blocks, program = extract_mpg_program(executable)
    landmarks = validate_models_landmarks(program)

    # VU memory qword 8 is the tag-template source selected when the MODELS
    # preamble control is 0x8000.  The template's named words are arranged for
    # the VU construction path: TAG1, REGS low/high, and the initial TAG0 word.
    template_vaddr = 0x00507B60
    offset = file_offset(template_vaddr, 16, executable)
    tag1, registers_low, registers_high, tag0 = struct.unpack_from("<4I", executable, offset)
    registers = registers_low | (registers_high << 32)
    tag = decode_giftag(tag0, tag1, registers)
    if tag0 != 0x8000 or tag1 != 0x312E4000 or registers != 0x412:
        raise Vu1ProbeError("MODELS GIFtag template differs from the canonical state")
    if (tag.pre, tag.flg, tag.nreg, tag.registers) != (1, 0, 3, (2, 1, 4)):
        raise Vu1ProbeError("unexpected MODELS GIFtag mode/register list")
    if tag.prim.raw != 0x25C:
        raise Vu1ProbeError("unexpected MODELS PRIM template")

    return {
        "executableSha256": digest,
        "upload": {
            "sourceCommand": f"0x{MPG_COMMAND_VADDR:08x}",
            "destinationStart": 0,
            "instructionCount": len(program),
            "extent": f"0x{len(program):x}",
            "blocks": [asdict(block) for block in blocks],
        },
        "microAddresses": {key: f"0x{value:03x}" for key, value in landmarks.items()},
        "gifTag": {
            "dynamicTag0": "vertex_count | 0x8000",
            "tag1": f"0x{tag1:08x}",
            "pre": tag.pre,
            "flg": tag.flg,
            "nreg": tag.nreg,
            "registers": list(tag.registers),
            "registerNames": ["ST", "RGBAQ", "XYZF2"],
            "prim": asdict(tag.prim),
        },
        "v4Routing": {
            "unpack": "unsigned V4-8 expands to four u32 VU lanes",
            "outputRegister": "RGBAQ",
            "alpha": "byte 3 reaches RGBAQ A unchanged (0x80 in all LEVEL00 MODELS records)",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, help="ignored/temp JSON summary")
    args = parser.parse_args()
    report = probe(args.executable.read_bytes())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
