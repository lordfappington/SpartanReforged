# Project Status

## Current Phase

Milestone 0 - Section Asset Architecture

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. GENERAL, FE_LANG, FE_TV, and FE_MAIN have been extracted into separate ignored directories after list-only safety audits. The evidenced boot path is GENERAL → FE_LANG → FE_TV → FE_MAIN, with FE_TV → FE_LOAD used by its display tester. FE_MAIN explicitly dispatches to 16 campaign section names, six arena sections, and FE_XTRA. The other 26 PAKs have not been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers have been identified. FE_LANG/FE_TV/FE_MAIN establish a repeated self-contained section-package architecture: WORLD state scripts and resource indexes, per-language localization snapshots and TIM2-plus-DIM fonts, plus duplicated `GENERIC_GRAPHICS`. FE_MAIN adds confirmed MPEG-2 `.PSS` attract videos, a large UI/state graph, and script-driven 2D emitters. MTL is structurally parsed as a resource/property container, and DIM has a confirmed 256-entry measurement layout with likely glyph-advance semantics. Geometry, skeletal animation, world/scene, and inner audio formats remain unidentified.

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
- Which additional formats and content categories are stored in the level, arena, and remaining front-end PAK archives?
- What does `FNT_END` mean, and how are `DATA\ENV` logical paths resolved to disc PAKs?
- What do the numeric MTL child properties mean, and how are symbolic resource names resolved to PAK entries?
- What are DIM's exact character mapping and `0x2000` sentinel, and which legacy code pages does each UI language use?
- Why does FE_MAIN request `MAP_512.TGA` while packaging `MAP_512.TM2`?
- Do gameplay sections reuse the script/MTL/TIM2 section snapshot architecture, and which formats carry geometry, skeletons, animation, placement, and 3D rendering data?
- What is the proprietary memory-card `.ICO` schema?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

In a separately authorized task, list `DATA/LEVEL00.PAK` and, if coherent, extract it into an isolated ignored directory. FE_MAIN explicitly dispatches to `level00`; it is the shortest evidenced route for testing the section-snapshot model against gameplay assets.
