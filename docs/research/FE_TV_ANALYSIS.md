# FE_TV.PAK Analysis

Analysis completed on 2026-08-29. Only `DATA/FE_TV.PAK` was listed and extracted during this task. Comparison was limited to the already-extracted FE_LANG tree; no other PAK was opened.

## Archive identity and safety

| Field | Value |
|---|---|
| Source | `game-extracted/disc/DATA/FE_TV.PAK` |
| Size | 8,282,688 bytes (`0x7e6240`) |
| SHA-256 before and after extraction | `ffd880ed25d385f8addbcbcee105032f5525112306f44db31f549c129cd9d6c4` |
| Magic / version | `PAK1` / 1 |
| Declared entries | 79 |
| Alignment | `0x800` |
| Extractor | QuickBMS 0.12.0 with `spartan_total_war.bms` 0.1.1 |
| Destination | `game-extracted/pak/FE_TV` (ignored) |

QuickBMS list-only mode ran first and returned exit code 0 with 79 entries. Archive order is ascending by offset, from `0x2000` through a final extent ending exactly at `0x7e6240`. The pre-extraction audit found 79 unique relative paths and no absolute paths, traversal, empty components, invalid/reserved Windows path components, case-insensitive duplicates, file/directory collisions, overlaps, out-of-bounds extents, or offsets inconsistent with `0x800` alignment.

The isolated destination did not exist before extraction. Extraction returned exit code 0 and produced exactly the 79 listed paths. Every logical size matched, no unexpected file appeared, and the source hash remained unchanged. The extracted files total 8,184,826 bytes. The raw listing and deterministic inventory reports remain local under `logs/analysis/FE_TV_*`.

## Inventory and directory structure

| Extension | Files | Total bytes | Size range | Classification |
|---|---:|---:|---:|---|
| `.tm2` | 35 | 7,378,368 | 1,344–263,232 | **CONFIRMED:** TIM2 textures and font atlases |
| `.txt` | 8 | 627,530 | 7,818–92,313 | **CONFIRMED:** seven UI localization tables and one front-end state script |
| `.dim` | 32 | 18,432 | 576 | **CONFIRMED structure / LIKELY semantics:** font measurement tables paired with TIM2 atlases |
| `.ico` | 3 | 159,408 | 53,136 | **LIKELY:** proprietary PS2 memory-card icon payloads, byte-identical to FE_LANG |
| `.mtl` | 1 | 1,088 | 1,088 | **CONFIRMED structure / LIKELY role:** resource declaration/index table; not established as a conventional material format |

The layout repeats FE_LANG's packaging convention:

- `DATA/ENV/FE_TV/WORLD`: `FE_TV.TXT`, `FE.MTL`, `GRAB_05.TM2`, and `SPARTAN_LOGO.TM2`.
- `DATA/ENV/FE_TV/TEXT`: seven UI tables and four font families for each of eight language directories.
- `DATA/GENERIC_GRAPHICS/MEMCARD`: three shared `.ICO` payloads.
- `DATA/GENERIC_GRAPHICS/TEXTURES`: `NON_LINEAR_REMAPPING.TM2`.

Japanese again has font resources but no `UI.TXT`. English, French, German, Italian, Spanish, Polish, and Czech have UI tables and all four font families.

## TIM2 resources

All 35 images use `TIM2` version 4, one picture, a 48-byte picture header, picture format 0, one mip level, CLUT type 3, image type 5 (8-bit indexed), 256 palette entries, and a 1,024-byte CLUT.

| Dimensions | Count | Image bytes | Resources |
|---:|---:|---:|---|
| 16×16 | 1 | 256 | `NON_LINEAR_REMAPPING.TM2` |
| 256×256 | 8 | 65,536 | the eight `FONT14.TM2` atlases |
| 512×512 | 26 | 262,144 | 24 `FONT18`/`FONT18G`/`FONT24` atlases plus `GRAB_05` and `SPARTAN_LOGO` |

`FE_TV.TXT` binds `GRAB_05.TM2` to texture page `tp_grab02` and `SPARTAN_LOGO.TM2` to `tp_spartan_logo`, then defines three texture regions and three sprites. `FE.MTL` repeats those symbolic texture-page/file-stem pairs.

Font textures form two language hash groups for every size/style: Czech and Polish share one atlas, while English, French, German, Italian, Japanese, and Spanish share another. `FONT18` and `FONT18G` have different texture hashes but identical DIM measurements within each language group, supporting `G` as a graphical variant with unchanged advances. Stock Noesis has a native TIM2 handler; no conversion or export was performed.

## DIM structure

