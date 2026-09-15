# Spartan: Total Warrior character production roster

Status: **authoritative inventory baseline; unresolved rows remain explicitly gated for human review**.

This is a public-safe metadata record. It contains no extracted models, textures, animations, reconstructed meshes, or original-game renders.

## Counting summary

- Gameplay type definitions: **85** (60 packaged; 25 not observed in campaign/arena type tables)
- Geometry-bearing top-level model families: **46** (plus one texture-only `STONE` helper)
- Unique high-detail geometry signatures: **51**
- Unique character textures/skins: **67** decoded images (68 logical TM2 paths)
- Meaningful visible appearances: **61**
- Reforged distinct high-poly masters: **42**
- Major derived variants: **9**
- Texture/skin-only variants: **10**
- Gameplay aliases/components requiring no new asset: **12**
- Unresolved gameplay definitions: **20**
- Tripo: Roman complete **1**; Swordsman in progress **1**; remaining distinct masters **40**

These categories are intentionally not collapsed into one character count. The 61 evidenced appearances partition into 42 masters, 9 major derivatives, and 10 skin-only variants; alias and unresolved counts refer to gameplay definitions.

## Factions and categories

| Category | Appearances | Distinct masters | Model families |
|---|---:|---:|---|
| Barbarians | 5 | 3 | BAR_AXTH, BAR_BSRK, BAR_WARR |
| Bosses | 7 | 5 | BEOWULF, MARS, MEDUSA, NEMESIS, SEJANUS, TALOS |
| Civilians | 4 | 2 | CIV_MAN, CIV_WMAN |
| Creatures/monsters | 7 | 4 | HYDRA, LADON, MINOTAUR |
| Gigantes | 3 | 2 | GIG_BOSS, GIG_PET, GIG_WARR |
| Gladiators | 3 | 3 | GLD_GRNT, GLD_HEAV, GLD_RNGD |
| Named heroes/NPCs | 7 | 7 | ARCHIMDS, CASTOR, CRASSUS, ELEKTRA, LEONIDAS, POLLUX, TIBERIUS |
| Player | 4 | 1 | SPARTAN |
| Romans | 12 | 9 | PRA_ARCH, PRA_ASSN, PRA_CARN, PRA_GRNT, PRA_INFR, PRA_LGNY, RMN_ARCH, RMN_CENT, RMN_GRNT, RMN_HGNT, RMN_PRIE |
| Spartan/Greek allies | 4 | 4 | ATH_ARCH, SPT_HOPL, SPT_SAPR, SPT_SWRD |
| Undead | 5 | 2 | POLLUX, RMN_GRNT, SEJANUS, SKL_ARCH, SKL_WARR |

## Canonical gameplay type table

