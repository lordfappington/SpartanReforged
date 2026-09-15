# Canonical common Spartan allied infantryman

Status: **preservation recovery complete for identity, static LOD geometry, rigid skeleton mapping, texture, equipment ownership, and bounded animation-family evidence**. Animation key-track compression and the executable-side character-model pointer remain outside this milestone.

All meshes, decoded textures, and renders named here are private local research outputs derived from copyrighted game data. They are deliberately excluded from Git.

## Identity decision

The canonical ordinary/common Spartan allied infantry target is `SPARTAN_SWORDSMAN`, global character type ID `11`, represented by `DATA/CHR_MDLS/SPT_SWRD/SSWRD*`. The gameplay identity is **CONFIRMED**. The asset-family link is **HIGH CONFIDENCE**, not absolute, because the final executable pointer field has not been decoded.

Two genuine generic Spartan grunt types exist, so the choice was not made from the word “Spartan” alone:

| Candidate | Type | Asset/animation family | Evidence and disposition |
|---|---:|---|---|
| `SPARTAN_SWORDSMAN` | 11 | `SPT_SWRD/SSWRD`; `GREEK/SWORD` | **Selected common infantry:** `COMMANDER_LEVEL GRUNT`; type/model co-occur in 17 campaign/arena packages; LEVEL04 contains 114 explicit group/patrol/reposition strings |
| `SPARTAN_HOPLITE` | 8 | `SPT_HOPL/SHOPL`; `GREEK/HOPLITE` | Distinct spear/hoplite grunt, packaged in 10 sections; not flattened into the common sword-and-shield target |
| `THE_SPARTAN` | 0 | `SPARTAN` body plus modular equipment | Player character, not the target |
| `SPARTAN_COMMANDER` | 19 | Commander role | 500 health; not ordinary infantry despite its `GRUNT` battle-tier field |
| `SPARTAN_SERGEANT` | 60 | Officer role | `COMMANDER_LEVEL CENTURION`, 500 health; not ordinary infantry |
| `ATHENIAN_ARCHER` | 12 | Archer family | Ranged specialist |
| `SPARTAN_ELITE`, `SPARTAN_SAPPER` | distinct gameplay roles | Elite/specialist | Explicitly not the common target |

`NAMES.TXT` resolves index 11 to `CHARACTER_TYPE_SPARTAN_SWORDSMAN`. `BATTLE.TXT` gives it mass 130, health 100, armour 30, block skill 70, default weapon damage 30, `CAN_BASH`, and `COMMANDER_LEVEL GRUNT`. LEVEL04 `CHAR_TYPES.BIN` contains 11, the archive carries `SPT_SWRD`, and its entity data names large numbered groups of `SPARTAN_SWORDSMAN` units. The same type/model family occurs in all six arena archives and LEVEL00, 01, 02, 03, 04, 05, 07, 09, 10, 12, and 13.

## Canonical source and geometry

Canonical archive: `DATA/LEVEL04.PAK`, SHA-256 `79b1bd562b831fe358e7d4a742905e71887075ff014bcf53413d85848e3caa39`. LEVEL04 was selected because it contains the type table, the complete model/texture/skeleton family, the generic Greek sword animations, and the densest explicit allied spawn evidence. The SSWRD files are byte-identical to their LEVEL00 copies.

The existing bounded decoder validates a 12-byte PSQ header followed by 48-byte rigid-skinned records containing position/ADC, normal, one UV, and one bone-matrix offset. Alternating triangle-strip winding gives:

| LOD | Source / SHA-256 | Bytes | Stream records | Unique XYZ | Triangles | Primary / shield |
|---:|---|---:|---:|---:|---:|---:|
| 0 | `SSWRD0.PSQ` / `1fcad107ea7ac29e20bda278b351e6081adbb102350d47d5bd5fc21bf0d516a8` | 32,844 | 684 | 251 | 478 | 430 / 48 |
| 1 | `SSWRD1.PSQ` / `fbf3f9be424b40f2c6d1c3c8e8a19f746d5f02d633e90779b78bc50e7949ac31` | 25,164 | 524 | 198 | 372 | 324 / 48 |
| 2 | `SSWRD2.PSQ` / `82456888794edea78d40c3d98bb5f88687fec736695768919cff032a02f7c8c3` | 18,300 | 381 | 137 | 250 | 218 / 32 |
| 3 | `SSWRD3.PSQ` / `d519218bc712140a643daa33cbc572254032b88e974a2a57a851fbb12d119c0b` | 10,908 | 227 | 99 | 152 | 136 / 16 |
| 4 | `SSWRD4.PSQ` / `e889ae9690942386c365edb59c7d102c6c86b627c1b5a8e4fdc82e487197e09e` | 7,020 | 146 | 68 | 94 | 78 / 16 |

