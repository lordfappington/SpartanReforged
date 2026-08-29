# File Format Registry

| Extension | Magic | Suspected Purpose | Confirmed Purpose | Parser/Tool | Notes | Status |
|---|---|---|---|---|---|---|
| `.93` (`SLES_533.93`) | `7f 45 4c 46` / ELF | Main game program | PS2 little-endian MIPS ELF32 boot executable | Header inspection; future Ghidra | Entry point `0x00200008`; no code analysis performed | Container/header confirmed |
| `.cnf` | ASCII `BOOT` | PS2 configuration | Text boot configuration | Text reader | Declares `SLES_533.93`, version 1.01, PAL | Confirmed |
| `.irx` | `7f 45 4c 46` / ELF | IOP runtime modules | ELF-based PS2 IOP modules | Header inspection; future Ghidra | 10 files under `IOP`; internal behavior not analyzed | Container/header confirmed |
| `.img` | `RESET`, `ROMDIR`, `EXTINFO` records | IOP reset/module image | Not fully parsed | Header inspection | `IOP/IOPRP300.IMG`; ROMDIR-style structure is visible | Likely; parsing pending |
| `.pak` | `50 41 4b 31` / `PAK1` | Game archive | PAK1 archive container | QuickBMS + `spartan_total_war.bms` 0.1.1 | 30 disc files; GENERAL, E_DATA, FE_LANG, and FE_TV safely listed; GENERAL, FE_LANG, and FE_TV isolated extractions verified | Header/list confirmed; three archives extracted; family extraction pending |
| `.mic` | Not inspected | Sound stream/sample data | Unknown | PAK list-only metadata | 10,670 entries in `E_DATA.PAK`, all below `DATA\SOUND` | Likely purpose; format unknown |
| `.msb` | Not inspected | Sound-bank data | Unknown | PAK list-only metadata | 630 entries; commonly paired by name with `.msh` | Likely purpose; format unknown |
| `.msh` | Not inspected | Sound-bank companion metadata/header | Unknown | PAK list-only metadata | 630 entries; commonly paired by name with `.msb` | Likely purpose; format unknown |
| `.cmh` | Not inspected | Sound-related companion metadata | Unknown | PAK list-only metadata | 301 entries below `DATA\SOUND` | Likely purpose; format unknown |
| `.bin` | Not inspected | Compiled sound scripts/data | Unknown | PAK list-only metadata | 455 entries, including localized `DATA\SOUND\SCRIPTS` paths | Likely purpose; format unknown |
| `.txt` | ASCII or legacy single-byte text | Ordered configuration, scripts, and localization tables | GENERAL manifests/configuration; FE_LANG/FE_TV state scripts and synchronized UI tables | Text reader; future custom parser | CRLF; `[key]` plus `{value}` localization records preserve ordered duplicates; FE_TV is an expanded 888-record snapshot; localized high bytes are non-UTF-8 | Front-end script/table families confirmed; parser pending |
| `.tm2` | `54 49 4d 32` / `TIM2` | PS2 textures | Single-picture, 8-bit indexed TIM2 textures and font atlases | Header parser; stock Noesis native TIM2 handler | 47 FE_LANG/FE_TV samples, 16×16 through 512×512, image type 5, one mip, 256-color CLUT | Container/header and front-end use confirmed; broader variants pending |
| `.dim` | `10 cd...` or `20 cd...` prefix | Font measurements | 1-byte size-class-like field, 63-byte `0xcd` fill, then 256 little-endian 16-bit measurements | Cross-font binary comparison | Values scale plausibly as glyph advances; paired with FONT14/18/18G/24 TIM2; `0x2000` Central-European FONT24 sentinel unknown | Structure confirmed; width semantics likely; edge cases pending |
| `.mtl` | No standalone magic | Resource declaration/index table | Name table plus length-delimited resource/property records | Cross-section binary parser/record comparison | u32 record offset/count, NUL names, variable top records and counted child blocks; five shared records byte-identical | Container structure confirmed; property semantics pending |
| `.ico` | `00 00 01 00 01 00...`, but not valid Windows ICO metadata | Memory-card icon/model data | Three byte-identical FE_LANG memory-card assets | Header inspection; stock Noesis recognition unconfirmed | 53,136 bytes each; generic `.ico` extension is misleading for this proprietary payload | Purpose likely; schema pending |

No standalone standard image, model, or audio-container files were found at the disc-filesystem level. Inner headers have been inspected only for the three specifically extracted archives: GENERAL, FE_LANG, and FE_TV.
