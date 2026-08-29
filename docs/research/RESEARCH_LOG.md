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
