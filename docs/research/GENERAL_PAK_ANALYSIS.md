# Root GENERAL.PAK Analysis

Analysis completed on 2026-08-29. Only the root `GENERAL.PAK` was extracted. No other PAK was opened or extracted during this task.

## Archive Identity

| Field | Value |
|---|---|
| Source | `game-extracted/disc/GENERAL.PAK` |
| Size | 29,074 bytes |
| SHA-256 before and after extraction | `0ec7ec24f69625d5302c0a040f55803ff084e48655f8142d299bfc9bb97f6e1c` |
| Container | PAK1, version 1 |
| Alignment | `0x800` |
| Extractor | QuickBMS 0.12.0 with `spartan_total_war.bms` 0.1.1 |

QuickBMS completed with exit code 0 and reported exactly two files. The isolated destination was empty before extraction, so no existing file was overwritten.

## Extracted Files

| Path below `game-extracted/pak/GENERAL` | Size | SHA-256 |
|---|---:|---|
| `DATA/SECTIONS.TXT` | 1,788 | `5f7aa226244a36e7c8aa41747737d4975e2d1118415099d81928e0ba571df5d9` |
| `DATA/SOUND/SCRIPTS/MISC.TXT` | 24,978 | `eaf11f7bfaa1625fc275208c71c588acfce3d1253540a463094eaafaf3e8805c` |

Both files are 7-bit ASCII using CRLF line endings. They remain ignored game data and are not tracked by Git.

## SECTIONS.TXT

### Confirmed purpose

`SECTIONS.TXT` is a logical section registration and memory-allocation manifest. Its own comments state that it must contain the front end and every level; launching an unlisted level from the front end would cause memory allocation at launch time and is explicitly described as undesirable.

The file contains 30 bracketed sections:

- One initialization section: `init`.
- Six front-end sections: `fe_splash`, `fe_main`, `fe_lang`, `fe_tv`, `fe_xtra`, and `fe_load`.
- Six arena sections: `ArenaB`, `ArenaG`, `ArenaP`, `ArenaR`, `ArenaU`, and `ArenaX`.
- Seventeen level/test sections: `level00` through `level14`, plus `level07D` and `level99`.

`init` sets `start_section` to `fe_lang`. Every other section has an ordered `TYPE` and `PATH` pair:

