# FE_MAIN.PAK Analysis

Analysis completed on 2026-08-29. Only `DATA/FE_MAIN.PAK` was listed and extracted during this task. Direct comparison was limited to the already-extracted FE_LANG and FE_TV trees; no other PAK was opened.

## Archive identity and safety

| Field | Value |
|---|---|
| Source | `game-extracted/disc/DATA/FE_MAIN.PAK` |
| Size | 144,123,908 bytes (`0x8972804`) |
| SHA-256 before and after extraction | `9b0edcf2bd8868de4450cf80bdd15967347bb5ea9b9dd7a312496cb1fb15d328` |
| Magic / version | `PAK1` / 1 |
| Declared entries | 114 |
| Alignment | `0x800` |
| Extractor | QuickBMS 0.12.0 with `spartan_total_war.bms` 0.1.1 |
| Destination | `game-extracted/pak/FE_MAIN` (ignored) |

QuickBMS list-only mode ran first and returned exit code 0 with 114 entries. Archive order is ascending by offset, from `0x2800` through a final extent ending exactly at archive EOF (`0x8972804`). All stored offsets are `0x800`-aligned. The audit found 114 unique relative paths and no absolute paths, traversal, empty components, malformed or reserved Windows names, case-insensitive duplicates, file/directory collisions, overlapping extents, out-of-bounds extents, or extraction-destination hazards.

The isolated destination did not exist before extraction. Extraction returned exit code 0 and produced exactly the 114 listed paths. Every logical size matched, no unexpected file appeared, and the source hash remained unchanged. Extracted files total 143,982,047 bytes. Raw listing and deterministic inventory reports remain local under `logs/analysis/FE_MAIN_*`.

## Inventory and directory map

| Extension | Files | Total bytes | Size range | Classification |
|---|---:|---:|---:|---|
| `.tm2` | 68 | 11,355,648 | 1,344–263,232 | **CONFIRMED:** TIM2 textures and font atlases |
| `.dim` | 32 | 18,432 | 576 | **CONFIRMED structure / LIKELY semantics:** font measurement tables paired with TIM2 atlases |
| `.txt` | 8 | 1,126,407 | 83,411–506,695 | **CONFIRMED:** seven localization snapshots and one main-menu/state script |
| `.ico` | 3 | 159,408 | 53,136 | **LIKELY:** proprietary PS2 memory-card icon payloads |
| `.pss` | 2 | 131,317,768 | 65,650,692–65,667,076 | **CONFIRMED:** MPEG program streams containing MPEG-2 attract-mode video |
| `.mtl` | 1 | 4,384 | 4,384 | **CONFIRMED structure / LIKELY role:** resource declaration/index table |

No extension family other than `.PSS` is new relative to FE_LANG and FE_TV.

- `DATA/ENV/FE_MAIN/WORLD` contains 39 entries: `FE_MAIN.TXT`, `FE.MTL`, 35 TIM2 resources, and the two PSS videos.
- `DATA/ENV/FE_MAIN/TEXT` contains four TIM2/DIM font pairs for each of eight language directories. Czech, English, French, German, Italian, Polish, and Spanish also contain `UI.TXT`; Japanese does not.
- `DATA/GENERIC_GRAPHICS/MEMCARD` contains three `.ICO` payloads.
- `DATA/GENERIC_GRAPHICS/TEXTURES` contains `NON_LINEAR_REMAPPING.TM2`.

This preserves both established conventions: section-local resources under `DATA/ENV/<SECTION>` and duplicated generic resources under `DATA/GENERIC_GRAPHICS`.

## TIM2 resources

All 68 files have `TIM2` version 4, one picture, a 48-byte picture header, picture format 0, one mip level, CLUT type 3, image type 5 (8-bit indexed), 256 palette entries, and a 1,024-byte CLUT.

