# PS2 Disc Filesystem

Full ISO9660 extraction completed on 2026-08-29 from the verified canonical `SLES-53393` image. The source ISO was read only, filenames and directory structure were preserved, and no PAK archive was unpacked.

## Extraction Summary

| Field | Value |
|---|---:|
| Method | 7-Zip 26.02 ISO extraction |
| Files | 43 |
| Directories below root | 2 |
| Extracted file bytes | 2,177,740,285 |
| Disc-level extensions | 5 |
| Destination | `game-extracted/disc` |

The local generated inventories are stored in `logs/extraction/disc_inventory.csv`, `disc_inventory.json`, `disc_extensions.csv`, and `disc_extensions.json`. They are not committed.

## Directory Map

| Path | Immediate files | Immediate subdirectories | Recursive files | Recursive file bytes |
|---|---:|---:|---:|---:|
| `.` | 4 | 2 | 43 | 2,177,740,285 |
| `DATA` | 27 | 0 | 27 | 658,961,242 |
| `IOP` | 12 | 0 | 12 | 684,033 |

## Complete Hierarchy

```text
/
├── SYSTEM.CNF
├── SLES_533.93
├── GENERAL.PAK
├── E_DATA.PAK
├── DATA/
│   ├── ARENAB.PAK
│   ├── ARENAG.PAK
│   ├── ARENAP.PAK
│   ├── ARENAR.PAK
│   ├── ARENAU.PAK
│   ├── ARENAX.PAK
│   ├── FE_LANG.PAK
│   ├── FE_LOAD.PAK
│   ├── FE_MAIN.PAK
│   ├── FE_TV.PAK
│   ├── FE_XTRA.PAK
│   ├── LEVEL00.PAK
│   ├── LEVEL01.PAK
│   ├── LEVEL02.PAK
│   ├── LEVEL03.PAK
│   ├── LEVEL04.PAK
│   ├── LEVEL05.PAK
│   ├── LEVEL06.PAK
│   ├── LEVEL07.PAK
│   ├── LEVEL07D.PAK
│   ├── LEVEL08.PAK
│   ├── LEVEL09.PAK
│   ├── LEVEL10.PAK
│   ├── LEVEL11.PAK
│   ├── LEVEL12.PAK
│   ├── LEVEL13.PAK
│   └── LEVEL14.PAK
└── IOP/
    ├── CDVDSTM.IRX
    ├── DBCMAN.IRX
    ├── DS2U.IRX
    ├── GENERAL.PAK
    ├── IOPRP300.IMG
    ├── LIBSD.IRX
    ├── MCMAN.IRX
    ├── MCSERV.IRX
    ├── SDRDRV.IRX
    ├── SIO2D.IRX
    ├── SIO2MAN.IRX
    └── STREAM.IRX
```

## Disc-Level Extension Summary

| Extension | Files | Total bytes | Smallest | Largest | Example |
|---|---:|---:|---|---|---|
| `.pak` | 30 | 2,173,426,979 | `IOP/GENERAL.PAK` (27,063) | `E_DATA.PAK` (1,514,409,600) | `DATA/LEVEL00.PAK` |
| `.irx` | 10 | 381,625 | `IOP/SIO2MAN.IRX` (6,641) | `IOP/STREAM.IRX` (162,512) | `IOP/CDVDSTM.IRX` |
| `.93` | 1 | 3,656,280 | `SLES_533.93` | `SLES_533.93` | `SLES_533.93` |
| `.img` | 1 | 275,345 | `IOP/IOPRP300.IMG` | `IOP/IOPRP300.IMG` | `IOP/IOPRP300.IMG` |
| `.cnf` | 1 | 56 | `SYSTEM.CNF` | `SYSTEM.CNF` | `SYSTEM.CNF` |

## Significant Files

| Path/group | Size | Type | Evidence-based purpose |
|---|---:|---|---|
| `SYSTEM.CNF` | 56 | Text configuration | **CONFIRMED:** PS2 boot configuration for `SLES_533.93`, version 1.01, PAL |
| `SLES_533.93` | 3,656,280 | MIPS ELF32 executable | **CONFIRMED:** main PS2 Emotion Engine boot executable |
| `E_DATA.PAK` | 1,514,409,600 | PAK1 archive | **CONFIRMED:** archive; safe listing shows only `DATA\SOUND` content paths |
| Root `GENERAL.PAK` | 29,074 | PAK1 archive | **CONFIRMED:** two-entry archive containing text-named configuration paths |
| `DATA/LEVEL*.PAK` | varies | PAK1 archives | **LIKELY:** level-specific archives based on names only; contents not listed or extracted |
| `DATA/ARENA*.PAK` | varies | PAK1 archives | **LIKELY:** arena-specific archives based on names only |
| `DATA/FE_*.PAK` | varies | PAK1 archives | **LIKELY:** front-end archives based on names only |
| `IOP/*.IRX` | 6,641–162,512 | ELF-based IRX modules | **CONFIRMED:** PS2 IOP modules; internal behavior not analyzed |
| `IOP/IOPRP300.IMG` | 275,345 | ROMDIR-style image | **LIKELY:** IOP reset/module image; header exposes `RESET`, `ROMDIR`, and `EXTINFO` records |
| `IOP/GENERAL.PAK` | 27,063 | PAK1 archive | **UNKNOWN:** IOP-adjacent archive; contents not listed |

## Required File Verification

| File | Size | SHA-256 |
|---|---:|---|
| `SLES_533.93` | 3,656,280 | `55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d` |
| `GENERAL.PAK` | 29,074 | `0ec7ec24f69625d5302c0a040f55803ff084e48655f8142d299bfc9bb97f6e1c` |
| `E_DATA.PAK` | 1,514,409,600 | `bd2d12fe350e9afa68094c30645eac664c99104ac592c41926a71488a5f03e45` |

`SYSTEM.CNF` exactly matches the previously recorded 56-byte boot configuration. All required root files and both required directories are present.

