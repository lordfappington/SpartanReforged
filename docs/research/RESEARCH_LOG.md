# Research Log

## 2026-08-28 - Initial environment audit

- Created the Milestone 0 workspace structure without inspecting or modifying game data.
- Confirmed Git, Python, pip, 7-Zip, GitHub Desktop, and PCSX2 were already installed.
- Began installation and verification of the remaining development tools.
- Identified `ran-j/PS2Recomp` as the active public PS2 static recompilation upstream.
- Identified Luigi Auriemma's `spartan_total_war.bms` for QuickBMS as the available game-specific PAK extraction script; rebuild support remains unverified.
- Installed Visual Studio Community 2022 with the Native Desktop workload and verified an MSVC C++20 configure/build/run smoke test using Windows SDK 10.0.26100.0.
- Installed CMake, Temurin JDK 21, Ghidra, HxD, Noesis, RenderDoc, Blender, FFmpeg, and ImageMagick. Ghidra headless startup and Noesis GUI startup were verified.
- Cloned PS2Recomp recursively at commit `14b1e5cb39b4af7e6fc12f9a29fdc751efde49d7` on branch `main`.
- Retrieved QuickBMS 0.12.0 and `spartan_total_war.bms` 0.1.1 from the author-operated mirror after the primary download endpoint returned HTTP 403.
- Syntax-checked and functionally tested all internal scripts using only generated dummy files under the ignored `temp` directory.

## 2026-08-29 - Canonical PS2 image identified

- Identified the in-place ISO as the Europe/Australia PAL release, serial `SLES-53393`, disc version 1.01.
- Recorded SHA-256 `7d7092a4d379cbd83da3ad1ede6ebd88db031c6c774039f39cf6c8f4af00dbf6` and MD5 `491931ef831f87bb22cceef3aca14871` for the 2,199,420,928-byte image.
- Confirmed an exact filename, size, and MD5 match with verified Redump record 7850.
- Read `SYSTEM.CNF` directly from its ISO extent: boot executable `SLES_533.93`, `VER = 1.01`, and `VMODE = PAL`.
- Confirmed the boot file is a little-endian MIPS ELF32 executable with entry point `0x00200008`.
- Parsed only the ISO9660 primary volume descriptor and root directory. Root entries are `SYSTEM.CNF`, `SLES_533.93`, `GENERAL.PAK`, `E_DATA.PAK`, `IOP`, and `DATA`; directories and PAK archives were not opened.
- Structural checks passed: valid descriptor chain, declared volume size equals file size, root records are consistent, and boot target/header are valid.
- Uncertainty: European versus Australian physical packaging cannot be distinguished because the verified disc data is shared by `SLES-53393` and `SLES-53393-ANZ` packaging variants.
- The original ISO remained in place, read-only from the workflow's perspective, ignored by Git, and unstaged.

## 2026-08-29 - Disc filesystem extracted and catalogued

- Verified an independent backup at `%USERPROFILE%\Downloads\bios\games\Spartan - Total Warrior (Europe, Australia) (En,Fr,De,Es,It).iso` with SHA-256 `7d7092a4d379cbd83da3ad1ede6ebd88db031c6c774039f39cf6c8f4af00dbf6`, exactly matching the canonical source.
- Extracted the complete ISO9660 filesystem with 7-Zip 26.02 into ignored `game-extracted/disc`; extraction completed without errors and no PAK was unpacked.
- Catalogued 43 files in 2 directories totaling 2,177,740,285 bytes. Disc-level extensions are `.pak` (30), `.irx` (10), `.93` (1), `.img` (1), and `.cnf` (1).
- Verified `SYSTEM.CNF`, `SLES_533.93`, `GENERAL.PAK`, `E_DATA.PAK`, `DATA`, and `IOP`; the executable retains its expected 3,656,280-byte size and the boot configuration matches the identity report.
- Recorded SHA-256 values: executable `55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d`, root `GENERAL.PAK` `0ec7ec24f69625d5302c0a040f55803ff084e48655f8142d299bfc9bb97f6e1c`, and `E_DATA.PAK` `bd2d12fe350e9afa68094c30645eac664c99104ac592c41926a71488a5f03e45`.
- Header survey found all 30 PAKs use `PAK1` and declare `0x800` alignment. Ten IRX files use ELF headers; `IOPRP300.IMG` exposes `RESET`, `ROMDIR`, and `EXTINFO` records.
- QuickBMS list-only mode completed successfully without extraction: root `GENERAL.PAK` contains 2 named text paths, while `E_DATA.PAK` contains 12,689 entries, all below `DATA\SOUND`.
- `E_DATA.PAK` listing extensions: `.mic` 10,670; `.msb` 630; `.msh` 630; `.bin` 455; `.cmh` 301; `.txt` 3.
- Important disc directories are `DATA` (27 PAKs) and `IOP` (10 IRX modules, one IMG, and one PAK).
- Unknowns include all proprietary inner schemas/codecs, the contents of level/arena/front-end archives, and the exact purpose of `IOP/GENERAL.PAK`.
- Generated CSV/JSON inventories and list-only output remain local under `logs/extraction` and are not committed.

## 2026-08-29 - Root GENERAL.PAK extracted and analyzed

