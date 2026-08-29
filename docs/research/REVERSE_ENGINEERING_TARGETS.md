# Reverse-Engineering Targets

Candidate targets are based only on disc filenames, standard headers, and safe list-only archive tables. “Likely” classifications are hypotheses for later testing, not understood formats.

## EXECUTABLE / CODE

- `SLES_533.93` — **CONFIRMED:** main MIPS ELF32 PS2 executable. Future Ghidra target; not analyzed in this task.
- `IOP/*.IRX` — **CONFIRMED:** ten ELF-based IOP modules. Candidate subsystem boundaries include disc streaming, memory-card access, controller/SIO2, and sound, inferred from conventional module names.

## ARCHIVES

- `GENERAL.PAK` — **CONFIRMED:** PAK1, 2 entries successfully extracted into an isolated ignored directory; contains the section manifest and global sound configuration.
- `E_DATA.PAK` — **CONFIRMED:** PAK1, 12,689 listed sound-tree entries.
- `DATA/FE_LANG.PAK` — **CONFIRMED:** PAK1, 32 entries safely listed and extracted in isolation; contains language tables, font resources, front-end script/material data, textures, and memory-card icon assets.
- `DATA/LEVEL*.PAK`, `DATA/ARENA*.PAK`, the other `DATA/FE_*.PAK` files, and `IOP/GENERAL.PAK` — **CONFIRMED:** PAK1 containers; contents not listed.

## TEXTURES

- `DATA/FE_LANG.PAK` — **CONFIRMED:** 12 single-picture, 256-color TIM2 textures from 16×16 through 256×256; includes eight font atlases.
- Other `DATA/FE_*.PAK`, `DATA/LEVEL*.PAK`, and `DATA/ARENA*.PAK` files — **UNKNOWN candidates:** not opened.

## MODELS

- `DATA/LEVEL*.PAK` and `DATA/ARENA*.PAK` — **UNKNOWN candidates:** no model format has been identified.

## ANIMATIONS

- `DATA/LEVEL*.PAK` and `DATA/ARENA*.PAK` — **UNKNOWN candidates:** no animation format has been identified.

## LEVEL DATA

- `DATA/LEVEL00.PAK` through `DATA/LEVEL14.PAK`, including `LEVEL07D.PAK` — **LIKELY:** level-specific content; `SECTIONS.TXT` confirms matching logical section names and `DATA\ENV\level*` paths.
- `DATA/ARENA*.PAK` — **LIKELY:** arena-specific content; `SECTIONS.TXT` confirms matching arena section names and `DATA\ENV\arena*` paths.
- `DATA/FE_LANG.PAK` — **CONFIRMED:** boot-time language-selection front end; `SECTIONS.TXT` declares it as `start_section`, and its script loads `fe_tv` after selection.
- `DATA/FE_TV.PAK` — **HIGH-VALUE NEXT TARGET:** direct destination of FE_LANG's `LEVEL fe_tv` actions and startup conditions; list-only inspection pending.

## AUDIO

- `E_DATA.PAK` — **CONFIRMED:** all listed paths are under `DATA\SOUND`.
- Inner `.MIC`, `.MSB`, `.MSH`, `.CMH`, and `.BIN` files — **LIKELY:** audio data, banks, metadata, or scripts based on path context; encodings remain unknown.
- `IOP/LIBSD.IRX`, `SDRDRV.IRX`, and `STREAM.IRX` — **LIKELY:** runtime sound/streaming modules based on conventional names; code not analyzed.

## SCRIPTS / CONFIGURATION

- `SYSTEM.CNF` — **CONFIRMED:** PS2 boot configuration.
- `GENERAL.PAK/DATA/SECTIONS.TXT` — **CONFIRMED:** ordered section/allocation manifest mapping front-end, arena, level, and test identifiers to `DATA\ENV` logical paths.
- `GENERAL.PAK/DATA/SOUND/SCRIPTS/MISC.TXT` — **CONFIRMED:** ordered cross-platform audio configuration covering global volumes, crowd sound-grid behavior, and PS2/Xbox effect presets.
- `FE_LANG.PAK/DATA/ENV/FE_LANG/WORLD/FE_LANG.TXT` — **CONFIRMED:** front-end menu/state script defining texture pages, sprites, focus navigation, actions, variables, and transitions to `fe_tv`.
- `FE_LANG.PAK/DATA/ENV/FE_LANG/TEXT/*/UI.TXT` — **CONFIRMED:** seven synchronized, ordered localization tables with duplicate keys and legacy single-byte encodings.
- Future executable string targets: `start_section`, `FNT_END`, `STD_LEVEL`, `SOUND_GRID`, `EFFECT_NAME`, and `DATA\ENV`.
- `E_DATA.PAK` entries below `DATA\SOUND\SCRIPTS` — **LIKELY:** localized or compiled sound scripts based on path names.

## IOP / PS2 SYSTEM MODULES

- `IOP/IOPRP300.IMG` — **LIKELY:** IOP reset/module image with `RESET`, `ROMDIR`, and `EXTINFO` header records.
- `IOP/*.IRX` — **CONFIRMED:** ten ELF-based IOP modules.
- `IOP/GENERAL.PAK` — **UNKNOWN:** two-entry PAK1 located beside system modules.

## UNKNOWN

- Proprietary structures inside all still-unlisted `DATA` PAKs.
- Exact FE_LANG `.DIM`, `.MTL`, and memory-card `.ICO` schemas, plus stock Noesis recognition of the nonstandard `.ICO` payload.
- Actual codecs and schemas for `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries.
- Relationships between `LEVEL07.PAK` and `LEVEL07D.PAK`.
- Meaning of arena suffixes `B`, `G`, `P`, `R`, `U`, and `X`.
