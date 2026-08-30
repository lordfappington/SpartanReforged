# LEVEL00.PAK Gameplay Asset Architecture

Analysis completed on 2026-08-30. Only `DATA/LEVEL00.PAK` was listed and extracted during this task. Comparisons were limited to the already-extracted FE_LANG, FE_TV, and FE_MAIN trees. No other PAK was opened, and no proprietary asset was converted, rendered, modified, or parsed speculatively.

## Archive identity and extraction safety

| Field | Value |
|---|---|
| Source | `game-extracted/disc/DATA/LEVEL00.PAK` |
| Size | 13,652,833 bytes (`0xd05361`) |
| SHA-256 before and after extraction | `e708df44976b93b4d0fa355f850e387f04dee580b27f927f4e906f1f9d095d80` |
| Magic / version | `PAK1` / 1 |
| Declared entries | 640 |
| Alignment | `0x800` |
| Extractor | QuickBMS 0.12.0 with `spartan_total_war.bms` 0.1.1 |
| Destination | `game-extracted/pak/LEVEL00` (ignored) |

QuickBMS list-only mode ran before extraction and returned exit code 0. All 640 entries are ordered by offset, every stored offset is `0x800`-aligned, the first entry begins at `0xf000`, and the final extent ends exactly at archive EOF. The path audit found no absolute or traversal paths, malformed/reserved Windows names, empty components, duplicate destinations, case-insensitive collisions, file/directory collisions, overlaps, or out-of-bounds extents.

Isolated extraction returned exit code 0. Exactly 640 listed files were created, all paths and logical sizes match, no unexpected file appeared, and the source hash remained unchanged. Extracted content totals 12,890,963 bytes. Raw listing, magic output, and inventory reports remain local under `logs/analysis/LEVEL00_*`.

## Complete extension and signature survey

Entropy values are Shannon bits/byte from full files up to 64 KiB or equal head/tail samples for larger files. They are descriptive only; no compressed/encrypted claim is based on entropy alone.

