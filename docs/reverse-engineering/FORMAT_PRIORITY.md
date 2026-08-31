# Proprietary Format Priority

Priorities reflect reconstruction dependencies exposed by LEVEL00, not format completeness. Counts and bytes are for the isolated LEVEL00 sample only.

## P0 — required to reconstruct or render the level

| Extension / target | Files | Bytes | Suspected purpose | Confidence | Dependencies and evidence | Recommended order |
|---|---:|---:|---|---|---|---:|
| `.BIN` / `MODELS.BIN` | 1 | 2,293,536 | descriptor-indexed PS2 VIF geometry/render streams | **CONFIRMED container/VIF/topology/UV; VISUALLY VALIDATED** | 1,338 descriptors, 2,128 batches, 88,314 vertices, 46,336 triangles; descriptors 118/5 validate coordinates, winding, source V, and image mapping | 1 |
| `.AAB` | 1 | 448,048 | world spatial quadtree and BIN descriptor lookup | **CONFIRMED tree/reference/bounds relationship; trailing fields partial** | Seven-level 4-way tree; 1,224 unique leaf references exactly cover descriptors 114–1337 and all referenced geometry fits its cell bounds | 2 |
| `.MTL` / `MODELS.MTL` | 1 | 5,952 | ordered resource/material declarations | **CONFIRMED binding, TEST/ZBUF/ALPHA controls, CPU pass order, and MODELS PRIM context** | child type 2 selects TEST/ZBUF, child type 16 selects ALPHA; resident VU1 supplies common ABE-on/context-2 PRIM | 3 |
| `.HMP` | 1 | 166,400 | land height/terrain field | **LIKELY** | `WORLD/LAND`, repeated float-like grid, low entropy | 4 |

Container segmentation is complete. Remaining P0 geometry work is now:

1. **P0a — topology control: COMPLETE for LEVEL00.** W `0x8000` suppresses the current triangle without resetting strip history; source-vertex parity continues.
2. **P0b — minimum attribute semantics: COMPLETE and visually validated.** V2-16 is signed Q4.12 (`raw / 4096`) with source V orientation. V4-8 is confirmed routed to GS RGBAQ; bytes 0–2 are RGB inputs and byte 3 is globally full-scale alpha `0x80`.
3. **P0c — material semantics (world baseline complete):** type 2 constructs alpha/depth-test state, type 16 constructs the blend equation, the MODELS VU route supplies ABE-on/context-2 triangle-strip PRIM, and the texture loader supplies RGBA/MODULATE TEX0. CLOUD is confirmed as an opaque V4-coloured dome; exact non-core effect mappings remain follow-up work.
4. **P0d — spatial placement:** retain the confirmed cell-bounds/reference containment and resolve only the remaining AAB leaf/trailing/culling fields.

The bounded, read-only MODELS pipeline is **LEVEL00 WORLD RECONSTRUCTION COMPLETE** for the asset-preservation milestone. All 30 unique strongly bound geometry TIM2 textures attach correctly, Blender preserves all 46,336 polygons, and source-derived V4/TEX0/TEST/ZBUF/ALPHA state explains CLOUD as an opaque coloured dome. Standard glTF still cannot express every PS2 alpha-test failure or blend equation exactly; seven unresolved special bindings and repeat-versus-mirror remain explicit secondary limitations.

## P1 — required for characters and functional gameplay