| Dimensions | Count | Image bytes per file | Principal resources |
|---:|---:|---:|---|
| 16×16 | 1 | 256 | `NON_LINEAR_REMAPPING` |
| 32×32 | 5 | 1,024 | `SMOKE`, `SMOKE2`, `SMOKE3`, `LONG_BAND`, `BLACKBOX` |
| 64×64 | 1 | 4,096 | `ICONS` |
| 128×128 | 4 | 16,384 | `ARROWS`, `FOG_ELEMENTS`, `GOD_COIN`, `GLOWS` |
| 256×256 | 19 | 65,536 | eight FONT14 atlases plus cards, symbols, masks, flares, and UI panels |
| 512×512 | 38 | 262,144 | 24 FONT18/18G/24 atlases plus map, mission, logo, toys, fog, bands, and upgrade pages |

The script declares 38 `TPAGE` bindings covering 35 distinct filenames. Every packaged WORLD TIM2 is referenced by name or stem except for one extension mismatch: the script requests `map_512.tga`, while the archive contains `MAP_512.TM2`. This may indicate extension-insensitive lookup, a stale source-script suffix, or runtime substitution; the mechanism is **UNKNOWN**.

Names and script bindings support UI classifications rather than 3D assets: mission and arena cards, map/mask, buttons/icons/arrows, logos, decorative bands, weapon upgrades, toys, and fog/glow/flare/smoke effects. No texture was converted or exported.

## DIM and fonts

All 32 DIM files preserve the established 576-byte layout:

| Offset | Size | Interpretation | Confidence |
|---:|---:|---|---|
| `0x00` | 1 | `0x10` for FONT14; `0x20` for FONT18/FONT18G/FONT24; size-class-like selector | **LIKELY** |
| `0x01` | 63 | constant `0xcd` fill | **CONFIRMED** |
| `0x40` | 512 | 256 little-endian u16 measurement values | **CONFIRMED structure** |

The first 64 bytes match the corresponding FE_TV files exactly, but every FE_MAIN DIM differs in between 1 and 17 of its 256 measurements. The paired font atlases also differ. This is evidence for section-specific font rendering/measurement snapshots, not a schema change. FONT18 and FONT18G retain identical DIM data within each language group despite having different atlas pixels.

FE_MAIN produces three language groups for each font family: Czech/Polish, English/French/German/Italian/Spanish, and Japanese. This separates Japanese from the Latin group seen in FE_TV. Czech and Polish FONT24 retain `0x2000` at measurement indices 191 and 223; its meaning remains **UNKNOWN**. No independent baseline, kerning, or spacing field was identified.

## MTL resource container

`FE.MTL` is 4,384 bytes. It parses completely with the established length-delimited hierarchy: record-area offset `0x250`, 45 NUL-terminated top-level names, padding to the record area, variable-sized top-level records, and counted variable child blocks. A full record walk lands exactly at EOF.

The 45 records include 35 texture-page-like symbols, four font symbols, and the stable `AMBIENT_FOLIAGE`, `NON_LINEAR_REMAPPING`, `GLOW_BUFFER_END`, and `APP_BLACKBARS` records. Texture records pair script-facing symbols with file stems, for example `TP_GLOWS` with `glows` and `TP_ARENA_A` with `arena_card_a`.

All 10 record names shared with FE_TV are byte-identical records: `TP_GRAB02`, `TP_SPARTAN_LOGO`, all four fonts, `AMBIENT_FOLIAGE`, `NON_LINEAR_REMAPPING`, `GLOW_BUFFER_END`, and `APP_BLACKBARS`. All seven names shared with FE_LANG are also byte-identical. This is stronger evidence for a stable resource-declaration/property system: the same record can persist even when the section-local texture or font content differs. Numeric property meanings and the exact loader lookup remain **UNKNOWN**; `.MTL` is not claimed to be a conventional material format.

## PSS attract videos

Both new `.PSS` files begin with MPEG program-stream pack start code `00 00 01 ba`. Read-only FFprobe inspection reports one MPEG-2 video stream and no audio stream in each:

| File | Size | Frame | Frame rate | Duration |
|---|---:|---:|---:|---:|
| `ATTRACT.PSS` | 65,667,076 | 512×224 | 30000/1001 fps | 94.060633 s |
| `ATTRACT_PAL.PSS` | 65,650,692 | 512×256 | 25 fps | 94.040000 s |

The script selects the 224-line or PAL 256-line file according to `int_platform` and `int_tv_system`, using `PLAY_FULLSCREEN_MPEG`, then returns locally to `titles`. This establishes their attract-mode role and shows that a section PAK can embed a large runtime video dependency directly.

