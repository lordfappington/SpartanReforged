# Research Log

## 2026-08-31 - Bounded native render-state executable investigation

- Reverified the canonical 3,656,280-byte `SLES_533.93` SHA-256, little-endian MIPS ELF32 identity, and entry point `0x00200008`; also reverified the 5,952-byte MODELS.MTL and its 55 records / 173 numeric children.
- Imported the executable headlessly in Ghidra 12.1.3 using `MIPS:LE:64:64-32addr` / `o32`, the closest stock R5900 approximation. Auto-analysis found 6,963 functions across `0x00200000..0x0057c77f`.
- Anchored the LEVEL00 MTL load path at `0x002c3400` / `0x002c345c`, deserialization entry `0x002605d0`, and large stream parser `0x0026d2d0`.
- Identified `FUN_002490c0` as a paired-context GS packet builder: instructions `0x00249124..0x00249138` install `TEST_1`, `ALPHA_1`, `ZBUF_1`, `TEST_2`, `ALPHA_2`, and `ZBUF_2` destinations. Its caller chain leads through graphics-context initialization, not a proven material branch.
- Stock Ghidra does not model the R5900 `LQ`/`SQ`, multimedia, or COP2/VU instructions crossing both critical regions. The required type-2-child -> runtime-field -> render-preset -> GS-payload trace could not be established safely.
- Kept type-2 values 2–5, CLOUD A/B/C/D/FIX, TEST/AREF, depth write/test, draw order, and V4 -> RGBAQ **UNKNOWN/LIKELY exactly as evidence permits**. No exporter/native-state mapping or Blender approximation was added.
- Added bounded reusable Ghidra survey, seeding, targeted decompile, and instruction-window scripts. All Ghidra projects and generated reports remain ignored under `temp`; no executable or game asset changed.
- All four Ghidra scripts compiled and executed headlessly. The unchanged relevant synthetic Python suite also passes 35/35 tests; no speculative native-state tests were added because no material-state mapping was recovered.
- Readiness remains **TEXTURED ASSEMBLY VALIDATED; WORLD RECONSTRUCTION NOT COMPLETE**. The next single task is validated R5900 language support followed by the same narrow data-flow trace.

## 2026-08-30 - LEVEL00 MODELS V4 effect attributes analyzed

- Reverified canonical MODELS.BIN (`8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3`) and MODELS.MTL (`57283516fc3cc8589eec4817cf8c25dc3ff0cc2185e4ff99e262fa6f3a4a54b2`) and confirmed CLOUD remains descriptor 48 / MTL 31 / type-2 value 5 with 1,957 records and 1,728 triangles.
- Surveyed all 88,314 V4-8 tuples. Bytes 0–2 span 0..255 with 147/147/125 unique values; byte 3 is exactly `0x80` globally. Signed and biased unit-normal hypotheses fit poorly.
- Established a six-tuple CLOUD gradient: its first three channels darken strongly with height and brighten toward the lower radial ring, while alpha never varies. The native opaque texture multiplied by full vertex alpha remains fully opaque.
- Correlated V4 behavior by all 39 used materials and MTL type-2 families. Type-2 values 3 and 4 use neutral `(127,127,127,128)`; GRKTREE/GREENERY use texture alpha plus likely tint; value 5 remains a broad mixed render family.
- Checked primary PS2 sources: ps2sdk and gsKit use component scaling by 128 and document `0x80` as 1.0 alpha; PCSX2/ps2sdk distinguish vertex modulation from programmable GS ALPHA operands. Spartan-specific VU routing remains likely, not confirmed.
- Added deterministic `models_v4_probe.py` and synthetic tests. The ignored aggregate report contains no raw dump and repeated generation is deterministic.
- Added opt-in exporter `--v4-color ps2-rgba`; forensic output still omits V4. The glTF-safe `min(byte/128,1)` transform round trip passes for all 88,314 records, and Blender imports 1,338 objects / 46,336 polygons with the color layer intact. Raw values above 128 remain lossless in the parser.
- Local opaque versus additive-family diagnostics explain CLOUD's shell: opaque texture-times-V4 occludes, while additive approximations expose the scene and retain its ring gradient. They do not establish exact GS operands or FIX.
- Classified V4 semantics **LIKELY color/light modulation**, CLOUD transparency source **LIKELY native blend/depth family**, and type-2 value 5 **LIKELY broad render family / exact equation UNKNOWN**. Readiness remains **TEXTURED ASSEMBLY VALIDATED**; world reconstruction is not complete.
- No other PAK was opened, no game asset was changed, and no Ghidra, PS2Recomp, installation, or push occurred.

