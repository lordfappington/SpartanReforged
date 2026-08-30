# LEVEL00 MODELS Family

This document records the evidence-based relationship among LEVEL00's `MODELS.BIN`, `MODELS.AAB`, `MODELS.MTL`, `MODELS.STL`, `MODELS.FLP`, `MODELS.MVR`, and `MODELS.INS`. All analysis was read-only and limited to the existing LEVEL00 extraction.

## Input identity

| File | Bytes | SHA-256 | Git tracked |
|---|---:|---|---|
| `MODELS.BIN` | 2,293,536 | `8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3` | No |
| `MODELS.AAB` | 448,048 | `ce46a8c58509d74ceeabedf22d1832dcd365c87d2f8bc583120f1f37797e99d7` | No |
| `MODELS.MTL` | 5,952 | `57283516fc3cc8589eec4817cf8c25dc3ff0cc2185e4ff99e262fa6f3a4a54b2` | No |
| `MODELS.STL` | 136 | `4b3a74944557c286c115ef2340dd4d88b4cd7cd76ae3ee9596b2653db3158bea` | No |
| `MODELS.FLP` | 1,136 | `a3bf1d99151af7cd83b06273d72cd9d902b67daaa1e7441baac26648f6f4876c` | No |
| `MODELS.MVR` | 1,600 | `7567423239a94da9f81a330f54510047ec78ee5f7b591e985d6da0b13b1c5620` | No |
| `MODELS.INS` | 32 | `06251ad6344c19686b0921f8e5974507903266aa9f063e89c937bc5188f333c3` | No |

Hash capitalization is presentation-only. The values were computed directly from the inputs immediately before analysis.

## Working family model

| File | Supported role | Confidence |
|---|---|---|
| BIN | Descriptor-indexed PS2 VIF geometry/render streams | **CONFIRMED container and VIF structure; geometry semantics LIKELY** |
| AAB | Seven-level 4-way spatial tree with bounding/cell records and BIN descriptor lists | **CONFIRMED tree/reference structure; exact runtime traversal UNKNOWN** |
| MTL | Ordered resource/material declaration records selected numerically by BIN | **CONFIRMED binding; individual property meanings UNKNOWN** |
| STL | 32-slot signed table containing MTL record indices 40–47 | **CONFIRMED structure/reference; runtime purpose UNKNOWN** |
| FLP | Fourteen fixed 80-byte transform/parameter records | **CONFIRMED structure; role LIKELY placement/variant data** |
| MVR | Six fixed 264-byte source/variant records naming `Brazier_Dark.CAS` | **CONFIRMED structure; runtime role LIKELY** |
| INS | Eight-u32 table dominated by the repeated value 32 | **CONFIRMED contents; purpose UNKNOWN** |

## MODELS.AAB structure

### Header

| Offset | Size | Value | Interpretation | Confidence |
|---:|---:|---|---|---|
| `0x00` | 4 | 448,048 | exact file size | **CONFIRMED** |
| `0x04` | 4 | 5,461 | total tree nodes | **CONFIRMED** by traversal |
| `0x08` | 4 | 16,382 | unknown; numerically `3 × 5461 - 1` | **UNKNOWN** |
| `0x0c` | 4 | 32 | bounding/cell record size | **LIKELY** |
| `0x10` | 4 | 1 | root/object count | **LIKELY** |
| `0x14` | 12 | `master_L00A` | tree/world identifier | **CONFIRMED** |
| `0x20` | 20 | five absolute offsets | root bounds pointer plus four child-node pointers | **CONFIRMED structure** |

A full pointer traversal produces exactly:

| Depth | Nodes |
|---:|---:|
| 0 | 1 |
| 1 | 4 |
| 2 | 16 |
| 3 | 64 |
| 4 | 256 |
| 5 | 1,024 |
| 6 | 4,096 |
| **Total** | **5,461** |

This is exactly `1 + 4 + 4² + … + 4⁶`, proving a complete seven-level 4-way tree. There are 1,365 internal nodes and 4,096 leaf nodes.

Each internal node has a `0x30` pointer record. Its first pointer targets an immediately following `0x80` block containing four 32-byte cell/bounds records; the other four pointers select child nodes. Leaf nodes are `0x30` zero records. X/Z origins follow a subdividing grid beginning near -512, while widths/depths halve through 256, 128, 64, 32, and 16. Occupied cells contain plausible vertical min/extent values; empty cells commonly use Y=100,000 and zero height. This is specific evidence for an axis-aligned spatial quadtree, not an inference from `.AAB` alone.

Four hundred eighty-four non-empty leaf-associated regions begin with a u32 count and u32 BIN descriptor IDs. Counts range from 1 to 11. Collectively they contain exactly 1,224 unique IDs, covering every BIN descriptor from 114 through 1337 once and no other ID. Some regions contain additional aligned words after the demonstrated ID list; those trailing fields remain unknown.

