# File Format Registry

| Extension | Magic | Suspected Purpose | Confirmed Purpose | Parser/Tool | Notes | Status |
|---|---|---|---|---|---|---|
| `.93` (`SLES_533.93`) | `7f 45 4c 46` / ELF | Main game program | PS2 little-endian MIPS ELF32 boot executable | Header inspection; future Ghidra | Entry point `0x00200008`; no code analysis performed | Container/header confirmed |
| `.cnf` | ASCII `BOOT` | PS2 configuration | Text boot configuration | Text reader | Declares `SLES_533.93`, version 1.01, PAL | Confirmed |
| `.irx` | `7f 45 4c 46` / ELF | IOP runtime modules | ELF-based PS2 IOP modules | Header inspection; future Ghidra | 10 files under `IOP`; internal behavior not analyzed | Container/header confirmed |
| `.img` | `RESET`, `ROMDIR`, `EXTINFO` records | IOP reset/module image | Not fully parsed | Header inspection | `IOP/IOPRP300.IMG`; ROMDIR-style structure is visible | Likely; parsing pending |
| `.pak` | `50 41 4b 31` / `PAK1` | Game archive | PAK1 archive container | QuickBMS + `spartan_total_war.bms` 0.1.1 | 30 disc files; all declare version 1 and `0x800` alignment; two root archives safely listed | Header and listing confirmed; extraction pending |
| `.mic` | Not inspected | Sound stream/sample data | Unknown | PAK list-only metadata | 10,670 entries in `E_DATA.PAK`, all below `DATA\SOUND` | Likely purpose; format unknown |
| `.msb` | Not inspected | Sound-bank data | Unknown | PAK list-only metadata | 630 entries; commonly paired by name with `.msh` | Likely purpose; format unknown |
| `.msh` | Not inspected | Sound-bank companion metadata/header | Unknown | PAK list-only metadata | 630 entries; commonly paired by name with `.msb` | Likely purpose; format unknown |
| `.cmh` | Not inspected | Sound-related companion metadata | Unknown | PAK list-only metadata | 301 entries below `DATA\SOUND` | Likely purpose; format unknown |
| `.bin` | Not inspected | Compiled sound scripts/data | Unknown | PAK list-only metadata | 455 entries, including localized `DATA\SOUND\SCRIPTS` paths | Likely purpose; format unknown |
| `.txt` | Not inspected inside PAK | Text configuration/data | Unknown until extraction | PAK list-only metadata | 2 entries in `GENERAL.PAK`, 3 in `E_DATA.PAK`; contents not read | Extension/path evidence only |

No standalone standard image, model, or audio-container files were found at the disc-filesystem level. Inner PAK entry headers remain deliberately uninspected.
