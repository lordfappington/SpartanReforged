# TIM2 Format — Verified LEVEL00 PSMT4 Subset

This note documents only the subset established from the canonical LEVEL00 `002.TM2`. The source remained read-only. `tools/conversion/tim2_decode.py` emits only native-resolution derived PNGs beneath ignored `temp` directories and rejects every unimplemented TIM2 variant.

## Canonical sample

| Property | Value | Confidence |
|---|---|---|
| Source | `DATA/ENV/LEVEL00/WORLD/002.TM2` | **CONFIRMED** |
| SHA-256 | `84f2b7c0b9592d5d6af8e5eaaec13b9ba02fb1065e770b52a289151d5d411dac` | **CONFIRMED** |
| File size | 43,648 bytes | **CONFIRMED** |
| Container | `TIM2`, version 4, format 0, one picture | **CONFIRMED** |
| Dimensions | 256×256 | **CONFIRMED** |
| Image type | 4, IDTEX4 / GS PSMT4, 4-bit indexed | **CONFIRMED** |
| CLUT | type 1, 16 RGB5A1 entries, 32 bytes | **CONFIRMED** |
| Mips | 4: 32,768 + 8,192 + 2,048 + 512 bytes | **CONFIRMED** |
| Alpha | RGB5A1 high bit; every sample entry is opaque | **CONFIRMED for 002** |
| Base-image storage | row-major packed indices, low nibble first | **CONFIRMED for 002** |
| GS swizzle step | none required for this payload | **CONFIRMED for 002** |

The picture begins at file offset `0x10`. Its declared total size is `0xaa70`, header size `0x50`, image payload size `0xaa00`, and CLUT size `0x20`. The image payload begins at `0x60`; the CLUT begins at `0xaa60` and ends at EOF.

## Decode algorithm

For each packed base-level byte, the even pixel uses bits 0–3 and the odd pixel bits 4–7. Each index selects one 16-bit little-endian CLUT entry:

```text
r8 = (entry & 0x1f) << 3
g8 = ((entry >> 5) & 0x1f) << 3
b8 = ((entry >> 10) & 0x1f) << 3
a8 = 255 if entry bit 15 is set, otherwise 0
```

The decoder preserves the stored row order, produces RGBA8, writes PNG scanlines without scaling or filtering, and uses deterministic zlib settings. The native PNG is 256×256; PNG SHA-256 is `99df51498b261e7d671b6ab6045fce6ea2137f7ca41ee9a32cce0e942ccee1b5`, and decoded RGBA SHA-256 is `dbd0582147aff1624e80d4f050990c847d5ba858f57d2666c1883d66cf1a116f`.

## Independent validation

Noesis 4.474 independently decoded the same source. Its PNG container bytes differ, but its 262,144 RGBA bytes match the project decoder exactly. Both routes report 256×256 pixels, 16 colors, and alpha 255 throughout. This proves the implemented pixel, palette, row, and alpha interpretation for `002.TM2`; producing a PNG alone was not treated as proof.

The standard format identifiers align with ps2dev gsKit's `GS_PSM_T4` classification and 16-color CLUT handling: [gsKit GS definitions](https://github.com/ps2dev/gsKit/blob/master/ee/gs/include/gsInit.h), [gsKit texture upload](https://github.com/ps2dev/gsKit/blob/master/ee/gs/src/gsTexture.c). These references support terminology; the byte-identical independent decode is the sample-specific validation.

## Limits

- **CONFIRMED:** the exact v4/format-0, one-picture PSMT4 + RGB5A1 subset above.
- **LIKELY:** other LEVEL00 type-4 samples with the same structural fields can use the same path, but they have not been accepted without validation.
- **UNKNOWN / unsupported:** TIM2 image types 3 and 5, 256-entry CLUTs, CSM variants, swizzled payloads, multiple pictures, other versions, and faithful export of the stored mip chain.
- The decoder intentionally fails on those variants and does not claim a general TIM2 implementation.

