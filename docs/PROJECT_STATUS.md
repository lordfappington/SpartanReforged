# Project Status

## Current Phase

Milestone 0 - World Geometry UV Reverse Engineering

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. GENERAL, FE_LANG, FE_TV, FE_MAIN, and LEVEL00 have been extracted into separate ignored directories after list-only safety audits. The evidenced path GENERAL → FE_LANG → FE_TV → FE_MAIN → LEVEL00 now reaches the first mapped gameplay section; LEVEL00's entity graph explicitly transitions to LEVEL01. The other 25 PAKs have not been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers are identified. LEVEL00 `MODELS.BIN` is segmented into 1,338 descriptor-indexed PS2 VIF blocks containing 2,128 batches and 88,314 vertex instances. Its implicit ADC-controlled strip topology is established: W `0x8000` suppresses without resetting history, and 46,336 zero-W vertices emit exactly 46,336 triangles. Numeric MTL binding and the AAB quadtree's exact 1,224-descriptor static-world mapping are established, including 1,224/1,224 descriptor bounds containment. V2-16 is confirmed as signed normalized Q4.12 UV (`int16 / 4096`) with zero global bias; intentional out-of-range coordinates support tiled materials. Readiness is **GEOMETRY READY** for a first read-only export. V4-8, MTL sampler properties, and target-specific coordinate/V conventions remain unresolved but do not block exporting positions, topology, material groups, and source UVs. No audio payload is embedded in LEVEL00; symbolic voice/music references resolve externally.

## Executable Analysis

Not started.

## Recompilation Status

PS2Recomp upstream commit `14b1e5cb39b4af7e6fc12f9a29fdc751efde49d7` is staged for later compatibility research. No Spartan recompilation has begun.

## Known Tools

See `research/TOOL_REGISTRY.md` and `SETUP_CHECKLIST.md`.

## Open Questions

- Was the source physical copy sold in European or Australian packaging? The disc data is identical for both catalogued variants.
- What executable and archive revisions exist across releases?
- Which PAK operations are safely supported beyond extraction?
- Which additional formats and content categories recur or differ across the other level, arena, and remaining front-end PAK archives?
- What does `FNT_END` mean, and how are `DATA\ENV` logical paths resolved to disc PAKs?
- What do the numeric MTL child properties mean, and how are symbolic resource names resolved to PAK entries?
- What are DIM's exact character mapping and `0x2000` sentinel, and which legacy code pages does each UI language use?
- Why does FE_MAIN request `MAP_512.TGA` while packaging `MAP_512.TM2`?
- What does MODELS.BIN's unsigned V4-8 attribute encode, and which MTL properties select repeat/mirror/clamp and other render states?
- What do MODELS.BIN header values 15/48/30, descriptor secondary IDs, field 11/0, and AAB leaf trailing words mean?
- What are the exact schemas for PSQ/PSW/MPH/BNS character data, ANM/SAM tracks, ENT records, and COL/PT2/IND spatial data?
- What is the proprietary memory-card `.ICO` schema?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

Implement one bounded, read-only first MODELS geometry exporter using the confirmed positions, ADC topology, descriptor/MTL groups, and signed Q4.12 UVs. Preserve source data, make coordinate/front-face/V conversion explicit, perform no rendering, and leave V4-8 and unknown material properties optional/uninterpreted.
