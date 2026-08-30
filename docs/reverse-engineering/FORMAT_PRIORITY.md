# Proprietary Format Priority

Priorities reflect reconstruction dependencies exposed by LEVEL00, not format completeness. Counts and bytes are for the isolated LEVEL00 sample only.

## P0 — required to reconstruct or render the level

| Extension / target | Files | Bytes | Suspected purpose | Confidence | Dependencies and evidence | Recommended order |
|---|---:|---:|---|---|---|---:|
| `.BIN` / `MODELS.BIN` | 1 | 2,293,536 | primary world geometry/render payload | **LIKELY** | MODELS family, exact-size header, numeric segments, paired AAB/MTL/environment textures | 1 |
| `.AAB` | 1 | 448,048 | world bounds/spatial acceleration | **LIKELY** | `master_L00A`, structured floats/indices, paired MODELS family | 2 |
| `.MTL` / `MODELS.MTL` | 1 | 5,952 | texture/resource/property declarations | **CONFIRMED container; properties UNKNOWN** | 55 records, 41 direct basename joins, exact shared engine records | 3 |
| `.HMP` | 1 | 166,400 | land height/terrain field | **LIKELY** | `WORLD/LAND`, repeated float-like grid, low entropy | 4 |

The first reverse-engineering task should isolate the `MODELS.BIN` header and segment table and correlate its offsets/counts with AAB and MTL. A converter or renderer should wait until those boundaries are demonstrated.

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
| `.FLP` | 1 | 1,136 | MODELS companion | **UNKNOWN** | 14 records, vector-like content |
| `.MVR` | 1 | 1,600 | model-source/variant reference table | **LIKELY** | six embedded `Brazier_Dark.CAS` paths |
| `.INS` | 1 | 32 | MODELS companion | **UNKNOWN** | basename adjacency only; too small to classify |
| `.STL` | 1 | 136 | MODELS index/lookup companion | **UNKNOWN** | small integer table; not standard STL |

Particle TXT definitions are already human-readable and should be used to validate DAT later rather than treated as an unknown format target.

## P3 — optional or already understood presentation data

| Extension / target | Files | Bytes | Role | Status |
|---|---:|---:|---|---|
| `.DIM` | 7 | 4,032 | font measurement tables | structure confirmed; exact semantics secondary |
| localization/name `.TXT` | 30 | 812,747 | UI/dialogue/objective/name tables | readable legacy text; parser useful but not blocking geometry |
| particle/config `.TXT` | 17 | 3,213 | effect dimensions/definitions and gameplay flags | readable; no proprietary decoding required |

TIM2 is standard and strategically important, but it is not a proprietary reverse-engineering target. LEVEL00 confirms additional image types, CLUT modes, and mipmapped environment textures that a later asset pipeline must support.

## Investigation gates

Before declaring any format understood:

- establish header fields and all section boundaries across more than one sample where possible;
- demonstrate cross-file references rather than infer them from extensions alone;
- distinguish counts, byte offsets, indices, flags, floats, and encoded command streams;
- validate PS2-specific packet claims structurally; incidental byte patterns are insufficient;
- defer converters and renderers until bounds checking and reference resolution are evidenced.
