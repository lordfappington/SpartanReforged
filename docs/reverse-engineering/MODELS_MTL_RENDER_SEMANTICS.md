# MODELS.MTL Render-Semantics Study

## Scope and result

This study is limited to face culling/two-sided rasterization and alpha test/blend behavior in the canonical LEVEL00 `MODELS.MTL`. It does not assign names to unrelated properties or claim a complete MTL schema.

The canonical file is 5,952 bytes with SHA-256 `57283516FC3CC8589EEC4817CF8C25DC3FF0CC2185E4FF99E262FA6F3A4A54B2`. Its header points to 55 ordered, length-delimited records at `0x250`; the strict record walk ends exactly at EOF. All record headers have zero at offsets `+0x08` and `+0x0c`. Thirty-nine records are selected by 1,338 MODELS descriptors.

Conclusions:

- **CULL/TWO-SIDED — LIKELY platform mapping, no MTL selector identified.** The PS2 GS `PRIM` state has no face-culling field. An opt-in all-`doubleSided` glTF experiment removes the systemic holes while preserving all geometry. Spartan could still cull before GS submission, so this is not a confirmed per-material native rule.
- **ALPHA-CAPABLE/RENDER FAMILY — STRONG correlation for child type 2.** Type 2 occurs on all nine bound materials whose decoded image has binary or partial alpha (9 true positives, 0 false negatives), but also on three opaque-image materials (`CLOUD`, `GIBS`, and `MEDUSA_TOWER`). Its values 1–5 therefore appear to select render families, not merely “has alpha.” Exact native enum names remain unknown.
- **ALPHA MASK — LIKELY for type-2 value 1 / `MISCALPHA`, not confirmed.** Its bound image has strictly binary alpha, but one sample cannot establish the native alpha-test operator or threshold.
- **ALPHA BLEND — LIKELY as a broad family, exact equations UNKNOWN.** Type-2 values 2–5 occur on foliage/effect materials, but standard glTF source-alpha blending cannot represent arbitrary GS equations.
- **ALPHA THRESHOLD — UNKNOWN.** No correlated field contains a defensible threshold. No `alphaCutoff` is emitted.

## Record/property matrix

`tools/analysis/models_mtl_render_probe.py` generates an ignored local JSON matrix and a 39-row used-material CSV. Every child records its absolute and record-relative byte offset, length, type, raw bytes, unsigned/signed u32 interpretations, and strings. The reusable parser retains unknown numeric properties without assigning semantics.

All numeric children seen in the 55 records have an eight-byte child header followed by two u32 payload words. The second word is zero except in type-11 UI records, where both words are nonzero and remain uninterpreted.

| Child type | Occurrences | Distinct first-word values | Bounded observation |
|---:|---:|---|---|
| 2 | 25 | 1, 2, 3, 4, 5 | strongest alpha/render-family candidate |
| 4 | 1 | -20 | `GREENERY` only; not a general alpha threshold |
| 8 | 12 | 0 | low-cardinality flag presence, not alpha-complete |
| 11 | 3 | paired nontrivial words | unused UI records only |
| 12 | 12 | 0,1,4,5,7,9,12–15 | particle/UI family-like selector |
| 13 | 10 | 0 | presence flag; several unresolved effects |
| 15 | 10 | 0,1,2,3,6,7,8,9 | effect/UI family-like selector |
| 16 | 19 | 0,1 | effect property; not alpha-complete |
| 17 | 3 | 0 | unused particle records only |
| 18 | 14 | 0,1,2 | effect/UI property |
| 19 | 40 | 0,1 | widespread terminal property; not alpha-specific |
| 21 | 10 | 1 | special/effect property |
| 22 | 12 | 0 | widespread on flags, pickups, foliage, and effects |
| 24 | 1 | 5 | unused `APP_SMOKE` only |
| 26 | 1 | 1 | `BEAM` only |

Type numbers above are engine property identifiers, not asserted GS register numbers.

## Culling correlation

No numeric child separates an evidenced “two-sided” material class from solid architecture:

- `PICKUPS_2SIDED` contains types 22 and 19, but ordinary `PICKUPS`, `L0_FLAGS`, `ARROW`, foliage, and effects also contain type 22.
- `TEMPLE_FLAGS` contains only its resource string, while `L0_FLAGS` contains types 22 and 19. The two flag families therefore do not expose a common numeric two-sided flag.
- Existing full-scene observation is scene-level: default glTF backface culling creates broad holes across architecture and terrain; forcing all submitted materials two-sided restores coherent surfaces. It is not a per-material ground-truth classification.

