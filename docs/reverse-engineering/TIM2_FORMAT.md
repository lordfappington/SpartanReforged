# TIM2 Format — LEVEL00 Geometry Subset

This note documents only the TIM2 combinations required by strongly resolved LEVEL00 `MODELS.MTL` geometry materials. The source files remain ignored and read-only. `tools/conversion/tim2_decode.py` writes deterministic native-resolution PNGs only beneath ignored `temp` directories; it does not scale, filter, enhance, or silently fall back to Noesis.

## Geometry-used coverage

The 1,338 MODELS descriptors use 39 MTL records. Thirty-two records resolve strongly to 30 unique TIM2 files; seven material names have no unique same-stem/alias texture binding and remain `UNRESOLVED_BINDING`. All 58 LEVEL00 TIM2 hashes were reverified against the local extraction inventory before this subset was decoded.

| Image / CLUT / mips | Unique textures | Decoder status | Independent result |
|---|---:|---|---|
| image 4 / PSMT4 + type 1 RGB5A1 / 1 mip | 3 | **SUPPORTED** | RGBA exact to Noesis |
| image 4 / PSMT4 + type 1 RGB5A1 / 4 mips | 16 | **SUPPORTED** | RGBA exact to Noesis |
| image 4 / PSMT4 + type 3 RGBA8888 / 1 mip | 3 | **SUPPORTED** | RGBA exact to Noesis |
| image 4 / PSMT4 + type 3 RGBA8888 / 4 mips | 2 | **SUPPORTED** | RGBA exact to Noesis |
| image 5 / PSMT8 + type 1 RGB5A1 / 1 mip | 3 | **SUPPORTED** | RGBA exact to Noesis |
| image 5 / PSMT8 + type 3 RGBA8888 / 1 mip | 3 | **SUPPORTED** | RGBA exact to Noesis |

No directly colored image is strongly bound to MODELS geometry. The decoder does not claim support for LEVEL00's unrelated image-type-3 resources or a general TIM2 implementation.

## Container and payload validation

**CONFIRMED:** the supported files are TIM2 version 4, format 0, with one picture. The picture begins at `0x10`. The decoder bounds-checks the picture header, declared total/image/CLUT sizes, image and CLUT alignment, palette count, supported type combination, dimensions, mip table, every declared mip size, zero alignment padding, and decoded cardinality. It rejects unsupported or inconsistent inputs rather than guessing.

**CONFIRMED:** four-level files store explicit sizes for base, half, quarter, and eighth dimensions. Their palette follows the complete mip payload and is shared. The current tool validates every level but intentionally decodes only the stored base level; it never generates mips.

## Indexed-image rules

### PSMT4 / image type 4

**CONFIRMED:** the base image is linear row-major packed indices. The even pixel uses the low nibble and the odd pixel uses the high nibble. No image unswizzle is required. A 16-entry CLUT is used without permutation.

### PSMT8 / image type 5

**CONFIRMED:** the base image is linear row-major, one byte per palette index. No image unswizzle is required.

**GENERIC PS2 RULE:** GS CSM1 256-color palettes exchange the 8-entry blocks at logical positions 8–15 and 16–23 inside each 32-entry group. Equivalently, logical palette index bits 3 and 4 are exchanged:

```text
stored_index = (logical & ~0x18)
             | ((logical & 0x08) << 1)
             | ((logical & 0x10) >> 1)
```

The operation is self-inverse. ps2dev's [gsKit CSM example](https://github.com/ps2dev/gsKit/blob/master/examples/clutcsm/clutcsm.c) explicitly performs this block exchange for CSM1; [gsKit texture code](https://github.com/ps2dev/gsKit/blob/master/ee/gs/src/gsTexture.c) independently establishes byte-per-pixel PSMT8 and half-byte-per-pixel PSMT4 storage.

**SPARTAN-SPECIFIC OBSERVATION:** applying that CSM1 permutation to the stored 256-entry LEVEL00 palettes makes all six geometry-bound PSMT8 textures match Noesis exactly. `CIRCLE` and `FLARE` and all three RGB5A1 samples require the exchange. This is palette reordering, not image-data unswizzling.

## CLUT and alpha rules

### Type 1: RGB5A1

Each little-endian 16-bit entry decodes as:

```text
r8 = (entry & 0x1f) << 3
g8 = ((entry >> 5) & 0x1f) << 3
b8 = ((entry >> 10) & 0x1f) << 3
a8 = 255 if entry bit 15 is set, otherwise 0
```

**CONFIRMED:** this reproduces Noesis exactly. Five-bit channels retain their stored high-bit expansion (`0..248`); no speculative bit replication is applied.

### Type 3: RGBA8888

Entries are stored in byte order `R, G, B, A_PS2`:

```text
r8, g8, b8 = stored bytes
a8 = min(255, A_PS2 * 2)
```

**CONFIRMED:** the PS2 `0..128` alpha convention and saturated doubling reproduce every geometry-bound type-3 CLUT byte-for-byte against Noesis.

## Independent pixel validation

All 30 unique strongly bound textures were decoded through both the project decoder and Noesis 4.474. Dimensions and all RGBA bytes, including alpha, are identical for all 30. The ignored local manifest records source TIM2, decoded RGBA, and deterministic PNG SHA-256 values per texture.

The previously validated outputs remain unchanged:

| Texture | Mips | Deterministic PNG SHA-256 | Decoded RGBA SHA-256 |
|---|---:|---|---|
| `002.TM2` | 4 | `99df51498b261e7d671b6ab6045fce6ea2137f7ca41ee9a32cce0e942ccee1b5` | `dbd0582147aff1624e80d4f050990c847d5ba858f57d2666c1883d66cf1a116f` |
| `L0_FLAGS.TM2` | 1 | `04626a87f45478eddaebeb63319d3d3ccbfd6e0aa5387d19d5cfb4168b24fac6` | `3acfec0e6c9987afc578c8522bfc24f77e59cea46a9eb0a9919f271ccbd4689a` |

## Confidence and limits

- **CONFIRMED:** the six format/mip combinations in the geometry-used matrix, native base-level decode, palette rules, alpha rules, and absence of an image unswizzle for these files.
- **CONFIRMED:** all strongly bound LEVEL00 MODELS textures are faithfully base-level decodable.
- **UNKNOWN / unsupported:** image type 3, CLUT types 0/2 or compound flag variants, direct color, multi-picture containers, other versions/container formats, and TIM2 combinations outside this geometry-required set.
- **UNRESOLVED BINDING:** seven geometry-used MTL records do not uniquely resolve to a LEVEL00 TIM2. This is a material/resource-reference question, not a failure of any encountered strongly bound texture format.

The first full textured validation assembly successfully attached all 30 decoded images to 32 confirmed materials with exact dimensions and no missing or cross-bound image in Blender. This adds pipeline-level evidence but no new TIM2 decode rule. Twenty-two unique images are fully opaque, one has binary alpha, and seven have partial alpha; native material alpha modes remain outside TIM2 and unresolved.