| ID | Internal name | Packaged | Category/role | Appearance/model | Production action | Confidence |
|---:|---|:---:|---|---|---|---|
| 0 | `THE_SPARTAN` | yes | Player / progression appearance | `PLAYER_SPARTAN_V4` / `SPARTAN` | DERIVE FROM PLAYER_SPARTAN_V1 | HIGH |
| 1 | `HYDRA` | yes | Creatures/monsters / multi-part monster | `HYDRA_DAUGHTER_TYPE1` / `HYDRA` | NEW HIGH-POLY MASTER | HIGH |
| 2 | `ROMAN_ARCHER` | yes | Romans / ranged infantry | `ROMAN_ARCHER` / `RMN_ARCH` | NEW HIGH-POLY MASTER | HIGH |
| 3 | `ROMAN_GRUNT` | yes | Romans / common infantry | `ROMAN_GRUNT` / `RMN_GRNT` | NEW HIGH-POLY MASTER | HIGH |
| 4 | `ROMAN_GRUNT_HEAVY` | yes | Romans / heavy infantry | `ROMAN_GRUNT_HEAVY` / `RMN_HGNT` | NEW HIGH-POLY MASTER | HIGH |
| 5 | `ROMAN_CENT` | yes | Romans / officer | `ROMAN_CENT` / `RMN_CENT` | NEW HIGH-POLY MASTER | HIGH |
| 6 | `PRAE_LEGIONARY` | yes | Romans / elite infantry | `PRAE_LEGIONARY` / `PRA_LGNY` | NEW HIGH-POLY MASTER | HIGH |
| 7 | `PRAE_ASSASSIN` | yes | Romans / assassin | `PRAE_ASSASSIN` / `PRA_ASSN` | NEW HIGH-POLY MASTER | HIGH |
| 8 | `SPARTAN_HOPLITE` | yes | Spartan/Greek allies / spear infantry | `SPARTAN_HOPLITE` / `SPT_HOPL` | NEW HIGH-POLY MASTER | HIGH |
| 9 | `MINATAUR` | yes | Creatures/monsters / monster | `MINATAUR` / `MINOTAUR` | NEW HIGH-POLY MASTER | HIGH |
| 10 | `CYCLOPS` | no | Creatures/monsters / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 11 | `SPARTAN_SWORDSMAN` | yes | Spartan/Greek allies / common infantry | `SPARTAN_SWORDSMAN` / `SPT_SWRD` | NEW HIGH-POLY MASTER | HIGH |
| 12 | `ATHENIAN_ARCHER` | yes | Spartan/Greek allies / ranged infantry | `ATHENIAN_ARCHER` / `ATH_ARCH` | NEW HIGH-POLY MASTER | HIGH |
| 13 | `BARBARIAN_WARRIOR` | yes | Barbarians / common infantry | `BARBARIAN_WARRIOR` / `BAR_WARR` | NEW HIGH-POLY MASTER | HIGH |
| 14 | `CASTOR` | yes | Named heroes/NPCs / named ally | `CASTOR` / `CASTOR` | NEW HIGH-POLY MASTER | HIGH |
| 15 | `POLLUX` | yes | Named heroes/NPCs / named ally | `POLLUX` / `POLLUX` | NEW HIGH-POLY MASTER | HIGH |
| 16 | `CRASSUS` | yes | Named heroes/NPCs / named Roman | `CRASSUS` / `CRASSUS` | NEW HIGH-POLY MASTER | HIGH |
| 17 | `SEJANUS` | yes | Bosses / named villain | `SEJANUS` / `SEJANUS` | NEW HIGH-POLY MASTER | HIGH |
| 18 | `LEONIDAS` | yes | Named heroes/NPCs / named ally | `LEONIDAS` / `LEONIDAS` | NEW HIGH-POLY MASTER | HIGH |
| 19 | `SPARTAN_COMMANDER` | no | Spartan/Greek allies / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 20 | `SKELETON_WARRIOR` | yes | Undead / melee infantry | `SKELETON_WARRIOR` / `SKL_WARR` | NEW HIGH-POLY MASTER | HIGH |
| 21 | `ROMAN_ZOMBIE_WARRIOR` | yes | Undead / undead infantry | `ROMAN_ZOMBIE_WARRIOR` / `RMN_GRNT` | TEXTURE/MATERIAL VARIANT OF ROMAN_GRUNT | HIGH |
| 22 | `SPARTAN_ZOMBIE_WARRIOR` | no | Undead / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 23 | `FAST_ROMAN_ZOMBIE_WARRIOR` | no | Undead / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 24 | `FAST_SPARTAN_ZOMBIE_WARRIOR` | no | Undead / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 25 | `MEDUSA` | yes | Bosses / boss | `MEDUSA` / `MEDUSA` | NEW HIGH-POLY MASTER | HIGH |
| 26 | `MEDUSA_SNAKES` | no | Bosses / alias/component | `MEDUSA` / `MEDUSA` | DUPLICATE / NO NEW ASSET | LIKELY |
| 27 | `ROMAN_ARCHER_SNOW` | yes | Romans / snow ranged infantry | `ROMAN_ARCHER_SNOW` / `PRA_ARCH` | TEXTURE/MATERIAL VARIANT OF ROMAN_ARCHER | HIGH |
| 28 | `ROMAN_GRUNT_SNOW` | yes | Romans / snow infantry | `ROMAN_GRUNT_SNOW` / `PRA_GRNT` | TEXTURE/MATERIAL VARIANT OF ROMAN_GRUNT | HIGH |
| 29 | `ROMAN_GRUNT_HEAVY_SNOW` | no | Romans / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 30 | `ROMAN_CENT_SNOW` | no | Romans / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 31 | `ROMAN_PRIEST` | yes | Romans / caster/support | `ROMAN_PRIEST` / `RMN_PRIE` | NEW HIGH-POLY MASTER | HIGH |
| 32 | `CIVILIAN_CHILD` | no | Civilians / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 33 | `CIVILIAN_MAN` | yes | Civilians / civilian | `CIVILIAN_MAN` / `CIV_MAN` | NEW HIGH-POLY MASTER | HIGH |
| 34 | `CIVILIAN_WOMAN` | yes | Civilians / civilian | `CIVILIAN_WOMAN` / `CIV_WMAN` | NEW HIGH-POLY MASTER | HIGH |
| 35 | `BARBARIAN_AXE_THROWER` | yes | Barbarians / ranged specialist | `BARBARIAN_AXE_THROWER` / `BAR_AXTH` | NEW HIGH-POLY MASTER | HIGH |
| 36 | `BARBARIAN_BERSERKER` | yes | Barbarians / heavy melee | `BARBARIAN_BERSERKER` / `BAR_BSRK` | NEW HIGH-POLY MASTER | HIGH |
| 37 | `BARBARIAN_GHOUL` | no | Undead / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 38 | `AMAZON_HUNTRESS` | yes | Named heroes/NPCs / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 39 | `AMAZON_WARRIOR` | yes | Named heroes/NPCs / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 40 | `SKELETON_ARCHER` | yes | Undead / ranged infantry | `SKELETON_ARCHER` / `SKL_ARCH` | NEW HIGH-POLY MASTER | HIGH |
| 41 | `PRAE_CARNIFEX` | yes | Romans / specialist | `PRAE_CARNIFEX` / `PRA_CARN` | NEW HIGH-POLY MASTER | HIGH |
| 42 | `PRAE_INFERNUS` | yes | Romans / specialist | `PRAE_INFERNUS` / `PRA_INFR` | NEW HIGH-POLY MASTER | HIGH |
| 43 | `GLADIATOR_THRACIAN` | yes | Gladiators / arena grunt | `GLADIATOR_THRACIAN` / `GLD_GRNT` | NEW HIGH-POLY MASTER | HIGH |
| 44 | `GLADIATOR_SAMNITE` | yes | Gladiators / arena ranged | `GLADIATOR_SAMNITE` / `GLD_RNGD` | NEW HIGH-POLY MASTER | HIGH |
| 45 | `GLADIATOR_CHAMPION` | yes | Gladiators / arena heavy | `GLADIATOR_CHAMPION` / `GLD_HEAV` | NEW HIGH-POLY MASTER | HIGH |
| 46 | `GIGANTES_WARRIOR` | yes | Gigantes / giant infantry | `GIGANTES_WARRIOR` / `GIG_WARR` | NEW HIGH-POLY MASTER | HIGH |
| 47 | `GIGANTES_BOSS` | yes | Gigantes / boss | `GIGANTES_BOSS` / `GIG_BOSS` | NEW HIGH-POLY MASTER | HIGH |
| 48 | `GIGANTES_CAPTAIN` | yes | Gigantes / captain skin | `GIGANTES_CAPTAIN` / `GIG_PET` | TEXTURE/MATERIAL VARIANT OF GIGANTES_WARRIOR | HIGH |
| 49 | `GAIUS` | yes | Named heroes/NPCs / named NPC | `GAIUS_TIBERIUS` / `TIBERIUS` | NEW HIGH-POLY MASTER | LIKELY |
| 50 | `ARCHIMEDES` | yes | Named heroes/NPCs / named NPC | `ARCHIMEDES` / `ARCHIMDS` | NEW HIGH-POLY MASTER | HIGH |
| 51 | `UNDEAD_SEJANUS` | yes | Undead / named boss variant | `UNDEAD_SEJANUS` / `SEJANUS` | DERIVE FROM SEJANUS | HIGH |
| 52 | `ARES` | yes | Bosses / god/boss | `ARES` / `MARS` | NEW HIGH-POLY MASTER | HIGH |
| 53 | `BEOWULF` | yes | Bosses / named boss | `BEOWULF` / `BEOWULF` | NEW HIGH-POLY MASTER | HIGH |
| 54 | `HIPPOLYTA` | no | Named heroes/NPCs / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 55 | `ELEKTRA` | yes | Named heroes/NPCs / named ally | `ELEKTRA` / `ELEKTRA` | NEW HIGH-POLY MASTER | HIGH |
| 56 | `NEMESIS` | yes | Bosses / boss/player-form variant | `NEMESIS` / `NEMESIS` | TEXTURE/MATERIAL VARIANT OF PLAYER_SPARTAN_V3 | HIGH |
| 57 | `LADON` | yes | Creatures/monsters / winged boss | `LADON` / `LADON` | NEW HIGH-POLY MASTER | HIGH |
| 58 | `TYPHON` | no | Creatures/monsters / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 59 | `HARPY` | no | Creatures/monsters / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 60 | `SPARTAN_SERGEANT` | no | Spartan/Greek allies / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 61 | `ROMAN_GRUNT_ELITE` | no | Romans / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 62 | `ROMAN_GRUNT_HEAVY_ELITE` | no | Romans / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 63 | `DUMMY_COLLUSION` | yes | Special/nonstandard / alias/component | `—` / `—` | DUPLICATE / NO NEW ASSET | HIGH |
| 64 | `ROMAN_CENT_ELITE` | no | Romans / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 65 | `ROMAN_CENT_ZOMBIE` | no | Undead / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 66 | `PRAE_CENT` | no | Romans / unresolved definition | `—` / `—` | HUMAN REVIEW REQUIRED | UNKNOWN |
| 67 | `HYDRA_MOTHERHEAD` | yes | Creatures/monsters / alias/component | `HYDRA_MOTHER` / `HYDRA` | DUPLICATE / NO NEW ASSET | HIGH |
| 68 | `HYDRA_HEADLESS_NECK` | yes | Creatures/monsters / alias/component | `HYDRA_MOTHER` / `HYDRA` | DUPLICATE / NO NEW ASSET | HIGH |
| 69 | `HYDRA_DECAPITATED_HEAD` | yes | Creatures/monsters / alias/component | `HYDRA_MOTHER` / `HYDRA` | DUPLICATE / NO NEW ASSET | HIGH |
| 70 | `BARBARIAN_WARRIOR_VER_B` | yes | Barbarians / warrior variant | `BARBARIAN_WARRIOR_VER_B` / `BAR_WARR` | DERIVE FROM BARBARIAN_WARRIOR | HIGH |
| 71 | `BARBARIAN_WARRIOR_VER_C` | yes | Barbarians / warrior variant | `BARBARIAN_WARRIOR_VER_C` / `BAR_WARR` | DERIVE FROM BARBARIAN_WARRIOR | HIGH |
| 72 | `DUMMY_COLLISION_NOT_BOW_TARGETTABLE` | yes | Special/nonstandard / alias/component | `—` / `—` | DUPLICATE / NO NEW ASSET | HIGH |
| 73 | `SPARTAN_ELITE` | no | Spartan/Greek allies / alias/component | `SPARTAN_SWORDSMAN` / `SPT_SWRD` | DUPLICATE / NO NEW ASSET | HIGH |
| 74 | `CIVILIAN_MAN_ATHENIAN` | yes | Civilians / civilian variant | `CIVILIAN_MAN_ATHENIAN` / `CIV_MAN` | DERIVE FROM CIVILIAN_MAN | HIGH |
| 75 | `CIVILIAN_WOMAN_ATHENIAN` | yes | Civilians / civilian variant | `CIVILIAN_WOMAN_ATHENIAN` / `CIV_WMAN` | DERIVE FROM CIVILIAN_WOMAN | HIGH |
| 76 | `TALOS` | yes | Bosses / boss phase | `TALOS_PHASE1` / `TALOS` | NEW HIGH-POLY MASTER | HIGH |
| 77 | `SPARTAN_SAPPER` | yes | Spartan/Greek allies / specialist | `SPARTAN_SAPPER` / `SPT_SAPR` | NEW HIGH-POLY MASTER | HIGH |
| 78 | `POLLUX_ZOMBIE` | yes | Undead / named undead variant | `POLLUX_ZOMBIE` / `POLLUX` | TEXTURE/MATERIAL VARIANT OF POLLUX | HIGH |
| 79 | `ROMAN_GRUNT_WEAK` | yes | Romans / weaker common infantry | `ROMAN_GRUNT_WEAK` / `RMN_GRNT` | TEXTURE/MATERIAL VARIANT OF ROMAN_GRUNT | HIGH |
| 80 | `THE_SPARTAN_USING_SWORD` | no | Player / alias/component | `PLAYER_SPARTAN_V1` / `SPARTAN` | DUPLICATE / NO NEW ASSET | HIGH |
| 81 | `THE_SPARTAN_USING_DAGGER` | no | Player / alias/component | `PLAYER_SPARTAN_V1` / `SPARTAN` | DUPLICATE / NO NEW ASSET | HIGH |
| 82 | `THE_SPARTAN_USING_SPEAR` | no | Player / alias/component | `PLAYER_SPARTAN_V1` / `SPARTAN` | DUPLICATE / NO NEW ASSET | HIGH |
| 83 | `THE_SPARTAN_USING_AXE` | no | Player / alias/component | `PLAYER_SPARTAN_V1` / `SPARTAN` | DUPLICATE / NO NEW ASSET | HIGH |
| 84 | `THE_SPARTAN_USING_TWIN_SWORDS` | no | Player / alias/component | `PLAYER_SPARTAN_V1` / `SPARTAN` | DUPLICATE / NO NEW ASSET | HIGH |

