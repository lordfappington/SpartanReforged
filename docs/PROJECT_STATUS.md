# Project Status

## Current Phase

Milestone 0 - Environment Setup

## Milestone 0 - Discovery

The workspace and research toolchain are being prepared. No game data has been extracted or analyzed.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

No canonical build selected. Candidate platforms and regions are tracked in `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Unknown. Findings will be recorded in `research/FILE_FORMAT_REGISTRY.md`.

## Executable Analysis

Not started.

## Recompilation Status

PS2Recomp upstream commit `14b1e5cb39b4af7e6fc12f9a29fdc751efde49d7` is staged for later compatibility research. No Spartan recompilation has begun.

## Known Tools

See `research/TOOL_REGISTRY.md` and `SETUP_CHECKLIST.md`.

## Open Questions

- Which regional PS2 release will be the canonical research target?
- What executable and archive revisions exist across releases?
- Which PAK operations are safely supported beyond extraction?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

Identify and hash the canonical legally owned game version without modifying it.
