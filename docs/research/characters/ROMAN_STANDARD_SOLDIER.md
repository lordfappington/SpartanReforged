# Canonical standard Roman soldier

Status: **preservation recovery complete for identity, static LOD geometry, rigid skeleton mapping, texture, equipment, and animation-family evidence**. Animation track compression and the executable-side character-model pointer remain outside this bounded milestone.

All reconstructed meshes, decoded textures, and renders named below are private local research outputs derived from copyrighted game data. They are deliberately excluded from Git.

## Identification

The canonical ordinary Roman infantryman is `ROMAN_GRUNT` (character type ID `3`), represented by the `DATA/CHR_MDLS/RMN_GRNT/RGRT*` asset family. Confidence in the gameplay identity is **CONFIRMED**; confidence in the name-based and archive-coincident link from `ROMAN_GRUNT` to `RMN_GRNT` is **HIGH** because the final executable-side pointer field has not yet been decoded.

This is not merely the first Roman-looking model found:

| Candidate | Asset family | Disposition |
|---|---|---|
| `ROMAN_GRUNT` | `RMN_GRNT` / `RGRT` | **Selected:** commander level `GRUNT`, ordinary stats, common campaign/arena presence, canonical shield-and-sword infantry reconstruction |
| `ROMAN_GRUNT_HEAVY` | `RMN_HGNT` / `HRGRT` | Heavy variant: 200 health, 60 armour, 65 shield strength, scale 1.08 |
| `ROMAN_CENT` | `RMN_CENT` / `RCENT` | Centurion/officer family |
| `ROMAN_ARCHER` | `RMN_ARCH` / `RARCH` | Ranged specialist |
| `PRAE_*` | `PRA_*` | Separate Praetorian elite families |

`BATTLE.TXT` describes `ROMAN_GRUNT` as the weak/basic Roman, gives it `COMMANDER_LEVEL: GRUNT`, and configures a breakable shield. Its active block has mass 130, health 100, block skill 15, shield strength 10, default weapon damage 10, and a 50/50 choice between `ATTACK1` and `ATTACK2`. The older roster comment says “never blocks”; the active numeric block-skill and shield fields are stronger runtime evidence and expose an internal documentation inconsistency.

Type ID 3 is present in `CHAR_TYPES.BIN` for archives that carry `RMN_GRNT`. Standard copies occur in `LEVEL01`, `02`, `03`, `06`, `07`, `09`, `10`, `13`, `14`, `ARENAR`, and `ARENAX`. `LEVEL01` entity strings also contain dense Roman-wave spawner naming and Roman kill objectives, supporting its use as mass infantry, although the binary ENT record schema is not yet decoded.

## Evidence chain

```text
DATA/BATTLE.TXT: CHARACTER ROMAN_GRUNT (type 3)
  -> DATA/ENV/LEVEL01/ENTITIES/CHAR_TYPES.BIN includes type 3
  -> DATA/CHR_MDLS/RMN_GRNT
     -> RGRT0..4.PSQ (five static/skinned LOD streams)
     -> RGRT2.BNS (16-bone hierarchy/rest translations)
     -> RGRT.TM2 (one shared colour atlas)
  -> DATA/ANIMS/ROMAN/GRUNT (unit-specific idles/reactions)
  -> DATA/ANIMS/ROMAN (Roman-family sword attacks)
  -> DATA/ANIMS/COMMON (locomotion, shield reactions, deaths)
```

No separate character `.MTL` or equipment model occurs in `RMN_GRNT`. The PSQ stream and adjacent TIM2 atlas form the static render package; exact runtime character GS constants remain untraced.

## Body and LODs

Canonical source archive: `DATA/LEVEL01.PAK`, SHA-256 `c9c1e2ee59755cd9cde37e5491313cb8251a06e3e141e9e8d4d0de3129fe0f1b`.

