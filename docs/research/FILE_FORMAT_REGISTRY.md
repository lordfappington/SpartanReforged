# File Format Registry

| Extension | Magic | Suspected Purpose | Confirmed Purpose | Parser/Tool | Notes | Status |
|---|---|---|---|---|---|---|
| `.93` (`SLES_533.93`) | `7f 45 4c 46` / ELF | Main game program | PS2 little-endian MIPS ELF32 boot executable | Header inspection; future Ghidra | Entry point `0x00200008`; no code analysis performed | Container/header confirmed |
| `.cnf` | ASCII `BOOT` | PS2 configuration | Text boot configuration | Text reader | Declares `SLES_533.93`, version 1.01, PAL | Confirmed |
| `.irx` | `7f 45 4c 46` / ELF | IOP runtime modules | ELF-based PS2 IOP modules | Header inspection; future Ghidra | 10 files under `IOP`; internal behavior not analyzed | Container/header confirmed |
| `.img` | `RESET`, `ROMDIR`, `EXTINFO` records | IOP reset/module image | Not fully parsed | Header inspection | `IOP/IOPRP300.IMG`; ROMDIR-style structure is visible | Likely; parsing pending |
| `.pak` | `50 41 4b 31` / `PAK1` | Game archive | PAK1 archive container | QuickBMS + `spartan_total_war.bms` 0.1.1 | 30 disc files; all declare version 1 and `0x800` alignment; root `GENERAL.PAK`, root `E_DATA.PAK`, and `DATA/FE_LANG.PAK` safely listed; GENERAL and FE_LANG isolated extractions verified | Header/list confirmed; two archives extracted; family extraction pending |
| `.mic` | Not inspected | Sound stream/sample data | Unknown | PAK list-only metadata | 10,670 entries in `E_DATA.PAK`, all below `DATA\SOUND` | Likely purpose; format unknown |
| `.msb` | Not inspected | Sound-bank data | Unknown | PAK list-only metadata | 630 entries; commonly paired by name with `.msh` | Likely purpose; format unknown |
| `.msh` | Not inspected | Sound-bank companion metadata/header | Unknown | PAK list-only metadata | 630 entries; commonly paired by name with `.msb` | Likely purpose; format unknown |
| `.cmh` | Not inspected | Sound-related companion metadata | Unknown | PAK list-only metadata | 301 entries below `DATA\SOUND` | Likely purpose; format unknown |
| `.bin` | Not inspected | Compiled sound scripts/data | Unknown | PAK list-only metadata | 455 entries, including localized `DATA\SOUND\SCRIPTS` paths | Likely purpose; format unknown |
| `.txt` | ASCII or legacy single-byte text | Ordered configuration, scripts, and localization tables | GENERAL manifests/configuration; FE_LANG world/menu script and seven synchronized UI tables | Text reader; future custom parser | CRLF; FE_LANG localization uses `[key]` plus `{value}` records and ordered duplicate keys; localized high bytes are non-UTF-8 | GENERAL and FE_LANG families confirmed; other archives pending |
| `.tm2` | `54 49 4d 32` / `TIM2` | PS2 textures | Single-picture, 8-bit indexed TIM2 textures and font atlases | Header parser; stock Noesis native TIM2 handler | FE_LANG sample: 12 images, 16×16 through 256×256, image type 5, 256-color CLUT | Container/header and purpose confirmed; broader variants pending |
| `.dim` | No standalone magic; `10 cd...` prefix | Font metrics | 64-byte prefix followed by 256 little-endian 16-bit glyph-width-like values | Header/table inspection | Paired with `FONT14.TM2`; Czech/Polish share a distinct table | Structure partly confirmed; semantics pending |
| `.mtl` | No standalone magic | Material/resource lookup table | FE_LANG binary table naming eight front-end resources | Header and printable-string inspection | Starts with `0x70`, count 8; record fields at `0x70` remain unknown | Purpose likely; schema pending |
| `.ico` | `00 00 01 00 01 00...`, but not valid Windows ICO metadata | Memory-card icon/model data | Three byte-identical FE_LANG memory-card assets | Header inspection; stock Noesis recognition unconfirmed | 53,136 bytes each; generic `.ico` extension is misleading for this proprietary payload | Purpose likely; schema pending |

No standalone standard image, model, or audio-container files were found at the disc-filesystem level. Inner headers have been inspected only for the two specifically extracted archives, GENERAL and FE_LANG.