| Extension | Count | Bytes | Size range | Header / median entropy | Classification and evidence |
|---|---:|---:|---:|---|---|
| `.anm` | 461 | 3,820,386 | 1,381–42,181 | `anm1`, 7.38 | **CONFIRMED animation resources:** all files use `anm1`; character/action directories and embedded metadata such as `FRAMES_TO_IMPACT` identify the role. Transform/key encoding unknown. |
| `.tm2` | 58 | 2,472,096 | 256–66,624 | `TIM2`, 6.23 | **CONFIRMED standard PS2 textures:** environment, characters, particles, UI, and fonts. |
| `.txt` | 46 | 1,101,535 | 0–277,524 | textual, 4.96 | **CONFIRMED:** battle tuning, character progression, display flags, particle definitions, resource lists, localization, and names. |
| `.psq` | 39 | 683,940 | 1,116–95,196 | no magic; counts/floats, 6.15 | **LIKELY character mesh/geometry segments:** `CHR_MDLS` location, LOD-like numeric suffixes, STANDARD/SHINEY/SHADOW names, texture adjacency, and repeated vector-like data. Layout unknown. |
| `.bns` | 7 | 2,135 | 305 | `bns2`, 5.86 | **LIKELY humanoid bone/bind data:** character pairing and identical shared files support skeleton compatibility; no names/hierarchy decoded. |
| `.dim` | 7 | 4,032 | 576 | `10 cd...`, 2.75 | **CONFIRMED structure / LIKELY font measurements:** same 576-byte font table family as the front end. |
| `.mph` | 4 | 246,368 | 47,840–75,024 | no magic; repeated counts/floats, 6.12 | **LIKELY facial mesh/morph geometry:** every file is named `FACE.MPH` under named character model directories. |
| `.bin` | 2 | 2,293,564 | 28–2,293,536 | incompatible headers, 3.42 median | **CONFIRMED overloaded extension:** `MODELS.BIN` is a likely world-geometry payload; `CHAR_TYPES.BIN` is exactly seven u32 character IDs. They are not one schema. |
| `.sam` | 2 | 1,245,184 | 589,824–655,360 | `sam2`, 6.07 | **CONFIRMED cutscene animation container role:** CUTSCENE paths, `ANIM_METADATA_CUTSCENE`, and direct ENT filename references. Track encoding unknown. |
| `.aab` | 1 | 448,048 | 448,048 | first u32 equals size, 1.52 | **LIKELY world spatial/bounds structure:** `MODELS` family, `master_L00A` identifier, structured floats/indices, and AAB naming. Exact AABB hierarchy unknown. |
| `.big` | 1 | 2,901 | 2,901 | `big1`, 6.89 | **LIKELY compiled interactive prop/model:** `BRAZIER_DARK`, vector-like data, ENT basename reference, and matching source-model reference in MVR. |
| `.col` | 1 | 49,136 | 49,136 | binary count/size then floats, 5.30 | **LIKELY collision planes:** `OLFS/PLANES.COL` name and repeated plane-like float records. Schema unknown. |
| `.dat` | 1 | 4,114 | 4,114 | binary index/table, 4.09 | **LIKELY compiled particle sample data:** `PARTICLES/SAMPLES.DAT`, adjacent requirements/effect files, and fragments matching effect parameters. |
| `.ent` | 1 | 233,812 | 233,812 | structured binary, 4.53 | **CONFIRMED entity/state graph role:** header offsets and explicit string area cover spawns, cameras, checkpoints, relays, cutscenes, audio, particles, and section change. Record schema unknown. |
| `.flp` | 1 | 1,136 | 1,136 | first u32 equals size, 2.67 | **UNKNOWN MODELS companion:** 14 declared items and matrix/vector-like values; exact role unknown. |
| `.hmp` | 1 | 166,400 | 166,400 | float-like grid, 2.22 | **LIKELY terrain/height field:** `WORLD/LAND.HMP`, low-entropy repeated samples, and spatial context. Dimensions/units unknown. |
| `.ind` | 1 | 23,940 | 23,940 | first u32 = size minus 4, 0.58 | **LIKELY waypoint index/connectivity table:** explicit `WAYPT_INDICES` basename and adjacency to PT2. |
| `.ins` | 1 | 32 | 32 | size-like fields, 0.45 | **UNKNOWN MODELS companion:** too little evidence for instance semantics despite the suffix. |
| `.mtl` | 1 | 5,952 | 5,952 | known length-delimited structure, 2.39 | **CONFIRMED resource declaration/property container:** same format as front-end MTL; 55 records. Property meanings remain unknown. |
| `.mvr` | 1 | 1,600 | 1,600 | first u32 equals size, 3.58 | **LIKELY model-source/variant reference table:** six entries include `Brazier_Dark.CAS` source-repository paths. Runtime semantics unknown. |
| `.psw` | 1 | 2,888 | 2,888 | counts/floats, 5.99 | **LIKELY weighted/skinned geometry:** exact filename `MULTIWEIGHTED.PSW` and enabled `mutiweighted` display flag. Weight layout unknown. |
| `.pt2` | 1 | 81,628 | 81,628 | size/offset fields then float vectors, 5.26 | **LIKELY 3D waypoint records:** exact `WAYPTS3D` basename, coordinate-like floats, and paired IND connectivity. |
| `.stl` | 1 | 136 | 136 | count and small indices, 1.36 | **UNKNOWN MODELS companion:** one small index table; not assumed to be standard STL geometry. |

The 19 extensions new relative to FE_LANG/FE_TV/FE_MAIN are ANM, PSQ, BNS, MPH, BIN, SAM, AAB, BIG, COL, DAT, ENT, FLP, HMP, IND, INS, MVR, PSW, PT2, and STL. None is a recognized standard interchange format merely because its suffix resembles one.

## Directory architecture

| Namespace | Files | Bytes | Evidence-backed role |
|---|---:|---:|---|
| `DATA/ANIMS` | 461 | 3,820,386 | common and character/action-specific animation library |
| `DATA/CHR_MDLS` | 65 | 1,530,604 | Spartan/equipment and level NPC character models, textures, bone/bind data, faces, and display flags |
| `DATA/ENV/LEVEL00/WORLD` | 30 | 3,837,821 | world model family, terrain/height field, material/resource declarations, environment textures, interactive brazier |
| `DATA/ENV/LEVEL00/ENTITIES` | 3 | 234,425 | entity/state graph, character dependency IDs, progression configuration |
| `DATA/ENV/LEVEL00/OLFS` | 3 | 154,704 | collision planes and 3D waypoint/connectivity candidates |
| `DATA/ENV/LEVEL00/CUTSCENE` | 2 | 1,245,184 | Leonidas and Sparky cutscene animation containers |
| `DATA/ENV/LEVEL00/PARTICLES` | 6 | 6,078 | level effect definition and compiled sample data |
| `DATA/ENV/LEVEL00/TEXT` | 7 | 477,492 | seven localized level dialogue/objective tables |
| `DATA/ENV/LEVEL00/AMBIENT` | 1 | 10 | empty/blank ambient text placeholder |
| `DATA/GENERIC_GRAPHICS/PARTICLES` | 8 | 211,136 | shared particle texture pages |
| `DATA/GENERIC_GRAPHICS/TEXTURES` | 13 | 281,504 | shared gameplay/UI/effect textures |
| `DATA/PARTICLES` | 10 | 1,348 | shared particle-page dimensions and base effect/material lists |
| `DATA/TEXT` | 30 | 812,747 | global localized tables, identical character-name map copies, and seven font pairs |
| `DATA/BATTLE.TXT` | 1 | 277,524 | global battle/AI/stat tuning snapshot |

