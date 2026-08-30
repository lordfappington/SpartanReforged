# MODELS.BIN V2-16 UV Format

This document covers the 88,314 V2-16 pairs in the already-extracted canonical LEVEL00 `MODELS.BIN`. The analysis was read-only: no archive was opened, no texture or geometry was converted, and no asset data was emitted. Aggregate local reports are produced by `tools/analysis/models_uv_probe.py` beneath `logs/analysis` and remain untracked.

## Result

The V2-16 stream is a signed Q4.12 normalized UV pair (**CONFIRMED for LEVEL00**):

```text
u_normalized = int16_le(raw_u) / 4096.0
v_normalized = int16_le(raw_v) / 4096.0

u_texel = u_normalized * texture_width
v_texel = v_normalized * texture_height
```

The stored values are independent of texture dimensions. The texture width and height enter only when normalized coordinates are converted to texel space. Bias is zero (**CONFIRMED**); no universal half-texel offset is present. Coordinates outside `0..1` are intentional (**CONFIRMED**), but the specific repeat/mirror/clamp state of each material remains **UNKNOWN** because MTL property semantics are not decoded.

## Inputs and binding coverage

| Input | SHA-256 |
|---|---|
| `MODELS.BIN` | `8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3` |
| `MODELS.MTL` | `57283516fc3cc8589eec4817cf8c25dc3ff0cc2185e4ff99e262fa6f3a4a54b2` |

All 58 LEVEL00 TIM2 resources were read for metadata and hashed; their hashes matched the existing LEVEL00 inventory. Geometry uses 39 MTL records. Type-0 MTL resource declarations resolve 29 direct TIM2 bindings and three explicit aliases, leaving seven effect-like records unresolved. Primary scale evidence therefore uses 32 strongly bound material groups, 83,959 vertices, and 42,686 triangles.

Bound textures represent dimensions `16×16`, `32×32`, `64×64`, `128×64`, `128×128`, and `256×256`. This dimensional range is the decisive control against confusing normalized values with fixed texel coordinates.

## Raw survey and signedness

| Measure | U | V |
|---|---:|---:|
| Records | 88,314 | 88,314 |
| Signed range | `-32763..32734` | `-32758..32757` |
| Unsigned range | `0..65535` | `0..65535` |
| Negative values | 12,502 (14.1563%) | 7,852 (8.8910%) |
| Exact zero | 3,500 | 5,809 |
| Absolute value ≤16 | 3,997 | 11,259 |
| Multiples of 16 | 22,975 | 20,991 |

Exact Q12 landmarks recur heavily: U contains 2,267 values at 4096 and 1,969 at 2048; V contains 1,888 at 4096 and 1,397 at 2048. Residue zero modulo 16 is the most frequent residue on both axes.

Signed interpretation is structurally preferable (**CONFIRMED for the UNPACK and strongly supported numerically**). The VIF opcode is the signed V2-16 form. Across topology edges, the signed absolute-delta p99 is 4,097, whereas reinterpretation as unsigned u16 produces p99 63,690 discontinuities. Masking to generic GS 14-bit UV also introduces large discontinuities unless circular wrap is assumed. Negative coordinates participate coherently in tiled material groups.

## Candidate models

The probe tests divisors 16, 32, 64, 128, 256, 512, 1024, and 4096 in both fixed-texel and fixed-normalized forms.

`raw / 4096` is the only model consistent across different texture dimensions. For example, the 32×32 `ARROW` page spans raw U `28..3940` and V `29..3949`, which becomes approximately `0.007..0.964` on both axes. Treating the same raw values as 12.4 texels would span roughly 246 texels on a 32-pixel texture. The same Q12 divisor explains 64-, 128-, and 256-pixel pages without a dimension-dependent stored range.

Representative strongly bound records:

| MTL record | Texture | Dimensions | Raw U / V | Q4.12 normalized U / V | Interpretation |
|---:|---|---:|---|---|---|
| 2 `ARROW` | `ARROW.TM2` | 32×32 | `28..3940` / `29..3949` | `0.00684..0.96191` / `0.00708..0.96411` | single-page inset |
| 23 `APP_BLOOD_02` | `APP_BLOOD_02.TM2` | 64×64 | `2..4093` / `2..4093` | `0.00049..0.99927` both | nearly full page |
| 27 `CIRCLE` | `CIRCLE.TM2` | 64×64 | `2..4093` / `2..4093` | `0.00049..0.99927` both | nearly full page |
| 38 `GREEK_PATERN` | `GREEK_PATERN.TM2` | 128×128 | `2..4152` / `2..4093` | `0.00049..1.01367` / `0.00049..0.99927` | slight U overshoot |
| 49 `FLARE_NOZREAD` | alias to `FLARE.TM2` | 128×64 | `97..4093` / `1302..3987` | `0.02368..0.99927` / `0.31787..0.97339` | sub-page region |
| 39 `RING_GLOW` | `RING_GLOW.TM2` | 16×16 | `-3983..-103` / `295..3862` | `-0.97241..-0.02515` / `0.07202..0.94287` | one-period-shifted U |
| 20 `STEPS` | `STEPS.TM2` | 256×256 | `0..4096` both | `0..1` both | exact full extent |
| 31 `CLOUD` | `CLOUD.TM2` | 256×256 | `0..4096` / `0..1792` | `0..1` / `0..0.4375` | vertical sub-region |

## Bias and texture boundaries

Zero global bias is supported by exact 0 and 4096 endpoints, 11,433 integer-UV boundary hits, and 40,320 exact texel-grid hits in bound material data. Only 8,663 coordinates land on a half-texel grid. Small offsets such as 2/4096 or 4093/4096 vary by asset and are deliberate page insets or quantization, not a universal bias.

