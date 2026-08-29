# Project Status

## Current Phase

Milestone 0 - Archive Structure Analysis

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. The small root `GENERAL.PAK` has now been extracted in isolation and its two text configuration files analyzed. No other PAK has been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers have been identified. `GENERAL.PAK` reveals an ordered section/allocation manifest and a cross-platform audio configuration syntax. No texture, model, animation, or inner audio format has yet been identified; see `research/FILE_FORMAT_REGISTRY.md`.

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
- Which formats and content categories are stored in the level, arena, and front-end PAK archives?
- What does `FNT_END` mean, and how are `DATA\ENV` logical paths resolved to disc PAKs?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

In a separately authorized task, list `DATA/FE_LANG.PAK` and, if coherent, extract it into an isolated ignored directory; it is the confirmed initial section and a small 32-entry archive.
