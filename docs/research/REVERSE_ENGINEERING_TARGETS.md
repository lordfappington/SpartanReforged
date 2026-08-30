# Reverse-Engineering Targets

Candidate targets are based only on disc filenames, standard headers, and safe list-only archive tables. “Likely” classifications are hypotheses for later testing, not understood formats.

## EXECUTABLE / CODE

- `SLES_533.93` — **CONFIRMED:** main MIPS ELF32 PS2 executable. Future Ghidra target; not analyzed in this task.
- `IOP/*.IRX` — **CONFIRMED:** ten ELF-based IOP modules. Candidate subsystem boundaries include disc streaming, memory-card access, controller/SIO2, and sound, inferred from conventional module names.

## ARCHIVES

- `GENERAL.PAK` — **CONFIRMED:** PAK1, 2 entries successfully extracted into an isolated ignored directory; contains the section manifest and global sound configuration.
- `E_DATA.PAK` — **CONFIRMED:** PAK1, 12,689 listed sound-tree entries.
- `DATA/FE_LANG.PAK` — **CONFIRMED:** PAK1, 32 entries safely listed and extracted in isolation; contains language tables, font resources, front-end script/material data, textures, and memory-card icon assets.
- `DATA/FE_TV.PAK` — **CONFIRMED:** PAK1, 79 entries safely listed, extracted, inventoried, analyzed, and compared with FE_LANG.
- `DATA/FE_MAIN.PAK` — **CONFIRMED:** PAK1, 114 entries safely listed, extracted, inventoried, and compared with FE_LANG/FE_TV; adds MPEG-2 `.PSS` video and a large main-menu script.
- `DATA/LEVEL00.PAK` — **CONFIRMED:** PAK1, 640 entries safely listed, extracted, inventoried, and architecture-mapped; first gameplay sample.
- The other `DATA/LEVEL*.PAK`, `DATA/ARENA*.PAK`, the other two `DATA/FE_*.PAK` files, and `IOP/GENERAL.PAK` — **CONFIRMED:** PAK1 containers; contents not listed.

## TEXTURES

- `DATA/FE_LANG.PAK` — **CONFIRMED:** 12 single-picture, 256-color TIM2 textures from 16×16 through 256×256; includes eight font atlases.
- `DATA/FE_TV.PAK` — **CONFIRMED:** 35 single-picture, 8-bit indexed TIM2 textures from 16×16 through 512×512; includes 32 font atlases.
- `DATA/FE_MAIN.PAK` — **CONFIRMED:** 68 single-picture, one-mip, 8-bit indexed TIM2 textures from 16×16 through 512×512; 32 font atlases plus UI cards, maps, icons, logos, and effect pages.
- `DATA/LEVEL00.PAK` — **CONFIRMED:** 58 one-picture TIM2 resources using image types 3/4/5, CLUT types 0/1/3, 16/256 colors, and one/four mip levels; covers world, character, particle, UI, and font resources.
- Other `DATA/FE_*.PAK`, `DATA/LEVEL*.PAK`, and `DATA/ARENA*.PAK` files — **UNKNOWN candidates:** not opened.

## MODELS

- `LEVEL00/.../WORLD/MODELS.BIN` — **P0 CONFIRMED and operationally exported:** strict parsing reconstructs 1,338 descriptor meshes from 2,128 batches, retains all 88,314 position/Q4.12 UV records and 39 material groups, and emits exactly 46,336 triangles to validated glTF. Exact byte-level accessor round-trip and Blender import pass. V4-8 remains unknown and material/render fidelity is not claimed.
- `LEVEL00/.../WORLD/MODELS.AAB` — **P0 CONFIRMED structure/reference/bounds:** complete seven-level 4-way spatial tree; leaf lists enumerate static BIN descriptors 114–1337 exactly once, and every referenced descriptor's vertices fit its associated cell bounds.
- `LEVEL00/.../WORLD/MODELS.MTL` — **CONFIRMED numeric join:** BIN descriptor high-u16 values select ordered resource records; 39 record indices are used.
- `LEVEL00/.../WORLD/MODELS.STL` — **CONFIRMED lookup structure:** 32 slots, eight of which select MTL particle records 40–47.
- `LEVEL00/.../WORLD/MODELS.FLP` / `MODELS.MVR` — **CONFIRMED fixed structures / LIKELY relationship:** fourteen 80-byte FLP transform records and six 264-byte MVR source/variant records share exact record data.
- LEVEL00 character `.PSQ` / `.PSW` / `.MPH` families — **P1 LIKELY:** render/LOD geometry, weighted geometry, and facial mesh/morph candidates respectively.
- `LEVEL00/.../WORLD/BRAZIER_DARK.BIG` — **P2 LIKELY:** compiled interactive prop/model correlated with ENT and MVR source identity.
- World positions, ADC strip topology, source winding, material assignment, and V2-16 UV mapping are established and reconstructed outside the PS2 runtime. The exporter exposes source/Z-reflection coordinates, source/reverse winding, and source/flipped V explicitly. Target-specific visual convention validation, V4-8 meaning, exact MTL sampler properties, and character vertex/index/weight schemas remain open.

