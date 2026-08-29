# PAK Archive Overview

The initial survey used header reads and QuickBMS 0.12.0 `-l` list-only mode. Later controlled tasks extracted the two-entry root `GENERAL.PAK` and the 32-entry `DATA/FE_LANG.PAK`; see `GENERAL_PAK_ANALYSIS.md` and `FE_LANG_ANALYSIS.md`. No other PAK has been extracted, rewritten, or reimported.

## Common Container Header

All 30 disc-level PAK files begin with ASCII `PAK1` (`50 41 4b 31`). The existing `spartan_total_war.bms` script identifies this as PAK version 1, reads a little-endian file count from offset `0x08`, and reads alignment from offset `0x0c`. Every surveyed archive declares `0x800` alignment.

The script logs stored extents and does not invoke a decompressor. This indicates that the current extraction recipe treats entries as uncompressed stored regions; deeper format validation remains pending.

## Root Archive Results

| Archive | Size | SHA-256 | Version | Alignment | Listed entries | Result |
|---|---:|---|---:|---:|---:|---|
| `GENERAL.PAK` | 29,074 | `0ec7ec24f69625d5302c0a040f55803ff084e48655f8142d299bfc9bb97f6e1c` | PAK1 | `0x800` | 2 | List-only and isolated extraction succeeded |
| `E_DATA.PAK` | 1,514,409,600 | `bd2d12fe350e9afa68094c30645eac664c99104ac592c41926a71488a5f03e45` | PAK1 | `0x800` | 12,689 | List-only succeeded |
| `DATA/FE_LANG.PAK` | 1,348,160 | `b805a6dd51074b35e9b69fe06bd585a167b663ac3e4c8e009c289eb4efb9fbcb` | PAK1 | `0x800` | 32 | List-only and isolated extraction succeeded |

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

## Other Disc PAKs

Header-only inspection originally found 28 PAK1 archives beyond the two root archives: 27 under `DATA` and one under `IOP`. FE_LANG has now been listed and extracted; the remaining 27 have not been listed or extracted.

| Group | Archives | Entry-count range | Status |
|---|---:|---:|---|
| `DATA/ARENA*.PAK` | 6 | 701–1,094 | Header confirmed; contents unknown |
| `DATA/FE_*.PAK` | 5 | 31–120 | FE_LANG analyzed; four sibling front-end archives remain header-only |
| `DATA/LEVEL*.PAK` | 16 | 554–1,036 | Header confirmed; contents unknown |
| `IOP/GENERAL.PAK` | 1 | 2 | Header confirmed; contents unknown |

## Safety and Limitations

- QuickBMS returned exit code 0 for the GENERAL, E_DATA, and FE_LANG list operations and for the two authorized extractions.
- `GENERAL.PAK` reported 2 files, `E_DATA.PAK` reported 12,689 files, and `FE_LANG.PAK` reported 32 files.
- The initial survey read only archive table names, offsets, and logical sizes. Later controlled tasks extracted only root GENERAL's two text files and FE_LANG's 32 resources.
- FE_LANG's list contained 32 unique safe relative paths, aligned non-overlapping in-bounds extents, and no overwrite risk in its new isolated destination.
- Detailed local listings are generated research output under `logs/extraction` and `logs/analysis` and are not committed.
- Rebuild/reimport compatibility remains unverified; neither extracted archive has been rewritten or reimported.
