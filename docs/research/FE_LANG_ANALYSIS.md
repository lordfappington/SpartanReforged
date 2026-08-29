# FE_LANG.PAK Analysis

Analysis completed on 2026-08-29. Only `DATA/FE_LANG.PAK` was listed and extracted during this task. No other PAK was opened.

## Archive identity and safety

| Field | Value |
|---|---|
| Source | `game-extracted/disc/DATA/FE_LANG.PAK` |
| Size | 1,348,160 bytes (`0x149240`) |
| SHA-256 before and after extraction | `b805a6dd51074b35e9b69fe06bd585a167b663ac3e4c8e009c289eb4efb9fbcb` |
| Magic / version | `PAK1` / 1 |
| Declared entries | 32 |
| Alignment | `0x800` |
| Extractor | QuickBMS 0.12.0 with `spartan_total_war.bms` 0.1.1 |
| Destination | `game-extracted/pak/FE_LANG` (ignored) |

QuickBMS list-only mode ran before extraction and reported 32 files. The raw local listing is `logs/analysis/FE_LANG_listing.txt`. A pre-extraction audit found 32 unique relative paths and no absolute paths, parent traversal, empty components, case-insensitive duplicates, file/directory collisions, overlapping extents, out-of-bounds extents, or offsets that violated the declared `0x800` alignment.

The isolated destination did not exist before extraction. QuickBMS then returned exit code 0, and verification found exactly 32 files: every relative path and logical size matched the list-only table, with no missing or unexpected files. The extracted files total 1,312,166 bytes. The source archive's SHA-256 was unchanged afterward.

## Inventory

| Extension | Files | Bytes | Size range | Confirmed or evidence-based role |
|---|---:|---:|---:|---|
| `.tm2` | 12 | 620,544 | 1,344–66,624 | PlayStation 2 TIM2 textures, including eight font atlases |
| `.txt` | 8 | 526,742 | 2,600–77,223 | Seven localized UI tables and one front-end world/menu script |
| `.ico` | 3 | 159,408 | 53,136 | Three byte-identical memory-card icon assets; proprietary payload despite the extension |
| `.dim` | 8 | 4,608 | 576 | Font glyph-width/dimension tables paired with `FONT14.TM2` |
| `.mtl` | 1 | 864 | 864 | Binary material/resource-name table for the front end |

Deterministic CSV/JSON inventory and extension reports, plus a 64-byte header survey, remain local under `logs/analysis/FE_LANG_*` and are not committed. QuickBMS exposed a logical size and offset for every entry but no separate compressed-size column. The script uses direct `log` operations and no decompressor, so this extraction recipe treats the extents as stored data; compression behavior in other PAK variants remains unproven.

## Directory and resource layout

The archive contains three functional groups:

- `DATA/ENV/FE_LANG/WORLD`: `FE_LANG.TXT`, `FE.MTL`, and three TIM2 images (`SMOKE`, `FLAGS`, `ARROWS`).
- `DATA/ENV/FE_LANG/TEXT`: localized UI tables for English, French, German, Italian, Spanish, Polish, and Czech, plus eight language directories containing `FONT14.TM2`/`FONT14.DIM` pairs. Japanese has a font pair but no `UI.TXT` in this archive.
- `DATA/GENERIC_GRAPHICS`: three memory-card `.ICO` files and `NON_LINEAR_REMAPPING.TM2`.

This mix confirms that a front-end section PAK can include section-specific environment data and shared `GENERIC_GRAPHICS` resources in one flat archive table.

## TIM2 textures and fonts

All 12 `.TM2` files begin with `TIM2`, declare one picture, use a 48-byte picture header, image type 5 (8-bit indexed), and a 256-color / 1,024-byte CLUT. Header metadata gives these dimensions:

| Resource group | Count | Dimensions | Image bytes per file |
|---|---:|---:|---:|
| `FONT14.TM2` and `FLAGS.TM2` | 9 | 256×256 | 65,536 |
| `ARROWS.TM2` | 1 | 128×128 | 16,384 |
| `SMOKE.TM2` | 1 | 32×32 | 1,024 |
| `NON_LINEAR_REMAPPING.TM2` | 1 | 16×16 | 256 |

The eight 66,624-byte font atlases form two byte-identical groups: Czech and Polish share SHA-256 `9383a07c8e1337723052ea38c9e6087f85932166da8e538c30541aa30de3360d`; English, French, German, Italian, Japanese, and Spanish share `3cf7da210389cfe81f08706e2fa2b6320e5590de36b3bac63deba2b3446615df`. This is consistent with a separate Central European glyph set, while Japanese's presence in the common group remains unexplained.

Each 576-byte `.DIM` begins with byte `0x10` followed by 63 bytes of `0xcd`, then 256 little-endian 16-bit values. Those values are plausible glyph widths (mostly 2–16), making the format a compact 64-byte prefix plus a 256-entry width table. DIM hashes group exactly like the atlases: Czech/Polish share one table, and the other six languages share another. Exact runtime semantics for the 64-byte prefix and character-code mapping remain unknown.

The installed stock Noesis 4.474 files contain the native `Image_LoadTIM2` handler, so TIM2 recognition is available without adding a third-party plugin. Recognition was established from the installed handler; no image was exported or converted.

## Localization tables

The seven `UI.TXT` files use CRLF and have no BOM or NUL bytes. They are not valid UTF-8 and contain locale-specific high bytes, indicating legacy single-byte encodings; Windows-1252 for the Western European tables and Windows-1250 for Czech/Polish are likely but not yet proven by an engine parser.