## Ordered MODELS.MTL table

The MTL header declares record offset `0x250` and 55 names. Each top-level record has a 16-byte header followed by counted length-delimited child blocks, and the complete walk ends at EOF. `BIN refs` counts descriptors whose packed high u16 selects that record.

| Index | Name | Children | Child lengths | Child types | Nonzero first numeric values | Resource reference | BIN refs |
|---:|---|---:|---|---|---|---|---:|
| 0 | `DESTRUCTABLES` | 4 | 16/16/32/16 | 21/8/0/19 | 21:1 | same stem | 13 |
| 1 | `L0_FLAGS` | 3 | 16/32/16 | 22/0/19 | — | same stem | 43 |
| 2 | `ARROW` | 4 | 16/16/16/16 | 8/22/0/19 | — | same stem | 2 |
| 3 | `PICKUPS` | 4 | 16/16/32/16 | 8/22/0/19 | — | same stem | 15 |
| 4 | `PICKUPS_2SIDED` | 4 | 32/32/16/16 | 0/1/22/19 | — | alias `pickups` | 1 |
| 5 | `002` | 1 | 16 | 0 | — | same stem | 440 |
| 6 | `RUINEDWALL1` | 1 | 32 | 0 | — | same stem | 41 |
| 7 | `BASEWALL` | 1 | 32 | 0 | — | same stem | 109 |
| 8 | `BASEWALL2` | 1 | 32 | 0 | — | same stem | 40 |
| 9 | `BASEWALL3` | 1 | 32 | 0 | — | same stem | 22 |
| 10 | `GENWOOD` | 1 | 32 | 0 | — | same stem | 42 |
| 11 | `ROOF` | 1 | 16 | 0 | — | same stem | 51 |
| 12 | `TEMPLE_FLAGS` | 1 | 32 | 0 | — | same stem | 76 |
| 13 | `TEMPLE1` | 1 | 32 | 0 | — | same stem | 68 |
| 14 | `TEMPLE3` | 1 | 32 | 0 | — | same stem | 54 |
| 15 | `LS_STONEWALL1` | 1 | 32 | 0 | — | same stem | 40 |
| 16 | `PILLARS` | 1 | 32 | 0 | — | same stem | 53 |
| 17 | `TEMPLE2` | 1 | 32 | 0 | — | same stem | 44 |
| 18 | `MISCALPHA` | 4 | 16/16/32/16 | 2/22/0/19 | 2:1 | same stem | 2 |
| 19 | `MOSAIC` | 1 | 16 | 0 | — | same stem | 21 |
| 20 | `STEPS` | 1 | 16 | 0 | — | same stem | 16 |
| 21 | `AMBIENT_FOLIAGE` | 6 | 16/16/16/16/32/16 | 2/16/13/15/0/19 | 2:5 | same stem | 0 |
| 22 | `HEAD_MARKERS` | 3 | 16/32/16 | 13/0/19 | — | same stem | 2 |
| 23 | `APP_BLOOD_02` | 5 | 16/16/16/32/16 | 16/8/2/0/19 | 2:3 | same stem | 1 |
| 24 | `APP_FIRE_BASE` | 6 | 32/32/16/16/16/16 | 0/1/16/8/2/19 | 16:1, 2:3 | alias `app_blood_02` | 1 |
| 25 | `LIGHTNING` | 4 | 16/16/16/32 | 13/19/18/0 | 19:1, 18:2 | same stem | 1 |
| 26 | `BEAM` | 8 | 16×8 | 21/13/16/19/26/18/22/0 | 21:1, 16:1, 19:1, 26:1, 18:2 | same stem | 1 |
| 27 | `CIRCLE` | 7 | 16×7 | 8/2/16/18/22/0/19 | 2:5, 16:1, 18:1 | same stem | 1 |
| 28 | `APP_MEDUSA` | 5 | 16/16/16/16/32 | 21/13/19/22/0 | 21:1, 19:1 | same stem | 1 |
| 29 | `LIGHT_SPHERE01` | 6 | 16/16/16/16/32/16 | 21/15/13/18/0/19 | 21:1, 15:6 | same stem | 1 |
| 30 | `LIGHT_SPHERE02` | 6 | 16/16/16/16/32/16 | 21/15/13/18/0/19 | 21:1, 15:7 | same stem | 1 |
| 31 | `CLOUD` | 4 | 16×4 | 21/2/0/19 | 21:1, 2:5 | same stem | 1 |
| 32 | `GIBS` | 4 | 16×4 | 8/2/0/19 | 2:5 | same stem | 8 |
| 33 | `GRKTREE` | 4 | 16/16/32/16 | 2/22/0/19 | 2:2 | same stem | 32 |
| 34 | `MEDUSA_TOWER` | 4 | 16/16/32/16 | 21/2/0/19 | 21:1, 2:5 | same stem | 16 |
| 35 | `GREENERY` | 5 | 16/16/16/32/16 | 2/4/22/0/19 | 2:5, 4:-20 | same stem | 57 |
| 36 | `NON_LINEAR_REMAPPING` | 6 | 16/16/16/16/32/16 | 21/15/8/18/0/19 | 21:1, 15:9 | same stem | 0 |
| 37 | `GLOW` | 4 | 16×4 | 13/8/0/19 | — | same stem | 18 |
| 38 | `GREEK_PATERN` | 6 | 16/16/16/16/32/16 | 21/2/16/8/0/19 | 21:1, 2:5 | same stem | 1 |
| 39 | `RING_GLOW` | 6 | 16/16/16/16/32/16 | 8/2/18/22/0/19 | 2:3, 18:1 | same stem | 1 |
| 40 | `APP_FIRE` | 6 | 16/16/16/16/32/16 | 12/2/17/16/0/19 | 2:3, 16:1 | same stem | 0 |
| 41 | `APP_SMOKE` | 6 | 16/16/16/16/32/16 | 12/2/16/24/0/19 | 12:1, 2:3, 24:5 | same stem | 0 |
| 42 | `APP_TORCH` | 6 | 16/16/16/16/32/16 | 12/2/17/16/0/19 | 12:4, 2:3 | same stem | 0 |
| 43 | `APP_GLOWBALLS` | 6 | 16/16/16/16/32/16 | 12/2/17/16/0/19 | 12:5, 2:3 | same stem | 0 |
| 44 | `APP_PROJECTILE` | 5 | 16/16/16/32/16 | 12/2/16/0/19 | 12:7, 2:3, 16:1 | same stem | 0 |
| 45 | `APP_ENV` | 5 | 16/16/16/32/16 | 12/2/16/0/19 | 12:9, 2:3 | same stem | 0 |
| 46 | `APP_BLOOD` | 5 | 16/16/16/32/16 | 12/2/16/0/19 | 12:12, 2:3 | same stem | 0 |
| 47 | `APP_DIRT` | 5 | 16/16/16/32/16 | 12/2/16/0/19 | 12:15, 2:3 | same stem | 0 |
| 48 | `GLOW_BUFFER_END` | 5 | 16/16/16/32/16 | 13/15/18/0/19 | 15:8, 18:1 | same stem | 0 |
| 49 | `FLARE_NOZREAD` | 8 | 16/32/16/16/16/16/16/16 | 0/1/16/2/8/18/22/19 | 16:1, 2:4, 18:1 | alias `flare` | 1 |
| 50 | `APP_BLACKBARS` | 6 | 16/16/16/16/32/16 | 21/15/13/18/0/19 | 21:1, 15:1 | same stem | 0 |
| 51 | `UI_PAGE1` | 8 | 16/16/16/16/16/16/32/16 | 2/16/15/12/11/18/0/19 | 2:5, 15:2, 12:13, 11:4096, 18:1 | same stem | 0 |
| 52 | `UI_PAGE2` | 8 | 16/16/16/16/16/16/32/16 | 2/16/15/12/11/18/0/19 | 2:5, 15:2, 12:13, 11:5120, 18:1 | same stem | 0 |
| 53 | `UI_PAGE3` | 9 | 16/16/16/16/32/32/16/16/16 | 2/15/12/16/0/1/11/18/19 | 2:5, 15:2, 12:13, 16:1, 11:4096, 18:1 | alias `ui_page2` | 0 |
| 54 | `APP_PS2FONT` | 7 | 16/16/16/16/16/32/16 | 2/16/15/12/18/0/19 | 2:5, 15:3, 12:14, 18:1 | same stem | 0 |