## 2026-08-30 - MODELS MTL culling/alpha semantics bounded

- Reverified the canonical 5,952-byte `MODELS.MTL` SHA-256 and parsed all 55 records to EOF. Generated an ignored record/property matrix joined to all 39 geometry-used materials, descriptor/triangle counts, confirmed texture bindings, and decoded alpha classes.
- Found no numeric MTL child that cleanly selects culling/two-sided behavior. PS2 GS `PRIM` has no cull field; an opt-in all-double-sided glTF approximation removes the full-scene culling holes, but Spartan pre-GS culling remains unknown.
- Established child type 2 as a **STRONG** alpha/render-family candidate: it covers all nine binary/partial-alpha bound materials with no false negatives and three opaque false positives. Values 1–5 recur coherently across cutout, foliage, and effect-like records, but native enum names/equations remain unknown.
- Corrected `CLOUD`: its decoded image alpha is fully opaque, not partial. MTL 31/type-2 value 5 uses one 1,728-triangle shell. Standard source-alpha glTF blending cannot remove it, so the native blend equation, V4-8, or another effect input remains required.
- Added opt-in `--mtl-render-semantics experimental`; raw remains the default. The experiment exports 39 double-sided materials, 30 OPAQUE, zero MASK, and nine BLEND, with no invented threshold. Exact 46,336-triangle round trip passes.
- Blender 5.2.1 LTS imported 1,338 meshes, 46,336 polygons, 39 materials, and 30 images; all 39 are double-sided and nine import blended. Culling holes and dark alpha-page regions improve; `CLOUD` remains the systemic occluder.
- Expanded the relevant synthetic suite to 30 passing tests. Readiness remains **TEXTURED ASSEMBLY VALIDATED**; complete world reconstruction is not yet justified.

## 2026-08-30 - Complete LEVEL00 textured assembly validated

- Reverified the canonical MODELS hashes, all 58 TIM2 inventory hashes, and deterministic bytes for all 30 strongly bound native PNG decodes. A repeat run reused all 30 cached images and reproduced identical glTF JSON and binary hashes.
- Extended the glTF exporter to decode unique bound textures once, reuse shared images, classify source alpha, emit explicit neutral `UNRESOLVED_*` materials, and record complete material/descriptor provenance. No source asset changed.
- Exported all 1,338 descriptors, 2,128 VIF batches, 88,314 source position/UV records, and 46,336 triangles with source coordinates/winding/V and Q4.12 UVs. Written-file glTF, external-link, and exact source round-trip checks pass.
- Attached 32 confirmed materials to 30 unique images; seven unresolved MTL bindings remain placeholders. Of the unique images, 22 are opaque, one has binary alpha, and seven have partial alpha. All glTF materials remain conservatively opaque and use explicit unconfirmed `REPEAT`.
- Blender 5.2.1 LTS imported 1,338 meshes, 87,682 referenced vertices, 46,336 polygons, 39 materials, 30 images, and 1,338 UV layers. No image, material, dimension, or cross-binding failure occurred.
- Controlled full renders exposed systemic single-sided culling holes and opaque occlusion by descriptor 48's then-misclassified `CLOUD` shell. A two-sided diagnostic restores coherent architecture/terrain without changing geometry. The later strict MTL study established that the decoded CLOUD image alpha is fully opaque.
- Expanded the synthetic MODELS/TIM2 suite to 26 passing tests. All glTF/PNG/manifests/logs/renders remain ignored and uncommitted.
- Advanced the phase to `Milestone 0 - Textured LEVEL00 Assembly Validated`. `LEVEL00 WORLD RECONSTRUCTION COMPLETE` remains unmarked until culling and alpha semantics are established.

## 2026-08-30 - LEVEL00 geometry TIM2 decode completed

