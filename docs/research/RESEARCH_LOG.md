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
