# MODELS.MTL Render-Semantics Study

## Scope and result

This study is limited to face culling/two-sided rasterization and alpha test/blend behavior in the canonical LEVEL00 `MODELS.MTL`. It does not assign names to unrelated properties or claim a complete MTL schema.

The canonical file is 5,952 bytes with SHA-256 `57283516FC3CC8589EEC4817CF8C25DC3FF0CC2185E4FF99E262FA6F3A4A54B2`. Its header points to 55 ordered, length-delimited records at `0x250`; the strict record walk ends exactly at EOF. All record headers have zero at offsets `+0x08` and `+0x0c`. Thirty-nine records are selected by 1,338 MODELS descriptors.

Conclusions:

- **CULL/TWO-SIDED — LIKELY platform mapping, no MTL selector identified.** The PS2 GS `PRIM` state has no face-culling field. An opt-in all-`doubleSided` glTF experiment removes the systemic holes while preserving all geometry. Spartan could still cull before GS submission, so this is not a confirmed per-material native rule.
- **ALPHA/DEPTH-TEST FAMILY — CONFIRMED for child type 2.** Executable data flow maps the parsed type-2 byte to material `TEST_2` and `ZBUF_2` payloads.
- **BLEND EQUATION FAMILY — CONFIRMED for child type 16.** Value 0/default constructs standard source-alpha and value 1 constructs source-alpha additive `ALPHA_2`; type 2 does not choose the equation.
- **ALPHA TEST — CONFIRMED per type-2 family.** Values 1, 2, and 5 use distinct operators/references; values 3 and 4 use `AFAIL=RGB_ONLY` and suppress depth writes.
- **CULL/TWO-SIDED — still LIKELY/UNKNOWN.** No material cull selector or pre-GS cull path was recovered.

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

The false positives are meaningful, not noise: `CLOUD`, `GIBS`, and `MEDUSA_TOWER` all use type-2 value 5 while their decoded texture alpha is fully opaque. Executable analysis now explains the correlation: type 2 selects alpha/depth testing, while child type 16 independently selects `ALPHA_2`.

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

The V4-8 survey and bounded executable trace resolve this question. CLOUD has six structured V4 tuples forming a dark upper dome and brighter warm lower ring; byte 3 is `0x80` for all 1,957 vertices. Runtime TEX0 is RGBA/MODULATE, and its PSMCT32 CLUT supplies full PS2 alpha `0x80`. Modulation therefore produces fragment alpha `0x80`; the GEQUAL/AREF `0x80` test passes, and the blend equation reduces to `Cs`. CLOUD is an opaque V4-coloured dome. The white shell in texture-only validation is explained by the missing confirmed V4 RGB input, not a missing transparency mode. See [GS_TEXTURE_ALPHA_PATH.md](GS_TEXTURE_ALPHA_PATH.md).

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

The generic GS blend equation is `(A - B) * C + D`. Executable analysis confirms that child type 16 value 0/default builds `(Cs-Cd)*As+Cd`, while value 1 builds `Cs*As+Cd`; both payloads carry FIX `0x80`, but neither selects FIX as C. CLOUD has no child 16 and therefore uses the standard source-alpha payload, disproving the earlier fixed-factor/additive material hypothesis.

A local Blender diagnostic exported V4 as glTF-safe `COLOR_0 = min(byte / 128, 1)`. CLOUD values require no clamp. Opaque texture-times-color retained the shell; transparent-plus-emission additive approximations exposed the complete scene while retaining the spatial ring. Geometry stayed at 46,336 polygons. The result explains the failure mode but is not a native mapping and is not a default exporter semantic.

## Confidence and readiness

| Semantic | Classification | Reason |
|---|---|---|
| submitted triangles should be double-sided in a GS-faithful validation | **LIKELY** | GS has no cull bit; scene diagnostic succeeds; pre-GS Spartan culling remains unknown |
| a specific MTL cull/two-sided field | **UNKNOWN** | no numeric field separates candidates |
| type 2 selects alpha/depth-test state | **CONFIRMED** | child byte reaches `FUN_00257cb0`, which constructs TEST_2/ZBUF_2 |
| native alpha test for value 1 | **CONFIRMED** | EQUAL, AREF `0x80`, AFAIL KEEP |
| alpha-test operators/references | **CONFIRMED** | recovered for values 0–5; type-3 alternate depends on child 17 |
| V4 bytes 0–2 are color/light modulation | **LIKELY** | material and spatial gradients; normal models fail; opt-in COLOR_0 diagnostic is coherent |
| V4 byte 3 is full vertex alpha | **CONFIRMED Spartan VU/GS routing** | emitted unchanged as RGBAQ alpha; globally `0x80` |
| child type 16 blend families | **CONFIRMED for values 0/default and 1** | standard-alpha and source-alpha-additive ALPHA_2 payloads recovered |
| depth-write behavior | **CONFIRMED for type 2 values 0–5** | values 3/4 set ZMSK; others clear it |
| material submission order | **CONFIRMED** | three material-index ranges; CLOUD is in `[21,total)` after ordinary world records |
| type 2 directly controls ABE | **REJECTED for MODELS route** | common VU tag template supplies ABE=1; type 2 controls TEST/ZBUF |
| PRIM.ABE and draw ordering | **CONFIRMED** | ABE=1/context2; CLOUD follows ordinary range without recovered depth sort |

Readiness is **LEVEL00 WORLD RECONSTRUCTION COMPLETE** for the world asset-preservation milestone. CLOUD's opacity is now source-derived rather than an unresolved artifact. Seven special/template texture bindings and exact non-core GS effects remain explicit limitations, not blockers to the world baseline.

## Bounded executable follow-up

Validated R5900 analysis supersedes the stock-Ghidra blocker. The path `0x002c3400` -> `0x002605d0` -> `0x0026d2d0` -> `0x00257cb0` proves child type 2 controls TEST/ZBUF and child type 16 controls ALPHA. CLOUD uses raw ALPHA `0x0000008000000044`, TEST `0x5380b`, and ZMSK 0. VU1 confirms ABE/context 2 and full vertex alpha; the texture loader confirms RGBA/MODULATE and direct PSMCT32 CLUT alpha. Standard glTF still cannot express all GS test-failure semantics, so native state remains preserved in research metadata rather than misrepresented. Full evidence is in [EXEC_RENDER_STATE.md](EXEC_RENDER_STATE.md), [VU1_MODELS_RENDER.md](VU1_MODELS_RENDER.md), and [GS_TEXTURE_ALPHA_PATH.md](GS_TEXTURE_ALPHA_PATH.md).