The hardware context explains this absence. The official PCSX2 GS register definition shows `GSRegPRIM` fields for primitive type, shading, texturing, fog, alpha blending, antialiasing, texture-coordinate mode, context, and fixed shading, but no culling bit. `GSRegTEST` carries alpha/depth test fields, and `GSRegALPHA` carries blend operands. The ps2sdk draw implementation likewise builds `PRIM` without a cull selector. See [PCSX2 `GSRegs.h`](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSRegs.h), [ps2sdk `libgs.h`](https://github.com/ps2dev/ps2sdk/blob/master/ee/libgs/include/libgs.h), and [ps2sdk `draw3d.c`](https://github.com/ps2dev/ps2sdk/blob/master/ee/draw/src/draw3d.c).

This establishes the **generic PS2 GS fact** that rasterizer culling is not a `PRIM` material bit. It does not establish whether **Spartan-specific CPU/VU code** discards faces before submission. Consequently all-material `doubleSided=true` remains opt-in and **LIKELY**, not canonical.

## Alpha correlation

Among the 39 geometry-used records:

- 23 bindings decode as fully opaque;
- one (`MISCALPHA`) has binary alpha;
- eight have partial alpha;
- seven texture bindings remain unresolved.

Type-2 presence versus decoded nonopaque alpha produces:

| Result | Count |
|---|---:|
| True positive | 9 |
| False positive | 3 |
| False negative | 0 |
| True negative | 27 |

The false positives are meaningful, not noise: `CLOUD`, `GIBS`, and `MEDUSA_TOWER` all use type-2 value 5 while their decoded texture alpha is fully opaque. Type 2 therefore likely selects a broader native render path whose semantics can include non-source-alpha blending.

### Type-2 anchors

| Value | Geometry-used examples | Texture alpha | Bounded inference |
|---:|---|---|---|
| 1 | `MISCALPHA` | binary | alpha test/cutout is likely; threshold unknown |
| 2 | `GRKTREE` | partial | foliage render family likely |
| 3 | `APP_BLOOD_02`, `APP_FIRE_BASE`, `RING_GLOW` | partial | effect blend family likely |
| 4 | `FLARE_NOZREAD` | partial | flare/special depth-blend family likely; name is supporting evidence only |
| 5 | `CIRCLE`, `GREENERY`, `GREEK_PATERN`; also opaque `CLOUD`, `GIBS`, `MEDUSA_TOWER` | mixed | broad special/render family; not equivalent to alpha blend |

## High-value materials

### CLOUD

`CLOUD` is MTL index 31, used by one descriptor (48), 1,957 streamed vertices, and 1,728 triangles. Its properties are type 21 value 1, type 2 value 5, resource `CLOUD`, and type 19 value 0. Its native 256×256 decode has alpha 255 at every pixel. The previous statement that it was a “partial-alpha texture” was incorrect and is superseded here.

The V4-8 survey resolves part of this question. CLOUD has six structured V4 tuples forming a dark upper dome and brighter warm lower ring, but byte 3 is `0x80` for all 1,957 vertices. In the common PS2 `/128` convention that is full vertex alpha. Texture alpha and vertex alpha are therefore both full: ordinary source-alpha blending cannot make the shell transparent. Bytes 0–2 are **LIKELY** RGB/color modulation; transparency itself is **LIKELY** supplied by a type-2-selected GS blend/fixed-factor and depth/order family. Exact state remains unknown. See [MODELS_V4_ATTRIBUTES.md](MODELS_V4_ATTRIBUTES.md).

### Vegetation

`GRKTREE` (index 33) uses type-2 value 2 and type 22; 32 descriptors and 8,828 triangles use it. `GREENERY` (index 35) uses type-2 value 5, the unique type-4 value -20, and type 22; 57 descriptors and 1,066 triangles use it. Both images have partial alpha. The experimental standard `BLEND` mapping removes their opaque dark pixel regions, but it does not establish whether the native game used alpha test, blend, or a custom equation.

### Banners and flags

`L0_FLAGS` (index 1) has types 22 and 19 and supplies 43 descriptors / 3,612 triangles. `TEMPLE_FLAGS` (index 12) has no numeric child. Both bound images are opaque. Record data therefore does not support an alpha rule or a shared two-sided field for flags. The all-double-sided GS approximation displays the thin geometry coherently.

### Effects

Type-2 value 3 groups `APP_BLOOD_02`, `APP_FIRE_BASE`, and `RING_GLOW`; value 4 occurs on `FLARE_NOZREAD`; value 5 occurs on `CIRCLE` and `GREEK_PATERN`. Their images have partial alpha, and standard glTF `BLEND` is useful for inspection. `LIGHTNING`, `BEAM`, `APP_MEDUSA`, two light spheres, and `GLOW` remain unresolved texture placeholders, so their record differences cannot yet be validated visually.

## Experimental glTF mapping

The exporter retains `--mtl-render-semantics raw` as its default. `--mtl-render-semantics experimental` applies only:

1. `doubleSided=true` to all selected materials, based on the GS no-cull fact and scene-level diagnostic;
2. `alphaMode=BLEND` when a material has MTL type 2 **and** its confirmed decoded texture has binary or partial alpha;
3. `OPAQUE` otherwise;
4. no `MASK`, no `alphaCutoff`, and no opacity alteration.

The complete controlled export remains exactly 1,338 descriptors, 2,128 batches, 88,314 source records, and 46,336 triangles. It contains 39 double-sided materials: 30 `OPAQUE`, zero `MASK`, and nine `BLEND`. Written glTF validation and exact geometry/UV/material round trip pass. Blender 5.2.1 LTS imports 1,338 objects/meshes, 46,336 polygons, 39 materials, 30 images, zero backface-culled materials, and no missing images.

The experiment removes the systemic culling holes and exposes coherent architecture/terrain. It improves foliage/effect transparency. `CLOUD` remains a white occluding shell, exactly as expected from its opaque pixels. Standard glTF blend ordering/equations are not a faithful substitute for arbitrary PS2 GS `ALPHA` state.

## V4 correlation and GS blend hypotheses

Every geometry record has a paired V4-8 tuple. Byte 3 is globally `0x80`; bytes 0–2 vary coherently by material and space. Type-2 values 3 (`APP_BLOOD_02`, `APP_FIRE_BASE`, `RING_GLOW`) and 4 (`FLARE_NOZREAD`) use the neutral tuple `(127,127,127,128)`, while type-2 value 5 spans both neutral and highly modulated resources. `GRKTREE` (value 2) and `GREENERY` (value 5) retain partial source texture alpha and full vertex alpha, so their transparency is texture-alpha driven even though V4 supplies likely tint/lighting.

The generic GS blend equation is `(A - B) * C + D`, commonly described for color as `(Cs - Cd) * alpha + Cd`. With CLOUD source and vertex alpha both full, that standard equation reduces to opaque source color. Plausible families that can expose the destination instead include additive source color (`Cs + Cd`) or fixed-factor additive color (`Cs * FIX + Cd`). Multiply/subtractive interpretations are weaker against the observed bright cloud-ring intent. This ranking is structural and diagnostic only: no MTL property has been mapped directly to GS `ALPHA` operands or `FIX`.

A local Blender diagnostic exported V4 as glTF-safe `COLOR_0 = min(byte / 128, 1)`. CLOUD values require no clamp. Opaque texture-times-color retained the shell; transparent-plus-emission additive approximations exposed the complete scene while retaining the spatial ring. Geometry stayed at 46,336 polygons. The result explains the failure mode but is not a native mapping and is not a default exporter semantic.

## Confidence and readiness

| Semantic | Classification | Reason |
|---|---|---|
| submitted triangles should be double-sided in a GS-faithful validation | **LIKELY** | GS has no cull bit; scene diagnostic succeeds; pre-GS Spartan culling remains unknown |
| a specific MTL cull/two-sided field | **UNKNOWN** | no numeric field separates candidates |
| type 2 selects an alpha/render family | **STRONG** | 9/9 nonopaque positives, no false negatives, structured values 1–5 |
| native alpha mask for value 1 | **LIKELY** | binary-alpha `MISCALPHA` anchor only |
| exact mask threshold/operator | **UNKNOWN** | no correlated threshold field |
| V4 bytes 0–2 are color/light modulation | **LIKELY** | material and spatial gradients; normal models fail; opt-in COLOR_0 diagnostic is coherent |
| V4 byte 3 is full vertex alpha | **LIKELY Spartan routing; CONFIRMED generic PS2 scale** | globally `0x80`; ps2sdk/gsKit use 128 as 1.0 |
| native alpha blend families for values 2–5 | **LIKELY family, UNKNOWN equations** | repeated foliage/effect anchors; opaque false positives prove broader semantics |
| exact depth-write/additive/multiplicative behavior | **UNKNOWN** | glTF cannot encode arbitrary GS state and the record mapping is incomplete |

Readiness remains **TEXTURED ASSEMBLY VALIDATED**. `LEVEL00 WORLD RECONSTRUCTION COMPLETE` is not justified: culling is presently a platform-derived opt-in approximation, and CLOUD's exact GS blend operands/fixed alpha/depth-write/order state remain unknown. The next single task should recover only the native render-state mapping for MTL type-2 values 2–5 from the executable/VU path; that bounded step now requires Ghidra rather than further asset-only correlation.

## Bounded executable follow-up

The canonical executable has now been imported into Ghidra and investigated along only this render-state path. The LEVEL00 `MODELS.MTL` loader/deserializer is anchored at `0x002c3400` -> `0x002605d0` -> `0x0026d2d0`; a low-level paired-context GS packet builder at `0x002490c0` installs destinations for `TEST_1/2`, `ALPHA_1/2`, and `ZBUF_1/2`. Stock Ghidra lacks R5900 `LQ`/`SQ`, multimedia, and COP2 semantics at both critical regions, so no defensible child-type-2 -> runtime field -> GS payload trace was recovered.

Accordingly all type-2 family states, CLOUD `ALPHA` operands/FIX, alpha threshold, ZMSK, and draw bucket remain **UNKNOWN**. No exporter mapping changed. Full address evidence and processor limitations are documented in [EXEC_RENDER_STATE.md](EXEC_RENDER_STATE.md).