The largest files are `MODELS.BIN` (2,293,536), `LEONIDAS_L00_CUTSCENE.SAM` (655,360), `SPARKY_L00_CUTSCENE.SAM` (589,824), `MODELS.AAB` (448,048), `BATTLE.TXT` (277,524), and `TEST.ENT` (233,812). The smallest are a zero-byte texture-requirements list, a 2-byte additional-materials list, the 10-byte ambient placeholder, the 13-byte effect list, and the 28-byte character-ID table.

## Resource families and archive ordering

Sixteen basenames occur with multiple extensions:

- `MODELS`: AAB, MTL, BIN, STL, FLP, MVR, and INS, adjacent as one world family around the environment textures.
- `APP_PS2FONT`: seven TM2/DIM pairs.
- `AARCH2`, `SHOPL2`, and `SSWRD2`: BNS/PSQ character pairs.
- `CASTR`, `POLLX`, and `LNIDS`: BNS plus matching character TM2.
- `APP_BLOOD`, `APP_DIRT`, `APP_ENV`, `APP_FIRE`, `APP_GLOWBALLS`, `APP_PROJECTILE`, `APP_SMOKE`, and `APP_TORCH`: shared particle TM2 plus dimension/config TXT.

The `MODELS` family is the central world candidate. `MODELS.BIN`, AAB, FLP, MVR, and INS all begin with size/count-like fields; BIN, AAB, FLP, MVR, and INS repeat their exact file size in the first u32. AAB names `master_L00A`. MVR declares six entries and embeds source paths ending in `Brazier_Dark.CAS`. `BRAZIER_DARK.BIG` is then named directly by the entity graph, providing a source-reference → compiled prop → entity-instance correlation. STL is a small index table, not the standard triangle STL format.

Thirty duplicate hash groups cover 79 files. Important reuse includes five identical NPC BNS files, shared animation clips across weapon/action directories, identical bow shadow PSQs, identical NAMES tables in all eight languages, two font language groups, and the same `NON_LINEAR_REMAPPING.TM2` used by all three analyzed front-end sections.

## Texture architecture

Gameplay continues to use TIM2, but adds formats not seen in the front end. All 58 files are TIM2 version 4 with one picture. They span 16×16 through 256×256 and include image types 3, 4, and 5, CLUT types 0, 1, and 3, 16- or 256-entry palettes where indexed, and either one or four mip levels.

- Twenty of the 21 world pages use 4-bit indexed image type 4; 18 of those have four mip levels, directly confirming mipmapped environment textures.
- Nine `CHR_MDLS` pages are 256×256, 8-bit indexed character/character-related textures based on directory and basename pairing.
- Eight particle pages range from 32×32 to 256×256 and pair with TXT frame/page dimensions.
- Generic pages cover destructables, pickups, blood, gibs, arrows, rings, flare, UI pages, and an `ENV.TM2` image-type-3 direct-color candidate.
- Seven 256×256 APP_PS2FONT atlases pair with the known 576-byte DIM layout.

Only `NON_LINEAR_REMAPPING.TM2` is hash-identical to FE_MAIN, FE_TV, and FE_LANG. No other LEVEL00 file matches those front-end trees by SHA-256. No texture was converted, viewed, or exported, so lightmap/sky classifications are limited to explicit names: `CLOUD` is sky-like and the MTL light/glow records are effects, but no file is asserted to be a lightmap.

## World geometry, models, and materials

`MODELS.BIN` is the leading world-geometry candidate. It is the largest non-cutscene binary, its first u32 equals its exact length, it sits in the seven-file MODELS family, and it is paired with environment texture declarations and a spatial AAB file. Its header includes additional counts/offset-like values and it contains large repeated numeric regions, but vertex/index/strip fields are not yet decoded.

Character geometry is more clearly partitioned:

- PSQ files occur only beneath `CHR_MDLS`, commonly as numbered `0`–`4` sets or STANDARD/SHINEY/SHADOW variants. Their headers contain plausible element counts followed by repeated float/vector-like records. This is strong evidence for geometry segments or render passes, but not enough to label exact vertex/index fields.
- The Spartan body combines `STANDARD.PSQ`, `MULTIWEIGHTED.PSW`, `FACE.MPH`, `TEXTURE.TM2`, `TEXTURE_EXTRAS.TM2`, `BONES.BNS`, and display flags. This is the best character-model study family.
- Four `FACE.MPH` files begin with matching first/second counts and occur only for Spartan, Castor, Pollux, and Leonidas, supporting facial mesh or morph data.
- PSW occurs only as `MULTIWEIGHTED.PSW`, with its display attribute enabled; it is the strongest skin-weight candidate.

`MODELS.MTL` has the same confirmed hierarchy as the front-end files: record area at `0x250`, 55 names, variable top-level records, and counted child/property blocks, with a complete walk ending at EOF. Four shared engine records—`AMBIENT_FOLIAGE`, `NON_LINEAR_REMAPPING`, `GLOW_BUFFER_END`, and `APP_BLACKBARS`—are byte-identical to all three front-end MTLs. Forty-one MTL names directly match packaged texture/config stems; other records are aliases or engine resources, including `PICKUPS_2SIDED`, `APP_FIRE_BASE`, `UI_PAGE3` aliasing `ui_page2`, and light/glow properties. Numeric material/render semantics remain unknown.

No validated VIF packet, GIF tag, DMA chain, VU microprogram, triangle strip, UV field, normal field, or bounding-box schema is claimed. TIM2 image/CLUT type fields are confirmed PS2 texture evidence; `APP_PS2FONT` is explicitly platform-named. PSQ/PSW names may also be platform-oriented, but the acronym has not been established.

## Skeleton and animation architecture

All 461 ANM files use `anm1`, a `0x10` header-size-like field, a varying field from 5 to 155 consistent with clip-dependent counts/timing, and a final header field of 3 in 460 samples. Paths organize COMMON clips and Greek/Roman/Mars/Minotaur/Hydra/Crassus character/action sets. Embedded metadata includes `ANIM_METADATA`, `FRAMES_TO_IMPACT`, X/Z impact offsets, ladder/get-up/loop markers, weapon-change frames, and attachment identifiers such as `WEAPON_SPARTAN_TWIN_SWORD_R`. Animation purpose is therefore **CONFIRMED**, while frames, tracks, time units, and transform compression remain unknown.

All seven BNS files use `bns2`, are exactly 305 bytes, and contain transform-like floats but no readable bone names. Castor, Pollux, Leonidas, Spartan Hoplite, and Spartan Swordsman share one exact BNS hash; Athenian Archer and Spartan body each differ. This supports shared humanoid skeleton/bind compatibility classes. It does not establish bone count, hierarchy, or skin-weight mapping.

The two SAM files use `sam2`, contain `ANIM_METADATA_CUTSCENE`, and are named and referenced as Leonidas/Sparky cutscene assets. Their header field of 120 is shared; later counts differ. They likely aggregate long cutscene tracks, but track-to-entity mapping remains unknown.

## Entity, scripting, AI, collision, and navigation

`TEST.ENT` is LEVEL00's central gameplay orchestration candidate. Its binary header contains its exact file size and offsets including a string area at `0x38320`. That area has 227 recovered NUL-terminated identifiers covering:

- `PLAYERSTART_L00A`, `THE_SPARTAN`, `CHECKPOINT_INTRO`, and section start/end state managers;
- NPC spawners, Leonidas and Sparky positions, squad and `CHAR-ZONE` identifiers;
- 25+ named cutscene cameras and matching position/relay markers;
- both SAM filenames and `MOCAP_L00A`;
- `MARS_SMOKE2`, interactive `BRAZIER_DARK`, use packages, markers, and camera targets;
- voice identifiers `L0A_01_LE_A` etc., `L0A_CUTSCENE_MUSIC`, default cut-in/out music, and arena-speaker references;
- `_SWITCHLEVEL_L00A_GO_TO_LEVEL_01` and literal `LEVEL01`.

`CHAR_TYPES.BIN` is a particularly useful cross-table key. Its seven little-endian u32 values are 0, 8, 11, 12, 14, 15, and 18. Those indices resolve through every identical `NAMES.TXT` copy to The Spartan, Spartan Hoplite, Spartan Swordsman, Athenian Archer, Castor, Pollux, and Leonidas—the character model families packaged in LEVEL00. This demonstrates a numeric-ID → global name table → section-local model/animation dependency chain.