- Reverified canonical MODELS hashes and all 58 extracted LEVEL00 TIM2 hashes against the local inventory. The 39 geometry-used MTL records produce 32 strong bindings to 30 unique TIM2 textures; seven material/resource names remain unresolved.
- Reduced the required decoder matrix to PSMT4 or PSMT8 images with RGB5A1 or RGBA8888 CLUTs. It comprises 19 PSMT4/RGB5A1, five PSMT4/RGBA8888, three PSMT8/RGB5A1, and three PSMT8/RGBA8888 unique textures; 18 of the PSMT4 files have four mips and the rest have one.
- Extended the strict native decoder with bounds-checked PSMT8 byte indices, 256-entry GS CSM1 palette ordering, RGBA8888 palettes, saturated PS2 alpha doubling, and exact mip-size validation. No geometry-used image requires image-data unswizzling or direct-color support.
- Independently decoded all 30 unique textures with Noesis 4.474. Dimensions and every RGBA byte, including alpha, match exactly for all 30. Existing `002` and `L0_FLAGS` deterministic hashes remain unchanged.
- Expanded synthetic, non-copyrighted coverage to 23 passing tests across the full MODELS/TIM2 suite. Derived PNGs, Noesis references, and the per-texture hash manifest remain ignored and uncommitted.
- Advanced the phase to `Milestone 0 - LEVEL00 Texture Decode Complete`. A full textured validation export is now justified but was intentionally not performed in this task.

## 2026-08-30 - Directional V orientation validated

- Ranked geometry-used directional candidates from the existing LEVEL00 extraction. Selected descriptor 5 / MTL 1 `L0_FLAGS`; alternatives included GRKTREE, MEDUSA_TOWER, and ARROW.
- Reverified canonical MODELS hashes and `L0_FLAGS.TM2` SHA-256 `1dc53a5566f1b0beb27d3717bf7fbad22d95a1e2c60adc0222918257e694b0a3`. Descriptor 5 remains three batches, 150 streamed vertices, 84 triangles, and UV U `0.00415..0.35889`, V `0.00415..1.0`.
- Decoded `L0_FLAGS.TM2` at native 256×256 PSMT4/RGB5A1. Deterministic project RGBA again matches Noesis across all 262,144 bytes; no source file was modified.
- Exported source-V and flipped-V variants with identical geometry/material/sampler settings. Blender imports both as one mesh, 84 polygons, one material, one image, one UV layer, and identical bounds.
- Source V places the lambda upright at the hanging banner's lower edge. Flipped V places it inverted at the top. Main-cloth UV rows increase while source Y decreases, independently confirming source V as the modern glTF/Blender convention.
- Tested explicit REPEAT and MIRRORED_REPEAT with descriptor 361 / MEDUSA_TOWER across more than 15 U periods. Both remain structurally coherent; without a native reference, exact MTL sampler semantics remain unresolved.
- Advanced MODELS readiness to **VISUALLY VALIDATED**. Full-level texture validation is now justified as a later task after remaining TIM2 image/CLUT variants are deterministically supported.

## 2026-08-30 - Descriptor 118 visual-convention validation

- Reverified canonical `MODELS.BIN`, `MODELS.MTL`, and `002.TM2` hashes and descriptor 118's MTL 5 / `002`, 12-vertex, eight-triangle reconstruction.
- Implemented a strict bounds-checked TIM2 v4 PSMT4/RGB5A1 decoder. The native 256×256 RGBA output for `002.TM2` matches Noesis 4.474 across all 262,144 bytes; source assets remained unchanged.
- Generated eight ignored/local glTF variants spanning source versus `(X,Z,-Y)` coordinates, source versus reversed winding, and source versus flipped V. All pass structural and exact accessor consistency checks with one attached unlit repeat-sampled image.
- Blender 5.2.1 LTS imported every variant as one mesh, 12 vertices, eight polygons, one material, one image, and one UV layer. Source coordinates make the AAB-evidenced Y height axis Blender Z-up; `(X,Z,-Y)` makes the terrain near-vertical.
- Source winding produces eight positive-Z Blender face normals and renders from above; reversed winding produces eight negative-Z normals and is back-face culled. Source coordinates/winding are confirmed for determinant-positive glTF export.
- Both V variants tile coherently but are vertical mirrors. `002` is a directionless stone texture and no local PCSX2 reference was available, so target V orientation and exact native repeat-versus-mirror remain unknown. Readiness stays **GEOMETRY READY**, not VISUALLY VALIDATED.
- Added synthetic tests for palette/alpha/nibble decoding, malformed TIM2 rejection, coordinate variants, V flip, winding reversal, and glTF material/image/repeat linkage. Derived PNG/glTF/renders/reports remain ignored and uncommitted.

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

