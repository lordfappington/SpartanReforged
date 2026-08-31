#!/usr/bin/env python3
"""Bounded CLOUD TEX0/texture-alpha probe for canonical LEVEL00.

The tool decodes symbolic GS state and reports aggregate alpha facts only. It
does not emit texture pixels, executable bytes, or runtime address data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import struct
from dataclasses import asdict, dataclass


EXECUTABLE_SHA256 = "55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d"
CLOUD_SHA256 = "694a16e09560cc0bbb3eb2469050541fdd092575333f6cb1ca0566459855b58e"
TEX0_ADDRESS_MASK = 0x3FFF | (0x3FFF << 37)


class GsTextureStateError(ValueError):
    """Input or state does not match the bounded supported path."""


@dataclass(frozen=True)
class Tex0State:
    raw: int
    tbp0: int
    tbw: int
    psm: int
    tw: int
    th: int
    tcc: int
    tfx: int
    cbp: int
    cpsm: int
    csm: int
    csa: int
    cld: int


@dataclass(frozen=True)
class TexaState:
    raw: int
    ta0: int
    aem: int
    ta1: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_tex0(raw: int) -> Tex0State:
    if raw < 0 or raw >= 1 << 64:
        raise GsTextureStateError("TEX0 must be an unsigned 64-bit value")
    return Tex0State(
        raw=raw,
        tbp0=raw & 0x3FFF,
        tbw=(raw >> 14) & 0x3F,
        psm=(raw >> 20) & 0x3F,
        tw=(raw >> 26) & 0xF,
        th=(raw >> 30) & 0xF,
        tcc=(raw >> 34) & 1,
        tfx=(raw >> 35) & 3,
        cbp=(raw >> 37) & 0x3FFF,
        cpsm=(raw >> 51) & 0xF,
        csm=(raw >> 55) & 1,
        csa=(raw >> 56) & 0x1F,
        cld=(raw >> 61) & 7,
    )


def decode_texa(raw: int) -> TexaState:
    if raw < 0 or raw >= 1 << 64:
        raise GsTextureStateError("TEXA must be an unsigned 64-bit value")
    return TexaState(raw=raw, ta0=raw & 0xFF, aem=(raw >> 15) & 1, ta1=(raw >> 32) & 0xFF)


def modulate_alpha(vertex_alpha: int, texture_alpha: int, tcc: int) -> int:
    if not (0 <= vertex_alpha <= 0xFF and 0 <= texture_alpha <= 0xFF):
        raise GsTextureStateError("alpha components must fit in one byte")
    if tcc == 0:
        return vertex_alpha
    if tcc != 1:
        raise GsTextureStateError("TCC must be zero or one")
    return min((vertex_alpha * texture_alpha) >> 7, 0xFF)


def alpha_test_gequal(alpha: int, reference: int) -> bool:
    return alpha >= reference


def rgb_only_failed_writes() -> dict[str, bool]:
    """GS AFAIL=RGB_ONLY behavior for a 32-bit framebuffer."""
    return {"rgb": True, "alpha": False, "depth": False}


def _log2_dimension(value: int) -> int:
    if value <= 0 or value & (value - 1):
        raise GsTextureStateError("CLOUD dimensions must be positive powers of two")
    return int(math.log2(value))


def cloud_runtime_tex0_template(header_raw: int, width: int, height: int) -> int:
    """Apply only the confirmed address-independent Spartan loader changes."""
    raw = header_raw & ~TEX0_ADDRESS_MASK
    raw &= ~(0x3F << 14)
    raw |= max(2, width >> 6) << 14
    raw &= ~((0xF << 26) | (0xF << 30) | (1 << 34) | (0x3 << 35) | (0x7 << 61))
    raw |= _log2_dimension(width) << 26
    raw |= _log2_dimension(height) << 30
    raw |= 1 << 34  # FUN_0025eed0 promotes loaded textures to RGBA/TCC=1.
    raw |= 1 << 61  # FUN_0025fd10 selects CLD=1 for this loaded indexed texture.
    return raw


def inspect_cloud(data: bytes) -> dict[str, object]:
    if sha256(data) != CLOUD_SHA256:
        raise GsTextureStateError("canonical CLOUD.TM2 hash mismatch")
    if data[:4] != b"TIM2" or len(data) < 0x40:
        raise GsTextureStateError("CLOUD is not the expected TIM2 picture")
    picture = 0x10
    clut_size, image_size = struct.unpack_from("<II", data, picture + 4)
    header_size, palette_count = struct.unpack_from("<HH", data, picture + 12)
    width, height = struct.unpack_from("<HH", data, picture + 20)
    clut_type, image_type = struct.unpack_from("<BB", data, picture + 18)
    header_tex0 = struct.unpack_from("<Q", data, picture + 24)[0]
    image_start = (picture + header_size + 15) & ~15
    clut_start = image_start + image_size
    if clut_start + clut_size != len(data) or clut_size != palette_count * 4:
        raise GsTextureStateError("unexpected CLOUD image/CLUT bounds")
    image = data[image_start:clut_start]
    clut = data[clut_start:]
    indices = sorted(set(image))
    palette = [tuple(clut[i:i + 4]) for i in range(0, len(clut), 4)]
    raw_alphas = sorted({entry[3] for entry in palette})
    if (width, height, image_type, clut_type, indices, raw_alphas) != (256, 256, 5, 3, [255], [0x80]):
        raise GsTextureStateError("canonical CLOUD format/content aggregate differs")
    if len(set(palette)) != 1 or palette[0] != (0xFF, 0xFF, 0xFF, 0x80):
        raise GsTextureStateError("canonical CLOUD palette is not uniform white/full-alpha")
    runtime_raw = cloud_runtime_tex0_template(header_tex0, width, height)
    runtime = decode_tex0(runtime_raw)
    fragment_alpha = modulate_alpha(0x80, 0x80, runtime.tcc)
    return {
        "sourceSha256": sha256(data),
        "dimensions": [width, height],
        "imageType": image_type,
        "clutType": clut_type,
        "imageIndices": indices,
        "clutUniqueRgbaPs2": [list(palette[0])],
        "headerTex0": asdict(decode_tex0(header_tex0)),
        "runtimeTex0AddressIndependent": asdict(runtime),
        "runtimeAddressFields": "TBP0 and CBP are allocated dynamically",
        "textureFunction": "MODULATE_RGBA",
        "vertexAlpha": 0x80,
        "textureAlphaPs2": 0x80,
        "textureAlphaDesktop": 0xFF,
        "fragmentAlphaPs2": fragment_alpha,
        "alphaTestGequal80": alpha_test_gequal(fragment_alpha, 0x80),
        "failedRgbOnlyWrites": rgb_only_failed_writes(),
        "texaApplicability": "IRRELEVANT: CPSM=PSMCT32 supplies CLUT alpha directly; TCC/TFX use it without TEXA expansion",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=pathlib.Path)
    parser.add_argument("cloud", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    executable = args.executable.read_bytes()
    if sha256(executable) != EXECUTABLE_SHA256:
        raise GsTextureStateError("canonical executable hash mismatch")
    report = {"executableSha256": sha256(executable), "cloud": inspect_cloud(args.cloud.read_bytes())}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