Records have an ASCII key line such as `[PRESS_START]` followed by a braced localized value such as `{PRESS START BUTTON}`. `//` comments provide translator context and historical notes. There is no explicit binary offset table: record identity comes from keys and file order. Every language has the same structure:

- 699 key/value records.
- 678 unique key names.
- The same 21 duplicated key names, each occurring twice: `1` through `9`, `Archers_squad`, `FORMAT_CARD`, `game_options`, `GAMMA`, `Giganties_pet`, `hoplite_squad`, `LOADING`, `MISSION`, `powderkeg#1`, `SAVE_GAME`, `swordsmen_squad`, and `vibration`.
- No language is missing a key from the 678-key union.

The duplicates mean a future parser must preserve record order rather than collapse the files into a unique-key dictionary. English contains 134 literal `{deleted}` values. The translated tables contain 118–155 reference-shaped placeholders such as `{** <641 [subtitles_on_off] >}`, suggesting unresolved/deleted master-record references rather than runtime display text; their exact parser behavior is unknown. Aside from braced values, these placeholders, and literal notation such as `(tm)`, no binary control-code layer was identified. Content includes menu/HUD labels, options for subtitles and speech volume, memory-card messages, mission/gameplay labels, and credits, but no separate dialogue/subtitle script structure was found. The shared ordering strongly suggests maintenance from a common master table.

## FE_LANG world script and material table

`WORLD/FE_LANG.TXT` is a 66-line CRLF ASCII front-end script. It declares three texture pages, 12 texture regions, one `FONT font14`, five flag sprites, focus navigation, smoke emitters, color actions, and two menus. The visible language choices map values 0–4 to UK English, French, German, Italian, and Spanish. Polish, Czech, Japanese, Korean, Chinese, and Portuguese texture-region names also occur in the flag atlas declarations, but they are not in the five-item visible `flags_list` in this build.

The script's five selection actions set `int_language` and load `fe_tv`. Its `main_menu` conditions either load `fe_tv` or transition to the local `lang_select` menu based on `int_platform`, `int_tv_system`, and language value 6. No direct `fe_main`, `fe_xtra`, or `fe_load` reference occurs in the extracted FE_LANG files.

`WORLD/FE.MTL` is binary. Its first two little-endian words are `0x70` and `8`, followed by eight NUL-terminated symbolic names: `TP_SMOKE`, `TP_FLAGS`, `TP_ARROWS`, `FONT14`, `AMBIENT_FOLIAGE`, `NON_LINEAR_REMAPPING`, `GLOW_BUFFER_END`, and `APP_BLACKBARS`. Structured records begin at `0x70` and include paired backslash-prefixed identifiers. This confirms a resource/material lookup role, but field meanings are not yet decoded.

## Memory-card `.ICO` files and Noesis

`ICON1.ICO`, `ICON2.ICO`, and `ICON3.ICO` are byte-identical 53,136-byte files with SHA-256 `77526f2d61f6325bc9ce91dec97e3377d242916b02fb20dc7350db7b6db062d3`. Their first six bytes resemble a one-image Windows ICO directory, but the following would-be entry encodes an impossible `0x3f800000` resource size for a 53,136-byte file. The data therefore is not a conventional Windows bitmap-icon container; the `MEMCARD` path makes a proprietary PlayStation 2 memory-card icon/model payload likely.

Stock Noesis registers a generic `.ico` image handler, but no installed handler specific to this payload was found. Because extension matching alone cannot prove that this nonstandard payload loads, stock Noesis recognition is **unconfirmed**. No plugin was installed and no conversion was attempted.

## Section relationships

Previously extracted `GENERAL.PAK/DATA/SECTIONS.TXT` declares `start_section="fe_lang"` and classifies `fe_lang`, `fe_main`, `fe_tv`, `fe_xtra`, `fe_load`, and `fe_splash` as `FNT_END`. Arena and numbered level sections instead use `STD_LEVEL`.

The present archive supplies direct behavioral evidence for the first transition: FE_LANG is a boot-time language-selection section and explicitly loads `fe_tv`. The sibling `FE_MAIN`, `FE_TV`, `FE_XTRA`, and `FE_LOAD` archives were not opened, so their detailed roles and subsequent transition graph remain unknown. `FNT_END` is now clearly associated with front-end section packages, but its literal expansion and memory/allocation semantics are still unknown; `STD_LEVEL` remains the distinct arena/level class.

## Reverse-engineering implications

- The front-end text system is an ordered, duplicate-preserving key/value format with legacy single-byte localization encodings.
- `FONT14.TM2` plus a 256-entry `.DIM` width table is the first confirmed font representation.
- `FE_LANG.TXT` provides concrete script tokens and state names for later executable string searches: `TPAGE`, `TEXTURE`, `FONT`, `SPRITE`, `FOCUS`, `CROSS`, `SET`, `LEVEL`, `TRANSITION`, `MENU`, `int_language`, `int_tv_system`, and `int_platform`.
- `FE.MTL` links symbolic texture/font/material names to a still-unknown binary record layout.
- The boot path evidence strengthens the hypothesis that section names select like-named PAKs and resolve `DATA\ENV\<section>` resources within them.

## Limits and next target

No asset was modified, rebuilt, reimported, converted, or upscaled. No executable analysis, Ghidra work, or PS2Recomp work occurred. Broad archive, texture, scripting, and level milestones remain incomplete because only two of 30 disc PAKs have been extracted and only FE_LANG's resource families have been sampled.

A useful next bounded task is a list-only inspection of `DATA/FE_TV.PAK`, because FE_LANG explicitly transfers control there. Extraction should again be conditional on a clean path-table audit and use its own ignored destination.