## 2026-08-30 - LEVEL00 MODELS triangle topology established

- Reverified the ignored canonical inputs: MODELS.BIN 2,293,536 bytes (`8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3`), MODELS.AAB 448,048 bytes (`ce46a8c58509d74ceeabedf22d1832dcd365c87d2f8bc583120f1f37797e99d7`), and MODELS.MTL 5,952 bytes (`57283516fc3cc8589eec4817cf8c25dc3ff0cc2185e4ff99e262fa6f3a4a54b2`).
- Checked generic ADC behavior against pinned PCSX2 GS source: ADC suppresses the primitive ending at the current vertex, but the vertex remains in triangle-strip history and advances the rolling window. It is not a restart; parity follows source submissions.
- Classified all 2,128 batches and 88,314 controls. There are 46,336 zeros and 41,978 `0x8000` flags. After the mandatory first pair, 37,588 of 37,722 internal flags occur as 18,794 exact pairs; only 134 occur singly.
- Compared five candidate models. The GS/ADC model emits exactly 46,336 triangles, equal to the zero-control count, with zero bad references, zero repeated-index triangles, three exact zero-area triangles, and eight near-zero cases. A no-suppression model emits 84,058 and 5,050 exact degenerates; a restart model emits only 12,907.
- Established the reconstruction rule: each batch is independent; every source vertex advances strip history/parity; W `0x8000` suppresses only the current primitive; even/odd source index determines alternating consistent winding. Absolute global front-face remains a consumer convention.
- V4-8 signed and 128-biased candidates neither cluster tightly at unit magnitude nor correlate with face normals, so the field remains unknown and was not used to overstate winding. V2-16 remains likely UV with exact one-to-one cardinality, but scale/wrapping remains unresolved.
- Validated AAB placement independently of topology: all vertices for all 1,224 static descriptors lie inside their associated decoded cell bounds. Each descriptor continues to select exactly one ordered MTL record, and no triangle crosses batch, descriptor, or material boundaries.
- Added deterministic read-only `models_topology_probe.py`, local per-batch/report outputs, `MODELS_TOPOLOGY.md`, and updated format/target/priority/status documentation. Readiness advanced to **TOPOLOGY READY** and the phase to `Milestone 0 - World Geometry Topology Reverse Engineering`.
- No PAK was opened, no extracted game data was modified, and no geometry was exported/rendered. No Ghidra, PS2Recomp, Blender, Noesis, installation, or push occurred.

## 2026-08-30 - LEVEL00 MODELS UV mapping established

