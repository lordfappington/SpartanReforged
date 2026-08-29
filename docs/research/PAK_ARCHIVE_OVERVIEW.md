# PAK Archive Overview

The initial survey used header reads and QuickBMS 0.12.0 `-l` list-only mode. Later controlled tasks extracted root `GENERAL.PAK`, `DATA/FE_LANG.PAK`, `DATA/FE_TV.PAK`, and `DATA/FE_MAIN.PAK`; see their individual analysis documents. No other PAK has been extracted, rewritten, or reimported.

## Common Container Header

All 30 disc-level PAK files begin with ASCII `PAK1` (`50 41 4b 31`). The existing `spartan_total_war.bms` script identifies this as PAK version 1, reads a little-endian file count from offset `0x08`, and reads alignment from offset `0x0c`. Every surveyed archive declares `0x800` alignment.

The script logs stored extents and does not invoke a decompressor. This indicates that the current extraction recipe treats entries as uncompressed stored regions; deeper format validation remains pending.

## Selected Archive Results

| Archive | Size | SHA-256 | Version | Alignment | Listed entries | Result |
|---|---:|---|---:|---:|---:|---|
| `GENERAL.PAK` | 29,074 | `0ec7ec24f69625d5302c0a040f55803ff084e48655f8142d299bfc9bb97f6e1c` | PAK1 | `0x800` | 2 | List-only and isolated extraction succeeded |
| `E_DATA.PAK` | 1,514,409,600 | `bd2d12fe350e9afa68094c30645eac664c99104ac592c41926a71488a5f03e45` | PAK1 | `0x800` | 12,689 | List-only succeeded |
| `DATA/FE_LANG.PAK` | 1,348,160 | `b805a6dd51074b35e9b69fe06bd585a167b663ac3e4c8e009c289eb4efb9fbcb` | PAK1 | `0x800` | 32 | List-only and isolated extraction succeeded |
| `DATA/FE_TV.PAK` | 8,282,688 | `ffd880ed25d385f8addbcbcee105032f5525112306f44db31f549c129cd9d6c4` | PAK1 | `0x800` | 79 | Listed, extracted, inventoried, and analyzed |
| `DATA/FE_MAIN.PAK` | 144,123,908 | `9b0edcf2bd8868de4450cf80bdd15967347bb5ea9b9dd7a312496cb1fb15d328` | PAK1 | `0x800` | 114 | Listed, extracted, inventoried, and analyzed |

`GENERAL.PAK` names exactly two paths:

- `DATA\SECTIONS.TXT`
- `DATA\SOUND\SCRIPTS\MISC.TXT`

`E_DATA.PAK` names 12,689 paths, all rooted at `DATA\SOUND`. Extension counts from its archive table are:

| Extension | Entries | Evidence-based observation |
|---|---:|---|
| `.mic` | 10,670 | **LIKELY:** audio stream/sample data based on `DATA\SOUND` location; codec/header not inspected |
| `.msb` | 630 | **LIKELY:** sound-bank data; frequently paired by name with `.msh` |
| `.msh` | 630 | **LIKELY:** companion sound metadata/header data; format unknown |
| `.bin` | 455 | **LIKELY:** compiled sound-script/data entries based on paths such as `DATA\SOUND\SCRIPTS\ENGLISH`; binary format unknown |
| `.cmh` | 301 | **LIKELY:** sound-related companion metadata based on location and naming; format unknown |
| `.txt` | 3 | **LIKELY:** text configuration/data by extension; entry content was not read |

Recurring path patterns include `DATA\SOUND\SCRIPTS`, `DATA\SOUND\STM`, and platform/category-like subfolders such as `EW` and `SW`. The largest listed entries are `.MIC` files below `DATA\SOUND\STM`; no codec claim is made without inspecting extracted entry headers in a later authorized task.

## FE_LANG Archive Result

`DATA/FE_LANG.PAK` was listed first, its paths and extents passed a traversal/duplicate/collision/bounds audit, and it was then extracted only to ignored `game-extracted/pak/FE_LANG`. All 32 paths and sizes matched the listing and the source hash remained unchanged. Its table contains 12 `.TM2`, 8 `.TXT`, 8 `.DIM`, 3 `.ICO`, and 1 `.MTL` entry. See `FE_LANG_ANALYSIS.md` for format and localization findings.

## FE_TV Archive Result

`DATA/FE_TV.PAK` is **LISTED, EXTRACTED, INVENTORIED, and ANALYZED**. Its 79 paths passed the same safety audit and extracted exactly to ignored `game-extracted/pak/FE_TV`, totaling 8,184,826 bytes. It contains 35 `.TM2`, 32 `.DIM`, 8 `.TXT`, 3 `.ICO`, and 1 `.MTL` entry. Comparison with FE_LANG found 20 hash-identical duplicated resources and strengthened the MTL/DIM structural models; see `FE_TV_ANALYSIS.md`.

## FE_MAIN Archive Result

`DATA/FE_MAIN.PAK` is **LISTED, EXTRACTED, INVENTORIED, and ANALYZED**. Its 114 ordered paths and extents passed the safety audit and extracted exactly to ignored `game-extracted/pak/FE_MAIN`, totaling 143,982,047 bytes. It contains 68 `.TM2`, 32 `.DIM`, 8 `.TXT`, 3 `.ICO`, 2 `.PSS`, and 1 `.MTL` entry. FE_MAIN adds confirmed MPEG-2 attract videos and explicit transitions to campaign, arena, and FE_XTRA sections; see `FE_MAIN_ANALYSIS.md`.

## Other Disc PAKs

Header-only inspection originally found 28 PAK1 archives beyond the two root archives: 27 under `DATA` and one under `IOP`. FE_LANG, FE_TV, and FE_MAIN have now been listed and extracted; the remaining 25 have not been listed or extracted.

| Group | Archives | Entry-count range | Status |
|---|---:|---:|---|
| `DATA/ARENA*.PAK` | 6 | 701–1,094 | Header confirmed; contents unknown |
| `DATA/FE_*.PAK` | 5 | 31–120 | FE_LANG, FE_TV, and FE_MAIN analyzed; FE_XTRA and FE_LOAD remain header-only |
| `DATA/LEVEL*.PAK` | 16 | 554–1,036 | Header confirmed; contents unknown |
| `IOP/GENERAL.PAK` | 1 | 2 | Header confirmed; contents unknown |

## Safety and Limitations

- QuickBMS returned exit code 0 for the GENERAL, E_DATA, FE_LANG, FE_TV, and FE_MAIN list operations and for the four authorized extractions.
- `GENERAL.PAK` reported 2 files, `E_DATA.PAK` 12,689, `FE_LANG.PAK` 32, `FE_TV.PAK` 79, and `FE_MAIN.PAK` 114.
- The initial survey read only archive table names, offsets, and logical sizes. Later controlled tasks extracted only GENERAL, FE_LANG, FE_TV, and FE_MAIN into separate ignored roots.
- FE_LANG's list contained 32 unique safe relative paths, aligned non-overlapping in-bounds extents, and no overwrite risk in its new isolated destination.
- FE_TV's 79-entry list passed equivalent checks, and its ordered final extent ends exactly at archive EOF.
- FE_MAIN's 114-entry list passed equivalent checks, and its ordered final extent ends exactly at archive EOF.
- Detailed local listings are generated research output under `logs/extraction` and `logs/analysis` and are not committed.
- Rebuild/reimport compatibility remains unverified; no extracted archive has been rewritten or reimported.