The bounded PSQ decoder validates a 12-byte header followed by 48-byte records containing position plus ADC control, normal, one UV set, and a byte-offset selecting one of 16 bone matrices. A record with position-W `2048.0` sets strip ADC/no-kick; records with W `0.0` complete triangles. Alternating strip winding reconstructs the following exact topology:

| LOD | Source / SHA-256 | Bytes | Stream records | Unique XYZ | Triangles | Primary / shield |
|---:|---|---:|---:|---:|---:|---:|
| 0 | `RGRT0.PSQ` / `c71d4f40d4cb915c5b8d1cd1b2db0943c2381ccde11beea91cd94d310a7c6bff` | 31,932 | 665 | 247 | 472 | 436 / 36 |
| 1 | `RGRT1.PSQ` / `44b2f3e38f9e9434916aaf84b8197b948d5370b364709634897d2c4d2df87e71` | 25,116 | 523 | 203 | 384 | 348 / 36 |
| 2 | `RGRT2.PSQ` / `eadc204b7f4160765ac3cbcb673f64f098c8e8ca39a8d4f1ebec374483f946d7` | 18,588 | 387 | 145 | 268 | 248 / 20 |
| 3 | `RGRT3.PSQ` / `e7324c49283a068c16c3ad7fe0c760aba633ae3cbec3ca45fde468f77acda61b` | 9,084 | 189 | 86 | 130 | 122 / 8 |
| 4 | `RGRT4.PSQ` / `1ab70c01c08f161c7c7f49f46ddc9e76358f29dbc3f6dc1dbc4f3e870a8d7785f` | 5,964 | 124 | 58 | 82 | 78 / 4 |

“Stream records” is the native render count; repeated strip vertices mean it is not a unique modeled-vertex count. LOD0 has one implicit texture/material slot and one UV set. Its header splits the primary range `[0,621)` from a 44-record shield range `[621,665)`.

After applying cumulative BNS rest translations, LOD0 bounds are `min (-1.352093, -0.982899, -0.272095)` and `max (0.916010, 0.876960, 0.637230)`. X is lateral, Y is up, and positive Z faces the reconstructed front camera. The broad X bound includes held equipment, not body width. Each record has one bone ID: this family is rigid-segment skinned, not multiweighted.

The head, face, helmet, hair/neck covering, torso armour, limbs, skirt panels, footwear, shield, and sword all occur in the PSQ stream. There are no modular files or alternate heads in the standard directory.

## Skeleton

`DATA/CHR_MDLS/RMN_GRNT/RGRT2.BNS` is 305 bytes with SHA-256 `c2061123f8cb42663aef5a9fe900fe3941aa7c3c0958bad0d5246769d36b9f83`. It has magic `bns2`, 16 bones, local translations, and parent IDs:

```text
[-1, 0, 1, 2, 0, 4, 5, 5, 7, 8, 5, 10, 11, 0, 13, 14]
```

The hierarchy resolves as root; two three-bone legs; a three-node torso/head chain; and two three-bone arms. Bone names are not stored. Geometry proves the terminal +X arm bone (ID 9) carries the sword and the terminal -X arm bone (ID 12) carries the shield. Helmet/head geometry follows the head-chain terminal (ID 6). These functional labels are inferred, not source names.

The BNS is byte-identical across `RMN_GRNT`, `RMN_HGNT`, `RMN_CENT`, and `RMN_ARCH`, and also matches LEVEL00 `ATH_ARCH`. It does **not** byte-match LEVEL00 Spartan body, Hoplite, or Swordsman skeletons. Roman-family animation sharing is therefore directly compatible at the 16-bone layout level; a future Spartan-to-Roman retarget must not assume skeleton identity.

## Material and texture

The family has one 66,112-byte `DATA/CHR_MDLS/RMN_GRNT/RGRT.TM2`, SHA-256 `248ba25048e1c45c09f4652fa48841d8d3fe1b6f015641aef5fce87be375ff06`.