## ANIMATIONS

- LEVEL00 `.ANM` — **CONFIRMED role / P1:** 461 `anm1` character/action clips with impact, loop, ladder, timing, and weapon-attachment metadata; track encoding unknown.
- LEVEL00 `.BNS` — **LIKELY / P1:** seven `bns2` bone/bind candidates; five files form an exact humanoid compatibility group.
- LEVEL00 `.SAM` — **CONFIRMED role / P1:** two `sam2` cutscene animation containers directly referenced by ENT.

## LEVEL DATA

- `DATA/LEVEL00.PAK` through `DATA/LEVEL14.PAK`, including `LEVEL07D.PAK` — **LIKELY:** level-specific content; `SECTIONS.TXT` confirms matching logical section names and `DATA\ENV\level*` paths.
- `DATA/ARENA*.PAK` — **LIKELY:** arena-specific content; `SECTIONS.TXT` confirms matching arena section names and `DATA\ENV\arena*` paths.
- `DATA/FE_LANG.PAK` — **CONFIRMED:** boot-time language-selection front end; `SECTIONS.TXT` declares it as `start_section`, and its script loads `fe_tv` after selection.
- `DATA/FE_TV.PAK` — **CONFIRMED:** video-mode/progressive-scan front end reached from FE_LANG; conditionally loads `fe_main` or `fe_load`.
- `DATA/FE_MAIN.PAK` — **CONFIRMED:** main-menu runtime section; dispatches to `level00`–`level14`, `level07d`, six arena sections, and `fe_xtra`.
- `DATA/LEVEL00.PAK` — **CONFIRMED:** first mapped gameplay section; explicitly transitions to `LEVEL01` through its entity graph.

## AUDIO

- `E_DATA.PAK` — **CONFIRMED:** all listed paths are under `DATA\SOUND`.
- Inner `.MIC`, `.MSB`, `.MSH`, `.CMH`, and `.BIN` files — **LIKELY:** audio data, banks, metadata, or scripts based on path context; encodings remain unknown.
- `FE_MAIN.PAK/.../ATTRACT.PSS` and `ATTRACT_PAL.PSS` — **CONFIRMED:** MPEG program streams with one MPEG-2 video stream; no audio stream reported by FFprobe.
- `IOP/LIBSD.IRX`, `SDRDRV.IRX`, and `STREAM.IRX` — **LIKELY:** runtime sound/streaming modules based on conventional names; code not analyzed.

## SCRIPTS / CONFIGURATION