All 32 DIM files are exactly 576 bytes. Cross-font comparison supports this tentative schema:

| Offset | Size | Interpretation | Confidence |
|---:|---:|---|---|
| `0x00` | 1 | `0x10` for FONT14; `0x20` for FONT18/FONT18G/FONT24; cell-height or atlas-metric selector | **LIKELY** |
| `0x01` | 63 | constant `0xcd` fill/sentinel bytes | **CONFIRMED** |
| `0x40` | 512 | 256 little-endian 16-bit font measurements | **CONFIRMED structure** |

The first measurements behave like horizontal glyph advances: FONT14 begins `5, 6, 9, 10...`, consistent with space and punctuation widths, and corresponding Latin-letter values grow in FONT18 and FONT24. This is strong evidence for advance/width semantics, but the engine's character-base index, units, and layout behavior remain unconfirmed.

FONT14 data is byte-identical to FE_LANG for every language. FONT18 and FONT18G reuse the same DIM table within each language group despite different atlas pixels. Czech/Polish remain distinct from the other six languages. In Czech/Polish FONT24, entries 191 and 223 contain `0x2000` rather than an ordinary 2–32 measurement; this is probably a special or missing-glyph marker, but its meaning is **UNKNOWN**. No baseline, kerning pair, or separate spacing field has been identified.

## MTL structure

FE_TV `FE.MTL` is 1,088 bytes versus FE_LANG's 864 bytes. Both parse completely with the same length-delimited structure. Calling this a resource declaration/index is better supported than calling it a material format.

### Tentative schema

| Offset / field | Interpretation | Confidence |
|---|---|---|
| `0x00`, u32 | offset of the record area (`0x90` in FE_TV; `0x70` in FE_LANG) | **CONFIRMED** |
| `0x04`, u32 | top-level record count (10; 8) | **CONFIRMED** |
| `0x08...` | exactly `count` NUL-terminated ASCII record names, then zero padding to a 16-byte boundary | **CONFIRMED** |
| record `+0x00`, u32 | total byte length of this record, always a multiple of 16 | **CONFIRMED** |
| record `+0x04`, u32 | child/property-block count | **CONFIRMED structurally** |
| record `+0x08`, 8 bytes | zero/reserved in both samples | **CONFIRMED observation; semantics UNKNOWN** |
| each child `+0x00`, u32 | child byte length, multiple of 16 | **CONFIRMED** |
| child payload | small numeric property/type values and/or backslash-prefixed ASCII identifiers | **CONFIRMED content; field meanings UNKNOWN** |

Walking each declared child block lands exactly at its parent record end, and walking all top-level records lands exactly at EOF in both files. Record sizes vary from `0x40` to `0x80`, so there is no fixed top-level record size.

FE_TV records are `TP_GRAB02`, `TP_SPARTAN_LOGO`, `FONT14`, `FONT18`, `FONT18G`, `FONT24`, `AMBIENT_FOLIAGE`, `NON_LINEAR_REMAPPING`, `GLOW_BUFFER_END`, and `APP_BLACKBARS`. Texture-page records contain paired identifiers such as `\TP_GRAB02` and `\grab_05`; font records contain `\FONT18` and `\font18`. Five records shared with FE_LANG—`FONT14`, `AMBIENT_FOLIAGE`, `NON_LINEAR_REMAPPING`, `GLOW_BUFFER_END`, and `APP_BLACKBARS`—are byte-identical, including their numeric properties. This strongly supports stable resource-type/property records across front-end sections. Numeric property IDs, flags, and external lookup rules remain unknown.

## Text and script findings

`FE_TV.TXT` is a 146-line CRLF 7-bit ASCII script using the same command-oriented grammar as FE_LANG. It declares:

- two texture pages, four fonts, three texture regions, three sprites, and 12 localization labels;
- eight local menus controlling progressive scan and PAL/NTSC/60 Hz selection;
- state variables `int_platform`, `int_tv_system`, `int_progressive`, `int_progressive_tmp`, and `int_default_tv_system`;
- `UP`, `DOWN`, and `CROSS` controller actions;
- sound actions `SFX_SELECT_MENU_ITEM` and `SFX_CONFIRM_MENU_ITEM`;
- local `TRANSITION` targets for selection/testing states.

Confirmed cross-section exits are:

- `LEVEL fe_main` when `int_tv_system` is 0 or 1 in `main_menu_a`.
- `LEVEL fe_load` after accepting 50 Hz or 60 Hz in the tester menu.