- Six front-end sections use `TYPE=FNT_END`.
- Twenty-three arena/level sections use `TYPE=STD_LEVEL`.
- Paths use the namespace `DATA\ENV\<name>\` (with case variation in the source).
- `level99` maps to `DATA\ENV\testlevel\`.

### Relationship to disc archives

**CONFIRMED:** section names align case-insensitively with every shipped arena archive, every numbered level archive including `LEVEL07D.PAK`, and five front-end archives (`FE_MAIN`, `FE_LANG`, `FE_TV`, `FE_XTRA`, `FE_LOAD`).

**LIKELY:** these logical paths are loader namespaces resolved against similarly named PAK archives. The configuration does not contain literal `.PAK` filenames, archive offsets, or numeric resource identifiers, so the resolution mechanism is not yet proven.

**UNKNOWN:** `fe_splash` and `level99/testlevel` have no same-named disc-level PAK. They may resolve to content in another archive, represent development/test remnants, or be handled specially.

The meaning of the token `FNT_END` is not defined. Its exclusive use by front-end sections makes a front-end classification likely, but the exact expansion and runtime semantics are unknown. `STD_LEVEL` plainly distinguishes the arena/level group, but its memory-layout behavior is also unknown.

## MISC.TXT

### Confirmed purpose

`MISC.TXT` is a global, cross-platform audio configuration file. It controls sound enablement and volumes, music/ambient behavior, stream fading, character fall-sound thresholds, crowd sound-grid aggregation, and hardware/platform reverb parameters.

It contains eight bracketed sections:

- `SOUND_CAMERA`
- `SPEECH`
- `GENERAL_SETTINGS`
- `CHARACTER_SOUND`
- `SOUND_GRID`
- `PS2_EFFECTS`
- `XBOX_EFFECTS`
- `GC_EFFECTS`

### Syntax

- Semicolon-prefixed comments.
- Bracketed section headers.
- Case-sensitive-looking symbolic keys with `=` assignments.
- Integer, decimal, negative, and quoted-string values.
- Ordered repeated keys within effect sections.

The repeated `EFFECT_NAME` and parameter keys mean this is not safely representable as a conventional unique-key INI dictionary. A future parser must preserve ordering, duplicate keys, and record boundaries implied by each `EFFECT_NAME`.

### Sound configuration and identifiers

The file defines platform-specific `PS2_`, `XBOX_`, and `GC_` volume/rolloff/doppler namespaces, suggesting a shared configuration source across the PS2, Xbox, and GameCube versions. `GC_EFFECTS` is present but empty in this build.

`SOUND_GRID` describes a 7×7 crowd-audio grid with small/medium/large troop thresholds, update cadence, sample duration, fade values, a maximum character-check count, and four sound nodes. Comments make the crowd-aggregation purpose explicit.

Both the PS2 and Xbox effect blocks contain 19 active preset identifiers:

`OFF`, `OUTDOORS`, `DUNGEONS`, `LOGO`, `ATHENS`, `ALPINE`, `ALPINE2`, `WEAPON_CLASH`, `FRONTEND`, `PRIESTESS`, `ROOM`, `STUDIO_A`, `STUDIO_B`, `STUDIO_C`, `HALL`, `HALL_SMALL`, `SPACE`, `DELAY`, and `PIPE`.

The PS2 block assigns `SOUND_FX_*` types and depth/delay/feedback/master-volume parameters. The Xbox block assigns room, decay, reflection, reverb, diffusion, density, and high-frequency parameters. A comment references `MultiStream 7.0.pdf`; that document is not present at disc level and the precise middleware relationship is unknown.

These are effect-preset names, not confirmed gameplay sound-event names. No audio filename, `.MIC`, `.MSB`, `.MSH`, `.CMH`, or other asset path is directly referenced by `MISC.TXT`.

## High-Value Reference Survey

| Term/category | Result |
|---|---|
| `LEVEL`, `ARENA`, `FE_` | Present extensively in section identifiers and environment paths |
| `SOUND`, `SCRIPT`, `DATA`, `SECTION` | Present; core namespaces are `DATA\ENV` and `DATA\SOUND\SCRIPTS` |
| `CHARACTER` | Present in fall-sound and sound-grid configuration |
| `WEAPON` | Present in the `WEAPON_CLASH` effect preset |
| `EFFECT` | Present extensively in PS2/Xbox reverb records |
| `PAK` | No literal reference inside either extracted text file |
| `TEXTURE`, `TEX`, `MODEL`, `MESH`, `ANIM` | Absent |
| `PLAYER`, `PARTICLE`, `MATERIAL` | Absent |

Other recurring namespaces and patterns include `PS2_`, `XBOX_`, `GC_`, `SOUND_FX_`, `XBOX_EFFECT_`, front-end identifiers, numbered levels, arena suffixes, and named environmental reverb presets.

## Reverse-Engineering Implications

- `start_section`, `FNT_END`, `STD_LEVEL`, `SOUND_GRID`, `EFFECT_NAME`, and the `DATA\ENV` namespace are high-value future string cross-references in the main executable.
- The direct alignment between section names and disc archive basenames strengthens the hypothesis that PAK selection is section-driven.
- Cross-platform PS2/Xbox/GameCube keys indicate shared engine configuration and may help compare platform executables or assets later.
- `FE_LANG.PAK` is especially valuable because it is the declared initial section, is the smallest front-end archive by byte size, and declares only 32 entries.

## Unknown Fields and Limits

- Exact runtime parser grammar, case sensitivity, and error behavior.
- Exact meaning of `FNT_END` and allocation behavior associated with each type.
- How logical `DATA\ENV` paths resolve to disc PAKs.
- Where `fe_splash` and `testlevel` content resides.
- Units or runtime interpretation for parameters not described by comments.
- Whether the referenced MultiStream documentation describes proprietary middleware or an internal subsystem.

## Recommended Next Target

In a separately authorized task, perform list-only inspection of `DATA/FE_LANG.PAK`, then—if its table is coherent—extract it into its own isolated directory. It is 1,348,160 bytes, declares 32 entries, and corresponds to the confirmed initial `start_section`.

