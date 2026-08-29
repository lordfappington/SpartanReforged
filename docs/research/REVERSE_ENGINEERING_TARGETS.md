# Reverse-Engineering Targets

Candidate targets are based only on disc filenames, standard headers, and safe list-only archive tables. “Likely” classifications are hypotheses for later testing, not understood formats.

## EXECUTABLE / CODE

- `SLES_533.93` — **CONFIRMED:** main MIPS ELF32 PS2 executable. Future Ghidra target; not analyzed in this task.
- `IOP/*.IRX` — **CONFIRMED:** ten ELF-based IOP modules. Candidate subsystem boundaries include disc streaming, memory-card access, controller/SIO2, and sound, inferred from conventional module names.

## ARCHIVES

- `GENERAL.PAK` — **CONFIRMED:** PAK1, 2 listed entries.
- `E_DATA.PAK` — **CONFIRMED:** PAK1, 12,689 listed sound-tree entries.
- `DATA/LEVEL*.PAK`, `DATA/ARENA*.PAK`, `DATA/FE_*.PAK`, `IOP/GENERAL.PAK` — **CONFIRMED:** PAK1 containers; contents not listed.

## TEXTURES

- `DATA/FE_*.PAK`, `DATA/LEVEL*.PAK`, and `DATA/ARENA*.PAK` — **UNKNOWN candidates:** no standalone standard image files exist at disc level and these archives were not opened.

## MODELS

- `DATA/LEVEL*.PAK` and `DATA/ARENA*.PAK` — **UNKNOWN candidates:** no model format has been identified.

## ANIMATIONS

- `DATA/LEVEL*.PAK` and `DATA/ARENA*.PAK` — **UNKNOWN candidates:** no animation format has been identified.

## LEVEL DATA

- `DATA/LEVEL00.PAK` through `DATA/LEVEL14.PAK`, including `LEVEL07D.PAK` — **LIKELY:** level-specific content based solely on archive names.
- `DATA/ARENA*.PAK` — **LIKELY:** arena-specific content based solely on names.

## AUDIO

- `E_DATA.PAK` — **CONFIRMED:** all listed paths are under `DATA\SOUND`.
- Inner `.MIC`, `.MSB`, `.MSH`, `.CMH`, and `.BIN` files — **LIKELY:** audio data, banks, metadata, or scripts based on path context; encodings remain unknown.
- `IOP/LIBSD.IRX`, `SDRDRV.IRX`, and `STREAM.IRX` — **LIKELY:** runtime sound/streaming modules based on conventional names; code not analyzed.

## SCRIPTS / CONFIGURATION

- `SYSTEM.CNF` — **CONFIRMED:** PS2 boot configuration.
- `GENERAL.PAK` paths `DATA\SECTIONS.TXT` and `DATA\SOUND\SCRIPTS\MISC.TXT` — **LIKELY:** text configuration/data; contents not extracted.
- `E_DATA.PAK` entries below `DATA\SOUND\SCRIPTS` — **LIKELY:** localized or compiled sound scripts based on path names.

## IOP / PS2 SYSTEM MODULES

- `IOP/IOPRP300.IMG` — **LIKELY:** IOP reset/module image with `RESET`, `ROMDIR`, and `EXTINFO` header records.
- `IOP/*.IRX` — **CONFIRMED:** ten ELF-based IOP modules.
- `IOP/GENERAL.PAK` — **UNKNOWN:** two-entry PAK1 located beside system modules.

## UNKNOWN

- Proprietary structures inside all unlisted `DATA` PAKs.
- Actual codecs and schemas for `.MIC`, `.MSB`, `.MSH`, `.CMH`, and sound `.BIN` entries.
- Relationships between `LEVEL07.PAK` and `LEVEL07D.PAK`.
- Meaning of arena suffixes `B`, `G`, `P`, `R`, `U`, and `X`.