No direct `fe_lang`, `fe_xtra`, or `fe_splash` reference occurs in FE_TV. `FNT_END`, `start_section`, `DATA\ENV`, `.DIM`, and `.MTL` are absent from the script; filenames occur only for the two world TIM2 pages. Platform value 2 selects GameCube-specific menu branches, confirming that the script source/state grammar is cross-platform even in this PS2 archive.

The seven `UI.TXT` files repeat FE_LANG's no-BOM, non-UTF-8 legacy single-byte encoding pattern. Each FE_TV table has 888 records, 867 unique keys, and the same 21 duplicated key names seen in FE_LANG. Every one of FE_LANG's 699 ordered records appears in the same relative key order, while FE_TV adds 189 keys per language. Additions are dominated by credits plus platform/options entries such as `very_hard`, `ngc_rumble`, `xbox_cancel_changes`, and `save_options_for_first_time`. Common values are not immutable: English has 45 revised values, and translated tables have 86–457 revisions, including video-mode text, memory-card requirements, mission brief formatting, and unresolved translation placeholders. FE_TV therefore packages a later/larger global localization snapshot rather than a small TV-only label set.

## Direct FE_LANG comparison

After normalizing `DATA/ENV/FE_TV` and `DATA/ENV/FE_LANG` to a common section placeholder, 28 paths match:

- 20 are byte-identical: all eight `FONT14.TM2`, all eight `FONT14.DIM`, the three memory-card `.ICO` files, and `NON_LINEAR_REMAPPING.TM2`.
- Eight are section-specific: seven larger FE_TV `UI.TXT` files and the larger FE_TV `FE.MTL`.

The four exact `DATA/GENERIC_GRAPHICS` paths are hash-identical across both archives. The icon hash is `77526f2d61f6325bc9ce91dec97e3377d242916b02fb20dc7350db7b6db062d3`; `NON_LINEAR_REMAPPING.TM2` is `0da39e2c5b3222d8603685625f9413626d66d7396c6c83749719f8b93af166fa`. Repeated FONT14 resources retain the FE_LANG language-group hashes documented previously.

These byte-identical files demonstrate duplication across self-contained section packages. They do **not** by themselves prove that FE_TV loads resources from FE_LANG at runtime.

## Preliminary dependency map

| From | To / resource | Relationship | Confidence |
|---|---|---|---|
| GENERAL `start_section` | FE_LANG | section transition/start selection | **CONFIRMED** |
| FE_LANG | FE_TV | `LEVEL fe_tv` section transition | **CONFIRMED** |
| FE_TV | FE_MAIN | conditional `LEVEL fe_main` transition | **CONFIRMED** |
| FE_TV | FE_LOAD | tester-menu `LEVEL fe_load` transition | **CONFIRMED** |
| FE_TV script | `GRAB_05.TM2`, `SPARTAN_LOGO.TM2` | filename reference through `TPAGE` | **CONFIRMED** |
| FE_TV script/MTL | FONT14/FONT18/FONT18G/FONT24 | symbolic resource lookup to paired TM2/DIM files | **LIKELY** |
| FE_TV and FE_LANG | 20 hash-identical files | duplicated shared resource content | **CONFIRMED** |
| MTL shared symbolic records | runtime resource system | suspected lookup/property metadata | **LIKELY; mechanism UNKNOWN** |

The evidence supports a boot chain of FE_LANG → FE_TV → FE_MAIN for ordinary 50/60 Hz states, with FE_LOAD used by the tester path. It does not establish the complete later loading order.

## Architecture implications and unknowns

The strongest result is that each front-end PAK appears to be a self-contained section package with a repeated architecture: a `DATA/ENV/<SECTION>/WORLD` script and MTL index, per-language UI snapshots and font pairs under `TEXT`, plus duplicated shared resources under `DATA/GENERIC_GRAPHICS`. Section-local duplication, rather than a single central front-end asset store, is directly evidenced by 20 identical files.

Remaining unknowns include MTL child property IDs and flags, the DIM `0x2000` sentinel and exact character mapping, the reason Japanese font assets accompany no Japanese UI table, the proprietary memory-card ICO schema, how the loader resolves symbolic names to archive entries, and the exact role of FE_LOAD outside the observed tester path.

No asset was modified, converted, exported, rebuilt, reimported, or upscaled. No Ghidra or PS2Recomp work occurred. Broad Milestone 0 checkboxes remain unchanged.

## Recommended next action

Perform a separately authorized list-only audit of `DATA/FE_MAIN.PAK`, the normal conditional destination of FE_TV. If safe, extract it to its own ignored directory and compare its WORLD/MTL/resource layout against FE_LANG and FE_TV.