BIN uses 39 distinct record indices, all between 0 and 49. The AAB-indexed static partition uses records 5–20 and 33–35; the unindexed partition uses records 0–4, 22–32, 37–39, and 49. BIN itself is name-free.

## Other companions

### MODELS.STL

The file is not standard STL geometry. It is exactly:

- u32 value 1;
- u32 slot count 32;
- 32 signed u32 slots.

Eight slots are active: `41, 42, 43, 45, 44, 46, 40, 47`; the other 24 are `-1`. These are valid MTL indices and resolve exactly to the eight particle-page records `APP_SMOKE`, `APP_TORCH`, `APP_GLOWBALLS`, `APP_ENV`, `APP_PROJECTILE`, `APP_BLOOD`, `APP_FIRE`, and `APP_DIRT`. The lookup relationship is **CONFIRMED**; the reason for the order and 32-slot capacity is unknown.

### MODELS.FLP

The first u32 equals 1,136 and the second is 14. A 16-byte header is followed by exactly fourteen 80-byte records. Each record contains a 64-byte matrix/transform-like region and a repeated four-u32 tail `(1, 5, 43, 60)`. The layout is **CONFIRMED**; placement/flip semantics remain **LIKELY/UNKNOWN**.

### MODELS.MVR

The header is `(1600, 0, 6, 0)`, followed by six fixed 264-byte records. Each begins with the same source path, `C:\legend_repository\repository\bin\Brazier_Dark.CAS`, at record offsets separated by exactly 264 bytes. Matrix/transform-like data recur. Ten of the fourteen FLP record positions, including duplicate records, occur as exact 80-byte sequences in MVR. This confirms a shared record vocabulary and strongly supports a source-variant/placement relationship, but not which file owns runtime transforms.