LOD0 splits the primary record range `[0,603)` from the shield range `[603,684)`. Its complete rest-pose bounds are min `(-1.257584, -0.982900, -0.465855)` and max `(0.915999, 0.898171, 0.840777)`. The native stream uses one rigid bone per record, one UV set, one implicit material slot, and one texture atlas.

The head/face, hair or dark neck fringe, helmet, torso armour, bare arms, waist, pteruges, skirt, legs, greaves/footwear, sword, and shield are all integrated in SSWRD PSQ. No separate equipment model occurs in `SPT_SWRD`. The shield is an explicit secondary range rigid on bone 12; the sword remains in the primary range on bone 9.

## Skeleton and attachment sides

`DATA/CHR_MDLS/SPT_SWRD/SSWRD2.BNS` is 305 bytes, SHA-256 `0a0fbdbea2eac53a5b6d9c162fab59e316c7c2864793e6d5d8529ca1df8db5a5`. It contains `bns2`, 16 bones, local translations, and parents:

```text
[-1, 0, 1, 2, 0, 4, 5, 5, 7, 8, 5, 10, 11, 0, 13, 14]
```

It is byte-identical to the Hoplite BNS. The player Spartan and recovered `ROMAN_GRUNT` use the same 16-bone parent topology and numerically near-identical translations, but their BNS files are not byte-identical. Bone names and bind rotations are not stored in this compact file.

The anatomical side result is **CONFIRMED BY RIGID GEOMETRY**. The reconstructed character faces positive Z; positive X therefore lies on the character's anatomical left when viewed from the front. Terminal bone 9 is at positive X and contains the sword. The complete secondary shield range is on terminal bone 12 at negative X.

```text
CHARACTER LEFT HAND: sword
CHARACTER LEFT ARM: sword arm; no shield
CHARACTER RIGHT HAND: shield grip
CHARACTER RIGHT ARM: shield
```

This source asymmetry must never be mirrored in future multiview inputs.

## Animation evidence

The NPC animation family adjacent to SSWRD in LEVEL04 is `DATA/ANIMS/GREEK/SWORD`, not the player's `DATA/ANIMS/GREEK/SPARTAN/SWORD1`. LEVEL04 contains 19 bounded `GREEK/SWORD` clips: stand/run, five idles, two conversations, combat-ready states, taunt, injured crawl, door bash, and four sword attacks. Shared locomotion, defence, shield reaction, targeting, and death clips occur under `DATA/ANIMS/COMMON`.

Nineteen Greek-sword clips and eleven representative common clips were checked. Every file has `anm1` magic, declares 16 bones and three channel groups, and has a positive frame count. Representative results include 31-frame stand, 13-frame run, 38-frame short stab, 36-frame combat ready, 21-frame common walk, 20-frame common defence ready, 11-frame shield impact, and 35/41-frame front/back deaths.

This establishes a generic Greek sword layer plus common-humanoid sharing. It does not decode compressed key tracks or prove the complete executable-side clip-selection graph.

## Texture and material identity

`DATA/CHR_MDLS/SPT_SWRD/SSWRD.TM2` is 66,112 bytes, SHA-256 `0a0b1c2952632d4e3dc44cba8e36c1645cfa069558c876aadcc70dcd444328eb`.

- 256 x 256, one mip
- `PSMT8 / IDTEX8` indexed pixels
- 256-entry `RGB5A1` CLUT with the PS2 CSM1 permutation
- decoded alpha 255..255, fully opaque
- one material/texture binding and one atlas
- dominant black/charcoal, bronze/brown, skin tan, pale cream/silver, and muted blue families

The atlas paints all body and equipment. Its most distinctive regions are the muted blue shield with a large pale lambda-like chevron, bronze-and-dark patterned shield rim, pale/silver torso and pteruges, geometric bronze waist band, bronze helmet/greaves, skin, and dark blue-grey skirt. No normal, roughness, or metalness maps exist.

## Original visual identity

### Body and silhouette

The source depicts a compact, broad-shouldered, muscular infantryman rather than a tall museum-style hoplite. Bare upper arms and thighs keep the body readable, while the very broad shield dominates one side. The neutral PSQ pose is a rigid T-pose used for evidence, not an authored gameplay stance.

### Head

The head is almost fully enclosed by a plain bronze, crestless helmet. It has a low faceted crown, strong brow/eye slit, full cheek plates, a long central nasal guard, and a modest flared rear/neck edge. No plume or officer ornament is present. Dark hair or a dark fringe is visible beneath the rear/sides; the face is largely hidden rather than presented as a distinct bearded portrait.

### Torso, shoulders, and waist

The upper torso uses pale silver/cream armour with dark edging and a dark radiating/fringed collar treatment. A rounded pale chest band sits above a wide bronze-brown geometric waist panel. Pale vertical pteruges hang over a dark blue-grey short skirt/tunic. These are integrated painted low-poly forms, not separate modern layers.

### Legs and footwear

