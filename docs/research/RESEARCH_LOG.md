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

## 2026-08-29 - FE_MAIN.PAK extracted, analyzed, and compared

- Verified `DATA/FE_MAIN.PAK`: 144,123,908 bytes, SHA-256 `9b0edcf2bd8868de4450cf80bdd15967347bb5ea9b9dd7a312496cb1fb15d328`, `PAK1` version 1, 114 entries, and `0x800` alignment.
- Ran QuickBMS list-only first. All ordered paths and extents passed traversal, malformed/reserved-name, duplicate, collision, alignment, overlap, and bounds checks; the final extent ends exactly at archive EOF.
- Extracted only FE_MAIN to ignored `game-extracted/pak/FE_MAIN`. All 114 paths and sizes matched, no extra appeared, total output is 143,982,047 bytes, and the source hash remained unchanged.
- Inventoried 68 `.TM2`, 32 `.DIM`, 8 `.TXT`, 3 `.ICO`, 2 `.PSS`, and 1 `.MTL` file. Generated listing/inventory/magic reports remain local under `logs/analysis`.
- Confirmed all 68 TIM2 resources are one-picture, one-mip, 8-bit indexed images with 256-color CLUTs, spanning 16×16 through 512×512. Names and script bindings identify UI atlases plus smoke/fog/glow/flare effect textures.
- Confirmed both PSS files as about 94-second MPEG program streams containing MPEG-2 video: 512×224 at 30000/1001 fps and 512×256 at 25 fps. FE_MAIN selects them by platform/video-system state for its attract loop; FFprobe reported no audio stream.
- Confirmed the 576-byte DIM layout in all 32 font tables. Their prefix schema matches FE_TV, but 1–17 measurements and all paired atlases differ; Czech/Polish FONT24 retain `0x2000` at indices 191 and 223.
- Parsed FE_MAIN MTL as 45 records ending exactly at EOF. All 10 FE_TV-shared and all 7 FE_LANG-shared records are byte-identical, even where the referenced section asset differs, strongly supporting stable resource declarations rather than a conventional material-file claim.
- Analyzed the 8,717-line main script: 35 distinct TIM2 filenames, 13 emitters, 111 menus, symbolic SFX/music, MPEG playback, save/profile/unlock logic, and explicit exits to `level00`–`level14`, `level07d`, six arena sections, and `fe_xtra`. The `map_512.tga` reference conflicts with packaged `MAP_512.TM2` and remains unexplained.
- FE_MAIN has no mesh/model, skeleton, character-animation, world-placement, 3D scene, or 3D camera payload evidence. Its animation/transform commands target UI objects, while its emitters confirm a front-end 2D effect system.
- Exact duplicated content includes 12 FE_MAIN files found in FE_TV and seven found in FE_LANG by hash. Seven UI tables exactly match FE_TV, and shared generic icons/remapping resources remain identical across all three sections.
- The self-contained-section model is strengthened: FE_MAIN embeds its script, declarations, localized text, fonts, UI/effect textures, generic assets, and both large videos. The phase is now `Milestone 0 - Section Asset Architecture`; broad format/unpacking milestones remain incomplete.
- No other PAK was opened. No asset conversion/modification, Ghidra, PS2Recomp, or installation occurred.

## 2026-08-30 - LEVEL00.PAK gameplay architecture mapped