- Reverified source `GENERAL.PAK` SHA-256 `0ec7ec24f69625d5302c0a040f55803ff084e48655f8142d299bfc9bb97f6e1c` before extraction.
- Extracted only root `GENERAL.PAK` with QuickBMS into ignored `game-extracted/pak/GENERAL`; the destination was empty and QuickBMS reported exactly two files with no errors.
- Verified `DATA/SECTIONS.TXT` (1,788 bytes, SHA-256 `5f7aa226244a36e7c8aa41747737d4975e2d1118415099d81928e0ba571df5d9`) and `DATA/SOUND/SCRIPTS/MISC.TXT` (24,978 bytes, SHA-256 `eaf11f7bfaa1625fc275208c71c588acfce3d1253540a463094eaafaf3e8805c`).
- Rehashed the source archive after extraction; its size, timestamp, and SHA-256 were unchanged.
- `SECTIONS.TXT` is a 30-section registration/allocation manifest. It declares `fe_lang` as the initial section, classifies six front-end entries as `FNT_END`, classifies 23 arena/level entries as `STD_LEVEL`, and maps them to `DATA\ENV` logical paths.
- Section names align with the front-end, arena, and level archive basenames, except that `fe_splash` and `level99/testlevel` have no same-named disc PAK.
- `MISC.TXT` is an ordered cross-platform audio configuration with duplicate-key record groups. It configures sound volumes, stream fading, character fall sounds, a 7×7 crowd sound grid, and 19 PS2/Xbox reverb presets; `GC_EFFECTS` is present but empty.
- No direct audio asset filenames occur in `MISC.TXT`; effect identifiers are presets rather than confirmed gameplay sound events.
- No other PAK was opened or extracted. The project-wide “PAK archives successfully unpacked” milestone remains incomplete.

## 2026-08-29 - FE_LANG.PAK extracted and analyzed

- Reverified `DATA/FE_LANG.PAK`: 1,348,160 bytes, SHA-256 `b805a6dd51074b35e9b69fe06bd585a167b663ac3e4c8e009c289eb4efb9fbcb`, `PAK1` version 1, 32 entries, and `0x800` alignment.
- Ran QuickBMS list-only first. All 32 paths passed traversal, absolute-path, duplicate, collision, alignment, overlap, and bounds checks.
- Extracted only FE_LANG to ignored `game-extracted/pak/FE_LANG`; all 32 paths and sizes matched the listing, no unexpected files appeared, and the source hash remained unchanged.
- Inventoried 12 `.TM2`, 8 `.TXT`, 8 `.DIM`, 3 `.ICO`, and 1 `.MTL` file totaling 1,312,166 extracted bytes. Generated reports remain local under `logs/analysis`.
- Confirmed TIM2 texture headers and dimensions from 16×16 through 256×256. Eight `FONT14.TM2` atlases pair with 576-byte `.DIM` tables containing 256 little-endian width-like values.
- Confirmed seven synchronized UI localization tables (English, French, German, Italian, Spanish, Polish, Czech): each has 699 records, 678 unique keys, and the same 21 duplicated key names. Japanese has a font pair but no UI table in this archive.
- Confirmed `FE_LANG.TXT` as a boot-time language menu script. It defines language selection and explicitly transfers control to `fe_tv`, matching GENERAL's `start_section="fe_lang"` and sibling `FNT_END` declarations.
- Found the three memory-card `.ICO` files are byte-identical proprietary payloads rather than conventional Windows ICO containers. Stock Noesis TIM2 support is present; recognition of the custom `.ICO` payload remains unconfirmed. No conversion or plugin installation occurred.
- No other PAK was opened. No Ghidra, PS2Recomp, conversion, modification, or upscaling work occurred, and broad Milestone 0 completion boxes remain unchanged.

## 2026-08-29 - FE_TV.PAK extracted, analyzed, and compared

- Verified `DATA/FE_TV.PAK`: 8,282,688 bytes, SHA-256 `ffd880ed25d385f8addbcbcee105032f5525112306f44db31f549c129cd9d6c4`, `PAK1` version 1, 79 entries, and `0x800` alignment.
- Ran QuickBMS list-only first. All paths and extents passed traversal, malformed/reserved-name, duplicate, collision, alignment, overlap, and bounds checks; entry order is ascending by offset.
- Extracted only FE_TV to ignored `game-extracted/pak/FE_TV`. All 79 listed paths and sizes matched, no extra appeared, total output is 8,184,826 bytes, and the source hash remained unchanged.
- Inventoried 35 `.TM2`, 32 `.DIM`, 8 `.TXT`, 3 `.ICO`, and 1 `.MTL` entry. Generated listings/reports remain local under `logs/analysis`.
- Confirmed all 35 TIM2 files are one-picture, one-mip, 8-bit indexed images with 256-color CLUTs; dimensions are 16×16, 256×256, or 512×512.
- Strengthened the DIM model to a 1-byte size-class-like value, 63 `0xcd` bytes, and 256 u16 advance-like measurements. FONT18/FONT18G share measurements; Czech/Polish FONT24 contains an unexplained `0x2000` sentinel.
- Parsed both front-end MTL samples as a name table plus variable length-delimited records containing counted child/property blocks. Five shared records are byte-identical; numeric property semantics remain unknown.
- FE_TV's UI tables contain all 699 FE_LANG records in the same key order plus 189 keys per language, while many localized values are revised. Twenty FE_TV assets are byte-identical to FE_LANG counterparts or shared paths.
- Confirmed the section graph FE_LANG → FE_TV, then FE_TV → FE_MAIN for normal video states or FE_TV → FE_LOAD from the tester path. No runtime order beyond these explicit script edges was inferred.
- No other PAK was opened. No asset conversion/modification, Ghidra, or PS2Recomp work occurred; broad milestone boxes remain unchanged.