A normalized half texel would require a raw offset of `2048 / width` on U and `2048 / height` on V. The represented dimensions would therefore require different raw offsets, which are not present as a consistent cross-material rule. Bias zero is **CONFIRMED**; material-specific sampling adjustments remain possible but unproven.

## Wrapping, tiling, and seams

Of the 32 strongly bound material groups, 21 contain at least one coordinate outside `0..1`. In bound geometry, 13,970 of 42,686 triangles cross or lie outside a single normalized extent. Across every geometry triangle the count is 13,974 of 46,336.

Architectural materials provide strong tiling evidence: `RUINEDWALL1`, `BASEWALL*`, `LS_STONEWALL1`, `TEMPLE_FLAGS`, and `MOSAIC` reach multiple integer periods, in some cases nearly `-8..8`. `RING_GLOW` demonstrates a coherent negative one-period shift. These observations confirm that out-of-range UVs must be preserved and that some materials require periodic sampling. They do not distinguish ordinary repeat from mirrored repeat, nor prove every material's GS clamp state.

Repeated XYZ positions yield 16,487 differing-UV pair combinations among strongly bound materials. Of these, 312 pairs differ by exact integer periods on both axes at Q12 scale. This independently supports explicit seams and wrap transitions rather than a second position-like attribute. Material boundaries cannot occur inside a descriptor, so these are vertex duplication/seam effects within the established material groups.

## Triangle quality

After Q4.12 decoding, all 46,336 topology triangles were evaluated in memory:

- 1,463 have exactly zero UV area;
- the count at doubled normalized area ≤ `1e-8` is also 1,463, so there are no additional nonzero near-degenerate cases at that threshold;
- doubled normalized UV area has median `0.0307312` and p99 `1.951395`;
- triangle maximum-axis UV span has median `0.370117` and p99 `2.888269`.

Within the 42,686 strongly texture-bound triangles, only 339 have zero/near-zero UV area. Most collapsed UVs therefore belong to the seven unresolved effect-like MTL groups, not ordinary textured world surfaces. Zero-area UV triangles are retained as legitimate data rather than rejected.

## PS2 GS relationship

Generic GS UV is not the representation stored here. Pinned PCSX2 source masks packed GS UV components to 14 bits, consistent with the GS's unsigned fixed-point UV register: [PCSX2 GS UV handler](https://github.com/PCSX2/pcsx2/blob/c10a5c9ad951c517dc48b722b5b84eb9bf7fdb42/pcsx2/GS/GSState.cpp#L1422-L1427). Pinned gsKit source converts texel coordinates to GS UV by multiplying by 16 and clamps against `texture width × 16` / `height × 16`: [gsKit textured-sprite setup](https://github.com/ps2dev/gsKit/blob/43122eb96289167975b56caa45beb71eb8684fa2/ee/gs/include/gsInline.h#L104-L131).

Spartan instead supplies signed V2-16 values to a VU program and stores the same approximately `-8..8` representable range regardless of texture size. The stored stream is therefore a VU-side custom normalized Q4.12 representation (**CONFIRMED from LEVEL00 data**), not direct GS UV. A downstream operation equivalent to `q12 × texture_dimension × 16` is **LIKELY** before fixed GS UV use, but the exact VU instructions, rounding, and clamp-state setup are **UNKNOWN** because no VU microprogram or direct GIF register stream is embedded in this file.

## V-axis orientation

The V2 stream defines a consistent signed normalized V coordinate. Descriptor 118's stone texture could not identify top/bottom, but the subsequent descriptor-5 test did: source V places an upright lambda at the lower edge of a suspended banner, while `1-v` puts it inverted at the top. Main-cloth V rows also increase monotonically as source Y descends. Source V is therefore **CONFIRMED for modern glTF/Blender output**; flip remains explicit for forensic comparison. See [MODELS_VISUAL_CONVENTIONS.md](MODELS_VISUAL_CONVENTIONS.md).

## Binding confidence

The supported chain is:

```text
BIN descriptor MTL index
  -> ordered MODELS.MTL record
    -> type-0 resource stem or explicit alias
      -> one LEVEL00 TIM2 resource
```

Direct bindings: 29. Explicit aliases: `PICKUPS_2SIDED -> PICKUPS.TM2`, `APP_FIRE_BASE -> APP_BLOOD_02.TM2`, and `FLARE_NOZREAD -> FLARE.TM2`. Seven unresolved records are `HEAD_MARKERS`, `LIGHTNING`, `BEAM`, `APP_MEDUSA`, `LIGHT_SPHERE01`, `LIGHT_SPHERE02`, and `GLOW`; they were excluded from texture-dimensional proof but retained in whole-stream statistics.

## Readiness and remaining unknowns

MODELS.BIN is **VISUALLY VALIDATED** for LEVEL00 geometry. Positions, strips, ADC suppression, winding, material assignment, Q4.12 UVs, coordinates, and source V are established through descriptors 118 and 5. Alternative reflections, axis conversions, and V flip remain explicit rather than silently altering source data.

V4-8 semantics do not block exporting positions, triangles, material groups, and UVs. They may later be required for faithful lighting, vertex color, or other rendering attributes. Exact MTL sampler properties, VU rounding, and unresolved effect-resource bindings remain open; those limit material fidelity, not the validated geometry/UV convention.

The first exporter now implements the formula directly, preserves all signed/out-of-range values, and offers explicit `source`/`flip` V modes. Reading the serialized glTF accessors back produced exact matches for all 88,314 Q4.12-derived UV pairs. No texture conversion or visual-orientation assumption was used. Pipeline details are in [MODELS_EXPORT_PIPELINE.md](MODELS_EXPORT_PIPELINE.md).
