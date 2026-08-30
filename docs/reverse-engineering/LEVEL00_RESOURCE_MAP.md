# LEVEL00 Resource Map

This map records evidenced dependencies in the isolated LEVEL00 extraction. Arrows mean explicit reference, basename/path pairing, or strong archive-family association as labeled; they do not imply that every resource is loaded simultaneously.

## Section package map

```text
LEVEL00.PAK
├─ world/environment
│  ├─ MODELS.BIN ─┬─ MODELS.AAB
│  │              ├─ MODELS.MTL ──> world/effect/UI TIM2 declarations
│  │              ├─ MODELS.FLP / INS / STL            [roles unknown]
│  │              └─ MODELS.MVR ──> Brazier_Dark.CAS source references
│  ├─ BRAZIER_DARK.BIG <── TEST.ENT basename reference
│  ├─ LAND.HMP                                      [likely height field]
│  └─ 19 environment TIM2 pages
├─ gameplay/entity state
│  ├─ TEST.ENT ─┬─> PLAYERSTART / checkpoint / spawners / squads
│  │            ├─> camera, position, relay, use-package identifiers
│  │            ├─> SPARKY/LEONIDAS cutscene SAM files
│  │            ├─> voice/music identifiers
│  │            ├─> MARS_SMOKE2 and BRAZIER_DARK
│  │            └─> LEVEL01 section transition
│  ├─ CHAR_TYPES.BIN ──> NAMES.TXT indices ──> packaged CHR_MDLS families
│  └─ CHARACTER_PROGRESSION.TXT ──> enabled weapons/display/progression
├─ collision/navigation/crowd
│  ├─ PLANES.COL
│  ├─ WAYPTS3D.PT2 <──> WAYPT_INDICES.IND
│  ├─ TEST.ENT spawners / SQUAD / CHAR-ZONE identifiers
│  └─ BATTLE.TXT combat, attackers, flanking, surrounding, commander tuning
├─ characters
│  ├─ Spartan body ─┬─ STANDARD.PSQ
│  │                ├─ MULTIWEIGHTED.PSW
│  │                ├─ FACE.MPH
│  │                ├─ BONES.BNS
│  │                ├─ TEXTURE / TEXTURE_EXTRAS.TM2
│  │                └─ DISPLAY_ATTRIBUTES.TXT
│  ├─ Spartan equipment ──> STANDARD / SHINEY / SHADOW PSQ + display flags
│  ├─ Hoplite / Swordsman / Athenian Archer ──> numbered PSQ + BNS + TM2
│  └─ Castor / Pollux / Leonidas ──> numbered PSQ + FACE.MPH + BNS + TM2
├─ animation
│  ├─ 461 ANM clips under COMMON and character/action namespaces
│  ├─ BNS compatibility groups
│  └─ 2 SAM cutscene animation containers
├─ effects
│  ├─ 8 APP_* particle TM2 <──> 8 APP_*.TXT page/frame descriptions
│  ├─ BASE_EFFECT_MATERIALS / BASE_EFFECTS
│  ├─ MARS_SMOKE2.TXT ──> EMITTER + PARTICLE parameters
│  └─ SAMPLES.DAT                                      [compiled companion]
├─ text/UI
│  ├─ 7 APP_PS2FONT TM2/DIM pairs
│  ├─ 7 GLOBALS localization tables
│  ├─ 8 identical NAMES character-ID maps
│  └─ 7 LEVEL01 dialogue/objective/audio-reference snapshots
└─ external runtime dependency
   └─ symbolic speech/music/effect identifiers ──> external sound system
```

## Confirmed cross-resource joins

| Source | Key/reference | Target | Evidence |
|---|---|---|---|
| `CHAR_TYPES.BIN` | u32 IDs 0, 8, 11, 12, 14, 15, 18 | Spartan, Hoplite, Swordsman, Athenian Archer, Castor, Pollux, Leonidas | Exact index resolution through `NAMES.TXT`; matching CHR_MDLS families exist |
| `TEST.ENT` | `SPARKY_L00_CUTSCENE.SAM`, `LEONIDAS_L00_CUTSCENE.SAM` | CUTSCENE files | Exact filenames in ENT string area |
| `TEST.ENT` | `MARS_SMOKE2` | particle definition | Exact basename in ENT and `EFFECT_LIST.TXT` |
| `TEST.ENT` | `BRAZIER_DARK` | BIG prop | Exact basename; use/kick markers nearby |
| `MODELS.MVR` | `Brazier_Dark.CAS` | source-art identity | Six embedded repository paths; runtime resolution unknown |
| `MODELS.MTL` | 41 direct resource stems | TIM2 and particle TXT/TM2 files | Case-insensitive basename matches |
| particle TXT | eight APP_* basenames | particle TIM2 pages | Exact basename and matching page/frame dimensions |
| `TEST.ENT` | L0A voice/music identifiers | external audio | Explicit symbolic strings; no audio payload in PAK |
| `TEST.ENT` | `LEVEL01` / switch-level identifier | next runtime section | Explicit section-transition string |

## Character compatibility observations

- Castor, Pollux, Leonidas, Spartan Hoplite, and Spartan Swordsman use byte-identical 305-byte BNS data. This is a confirmed content identity and a likely common humanoid skeleton/bind compatibility group.
- Athenian Archer and Spartan body use distinct BNS hashes.
- Numbered NPC PSQ sets commonly descend in size from suffix 0 through 4, consistent with component/LOD partitioning, but the precise partition rule is unknown.
- Spartan equipment uses named render variants (`STANDARD`, `SHINEY`, `SHADOW`) controlled by small display-attribute text files.
- ANM directories are organized by reusable COMMON clips and character/weapon-specific sets. Embedded attachment metadata connects some attack clips to named weapons/body parts.

## World companion uncertainty

The seven `MODELS.*` files are unquestionably an archive family by basename, directory, adjacency, and size/count headers. The following role assignments remain hypotheses:

| File | Evidence | Current classification |
|---|---|---|
| `MODELS.BIN` | largest world binary, size header, MTL/texture adjacency | likely primary world geometry/render payload |
| `MODELS.AAB` | `master_L00A`, structured spatial data, AAB suffix | likely bounds/spatial acceleration |
| `MODELS.FLP` | 14 records and vector/matrix-like data | unknown, possibly flip/plane data |
| `MODELS.MVR` | six `Brazier_Dark.CAS` source paths | likely model-source/variant references |
| `MODELS.INS` | only 32 bytes, size-like fields | unknown |
| `MODELS.STL` | one count plus small indices | unknown lookup/index table; not standard STL |
| `MODELS.MTL` | completely parsed resource/property hierarchy | confirmed declaration container; numeric properties unknown |

## External/shared boundary

LEVEL00 duplicates global battle data, common animations, generic textures/effects, localization/name tables, and font resources, reinforcing the self-contained section-snapshot model. It does not embed sound payloads: voice, music, and effects remain symbolic. The section is therefore self-contained for most visual/gameplay definitions but depends on the external sound asset system.