Upper thighs are bare. Both lower legs carry tall bronze greaves with bright central highlights and pointed upper/lower contours. Dark sandal/boot geometry encloses the feet; there are no separate footwear files.

### Shield

The right-arm shield is unusually broad and shallow-curved, not a circular hoplon or tall scutum. In a shield-front projection it spans about `0.947200 x 0.430161` source units, width:height `2.202:1`; depth in the held rest orientation is about `0.858455`. It has a muted blue face, large pale lambda-like chevron, bronze/dark patterned rim, and plain dark interior/rear. LOD0 assigns it 48 triangles.

### Sword

The left hand carries a one-handed straight, leaf-shaped sword with a pointed blade, small guard, wrapped grip, and compact faceted pommel. The terminal attachment envelope is about `0.114252 x 0.101897 x 1.005533` source units; this includes hand/attachment geometry and is not asserted as pure blade length. No spear or secondary weapon is integrated.

### Colour and asymmetry

Bronze/gold helmet and greaves, pale silver/cream torso and pteruges, warm skin, a dark blue-grey skirt, and a blue/pale/bronze shield create the faction identity. The decisive asymmetry is sword on anatomical left and shield on anatomical right.

## Relationship to the player Spartan

The generic soldier is **not** the player mesh. SSWRD is a compact integrated NPC family. The player uses a 95,196-byte body PSQ plus `FACE.MPH`, multiweighted data, two body textures, and separate modular sword, shield, bow, and other weapon families. None of those geometry hashes matches SSWRD.

The rigs are compatible in broad layout: both have the same 16-bone parent topology and near-identical rest translations. They are not byte-identical (`SSWRD2.BNS` starts `0a0f...`; player `BONES.BNS` starts `84c6...`). Animation packaging also remains distinct: generic `GREEK/SWORD` plus `COMMON` versus player `GREEK/SPARTAN/SWORD1` and other player weapon namespaces. The soldier is therefore separate NPC geometry using the common humanoid rig plan, not a simplified copy of the player character.

## Private canonical reconstruction

The source-derived output is private and ignored:

```text
temp/character-research/SPARTAN_SWORDSMAN/reconstruction/spartan_swordsman_lod0.obj
temp/character-research/SPARTAN_SWORDSMAN/reconstruction/spartan_swordsman_lod0.mtl
temp/character-research/SPARTAN_SWORDSMAN/decoded/sswrd.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-turnaround.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-front.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-front-three-quarter.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-character-left-profile.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-character-right-profile.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-rear-three-quarter.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-rear.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-head-helmet.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-torso.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-waist.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-shield-front.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-shield-rear.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-weapon.png
temp/character-research/SPARTAN_SWORDSMAN/turnaround/spartan-swordsman-closeup-footwear.png
```

The profiles are named for the character's anatomy: the left profile camera is at positive X, and the right profile camera is at negative X. The reconstruction uses source topology, rest translations, UVs, atlas, neutral lighting, and no geometry/material redesign.

## Art-direction lock for a future Reforged interpretation

Must preserve:

- ordinary non-officer, compact muscular Spartan infantry silhouette
- plain crestless full-face bronze helmet with eye slit, cheek plates, nasal guard, and modest rear flare
- pale/silver chest and shoulder treatment, dark radiating collar/fringe, geometric bronze waist band
- pale vertical pteruges over a dark blue-grey skirt, bare arms/thighs, tall bronze greaves and dark footwear
- extremely broad shallow-curved blue shield, pale lambda-like chevron, patterned bronze/dark rim, and dark rear
- leaf-shaped one-handed sword
- **sword in anatomical left hand; shield on anatomical right arm**

Human judgement is still required for the exact interpretation of the helmet's faceted low-poly crown, the dark collar/hair boundary, the heraldic name of the pale shield marking, and how much PS2 texture-painted structure should become modern geometry.

Do not “correct” the soldier into a generic historical hoplite, swap him with the distinct `SPARTAN_HOPLITE`, add a crest, change the shield into a round hoplon, or mirror the source equipment.

## Future multiview specification

```text
FRONT:
Camera faces the character's front (+Z-facing source identity).

CHARACTER LEFT PROFILE:
Camera is on the character's anatomical LEFT (+X).
The left hand visibly owns the sword; the right-arm shield remains on the far side.

CHARACTER RIGHT PROFILE:
Camera is on the character's anatomical RIGHT (-X).
The right arm visibly owns the shield; the left-hand sword remains on the far side.

REAR:
Camera faces the character's back.
Sword remains left; shield remains right. No mirroring is permitted.
```

Machine-readable metadata is in `research/characters/spartan_swordsman_manifest.json`.

## Remaining uncertainty

- exact executable/entity pointer from type 11 to `SPT_SWRD`
- source bone names, rotations, and attachment labels absent from BNS
- compressed ANM key-track schema and full runtime selection graph
- exact character GS/material constants
- exact intended heraldic name for the pale shield mark