- 256 x 256, one mip
- `PSMT8 / IDTEX8` indices
- 256-entry `RGB5A1` CLUT with the PS2 CSM1 index permutation
- decoded alpha range 255..255 (fully opaque)
- one colour atlas covering face/skin, helmet and armour, red-brown cloth/leather, footwear, weapon, and both shield faces/emblem

The atlas is a traditional colour texture; no normal/roughness/metalness maps exist and none were invented for reconstruction. The private decoded PNG is `temp/roman-research/decoded/rgrt.png`.

## Equipment identity

- **Helmet:** integrated plain dark metal helmet with a close crown, brow edge, cheek/side flares, and small rivet highlights; no crest or officer plume.
- **Armour:** integrated dark segmented/lamellar-looking torso with shoulder plates, pale trim highlights, repeated fasteners, and studded vertical skirt strips over red-brown cloth. Bare lower legs end in dark boots/sandals.
- **Shield:** integrated secondary PSQ range, rigid on bone 12. LOD0 uses 44 records / 36 triangles. In its held rest orientation the range spans about `0.913 x 0.445 x 0.584` source units. It is a broad, shallow-curved, horizontally oriented red shield with dark borders and a large black eagle/wing motif around a central boss. This compact, distinctive proportion and emblem—not a generic tall historical scutum—are mandatory identity traits.
- **Weapon:** integrated in the primary range, rigid on bone 9. The terminal-bone geometry spans about 0.806 units along its long axis and reconstructs as a short straight gladius-like sword with pointed blade. No secondary weapon or separate scabbard model was found.

The shield interior/rear is geometrically present and textured more plainly than the emblematic front. No standalone shield or sword PSQ exists, so later replacement work must either preserve equivalent submesh/bone attachment semantics or deliberately introduce a documented modular system.

## Animation family

A bounded extraction checked 28 relevant clips. Every checked file has `anm1` magic and declares 16 bones, matching the BNS count.

- `DATA/ANIMS/ROMAN/GRUNT`: distinctive idle/look/yawn/fidget/tinker/converse, celebrate, examine-ground, and terror clips.
- `DATA/ANIMS/ROMAN`: sword attacks including short stab, centre stab, overhead chop, sweep/backslash, running chop, and run/jump attacks.
- `DATA/ANIMS/COMMON`: `IDLE1`, `WALK`, `RUN`, shield impact/push, front/back deaths, and broader common reaction/death libraries.

Representative headers give 47 frames for common idle, 21 walk, 13 run, 38 short stab, 11 shield impact, 24 defensive shield push, 35 front death, and 41 back death. This establishes unit-specific, Roman-family, and generic-humanoid sharing layers. It does not decode compressed key tracks or prove the complete runtime clip-selection graph.

## Variants

`RMN_GRNT/WEAK` uses byte-identical PSQ LODs and BNS but swaps `RGRT.TM2` to SHA-256 `4279da232f58c157fca04d6a575c073b4a39a1743281d0687a32c47f1809a6c3`. `RMN_GRNT/ZOMBIE` retains the RGRT file family and uses texture hash `2ed57649b3a48c530c94e3a128b6f9e5207b0715207192c317023db26d07b882`; bounded evidence indicates geometry reuse, but a canonical extracted zombie copy should be hash-checked before upgrading that statement to confirmed. No standard-folder alternate face, helmet, shield, or weapon geometry was found.

The game also has heavy, centurion, archer, elite, snow, Praetorian, and undead Roman families. They are role/geometry families, not random skins of the canonical grunt, and must stay distinct in future planning.

## Private preservation reconstruction

`tools/analysis/psq_character.py` reconstructs the LOD0 strip topology, applies the 16-bone rest translations, exports UVs/normals, and writes a Blender-compatible OBJ/MTL. The private output is:

```text
temp/roman-research/reconstruction/roman_standard_soldier_lod0.obj
temp/roman-research/reconstruction/roman_standard_soldier_lod0.mtl
```

The render uses the original decoded atlas, neutral lighting, no smoothing, no geometry changes, and no PBR reinterpretation. Private inspection outputs:

