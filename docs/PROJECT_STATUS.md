# Project Status

## Current Phase

Milestone 0 - World Geometry Format Reverse Engineering

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. GENERAL, FE_LANG, FE_TV, FE_MAIN, and LEVEL00 have been extracted into separate ignored directories after list-only safety audits. The evidenced path GENERAL → FE_LANG → FE_TV → FE_MAIN → LEVEL00 now reaches the first mapped gameplay section; LEVEL00's entity graph explicitly transitions to LEVEL01. The other 25 PAKs have not been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers are identified. LEVEL00 `MODELS.BIN` is now segmented into 1,338 descriptor-indexed PS2 VIF blocks containing 2,128 batches and 88,314 streamed vertex instances. Numeric MTL binding and the AAB quadtree's exact 1,224-descriptor static-world mapping are established. Triangle topology/control, UV scaling, and packed V4-8 semantics remain unresolved, so no production geometry parser or renderer is justified yet. No audio payload is embedded in LEVEL00; symbolic voice/music references resolve externally.

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
- Does position W=`0x8000` implement the expected PS2 ADC strip-control rule, including internal restarts, degenerates, and winding?
- What scale/bias applies to MODELS.BIN's V2-16 attribute, and what does its unsigned V4-8 attribute encode?
- What do MODELS.BIN header values 15/48/30, descriptor secondary IDs, field 11/0, and AAB leaf trailing words mean?
- What are the exact schemas for PSQ/PSW/MPH/BNS character data, ANM/SAM tracks, ENT records, and COL/PT2/IND spatial data?
- What is the proprietary memory-card `.ICO` schema?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

Perform one bounded read-only topology task on a representative set of MODELS.BIN VIF batches: prove the position-W `0x8000` ADC/restart/winding rule and determine whether the 46,336 zero-control vertices correspond one-to-one with emitted triangles. Do not export or render geometry.
