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