```text
temp/roman-research/turnaround/roman-standard-turnaround.png
temp/roman-research/turnaround/roman-standard-front.png
temp/roman-research/turnaround/roman-standard-front-three-quarter.png
temp/roman-research/turnaround/roman-standard-side.png
temp/roman-research/turnaround/roman-standard-rear-three-quarter.png
temp/roman-research/turnaround/roman-standard-rear.png
temp/roman-research/turnaround/roman-standard-closeup-head-helmet.png
temp/roman-research/turnaround/roman-standard-closeup-torso-armour.png
temp/roman-research/turnaround/roman-standard-closeup-shield-front.png
temp/roman-research/turnaround/roman-standard-closeup-shield-rear.png
temp/roman-research/turnaround/roman-standard-closeup-weapon.png
```

These files remain ignored/private and are not suitable for the public repository.

## Reforged concept and human-base workflow

The human-approved Reforged target is tracked at
`assets/Concept/Characters/Roman-Grunt/roman-grunt-reforged-concept-v1-approved.png`
(SHA-256 `cf708a857497ab432507b74c8ac074874ff90eb569bb60159a62cd517667dddf`).
It controls modern visual interpretation; the recovered PS2 evidence in this
document remains canonical for structural/gameplay identity.

Procedural V1/V2 character experiments were rejected as production anatomical
foundations. The replacement workflow, candidate licensing audit, selected CC0
continuous male mesh, anatomy-first gate and private Human Base Build 1 outputs
are documented in [HUMAN_BASE_MESH_WORKFLOW.md](HUMAN_BASE_MESH_WORKFLOW.md).

## Future Reforged guidance

### Must preserve

- ordinary, non-officer silhouette and plain uncrested helmet
- dark segmented torso armour, red-brown skirt/tunic identity, bare lower legs, dark footwear
- unusually broad red curved shield, black eagle/wing motif, central boss, and held orientation
- short straight sword identity and opposite-hand attachment relationship
- compact PS2 proportions where they contribute to immediate recognition

### Safe to enhance

- facial anatomy, ears, hands/fingers, cloth folds, armour and shield thickness
- believable plate/strap/rivet construction, helmet construction, shield edge and grip, sword hilt/blade detail
- higher-density deformation geometry while preserving the established silhouette and equipment placement

### Modern material opportunities

- separately authored iron/bronze, leather, cloth, skin, wood, painted shield, and dirt/wear responses
- modern roughness/normal detail derived from faithful authored source interpretation, never misrepresented as original data

### Possible variation

Texture/palette variants are source-supported. Geometry variants should remain explicit heavy/centurion/archer/Praetorian families rather than being flattened into arbitrary grunt randomization. Extra faces, helmet wear, or shield paint variation are candidates only if art direction keeps the canonical standard version available unchanged in identity.

## Crowd/performance implications

The original already supplies five aggressive LODs (472, 384, 268, 130, 82 triangles), one 256² atlas, one material, 16 shared bones, rigid one-bone influences, and Roman/common animation sharing. Those choices explain how the game fields mass armies.

A future pipeline should retain four conceptual tiers—hero/close NPC, standard battle NPC, distant battle NPC, and mass-army LOD—without fixing triangle budgets until the renderer/platform target is measured. Preserve one/few materials, texture arrays or atlases, shared skeleton/animation evaluation, instancing/batching, animation LOD, and distant crowd simplification. Close variants may add material definition and deformation quality, but mass tiers should exploit shared animation and equipment-compatible skeletons rather than unique draw/animation state per soldier.

## Remaining uncertainties

- exact executable/entity field linking type 3 to `RMN_GRNT`
- source bone names, bind rotations, and attachment names (not present in this BNS)
- compressed ANM track schema and complete runtime selection tables
- exact character material/GS constants in the executable
- canonical hash confirmation for zombie geometry

Machine-readable evidence is in `research/characters/roman_standard_soldier_manifest.json`.
