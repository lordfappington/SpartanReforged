# Project Status

## Current Phase

Milestone 0 - Front-End Asset Architecture

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. GENERAL, FE_LANG, and FE_TV have been extracted into separate ignored directories after list-only safety audits. FE_LANG → FE_TV → FE_MAIN is now the evidenced normal front-end path, with FE_TV → FE_LOAD used by its display tester. The other 27 PAKs have not been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers have been identified. FE_LANG/FE_TV establish a repeated section-package architecture: WORLD state scripts and resource indexes, per-language localization snapshots and TIM2-plus-DIM fonts, plus duplicated `GENERIC_GRAPHICS`. MTL is now structurally parsed as a resource/property container, and DIM has a confirmed 256-entry measurement layout with likely glyph-advance semantics. Model, animation, and inner audio formats remain unidentified.

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
- What is the proprietary memory-card `.ICO` schema?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

In a separately authorized task, list `DATA/FE_MAIN.PAK` and, if coherent, extract it into an isolated ignored directory. FE_TV conditionally loads `fe_main` for established 50/60 Hz states, making it the next normal-path target.