### MODELS.INS

The eight u32 values are `(32, 0, 32, 0, 0, 32, 0, 0)`. The repeated 32 also appears as STL's slot count and AAB's record-size field, but no structural join proves that these meanings are shared. INS remains **UNKNOWN**.

## Cross-file count matrix

| Count | Source and field | Recurrence/correlation | Confidence | Possible interpretation |
|---:|---|---|---|---|
| 1,338 | BIN `0x08` | Exact descriptor-table length | **CONFIRMED** | Total VIF blocks |
| 114 | BIN descriptor/block split | Exactly the descriptors absent from AAB and carrying flag `0x10000` | **CONFIRMED split** | Special/dynamic/effect blocks **LIKELY** |
| 1,224 | BIN remainder; AAB leaf references | AAB enumerates IDs 114–1337 exactly once | **CONFIRMED** | Spatial/static world blocks |
| 2,128 | BIN block batch counts | Exact VIF batch parse; sum of all block headers | **CONFIRMED** | Render/strip batches |
| 88,314 | BIN three matching UNPACK counts | Same count across position/V2-16/V4-8 streams | **CONFIRMED streamed count** | Vertex instances **LIKELY** |
| 46,336 | BIN position-W zeros | Complement of 41,978 `0x8000` values | **CONFIRMED value; LIKELY** emitted triangles under ADC |
| 55 | MTL `0x04` | Ordered records; BIN IDs stay within first 50 | **CONFIRMED** | Resource/material declarations |
| 39 | Distinct BIN high-u16 values | Map to meaningful ordered MTL records | **CONFIRMED count and join** | Used render/material records |
| 5,461 | AAB `0x04` | `1+4+…+4⁶`; exact pointer traversal | **CONFIRMED** | Spatial-tree nodes |
| 1,365 / 4,096 | AAB traversal | Internal/leaf split in full depth-six tree | **CONFIRMED** | Quadtree topology |
| 16,382 | AAB `0x08` | Exactly `3×5461-1` | **CONFIRMED arithmetic; meaning UNKNOWN** | Unknown aggregate count |
| 32 | AAB `0x0c`, STL slot count, INS values | Independent recurrence without a reference join | **CONFIRMED values only** | Record size / capacity / unknown; do not merge meanings |
| 14 | FLP `0x04` | Exactly fills file as 14×80 after header | **CONFIRMED** | Transform/parameter records |
| 6 | MVR `0x08` | Exactly fills file as 6×264 after header | **CONFIRMED** | Source/variant records |
| 10 of 14 | FLP records found in MVR | Exact 80-byte sequence matches, duplicates included | **CONFIRMED match** | Shared transform vocabulary |

Global BIN header values 15, 48, and 30 have no safe count correlation and remain unknown.

## Evidence-based dependency hypothesis

```text
LEVEL00 world
├─ MODELS.AAB spatial quadtree
│  └─ exact leaf lists -> BIN descriptors 114–1337
├─ MODELS.BIN descriptor table
│  ├─ VIF batches -> positions + packed attributes + implicit topology
│  └─ high-u16 MTL index -> MODELS.MTL ordered record
│     └─ resource stem/alias -> packaged TM2/config resource
├─ MODELS.STL -> MTL particle-page indices 40–47
├─ MODELS.FLP <-> MODELS.MVR shared 80-byte transform records
│  └─ MVR source identity -> Brazier_Dark.CAS
└─ MODELS.INS -> unknown 32-valued table
```

The static-world path is directly evidenced. The FLP/MVR/INS runtime relationship remains a hypothesis and should not yet be implemented.

## Next research gate

Do not write a renderer/importer yet. The next bounded task should prove the BIN position-W topology rule and identify the V2-16 scale/bias and V4-8 attribute meaning. A real geometry parser becomes justified only after triangle assembly and attribute semantics are repeatably validated.
