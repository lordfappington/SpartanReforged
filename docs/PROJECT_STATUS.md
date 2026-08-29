# Project Status

## Current Phase

Milestone 0 - Disc Extraction and Content Inventory

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup. Its complete ISO9660 filesystem has been extracted read-only and catalogued without unpacking any PAK archive.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers have been identified. No standalone image/model/audio formats were found outside archives. Inner sound-tree extensions are catalogued but their proprietary formats remain unknown; see `research/FILE_FORMAT_REGISTRY.md`.

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
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

In a separately authorized task, perform a controlled extraction of the smallest root archive (`GENERAL.PAK`) into `game-extracted/pak` and validate the result before extracting larger archives.