- `SYSTEM.CNF` — **CONFIRMED:** PS2 boot configuration.
- `GENERAL.PAK/DATA/SECTIONS.TXT` — **CONFIRMED:** ordered section/allocation manifest mapping front-end, arena, level, and test identifiers to `DATA\ENV` logical paths.
- `GENERAL.PAK/DATA/SOUND/SCRIPTS/MISC.TXT` — **CONFIRMED:** ordered cross-platform audio configuration covering global volumes, crowd sound-grid behavior, and PS2/Xbox effect presets.
- `FE_LANG.PAK/DATA/ENV/FE_LANG/WORLD/FE_LANG.TXT` — **CONFIRMED:** front-end menu/state script defining texture pages, sprites, focus navigation, actions, variables, and transitions to `fe_tv`.
- `FE_LANG.PAK/DATA/ENV/FE_LANG/TEXT/*/UI.TXT` — **CONFIRMED:** seven synchronized, ordered localization tables with duplicate keys and legacy single-byte encodings.
- `FE_TV.PAK/DATA/ENV/FE_TV/WORLD/FE_TV.TXT` — **CONFIRMED:** cross-platform video-mode state script with TIM2/font/SFX references, local menu transitions, and section exits to `fe_main`/`fe_load`.
- `FE_TV.PAK/DATA/ENV/FE_TV/WORLD/FE.MTL` — **HIGH-VALUE FORMAT TARGET:** confirmed length-delimited resource/property container; numeric child-property meanings remain unknown.
- `FE_MAIN.PAK/DATA/ENV/FE_MAIN/WORLD/FE_MAIN.TXT` — **CONFIRMED:** large main-menu state graph binding 35 TIM2 filenames, 13 emitters, symbolic SFX/music, MPEG playback, save/profile/unlock logic, and gameplay/front-end section exits.
- `FE_MAIN.PAK/DATA/ENV/FE_MAIN/WORLD/FE.MTL` — **CONFIRMED structure:** 45-record resource table; every shared FE_LANG/FE_TV record is byte-identical, strengthening the stable declaration/property model.
- `LEVEL00.PAK/DATA/ENV/LEVEL00/ENTITIES/TEST.ENT` — **P1 TARGET:** binary entity/state graph with a recovered string area for checkpoints, spawns, squads, cameras, cutscenes, particles, audio, and section transition.
- `LEVEL00.PAK/DATA/BATTLE.TXT` — **CONFIRMED:** global battle/combat/crowd-AI tuning snapshot with 75 character sections.
- `LEVEL00.PAK/.../CHAR_TYPES.BIN` + `DATA/TEXT/*/NAMES.TXT` — **CONFIRMED JOIN:** seven numeric IDs resolve to the seven packaged character families.
- `LEVEL00.PAK/DATA/ENV/LEVEL00/OLFS/*` — **P1 TARGETS:** collision-plane and 3D waypoint/connectivity candidates.
- Front-end `FONT*.DIM` — **HIGH-VALUE FORMAT TARGET:** confirmed 256-entry u16 measurement structure; exact character mapping and sentinel semantics remain unknown.
- Future executable string targets: `start_section`, `FNT_END`, `STD_LEVEL`, `SOUND_GRID`, `EFFECT_NAME`, and `DATA\ENV`.
- `E_DATA.PAK` entries below `DATA\SOUND\SCRIPTS` — **LIKELY:** localized or compiled sound scripts based on path names.

## IOP / PS2 SYSTEM MODULES

- `IOP/IOPRP300.IMG` — **LIKELY:** IOP reset/module image with `RESET`, `ROMDIR`, and `EXTINFO` header records.
- `IOP/*.IRX` — **CONFIRMED:** ten ELF-based IOP modules.
- `IOP/GENERAL.PAK` — **UNKNOWN:** two-entry PAK1 located beside system modules.

## UNKNOWN

- Proprietary structures inside all still-unlisted `DATA` PAKs.
- Exact MTL property IDs/flags, DIM character mapping/`0x2000` sentinel, and memory-card `.ICO` schema; stock Noesis recognition of the nonstandard `.ICO` payload.
- Actual codecs and schemas for `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries.
- Relationships between `LEVEL07.PAK` and `LEVEL07D.PAK`.
- Meaning of arena suffixes `B`, `G`, `P`, `R`, `U`, and `X`.
- Meaning of FE_MAIN's `MAP_512.TGA` script reference when the packaged texture is `MAP_512.TM2`.
- V4-8 packed-attribute semantics for LEVEL00 world BIN, exact per-material MTL sampler states, remaining AAB leaf fields, HMP layout, character PSQ/PSW/MPH/BNS, ANM/SAM tracks, ENT records, and OLFS COL/PT2/IND data. LEVEL00 BIN connectivity/topology and V2-16 UVs are established; direct VU routing and target-renderer coordinate/front-face/V convention remain open.
- Runtime roles of LEVEL00 MODELS.FLP/MVR/INS/STL companions and whether `.CAS` is source-only or has a runtime counterpart.
