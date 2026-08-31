# Project Status

## Current Phase

Milestone 0 - VU1 World Render Recovery

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. GENERAL, FE_LANG, FE_TV, FE_MAIN, and LEVEL00 have been extracted into separate ignored directories after list-only safety audits. The evidenced path GENERAL → FE_LANG → FE_TV → FE_MAIN → LEVEL00 now reaches the first mapped gameplay section; LEVEL00's entity graph explicitly transitions to LEVEL01. The other 25 PAKs have not been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers are identified. A strict read-only pipeline reconstructs LEVEL00 outside the PS2 runtime as 1,338 traceable glTF meshes and exactly 46,336 triangles. Its confirmed texture assembly uses 32 textured materials, seven placeholders, and 30 native images. The pipeline is **VISUALLY VALIDATED for geometry and TEXTURED ASSEMBLY VALIDATED**, not native game rendering. Native MTL TEST/ZBUF/ALPHA and CPU ordering are recovered. Resident VU1 analysis confirms triangle-strip `PRIM=0x25c`, ABE enabled, context 2, and V4-to-RGBAQ. CLOUD remains opaque mathematically because both known alpha sources are full.

## Executable Analysis

Ghidra 12.1.3 with the pinned Emotion Engine Reloaded extension imports the hash-verified ELF as `r5900:LE:32:default`; 7,749 functions and LQ/SQ/MMI/COP2 decoding are validated. Bounded CPU/VU data flow proves the MTL state path, three-range queue, resident program upload, MODELS `MSCALF 0` dispatch, GIFtag/PRIM construction, and V4/RGBAQ route. No general gameplay/code analysis or unrelated VU investigation has begun.

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
- Which effective `TEX0.TCC/TFX`/`TEXA` state reaches CLOUD, and does it provide an alpha source not present in its opaque TIM2 and full V4 alpha?
- What do MODELS.BIN header values 15/48/30, descriptor secondary IDs, field 11/0, and AAB leaf trailing words mean?
- What are the exact schemas for PSQ/PSW/MPH/BNS character data, ANM/SAM tracks, ENT records, and COL/PT2/IND spatial data?
- What is the proprietary memory-card `.ICO` schema?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

Trace only CLOUD's effective context-2 TEX0 texture-function/alpha state far enough to explain—or rule out—a non-full fragment alpha source.
