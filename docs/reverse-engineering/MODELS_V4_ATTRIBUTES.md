# MODELS.BIN V4-8 Attributes

## Scope and result

This study covers only the four-byte stream paired one-to-one with LEVEL00 `MODELS.BIN` positions and UVs. It does not identify unrelated material fields or claim the original VU-to-GS program.

All 88,314 records were surveyed. The strongest bounded interpretation is **LIKELY vertex RGBA/color modulation**:

- bytes 0–2 contain structured, material- and position-dependent color/intensity values;
- byte 3 is exactly `0x80` in every record;
- PS2 APIs conventionally scale floating RGBA by 128 before emitting `RGBAQ`, so `0x80` represents 1.0/full alpha;
- signed-normal and 128-biased-normal interpretations fit poorly;
- CLOUD has a pronounced spatial gradient in bytes 0–2 but no varying alpha.

The parser continues to retain raw bytes. The exporter exposes the interpretation only through opt-in `--v4-color ps2-rgba`; the forensic default remains `omitted`. glTF requires vertex colors in `[0,1]`, so this diagnostic maps `min(byte / 128, 1)`. Values above 128 remain available raw in the parser but cannot be represented faithfully as core glTF `COLOR_0`. CLOUD is unaffected because its first three bytes never exceed 108.

## Stream and cardinality

Each parsed VIF batch contains a V4-8 unpack with exactly the same element count as its position and V2-16 UV streams. Across 2,128 batches:

| Measure | Value |
|---|---:|
| V4-8 records | 88,314 |
| Position records | 88,314 |
| UV records | 88,314 |
| Byte width | 4 |
| Byte 3 equal to `0x80` | 88,314 / 88,314 |

This establishes the storage and pairing as **CONFIRMED**. Consumer semantics remain inferred from correlation.

## Global distributions

| Channel | Unsigned range | Unique | zero | `0x80` | `0xff` | Mean | Median |
|---|---|---:|---:|---:|---:|---:|---:|
| byte 0 | 0..255 | 147 | 5,036 | 0 | 4,277 | 51.383 | 31 |
| byte 1 | 0..255 | 147 | 5,030 | 0 | 4,277 | 50.289 | 32 |
| byte 2 | 0..255 | 125 | 5,156 | 0 | 4,289 | 42.836 | 24 |
| byte 3 | 128..128 | 1 | 0 | 88,314 | 0 | 128 | 128 |

Signed reinterpretation changes `128..255` to `-128..-1` but does not produce a credible normal distribution. Treating bytes 0–2 as signed components gives mean vector length 0.494 and only 6.92% within ten percent of unit length. Treating them as 128-biased components gives mean length 1.263 and only 8.29% near unit. CLOUD alone has 0% near unit under either interpretation.

Opaque architecture is not constant: materials such as `002` and `BASEWALL` contain many tuples and spatial variation. Values above 128 occur 12,903 times in bytes 0–2 among materials without type 2; under PS2 `/128` color scaling these are valid brightening values rather than signed negatives. This strengthens the color/lighting interpretation.

## Material and type-2 correlations

| MTL type-2 | V4 records | Unique tuples | Representative behavior |
|---:|---:|---:|---|
| absent | 65,579 | 4,010 | broad world lighting/color range, including values above 128 |
| 1 | 40 | 20 | `MISCALPHA`; varying dark/modulated RGB, alpha 128 |
| 2 | 17,180 | 35 | `GRKTREE`; narrow green/brown modulation, alpha 128 |
| 3 | 142 | 1 | blood/fire/ring-glow all `(127,127,127,128)` |
| 4 | 182 | 1 | `FLARE_NOZREAD` `(127,127,127,128)` |
| 5 | 5,191 | 355 | mixed family: CLOUD/greenery/other special materials |

Type 2 does not determine one V4 pattern. Values 3 and 4 use neutral full-scale color, while value 5 spans CLOUD gradients, GREENERY variation, MEDUSA_TOWER lighting, and neutral special geometry. This supports type 2 as a render-family selector but not as the V4 encoding.

Vegetation alpha is texture driven: `GRKTREE` and `GREENERY` have partial-alpha textures while every vertex alpha remains `0x80`. Their first three channels plausibly tint or light the foliage. Likewise, type-2 values 3 and 4 leave vertex color essentially neutral, making texture and native blend state the likely effect drivers.

## CLOUD deep dive

`CLOUD` is descriptor 48, MTL index 31, type-2 value 5: 27 batches, 1,957 records, and 1,728 triangles. Its native 256×256 texture alpha is fully opaque.

Only six V4 tuples occur:

| Tuple | Count | Observed Y range | V |
|---|---:|---:|---:|
| `(0,0,0,128)` | 1,483 | 66.324..156.970 | 0..0.3125 |
| `(39,37,25,128)` | 136 | 33.702..46.783 | 0.40625 |
| `(25,23,15,128)` | 135 | 57.378 | 0.34375 |
| `(31,28,19,128)` | 124 | 49.860..50.189 | 0.375 |
| `(108,88,55,128)` | 68 | 18.348..29.854 | 0.4375 |
| `(35,33,23,128)` | 11 | 50.189 | 0.375 |

Bytes 0–2 correlate strongly and negatively with world Y (`-0.701`, `-0.724`, `-0.735`) and positively with V (`0.663`, `0.686`, `0.697`). They also correlate with radial distance (`0.632`–`0.664` in 3D), while X, Z, U, local vertex index, and batch index are weak. No repeated position/UV pair carries conflicting attributes. This is a coherent dark upper dome and brighter warm lower ring, strongly supporting color/intensity modulation rather than arbitrary control data.

Byte 3 never varies, so neither standard texture-alpha multiplication nor vertex-alpha multiplication can make CLOUD translucent: `texture alpha 255 × vertex alpha 128/128 = 1.0`. The missing transparency must be supplied by native render state—most likely a type-2-selected GS blend equation/fixed factor and ordering/depth behavior—not by V4 alpha.

## Generic PS2 evidence

This evidence describes PS2 conventions, not proven Spartan routing:

- ps2sdk converts float RGB(A) to `RGBAQ` by multiplying components by 128, directly supporting `0x80 == 1.0`: [ps2sdk `draw3d.c`](https://github.com/ps2dev/ps2sdk/blob/master/ee/draw/src/draw3d.c).
- gsKit initializes alpha with the explicit convention that `0x80` is 1.0: [gsKit `gsInit.c`](https://github.com/ps2dev/gsKit/blob/master/ee/gs/src/gsInit.c).
- PS2 texture function `MODULATE` and the GS `ALPHA` selectors are defined independently: [PCSX2 `GSRegs.h`](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSRegs.h) and [ps2sdk `libgs.h`](https://github.com/ps2dev/ps2sdk/blob/master/ee/libgs/include/libgs.h).

V4-8 cannot itself be a complete `RGBAQ` packet because Q is a separate 32-bit floating value in the GS vertex interface. A plausible pipeline is that VU code expands these bytes to RGBA while supplying Q elsewhere. That routing is **UNKNOWN** without executable/VU analysis.

## Controlled diagnostic

An opt-in glTF `COLOR_0` export maps each channel as `min(float(byte) / 128.0, 1.0)`, as required by the [glTF 2.0 vertex-color rule](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc). Full-scene transform round-trip validation retained 1,338 descriptors, 2,128 batches, 88,314 color records, and 46,336 triangles. Blender 5.2.1 imported 1,338 objects and 46,336 polygons and preserved the color attribute as a corner-domain byte-color layer. The source parser, not glTF, remains the lossless home for values above 128.

Under opaque imported material behavior the black upper CLOUD still depth-occludes the world and its bright lower band remains an opaque shell. Local additive-family approximations reveal the scene through the shell while preserving its V4-driven ring gradient; full and half-strength variants both do so. These renders are diagnostic approximations, not decoded GS state. They establish that an additive-family equation can explain the symptom, not which exact native operands or fixed factor Spartan uses.

## Confidence

| Finding | Classification |
|---|---|
| four-byte stream and one-to-one position/UV cardinality | **CONFIRMED** |
| byte 3 is globally `0x80` | **CONFIRMED** |
| generic PS2 meaning of `0x80` as full-scale alpha | **CONFIRMED** |
| bytes 0–2 are vertex RGB/color-light modulation in Spartan | **LIKELY** |
| byte 3 is routed as vertex alpha in Spartan | **LIKELY**, not directly observed |
| signed or biased unit normal | **REJECTED by distribution evidence** |
| CLOUD V4 carries a spatial color/intensity gradient | **CONFIRMED** |
| CLOUD transparency comes from varying V4 alpha | **REJECTED** |
| CLOUD transparency comes from a type-2-selected native blend/depth family | **LIKELY** |
| exact GS ALPHA operands, FIX, depth write, and ordering | **UNKNOWN** |
| type-2 value 5 denotes one exact render equation | **UNKNOWN** |

Readiness remains **TEXTURED ASSEMBLY VALIDATED**. The opaque-shell failure is explained, but it is not yet reproduced from an exact source-derived GS state.

Validated R5900 analysis has since recovered the MTL child-to-GS `TEST`/`ZBUF`/`ALPHA` path, but the bounded trace did not naturally establish V4 routing through VU submission to GS `RGBAQ`. V4 -> GS `RGBAQ` therefore remains **LIKELY**, not executable-confirmed. See [EXEC_RENDER_STATE.md](EXEC_RENDER_STATE.md).
