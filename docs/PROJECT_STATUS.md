# Project Status

## Current Phase

Milestone 0 - Effect Attribute / Blend Reverse Engineering

## Milestone 0 - Discovery

The canonical PS2 ISO has an independently verified matching backup and a complete ignored filesystem extraction. GENERAL, FE_LANG, FE_TV, FE_MAIN, and LEVEL00 have been extracted into separate ignored directories after list-only safety audits. The evidenced path GENERAL → FE_LANG → FE_TV → FE_MAIN → LEVEL00 now reaches the first mapped gameplay section; LEVEL00's entity graph explicitly transitions to LEVEL01. The other 25 PAKs have not been extracted.

## Environment

Windows native C++ and reverse-engineering environment installed and smoke-tested. Visual Studio, MSVC, Windows SDK, CMake, Java 21, Ghidra, and supporting inspection/media tools are ready. Exact verified versions are recorded in `research/TOOL_REGISTRY.md`.

## Game Versions

Canonical build: PlayStation 2 Europe/Australia PAL, serial `SLES-53393`, disc version 1.01, executable `SLES_533.93`. Its 2,199,420,928-byte image matches verified Redump record 7850 by filename, size, and MD5. Details are recorded in `research/PS2_DISC_IDENTITY.md` and `research/GAME_VERSION_MATRIX.md`.

## Asset Formats

Disc-level ELF, IRX, ROMDIR-style IMG, text configuration, and PAK1 containers are identified. A strict read-only pipeline reconstructs LEVEL00 outside the PS2 runtime as 1,338 traceable glTF meshes and exactly 46,336 triangles. Its complete confirmed texture assembly uses 32 textured materials, seven explicit placeholders, and 30 unique native images. Blender imports every polygon, material, image, and UV layer with no broken/cross-bound link. The pipeline is **VISUALLY VALIDATED for geometry and TEXTURED ASSEMBLY VALIDATED**, not native game rendering or complete visual reconstruction. All 88,314 V4-8 records have now been surveyed: bytes 0–2 are likely PS2 vertex color/light modulation, while byte 3 is globally full-scale `0x80`. CLOUD's V4 gradient explains its dark dome/bright ring but cannot supply transparency; its exact type-2-selected GS blend/depth/order state remains the blocker.

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
- How does Spartan route likely V4-8 vertex color/light data through its VU program, how do MTL type-2 values 1–5 select native GS blend/depth families, and what are the alpha-test threshold and repeat/mirror/clamp rules?
- What do MODELS.BIN header values 15/48/30, descriptor secondary IDs, field 11/0, and AAB leaf trailing words mean?
- What are the exact schemas for PSQ/PSW/MPH/BNS character data, ANM/SAM tracks, ENT records, and COL/PT2/IND spatial data?
- What is the proprietary memory-card `.ICO` schema?
- Where are the `fe_splash` and `level99/testlevel` sections stored?
- What are the actual codecs and schemas for the `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries?
- Which PS2 hardware and middleware dependencies block recompilation?

## Next Actions

Perform a bounded Ghidra/VU-path investigation of the native render-state mapping for MTL type-2 values 2–5, beginning with CLOUD. Recover the GS `ALPHA` operands/fixed factor and relevant depth-write/order behavior without broadening into complete engine or character analysis.