## Meaningful visible appearances and production classification

| Appearance | Type IDs | Family | Classification | Priority | Derivation |
|---|---|---|---|---|---|
| `PLAYER_SPARTAN_V1` | 0 | `SPARTAN` | DISTINCT MASTER | P0 | `NEW HIGH-POLY MASTER` |
| `PLAYER_SPARTAN_V2` | 0 | `SPARTAN` | MAJOR VARIANT | P4 | `PLAYER_SPARTAN_V1` |
| `PLAYER_SPARTAN_V3` | 0 | `SPARTAN` | MAJOR VARIANT | P4 | `PLAYER_SPARTAN_V1` |
| `PLAYER_SPARTAN_V4` | 0 | `SPARTAN` | MAJOR VARIANT | P4 | `PLAYER_SPARTAN_V1` |
| `HYDRA_DAUGHTER_TYPE1` | 1 | `HYDRA` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `HYDRA_DAUGHTER_TYPE2` | component/skin | `HYDRA` | SKIN VARIANT | P4 | `HYDRA_DAUGHTER_TYPE1` |
| `HYDRA_DAUGHTER_TYPE3` | component/skin | `HYDRA` | SKIN VARIANT | P4 | `HYDRA_DAUGHTER_TYPE1` |
| `HYDRA_DAUGHTER_TYPE4` | component/skin | `HYDRA` | SKIN VARIANT | P4 | `HYDRA_DAUGHTER_TYPE1` |
| `HYDRA_MOTHER` | component/skin | `HYDRA` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `ROMAN_ARCHER` | 2 | `RMN_ARCH` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `ROMAN_GRUNT` | 3 | `RMN_GRNT` | DISTINCT MASTER | P0 | `NEW HIGH-POLY MASTER` |
| `ROMAN_GRUNT_WEAK` | 79 | `RMN_GRNT` | SKIN VARIANT | P4 | `ROMAN_GRUNT` |
| `ROMAN_ZOMBIE_WARRIOR` | 21 | `RMN_GRNT` | SKIN VARIANT | P4 | `ROMAN_GRUNT` |
| `ROMAN_GRUNT_HEAVY` | 4 | `RMN_HGNT` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `ROMAN_CENT` | 5 | `RMN_CENT` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `PRAE_LEGIONARY` | 6 | `PRA_LGNY` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `PRAE_ASSASSIN` | 7 | `PRA_ASSN` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `SPARTAN_HOPLITE` | 8 | `SPT_HOPL` | DISTINCT MASTER | P0 | `NEW HIGH-POLY MASTER` |
| `MINATAUR` | 9 | `MINOTAUR` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `SPARTAN_SWORDSMAN` | 11 | `SPT_SWRD` | DISTINCT MASTER | P0 | `NEW HIGH-POLY MASTER` |
| `ATHENIAN_ARCHER` | 12 | `ATH_ARCH` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `BARBARIAN_WARRIOR` | 13 | `BAR_WARR` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `BARBARIAN_WARRIOR_VER_B` | 70 | `BAR_WARR` | MAJOR VARIANT | P4 | `BARBARIAN_WARRIOR` |
| `BARBARIAN_WARRIOR_VER_C` | 71 | `BAR_WARR` | MAJOR VARIANT | P4 | `BARBARIAN_WARRIOR` |
| `CASTOR` | 14 | `CASTOR` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `POLLUX` | 15 | `POLLUX` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `POLLUX_ZOMBIE` | 78 | `POLLUX` | SKIN VARIANT | P4 | `POLLUX` |
| `CRASSUS` | 16 | `CRASSUS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `SEJANUS` | 17 | `SEJANUS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `UNDEAD_SEJANUS` | 51 | `SEJANUS` | MAJOR VARIANT | P3 | `SEJANUS` |
| `LEONIDAS` | 18 | `LEONIDAS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `SKELETON_WARRIOR` | 20 | `SKL_WARR` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `MEDUSA` | 25 | `MEDUSA` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `ROMAN_ARCHER_SNOW` | 27 | `PRA_ARCH` | SKIN VARIANT | P4 | `ROMAN_ARCHER` |
| `ROMAN_GRUNT_SNOW` | 28 | `PRA_GRNT` | SKIN VARIANT | P4 | `ROMAN_GRUNT` |
| `ROMAN_PRIEST` | 31 | `RMN_PRIE` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `CIVILIAN_MAN` | 33 | `CIV_MAN` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `CIVILIAN_MAN_ATHENIAN` | 74 | `CIV_MAN` | MAJOR VARIANT | P4 | `CIVILIAN_MAN` |
| `CIVILIAN_WOMAN` | 34 | `CIV_WMAN` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `CIVILIAN_WOMAN_ATHENIAN` | 75 | `CIV_WMAN` | MAJOR VARIANT | P4 | `CIVILIAN_WOMAN` |
| `BARBARIAN_AXE_THROWER` | 35 | `BAR_AXTH` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `BARBARIAN_BERSERKER` | 36 | `BAR_BSRK` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `SKELETON_ARCHER` | 40 | `SKL_ARCH` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `PRAE_CARNIFEX` | 41 | `PRA_CARN` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `PRAE_INFERNUS` | 42 | `PRA_INFR` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `GLADIATOR_THRACIAN` | 43 | `GLD_GRNT` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `GLADIATOR_SAMNITE` | 44 | `GLD_RNGD` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `GLADIATOR_CHAMPION` | 45 | `GLD_HEAV` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |
| `GIGANTES_WARRIOR` | 46 | `GIG_WARR` | DISTINCT MASTER | P1 | `NEW HIGH-POLY MASTER` |
| `GIGANTES_CAPTAIN` | 48 | `GIG_PET` | SKIN VARIANT | P4 | `GIGANTES_WARRIOR` |
| `GIGANTES_BOSS` | 47 | `GIG_BOSS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `GAIUS_TIBERIUS` | 49 | `TIBERIUS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `ARCHIMEDES` | 50 | `ARCHIMDS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `ARES` | 52 | `MARS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `BEOWULF` | 53 | `BEOWULF` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `ELEKTRA` | 55 | `ELEKTRA` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `NEMESIS` | 56 | `NEMESIS` | SKIN VARIANT | P3 | `PLAYER_SPARTAN_V3` |
| `LADON` | 57 | `LADON` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `TALOS_PHASE1` | 76 | `TALOS` | DISTINCT MASTER | P3 | `NEW HIGH-POLY MASTER` |
| `TALOS_PHASE2` | component/skin | `TALOS` | MAJOR VARIANT | P3 | `TALOS_PHASE1` |
| `SPARTAN_SAPPER` | 77 | `SPT_SAPR` | DISTINCT MASTER | P2 | `NEW HIGH-POLY MASTER` |

## Geometry and texture deduplication

Every PSQ in the 22 campaign/arena extracts was hashed and decoded through the common 48-byte record layout for an order/winding-independent mesh fingerprint. All decoded duplicate groups matched byte-identical groups; no container-only geometry duplicate was found. The principal production-relevant exact reuse is:

- `PRA_ARCH/PARCH*` geometry equals `RMN_ARCH/RARCH*`.
- `PRA_GRNT/PGRT*`, base/weak/zombie `RMN_GRNT/RGRT*` geometry equals across all five LODs.
- `GIG_PET/GWARR*` equals `GIG_WARR/GWARR*` geometry.
- Pollux and Zombie Pollux geometry is identical.
- Nemesis body PSQ, shiny PSQ, and multiweight data equal player body variation 3.
- Player weapon aliases and Hydra component types are states/components, not new characters.

There are 68 logical character/helper TM2 paths and 67 unique byte/decoded-RGBA images. The sole exact texture duplicate is player `TEXTURE_EXTRAS` variation 1 = variation 2; no container-different decoded duplicate was found.

## Skeleton reuse

The corpus contains **16 byte-distinct BNS files** but only **6 parent-topology families**: the dominant 16-bone humanoid topology plus 1-bone dummy, 18-bone Minotaur, 19-bone Hydra, 21-bone Gigantes, and 60-bone Ladon families.

The exact 16-bone sharing groups are retained in the manifest. Particularly useful reuse clusters are the broad Roman/common humanoid BNS, the allied/named Greek BNS, the Barbarian/Gladiator BNS, and the Gigantes BNS.

## Animation-family inventory

- **shared:** `COMMON`
- **player:** `GREEK/SPARTAN/AXE`, `GREEK/SPARTAN/SPEAR`, `GREEK/SPARTAN/SWORD1`, `GREEK/SPARTAN/TWIN`, `GREEK/SPARTAN/IMPACTS`
- **Greek/allied:** `GREEK/ATH_ARCH`, `GREEK/CASTOR`, `GREEK/CIV_MAN`, `GREEK/CIV_WMAN`, `GREEK/HOPLITE`, `GREEK/LEONIDAS`, `GREEK/NEMESIS`, `GREEK/POLLUX`, `GREEK/SAPPER`, `GREEK/SWORD`
- **Roman:** `ROMAN/ARCHER`, `ROMAN/CENT`, `ROMAN/GRUNT`, `ROMAN/PRA_ASS`, `ROMAN/PRA_CARN`, `ROMAN/PRA_INFR`, `ROMAN/PRA_LGNY`, `ROMAN/PRIESTESS`, `ROMAN/UNDEAD/ZOMBIE_1`
- **Barbarian:** `BRBARIAN/AXTHROWR`, `BRBARIAN/BEOWULF`, `BRBARIAN/BERSRKER`, `BRBARIAN/WARRIOR`
- **special/boss:** `AMAZON/ELEKTRA`, `CRASSUS`, `GIGANTES`, `GIGANTES/BOSS`, `GLADIATOR/GRUNT`, `GLADIATOR/HEAVY`, `GLADIATOR/RANGED`, `HYDRA/DGHTR`, `HYDRA/MOTHR`, `LADON`, `MARS`, `MEDUSA`, `MINOTAUR`, `SEJANUS/ALIVE`, `SKELETON/WARRIOR`, `TALOS`

## Tripo high-poly master queue

| Rank | Master | Faction | Status | Derived variants |
|---:|---|---|---|---|
| 1 | `ROMAN_GRUNT` | Romans | HUMAN APPROVED / COMPLETE — ROMAN_GRUNT_REFORGED_HIGH_MASTER_V1 | ROMAN_GRUNT_WEAK, ROMAN_ZOMBIE_WARRIOR, ROMAN_GRUNT_SNOW |
| 2 | `SPARTAN_SWORDSMAN` | Spartan/Greek allies | CANONICAL RECOVERY COMPLETE — REFORGED CONCEPT / TRIPO MASTER IN PROGRESS | — |
| 3 | `PLAYER_SPARTAN_V1` | Player | NOT STARTED | PLAYER_SPARTAN_V2, PLAYER_SPARTAN_V3, PLAYER_SPARTAN_V4 |
| 4 | `SPARTAN_HOPLITE` | Spartan/Greek allies | NOT STARTED | — |
| 5 | `ATHENIAN_ARCHER` | Spartan/Greek allies | NOT STARTED | — |
| 6 | `SPARTAN_SAPPER` | Spartan/Greek allies | NOT STARTED | — |
| 7 | `ROMAN_ARCHER` | Romans | NOT STARTED | ROMAN_ARCHER_SNOW |
| 8 | `ROMAN_GRUNT_HEAVY` | Romans | NOT STARTED | — |
| 9 | `ROMAN_CENT` | Romans | NOT STARTED | — |
| 10 | `PRAE_LEGIONARY` | Romans | NOT STARTED | — |
| 11 | `PRAE_ASSASSIN` | Romans | NOT STARTED | — |
| 12 | `PRAE_CARNIFEX` | Romans | NOT STARTED | — |
| 13 | `PRAE_INFERNUS` | Romans | NOT STARTED | — |
| 14 | `ROMAN_PRIEST` | Romans | NOT STARTED | — |
| 15 | `BARBARIAN_WARRIOR` | Barbarians | NOT STARTED | BARBARIAN_WARRIOR_VER_B, BARBARIAN_WARRIOR_VER_C |
| 16 | `BARBARIAN_AXE_THROWER` | Barbarians | NOT STARTED | — |
| 17 | `BARBARIAN_BERSERKER` | Barbarians | NOT STARTED | — |
| 18 | `SKELETON_WARRIOR` | Undead | NOT STARTED | — |
| 19 | `SKELETON_ARCHER` | Undead | NOT STARTED | — |
| 20 | `GLADIATOR_THRACIAN` | Gladiators | NOT STARTED | — |
| 21 | `GLADIATOR_SAMNITE` | Gladiators | NOT STARTED | — |
| 22 | `GLADIATOR_CHAMPION` | Gladiators | NOT STARTED | — |
| 23 | `GIGANTES_WARRIOR` | Gigantes | NOT STARTED | GIGANTES_CAPTAIN |
| 24 | `GIGANTES_BOSS` | Gigantes | NOT STARTED | — |
| 25 | `CIVILIAN_MAN` | Civilians | NOT STARTED | CIVILIAN_MAN_ATHENIAN |
| 26 | `CIVILIAN_WOMAN` | Civilians | NOT STARTED | CIVILIAN_WOMAN_ATHENIAN |
| 27 | `CASTOR` | Named heroes/NPCs | NOT STARTED | — |
| 28 | `POLLUX` | Named heroes/NPCs | NOT STARTED | POLLUX_ZOMBIE |
| 29 | `LEONIDAS` | Named heroes/NPCs | NOT STARTED | — |
| 30 | `CRASSUS` | Named heroes/NPCs | NOT STARTED | — |
| 31 | `SEJANUS` | Bosses | NOT STARTED | UNDEAD_SEJANUS |
| 32 | `GAIUS_TIBERIUS` | Named heroes/NPCs | NOT STARTED | — |
| 33 | `ARCHIMEDES` | Named heroes/NPCs | NOT STARTED | — |
| 34 | `ELEKTRA` | Named heroes/NPCs | NOT STARTED | — |
| 35 | `HYDRA_DAUGHTER_TYPE1` | Creatures/monsters | NOT STARTED | HYDRA_DAUGHTER_TYPE2, HYDRA_DAUGHTER_TYPE3, HYDRA_DAUGHTER_TYPE4 |
| 36 | `HYDRA_MOTHER` | Creatures/monsters | NOT STARTED | — |
| 37 | `MINATAUR` | Creatures/monsters | NOT STARTED | — |
| 38 | `MEDUSA` | Bosses | NOT STARTED | — |
| 39 | `ARES` | Bosses | NOT STARTED | — |
| 40 | `BEOWULF` | Bosses | NOT STARTED | — |
| 41 | `LADON` | Creatures/monsters | NOT STARTED | — |
| 42 | `TALOS_PHASE1` | Bosses | NOT STARTED | TALOS_PHASE2 |

## Unused or unresolved definitions

The following global types lack a safely established distinct appearance in the audited campaign/arena packages. They must not consume a paid master slot until additional evidence or human review resolves them:

- `10 CYCLOPS` — not present in any audited CHAR_TYPES table.
- `19 SPARTAN_COMMANDER` — not present in any audited CHAR_TYPES table.
- `22 SPARTAN_ZOMBIE_WARRIOR` — not present in any audited CHAR_TYPES table.
- `23 FAST_ROMAN_ZOMBIE_WARRIOR` — not present in any audited CHAR_TYPES table.
- `24 FAST_SPARTAN_ZOMBIE_WARRIOR` — not present in any audited CHAR_TYPES table.
- `29 ROMAN_GRUNT_HEAVY_SNOW` — not present in any audited CHAR_TYPES table.
- `30 ROMAN_CENT_SNOW` — not present in any audited CHAR_TYPES table.
- `32 CIVILIAN_CHILD` — not present in any audited CHAR_TYPES table.
- `37 BARBARIAN_GHOUL` — not present in any audited CHAR_TYPES table.
- `38 AMAZON_HUNTRESS` — packaged but unresolved.
- `39 AMAZON_WARRIOR` — packaged but unresolved.
- `54 HIPPOLYTA` — not present in any audited CHAR_TYPES table.
- `58 TYPHON` — not present in any audited CHAR_TYPES table.
- `59 HARPY` — not present in any audited CHAR_TYPES table.
- `60 SPARTAN_SERGEANT` — not present in any audited CHAR_TYPES table.
- `61 ROMAN_GRUNT_ELITE` — not present in any audited CHAR_TYPES table.
- `62 ROMAN_GRUNT_HEAVY_ELITE` — not present in any audited CHAR_TYPES table.
- `64 ROMAN_CENT_ELITE` — not present in any audited CHAR_TYPES table.
- `65 ROMAN_CENT_ZOMBIE` — not present in any audited CHAR_TYPES table.
- `66 PRAE_CENT` — not present in any audited CHAR_TYPES table.

## Private visual-review material

A private atlas-evidence contact sheet and CSVs are generated under `temp/character-roster-audit`. It covers every appearance's canonical texture evidence. A uniform full-model contact sheet is not claimed: current tooling does not generically reconstruct PSW/multiweighted Hydra, Ladon, or player geometry with reliable material assembly, so filling those gaps with guessed renders would be misleading.

## Confidence and remaining work

- **CONFIRMED:** global type count and names, package type presence, disc model/texture/skeleton paths, hashes, exact duplicates, texture decoding, and BNS topology grouping.
- **HIGH:** straightforward name/prefix/archive mappings such as Roman, Spartan, Barbarian, Gladiator, civilian, and named families.
- **LIKELY:** global `GAIUS` type 49 maps to the coincident `TIBERIUS` directory; the executable pointer remains untraced.
- **UNKNOWN:** 21 unresolved definitions, especially packaged Amazon types 38/39 without a matching model directory and unobserved boss/special definitions.
- Equipment descriptions are conservative inventory labels, not a substitute for later canonical per-character recovery.

Machine-readable paths, hashes, LOD metadata, texture metadata, skeleton groups, appearances, type rows, and queue status are in `research/characters/character_roster_manifest.json`.