- Verified `DATA/LEVEL00.PAK`: 13,652,833 bytes, SHA-256 `e708df44976b93b4d0fa355f850e387f04dee580b27f927f4e906f1f9d095d80`, `PAK1` version 1, 640 entries, and `0x800` alignment.
- Ran QuickBMS list-only first. Every ordered path and extent passed traversal, malformed/reserved-name, duplicate, collision, alignment, overlap, and bounds checks; the final extent ends exactly at archive EOF.
- Extracted only LEVEL00 to ignored `game-extracted/pak/LEVEL00`. All 640 paths and sizes matched, no extra appeared, total output is 12,890,963 bytes, and the source hash remained unchanged.
- Catalogued 23 extensions: 461 ANM, 58 TM2, 46 TXT, 39 PSQ, 7 BNS, 7 DIM, 4 MPH, 2 BIN, 2 SAM, and one each AAB/BIG/COL/DAT/ENT/FLP/HMP/IND/INS/MTL/MVR/PSW/PT2/STL. Nineteen extensions are new relative to the three front-end sections.
- Confirmed 461 `anm1` animation resources and two `sam2` cutscene animation containers. Embedded metadata identifies impact timing/offsets, loop/ladder behavior, weapon attachments, and cutscene tracks; binary track schemas remain unknown.
- Identified PSQ, PSW, MPH, and BNS character families. The Spartan body is the richest set: standard geometry candidate, multiweighted candidate, face candidate, BNS, two textures, and display flags. Five NPC BNS files are byte-identical, supporting a shared humanoid compatibility class.
- Mapped the seven-file `MODELS.*` world family. `MODELS.BIN` is the P0 world-geometry candidate; AAB likely carries spatial bounds, MTL provides 55 resource records, MVR embeds `Brazier_Dark.CAS` source identities, and FLP/INS/STL remain unresolved companions.
- Confirmed LEVEL00 TIM2 use across environment, characters, particles, UI, and fonts. Gameplay adds image types 3/4/5, multiple CLUT modes, 16/256 colors, and four-mip 4-bit indexed environment pages. Only `NON_LINEAR_REMAPPING.TM2` matches the front-end trees by hash.
- Recovered a 227-identifier string area in `TEST.ENT` covering player start/checkpoint, spawners/squads/character zones, cameras and relays, SAM filenames, particles, an interactive brazier, voice/music IDs, and a transition to LEVEL01.
- Proved that the seven u32 values in `CHAR_TYPES.BIN` resolve through identical NAMES tables to the seven packaged model families: Spartan, Hoplite, Swordsman, Athenian Archer, Castor, Pollux, and Leonidas.
- Identified the OLFS collision/navigation family: `PLANES.COL`, `WAYPTS3D.PT2`, and `WAYPT_INDICES.IND`. Together with ENT spawners/zones and the 75-character BATTLE combat/AI tuning table, these are high-value crowd-system targets.
- Mapped the readable particle dependency chain from eight APP_* TIM2 pages through same-named page-description TXT files, base material/effect lists, `MARS_SMOKE2` emitter parameters, and compiled `SAMPLES.DAT` candidate.
- Confirmed audio is external to LEVEL00: ENT and localization files provide symbolic voice/music references, but no audio payload or E_DATA mapping is packaged.
- Assessed LEVEL00 as a suitable initial gameplay Rosetta Stone because it includes every major visual/gameplay category except audio payloads and provides several explicit cross-file joins. Recommended next target is bounded structural analysis of `MODELS.BIN`.
- Advanced the phase to `Milestone 0 - Gameplay Asset Architecture` and marked texture, model investigation, animation investigation, level/scene investigation, and scripts/config/data-table investigation as supported. All-PAK unpacking and audio remain incomplete.
- No other PAK was opened. No conversion, rendering, asset modification, Ghidra, PS2Recomp, speculative parser, or installation occurred.

## 2026-08-30 - LEVEL00 MODELS world structures mapped

- Reverified all seven ignored MODELS-family inputs directly. `MODELS.BIN` is 2,293,536 bytes with SHA-256 `8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3`; AAB and MTL identities are recorded in the new family document.
- Confirmed the BIN header's exact-size field and 1,338-count descriptor table. Its 16-byte descriptors are contiguous, aligned, cover the complete payload from `0x53c0` to EOF, and carry ordered MTL indices in their high u16.
- Parsed all 1,338 payload blocks end-to-end as 2,128 coherent PS2 VIF batches: STCYCL, duplicated V4-32 control vectors, V4-32 position/control data, V2-16 attributes, V4-8 attributes, and MSCALF with alignment NOPs. No unknown command or recovery scan was required.
- Counted 88,314 streamed vertex instances. Position W is only zero or `0x8000`, and the first two vertices of every batch are `0x8000`; this strongly supports implicit ADC-controlled triangle strips, but the 46,336 candidate emitted triangles remain likely until winding/restart behavior is proven.
- Proved that BIN is name-free and binds numerically to the 55 ordered MTL records. Thirty-nine MTL indices are used; the AAB-indexed static partition uses world records 5–20 and 33–35.
- Traversed AAB as a complete seven-level 4-way tree: 5,461 nodes, 1,365 internal nodes, and 4,096 leaves. Its 484 non-empty leaf-associated lists contain 1,224 unique descriptor IDs covering BIN 114–1337 exactly once.
- Confirmed STL as a 32-slot table whose eight active values select MTL particle records 40–47. Confirmed FLP as fourteen 80-byte records and MVR as six 264-byte `Brazier_Dark.CAS` records; exact FLP records recur in MVR. INS remains an unexplained eight-u32 table.
- Added deterministic standard-library `tools/analysis/models_family_probe.py`; syntax checks pass and repeated reports are byte-identical. Generated output remains local under `logs/analysis`.
- Advanced the phase to `Milestone 0 - World Geometry Format Reverse Engineering`. MODELS container/VIF/AAB/MTL relationships are established, but the format is not marked understood and no production parser, converter, renderer, or geometry export was created.
- No PAK was opened, no extracted game file was changed, and no Ghidra, PS2Recomp, mutation, installation, or push occurred.