## Script and state architecture

`FE_MAIN.TXT` is a 506,695-byte, 8,717-line CRLF command script. Its grammar is the same declarative/action language seen in FE_LANG and FE_TV, but at a much larger scale. It contains 38 TPAGE declarations, four FONT declarations, 193 texture regions, 567 sprites, 13 emitters, seven flipbooks, 156 buttons, 111 menus, 824 action blocks, 586 local transitions, 53 `PLAY` commands, and 28 `STREAM` commands.

The menu graph covers boot/title/attract flow, main start, new/load/save games, memory-card management and formatting, options and volume controls, mission map/free play, arena selection and high scores, Fog upgrades, toys/gallery/extras, mission completion, credits, profile/save state, and unlock presentation. `UP`, `DOWN`, `LEFT`, `RIGHT`, `CROSS`, `CIRCLE`, `SQUARE`, `TRIANGLE`, and `MENU` handlers drive focus and state actions.

Confirmed section exits are:

- `level00` through `level14`, including `level07d`, selected from campaign/free-play state;
- `arenar`, `arenab`, `arenau`, `arenap`, `arenag`, and `arenax`, selected by arena pointer;
- `fe_xtra`, selected from the extras menu.

There is no `fe_load`, `fe_tv`, `fe_lang`, `start_section`, `FNT_END`, or `STD_LEVEL` token in the script. The FE_TV tester edge to FE_LOAD remains independent of FE_MAIN's observed routes.

Audio references are symbolic rather than embedded audio files. They include menu SFX, level-completion cues `sfx_oc_level01` through `sfx_oc_level14`, weapon/reward/stat cues, and streams such as `MAIN_MENU_MUSIC`, `quest_music`/`quest_stream`, arena, gallery, credits, extras, options, save/load, and mission-complete identifiers.

## High-priority architecture survey

- **Geometry/model:** no mesh, model, vertex, index, primitive, polygon, strip, or geometry file family or script declaration was found. **No evidence.**
- **Skeleton/character animation:** no skeleton, bone, joint, rig, pose, or keyframe payload was found. `ANIMATE`, `ROTATE`, `TRANSLATE`, and `RESIZE` operate on UI objects; they do not establish skeletal animation. **No evidence.**
- **Materials/rendering:** MTL supplies stable resource/property records and scripts bind texture pages/regions, but property semantics, UV representation, blend modes, and render flags are not decoded. **LIKELY resource/render metadata; conventional material semantics UNKNOWN.**
- **Effects/particles:** `SMOKE*`, `FOG_*`, `GLOWS`, and `FLARES` textures are explicitly consumed by 13 `EMITTER` declarations and sprite animations. This confirms a script-driven 2D particle/effect system in FE_MAIN. It does not establish gameplay particle serialization.
- **Scene/camera/light:** no scene graph, object-placement, transform hierarchy, light, or 3D camera data was found. Camera text refers to user options such as inverted/game/ballista camera. UI transforms are not evidence of a 3D scene format.
- **UI:** the archive extensively binds TIM2 pages to regions, sprites, buttons, emitters, text, focus navigation, local transitions, and section loads. This is FE_MAIN's dominant architecture.

## FE_LANG and FE_TV comparison

After normalizing each `DATA/ENV/<SECTION>` prefix, FE_MAIN and FE_TV have 78 matching paths: 12 are byte-identical and 66 differ. Exact matches are the seven `UI.TXT` files, `GRAB_05.TM2`, the three generic memory-card icons, and `NON_LINEAR_REMAPPING.TM2`. The 32 TIM2 and 32 DIM font files, `SPARTAN_LOGO.TM2`, and `FE.MTL` differ as whole files. Despite the MTL file difference, all 10 shared MTL records are identical.

FE_MAIN and FE_LANG have 30 matching normalized paths: five exact-path matches and 25 variants. The exact paths are the three memory-card icons, `NON_LINEAR_REMAPPING.TM2`, and `SMOKE.TM2`. Broader hash matching finds seven FE_MAIN files with FE_LANG content because `SMOKE`, `SMOKE2`, and `SMOKE3` all duplicate FE_LANG's single `SMOKE.TM2`. No FE_MAIN UI table is identical to FE_LANG; the seven tables instead exactly duplicate the expanded FE_TV snapshots.