`BATTLE.TXT` is a 6,207-line global gameplay tuning snapshot with 75 active CHARACTER sections. It defines health, mass, combat modules, aggression/flanking/surrounding behavior, attacker counts, attack probability/timing, weapon damage, impact levels/remapping, blocking/dodging, pickups, gore, and boss/special-character flags. This is strong combat/crowd-AI configuration evidence, but it is not a spatial navigation file.

Spatial AI candidates are explicit: `WAYPTS3D.PT2` contains coordinate-like floats and a header count of 87; `WAYPT_INDICES.IND` is a low-entropy connectivity/index candidate; and `PLANES.COL` contains repeated plane-like float records. Together with entity spawners, squads, character zones, and BATTLE attacker/surrounding rules, they form the strongest crowd/AI spatial family. Exact graph nodes, edges, collision primitives, and coordinate units are not decoded.

`LAND.HMP` is likely a terrain/height field, while AAB is likely spatial bounds/acceleration data. Neither is yet proven to be collision geometry. Cameras and placement are represented through ENT identifiers and binary records; no separate human-readable scene script exists.

## Text, audio, effects, and cross-platform evidence

`CHARACTER_PROGRESSION.TXT` enables sword, bow, and shield, disables spear/axe/twin swords for this section, sets Spartan display 1, and progression class 1. Five display files select standard, multiweighted, shiny, and metallic character render variants.

Seven `LEVEL01.TXT` files each have 217 synchronized keys, including six `L0A` entries plus later level dialogue/objective keys; the filename/content mismatch indicates a bundled localization snapshot rather than LEVEL00-only text. English contains 158 non-empty `Audio File Name` comments. Seven GLOBALS files have 321 ordered keys (320 unique), while all eight 19,297-byte NAMES files are byte-identical character-ID maps. Localized high bytes use legacy single-byte encodings. Japanese contains NAMES/GLOBALS only and again lacks the complete localized section table/font pair present for the other seven languages.

LEVEL00 contains no audio payload. ENT supplies symbolic voice and music identifiers, and localized tables annotate external audio names. This is consistent with audio being resolved from E_DATA or another external sound system, but no E_DATA path or numeric sound-bank mapping is present and E_DATA was not opened.

The particle system is unusually transparent. Eight shared TM2 pages pair by basename with TXT frame/page dimensions. `BASE_EFFECT_MATERIALS.TXT` lists those eight materials, `BASE_EFFECTS.TXT` declares capacity-like counts for blood, torches, sparks, trails, gibs, shrines, highlights, breath, and other effects, and `MARS_SMOKE2.TXT` provides a nested EMITTER/PARTICLE definition with lifetime, velocity, density, size, color, alpha, resistance, rotation, turbulence, and interpolation timing. `SAMPLES.DAT` is the compiled/lookup companion candidate.

Cross-platform localization keys explicitly include Xbox and NGC controls while `APP_PS2FONT` and TIM2 identify PS2-specific presentation data. Core ANM, ENT, BATTLE, and particle definitions contain no reliable PS2/Xbox/GameCube markers, supporting—but not proving—a shared-data layer with platform-specific rendering/input resources. Incidental byte matches for strings such as `VIF`, `GIF`, or `DMA` inside arbitrary binary data were rejected as evidence.

## Architecture conclusion and Rosetta Stone assessment

LEVEL00 is a strong initial gameplay Rosetta Stone. It contains environment/world candidates, mipmapped textures, stable MTL declarations, a complete character subset, bone/bind candidates, hundreds of animation clips, cutscene tracks, an entity/state graph, collision and waypoint candidates, combat/crowd tuning, particles, localization/fonts, and external audio references. It is especially valuable because several links are explicit rather than inferred: character IDs resolve through NAMES to packaged model families; ENT names SAM/particle/prop/audio/next-section resources; particle TXT files pair with same-named TIM2 files; and MTL names map to world/effect/UI textures.

The archive is not self-sufficient for audio, and no actual audio data is included. Some global tables and common animation/effect assets are duplicated into the section snapshot, while the sound system remains external. Geometry, entity records, skeleton hierarchy, skinning, animation tracks, collision, and waypoint schemas are identified only by role and must still be reverse-engineered.

The most strategically important next target is `MODELS.BIN`: establish its header, segment/offset table, and relationship to `MODELS.AAB`, MTL texture records, and companion files using read-only structural analysis. Do not write a converter or renderer until those boundaries and references are evidenced.