| Extension / target | Files | Bytes | Suspected purpose | Confidence | Dependencies and evidence | Recommended order |
|---|---:|---:|---|---|---|---:|
| `.ENT` | 1 | 233,812 | entity placement/state/mission graph | **CONFIRMED role** | explicit strings for spawns, cameras, cutscenes, effects, audio, transition; record layout unknown | 5 |
| `.PSQ` | 39 | 683,940 | character/equipment geometry segments | **LIKELY** | CHR_MDLS-only, render/LOD naming, counts/floats, paired textures | 6 |
| `.PSW` | 1 | 2,888 | weighted/skinned geometry | **LIKELY** | `MULTIWEIGHTED` filename and enabled display flag | 7 |
| `.BNS` | 7 | 2,135 | bone/bind/skeleton compatibility data | **LIKELY** | `bns2`, character pairing, five-file identity group, transform-like floats | 8 |
| `.ANM` | 461 | 3,820,386 | character/action animation clips | **CONFIRMED role** | `anm1`, paths, impact/weapon metadata | 9 |
| `.MPH` | 4 | 246,368 | facial mesh/morph data | **LIKELY** | all named `FACE.MPH`, character adjacency, counts/floats | 10 |
| `.SAM` | 2 | 1,245,184 | cutscene animation tracks | **CONFIRMED role** | `sam2`, cutscene metadata and ENT references | 11 |
| `.COL` | 1 | 49,136 | collision planes | **LIKELY** | `PLANES.COL`, plane-like floats | 12 |
| `.PT2` + `.IND` | 2 | 105,568 | 3D waypoints plus connectivity | **LIKELY** | exact basenames, adjacency, coordinates and low-entropy indices | 13 |
| `.BIN` / `CHAR_TYPES.BIN` | 1 | 28 | section character dependency IDs | **CONFIRMED** | seven u32 values resolve exactly through NAMES to packaged model families | 14 |

ENT should be studied before animation internals if the immediate goal is a playable scene graph; PSQ/PSW/BNS/ANM should be studied together if the immediate goal is a character prototype.

## P2 — secondary gameplay and presentation systems

| Extension / target | Files | Bytes | Suspected purpose | Confidence | Dependencies and evidence |
|---|---:|---:|---|---|---|
| `.BIG` | 1 | 2,901 | compiled interactive prop/model | **LIKELY** | `big1`, BRAZIER_DARK ENT link, MVR source path |
| `.DAT` | 1 | 4,114 | compiled particle samples/lookup | **LIKELY** | particle directory and parameter fragments |
| `.FLP` | 1 | 1,136 | transform/parameter companion | **CONFIRMED 14×80 structure; role LIKELY** | 16-byte header plus fourteen matrix-like 80-byte records; exact sequences recur in MVR |
| `.MVR` | 1 | 1,600 | model-source/variant reference table | **CONFIRMED 6×264 structure; role LIKELY** | six fixed records with `Brazier_Dark.CAS` path and FLP-compatible transform data |
| `.INS` | 1 | 32 | MODELS companion | **UNKNOWN** | eight u32 values `(32,0,32,0,0,32,0,0)`; no proven join |
| `.STL` | 1 | 136 | 32-slot MTL lookup companion | **CONFIRMED structure/reference; purpose UNKNOWN** | eight active slots resolve exactly to MTL particle records 40–47; not standard STL |

Particle TXT definitions are already human-readable and should be used to validate DAT later rather than treated as an unknown format target.

## P3 — optional or already understood presentation data

| Extension / target | Files | Bytes | Role | Status |
|---|---:|---:|---|---|
| `.DIM` | 7 | 4,032 | font measurement tables | structure confirmed; exact semantics secondary |
| localization/name `.TXT` | 30 | 812,747 | UI/dialogue/objective/name tables | readable legacy text; parser useful but not blocking geometry |
| particle/config `.TXT` | 17 | 3,213 | effect dimensions/definitions and gameplay flags | readable; no proprietary decoding required |

TIM2 is standard and strategically important, but it is not a proprietary reverse-engineering target. The geometry-required LEVEL00 subset is operational and independently pixel-verified; unrelated image-type-3 and other TIM2 combinations remain outside scope.

## Investigation gates

Before declaring any format understood:

- establish header fields and all section boundaries across more than one sample where possible;
- demonstrate cross-file references rather than infer them from extensions alone;
- distinguish counts, byte offsets, indices, flags, floats, and encoded command streams;
- validate PS2-specific packet claims structurally; incidental byte patterns are insufficient;
- defer converters and renderers until bounds checking and reference resolution are evidenced.