The three generic `.ICO` files all share SHA-256 `77526f2d61f6325bc9ce91dec97e3377d242916b02fb20dc7350db7b6db062d3`. `NON_LINEAR_REMAPPING.TM2` is `0da39e2c5b3222d8603685625f9413626d66d7396c6c83749719f8b93af166fa`, `GRAB_05.TM2` is `d61e57ba0f7333215309e387bc2a2c010aeb062dbc2dc66efcf71bddf0034889`, and the shared smoke content is `c91c8777572b3a58e86631fe5408d580248f820809854c2eed2c22f59529f5a1`.

## Resource dependency graph

| From | To / resource | Relationship | Confidence |
|---|---|---|---|
| GENERAL `start_section` | FE_LANG | initial section selection | **CONFIRMED** |
| FE_LANG | FE_TV | `LEVEL fe_tv` section transition | **CONFIRMED** |
| FE_TV | FE_MAIN | ordinary video-state `LEVEL fe_main` transition | **CONFIRMED** |
| FE_TV | FE_LOAD | display-tester `LEVEL fe_load` transition | **CONFIRMED** |
| FE_MAIN | LEVEL00–LEVEL14 and LEVEL07D | campaign/free-play `LEVEL` transitions | **CONFIRMED** |
| FE_MAIN | ARENAR/B/U/P/G/X | arena-selection `LEVEL` transitions | **CONFIRMED** |
| FE_MAIN | FE_XTRA | extras-menu `LEVEL fe_xtra` transition | **CONFIRMED** |
| FE_MAIN script | 35 WORLD TIM2 resources and two PSS files | filename/resource reference | **CONFIRMED**, except `MAP_512.TGA` suffix mismatch |
| FE_MAIN script/MTL | fonts and texture pages | symbolic resource lookup | **LIKELY; loader mechanism UNKNOWN** |
| FE_MAIN / FE_TV / FE_LANG | exact repeated files and MTL records | duplicated shared resource content | **CONFIRMED** |

These are explicit edges or content relationships, not an inferred total runtime order.

## Architecture conclusions and gameplay relevance

FE_MAIN strongly reinforces the self-contained-section hypothesis. It packages its complete main-menu script, section-specific MTL declaration set, every referenced texture page except the `MAP_512` suffix anomaly, all four fonts for eight languages, the full seven-language localization snapshot, shared memory-card/remapping resources, and both regional attract videos. The section even duplicates identical generic content and uses section-specific variants for fonts and the Spartan logo. This is consistent with a runtime-section snapshot, not a thin menu that depends on FE_LANG or FE_TV remaining resident.

FE_MAIN does not reveal a mesh, skeletal animation, world-placement, 3D material, or gameplay scene family likely to unlock LEVEL/ARENA archives. It does establish engine-wide candidates that may recur: PAK1 section packaging, command scripts, TIM2 pages, MTL resource declarations, symbolic audio lookups, and script-driven emitters. `.PSS` is a new standard-container asset family likely relevant to other cinematic-bearing sections, but recurrence in gameplay PAKs is not yet evidenced. The direct LEVEL and ARENA destinations make one gameplay archive the next useful architectural comparison.

## Unknowns and recommended next action

Remaining unknowns include MTL numeric child-property semantics, DIM character mapping and `0x2000`, the `MAP_512.TGA`/`.TM2` lookup behavior, PSS private/system packet details and whether audio is intentionally absent, proprietary ICO structure, whether FE_MAIN resources are unloaded on `LEVEL`, and all gameplay geometry/animation/world formats.

No asset was modified, converted, exported, rebuilt, reimported, or upscaled. No Ghidra or PS2Recomp work occurred. Broad Milestone 0 completion boxes remain unchanged.

Recommended next action: in a separately authorized task, perform the same list-first isolated analysis of `DATA/LEVEL00.PAK`. FE_MAIN directly dispatches to `level00`, and comparing the tutorial/prologue section against the established section-package model is the shortest evidence-based route to gameplay asset architecture. Stop before any other archive unless separately authorized.