- Reverified the ignored canonical inputs: MODELS.BIN SHA-256 `8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3` and MODELS.MTL SHA-256 `57283516fc3cc8589eec4817cf8c25dc3ff0cc2185e4ff99e262fa6f3a4a54b2`. All 58 LEVEL00 TIM2 hashes matched the existing inventory.
- Surveyed all 88,314 V2-16 pairs. Signed ranges are U `-32763..32734` and V `-32758..32757`; negatives account for 12,502 U and 7,852 V values. Signed edge deltas are far more coherent than unsigned reinterpretation.
- Confirmed V2-16 as signed normalized Q4.12: `u = int16(raw_u) / 4096`, `v = int16(raw_v) / 4096`. Bound texture dimensions then convert normalized coordinates to texels. Divisors 16–1024 and fixed-texel interpretations fail cross-dimension checks.
- Strengthened the descriptor → MTL record → resource stem/alias → TIM2 chain for 32 of 39 used MTL records: 29 direct and three explicit alias bindings. The bound set covers 83,959 vertices, 42,686 triangles, and texture dimensions from 16×16 through 256×256.
- Established zero global bias. Exact endpoints/grid alignments dominate the evidence, with 40,320 exact texel-grid hits versus 8,663 half-texel-grid hits; asset-specific insets are not a universal half-texel rule.
- Confirmed intentional out-of-range coordinates: 21 of 32 bound material groups and 13,970 of 42,686 bound triangles leave one `0..1` extent. Walls, temple surfaces, and other architectural materials span multiple periods; exact MTL repeat/mirror/clamp states remain unknown.
- Evaluated every emitted triangle after decode. Exactly 1,463 of 46,336 have zero UV area, and no additional nonzero triangles fall below the `1e-8` near-area threshold. Strongly bound ordinary textures account for only 339 of these.
- Found 16,487 differing-UV repeated-position pair combinations in strongly bound materials, including 312 exact integer-period pairs, independently supporting seams and wrap transitions.
- Added deterministic read-only `models_uv_probe.py` and local aggregate reports. Syntax passed and repeated output hashes were identical; no raw vertex/UV table or game asset was committed.
- Advanced readiness to **GEOMETRY READY** and the phase to `Milestone 0 - World Geometry UV Reverse Engineering`. V4-8 does not block a first position/topology/material/UV export; exact MTL sampler semantics and target coordinate/V conventions remain later validation work.
- No PAK was opened, no game data was modified, and no geometry was exported or rendered. No Ghidra, PS2Recomp, Blender, Noesis, installation, or push occurred.

## 2026-08-30 - First LEVEL00 world geometry reconstruction exported

- Reverified canonical MODELS.BIN, MODELS.AAB, and MODELS.MTL hashes and all 58 LEVEL00 TIM2 hashes against the existing inventory. No archive was opened and every game input remained read-only.
- Added target-neutral `spartan_models.py` with strict header/table/extent/material/VIF/cardinality/topology/AAB validation. The independent parser reproduces 1,338 descriptors, 2,128 batches, 88,314 streamed positions, 46,336 triangles, 55 MTL records, and 1,224 AAB references.
- Added `export_models_gltf.py` with descriptor/static/special/material selection; explicit source/Z-reflection coordinate, source/reverse winding, and source/flipped-V modes; traceable descriptor/MTL/batch extras; placeholder materials; and no normals or texture conversion.
- Passed the small gate with static descriptor 118: MTL 5 `002`, one batch, 12 streamed vertices, eight triangles, no geometric/UV collapse, and UV range U `-2.5..-0.5`, V `-0.500244..1.499756`.
- Exported the complete local ignored LEVEL00 scene in source coordinate/winding/V modes: 1,338 meshes/nodes, 2,128 batches, 88,314 POSITION/TEXCOORD records, 139,008 indices, 46,336 triangles, and 39 placeholder materials.
- Structural glTF validation passed both before and after serialization: valid JSON/2.0 asset, 2,044,830-byte external buffer, 4,014 buffer views/accessors, finite values, valid ranges/material references, matching position/UV counts, and in-range triangle indices.
- Exact round-trip validation reread the glTF buffer and matched every descriptor/material membership, position, Q4.12 UV, and reconstructed index. Three geometric degenerates and 1,463 collapsed-UV triangles remain intentionally retained.
- Blender 5.2.1 LTS imported the full glTF without rendering or saving: 1,338 mesh objects, 87,682 imported vertices, 46,336 polygons, and 39 materials. The 632-vertex difference exactly equals source-stream vertices unreferenced by emitted triangles; they remain in glTF accessors but Blender omits them.
- Added nine synthetic tests covering ADC topology/parity, winding reversal, Q4.12 and V flip, coordinate conversion, material grouping, selection, accessor construction/range validation, and malformed descriptor bounds. All pass without copyrighted fixtures.
- Advanced the phase to `Milestone 0 - First Native Geometry Reconstruction`. LEVEL00 world geometry is reconstructable outside the PS2 runtime, but native rendering, material fidelity, original V4-8 semantics, and final coordinate/front-face/V conventions are not claimed.
- Generated glTF/binary/report/manifest files remain local and ignored beneath `temp/exports/level00_validation`. No game asset, derived geometry, converted texture, or manifest is tracked. No Ghidra, PS2Recomp, remastering, installation, or push occurred.
