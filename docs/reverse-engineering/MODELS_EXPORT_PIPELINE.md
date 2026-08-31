# MODELS Geometry Export Pipeline

The first LEVEL00 world-geometry reconstruction was completed on 2026-08-30 using only the existing isolated LEVEL00 extraction. This pipeline reconstructs confirmed source geometry outside the PS2 runtime; it does not reproduce native game rendering.

## Source and derived-data boundary

**SOURCE DATA** are the ignored, read-only `MODELS.BIN`, `MODELS.AAB`, `MODELS.MTL`, and referenced TIM2 files beneath the LEVEL00 extraction. The exporter verifies the three MODELS hashes against canonical constants and can verify all 58 TIM2 hashes against the local LEVEL00 inventory.

**GENERATED/DERIVED DATA** are glTF JSON, external glTF binary buffers, validation reports, and manifests. They are written only beneath `temp`, remain ignored, and must not be committed. No source resource is modified.

## Tools and architecture

- `tools/conversion/spartan_models.py` is target-neutral. It parses MODELS.BIN/MTL/AAB, validates boundaries and cross-references, reconstructs ADC topology, decodes Q4.12 UVs, exposes selection, and implements explicit coordinate transforms.
- `tools/conversion/export_models_gltf.py` builds glTF 2.0 buffers/accessors, creates traceable descriptor meshes/materials, optionally attaches explicit native decoded PNGs with an unlit selectable sampler, validates serialized glTF, and performs an exact source-to-accessor consistency check.
- With `--decode-bound-textures`, the exporter decodes each unique strongly resolved selected TIM2 once beneath the ignored export, reuses deterministic cached PNG bytes, classifies source alpha, and emits explicit neutral `UNRESOLVED_*` placeholders rather than substituting resources.
- `tools/conversion/tim2_decode.py` strictly decodes the geometry-required PSMT4/PSMT8 and RGB5A1/RGBA8888 TIM2 combinations to deterministic native-resolution PNG.
- `tests/formats/test_spartan_models.py` and `test_tim2_decode.py` use synthetic, non-copyrighted inputs only.

The parser and exporter are separate so the confirmed source representation is not coupled to glTF policy.

## Parser validation

Parsing fails loudly on:

- file-size or canonical hash mismatch;
- descriptor-table, descriptor-payload, or AAB pointer ranges outside their files;
- non-aligned, non-contiguous, overlapping, or incomplete descriptor payload coverage;
- MTL indices outside the ordered record table;
- unexpected block wrappers or VIF commands;
- VIF payloads crossing descriptor boundaries;
- preamble/position/UV/V4-8 cardinality disagreement;
- position NaN/Inf or W values other than zero/`0x8000`;
- topology indices outside a batch;
- malformed AAB traversal, cycles, duplicate references, or out-of-range references.

The canonical parse independently produces 1,338 descriptors, 2,128 batches, 88,314 streamed positions, 46,336 emitted triangles, 55 MTL records, and 1,224 AAB-indexed descriptors.

## Topology and vertex preservation

Each descriptor becomes one glTF mesh/node with one TRIANGLES primitive. Batches inside it retain independent strip reconstruction, then use descriptor-local indices. No triangle crosses a batch, descriptor, or material boundary. Node, mesh, primitive, material, and per-batch `extras` retain descriptor IDs, MTL IDs, secondary IDs, AAB membership, and source vertex/index ranges.

All 88,314 streamed position/UV records are retained in accessors. Only 87,682 are referenced by emitted triangles; the remaining 632 are suppressed/history vertices that never participate in a retained triangle. This is intentional forensic preservation. Blender discards these unreferenced vertices on import while retaining all polygons.

## Coordinates

No scale is applied. Source positions remain available internally and are recorded in validation reports.

| CLI mode | Mapping | Determinant | Winding consequence |
|---|---|---:|---|
| `--coords source` | `(X,Y,Z) -> (X,Y,Z)` | +1 | no coordinate-induced reversal |
| `--coords gltf` | `(X,Y,Z) -> (X,Y,-Z)` | -1 | reflection reverses orientation unless `--winding reverse` is also selected |
| `--coords x_z_neg_y` | `(X,Y,Z) -> (X,Z,-Y)` | +1 | explicit proper-rotation validation mode |
| `--coords x_z_y` | `(X,Y,Z) -> (X,Z,Y)` | -1 | explicit reflected validation mode |

Descriptor-118 validation establishes that source Y already matches glTF +Y-up. `--coords source` is therefore the selected glTF convention; Blender performs its normal glTF Y-up to Blender Z-up import conversion. The exporter never automatically changes winding.

## Winding and UV options

- `--winding source` emits the confirmed relative strip winding.
- `--winding reverse` swaps the second and third index of every emitted triangle.
- `--v-mode source` exports `v = int16(raw_v) / 4096`.
- `--v-mode flip` exports `v = 1 - int16(raw_v) / 4096`.

Descriptor-5 banner validation confirms `--v-mode source` as the modern glTF/Blender convention and default. The flip option remains available for forensic comparison. U is always `int16(raw_u) / 4096`. Negative and greater-than-one coordinates are preserved. Neither V mode clamps or wraps coordinates. Every selected option and exact coordinate mapping is recorded in glTF asset extras, the report, and the manifest.

## Normals, materials, and textures

Normals are omitted by default and no normal-generation option is used. V4-8 remains retained raw in the parser. The exporter omits it by default; `--v4-color ps2-rgba` is an explicit diagnostic that emits legal glTF `COLOR_0 = min(byte / 128.0, 1.0)`. This likely represents PS2 vertex color/light modulation, but original VU routing is not confirmed and native values above 128 remain lossless only in the parser.

One placeholder glTF material is created for every selected, geometry-used MTL record. Names retain the source MTL index and name. No metallic, roughness, alpha, blend, or emissive interpretation is claimed. When an image is explicitly attached, an unlit validation material and user-selected wrap mode are emitted; these are target validation settings rather than decoded Spartan material properties.

Strongly resolved TIM2 references are recorded in material extras with source-relative paths and SHA-256 values. An explicit `--texture-image` PNG beside the output glTF may be attached by matching basename. Attached validation materials use `KHR_materials_unlit`, a neutral base color, and explicit `--sampler repeat|mirrored-repeat`; this avoids interpreting unknown MTL lighting/render properties. `REPEAT` remains the conservative default while MTL sampler fields are unknown. Source TIM2 files are never modified. The strict decoder performs no scale, filter, enhancement, or color correction.

For descriptor 118, `002.TM2` decoded to native 256×256 RGBA8 and matched Noesis pixel-for-pixel. Periodic sampling is required by its two-period UV span; exact native repeat-versus-mirror semantics remain unresolved.

Across all geometry materials, 32 of 39 used MTL records resolve strongly to 30 unique TIM2 files. The decoder covers all six image/CLUT/mip combinations in that set. Every native base-level RGBA buffer matches Noesis 4.474 byte-for-byte. PSMT4 is linear low-nibble-first; PSMT8 is linear byte-indexed with the standard CSM1 palette permutation; no image unswizzle is required. Type-3 CLUT alpha uses saturated PS2 doubling.

The complete textured assembly has now been performed locally. Thirty-two materials attach to 30 reused images; seven remain explicit placeholders. All source alpha is retained, but glTF materials deliberately remain `OPAQUE` because blend/mask modes and cutout thresholds are unknown. The serialized glTF and external links validate, exact reconstruction round-trip passes, and Blender imports all 46,336 polygons with no missing or cross-bound images.

## Selection

The CLI supports:

```text
--all
--static-only
--special-only
--descriptor ID       (repeatable)
--material ID         (repeatable)
```

Static selection comes from the parsed AAB descriptor-reference set, not a transform. Positions already fit AAB cells and are exported unchanged.

## Validation exports

All initial exports used `--coords source --winding source --v-mode source`, omitted normals, and did not convert textures.

### Small gate

Descriptor 118 was selected because it is a small AAB-indexed static descriptor with a confirmed MTL/TIM2 relationship:

| Property | Value |
|---|---|
| Descriptor | 118 |
| Material | MTL 5, `002` |
| TIM2 reference | `DATA/ENV/LEVEL00/WORLD/002.TM2` |
| Batches | 1 |
| Streamed vertices | 12 |
| Triangles | 8 |
| UV range | U `-2.5..-0.5`; V `-0.500244140625..1.499755859375` |
| Source/output bounds | min `(-152.000015, 20.325733, -136.000015)`, max `(-136.000015, 32.828007, -120.000031)` |

The serialized glTF has one mesh/node/material, 12 POSITION and 12 TEXCOORD_0 values, and 24 indices. Structural and exact round-trip checks pass.

### Full LEVEL00

| Property | Value |
|---|---:|
| Descriptor meshes/nodes | 1,338 |
| VIF batches represented | 2,128 |
| Streamed POSITION/TEXCOORD records | 88,314 |
| Referenced vertices | 87,682 |
| Emitted triangles | 46,336 |
| Indices | 139,008 |
| Geometry-used materials | 39 |
| Buffer views/accessors | 4,014 / 4,014 |
| Binary buffer bytes | 2,044,830 |

Source and output bounds are identical in source coordinate mode: min `(-176.0, -12.383148, -176.0)`, max `(175.999954, 156.970108, 175.999954)`.

The built-in validator confirms valid glTF 2.0 JSON, buffer/view/accessor extents, finite values, matching position/UV cardinality, TRIANGLES primitives, valid material references, index divisibility, and indices within vertex counts. The independent consistency pass reads the actual accessor bytes and exactly matches every selected descriptor/material, transformed position, Q4.12 UV, and reconstructed index.

Blender 5.2.1 LTS imported the full glTF in background mode without rendering or saving: 1,338 mesh objects, 87,682 imported vertices, 46,336 polygons, and 39 materials. The imported-vertex difference is exactly the 632 unreferenced source-stream records described above.

## Retained anomalies and limitations

- Three exact geometric degenerates are preserved.
- 1,463 collapsed-UV triangles are preserved.
- 632 unreferenced streamed vertices are preserved in glTF accessors; importers may omit them.
- V4-8 bytes 0–2 are likely vertex color/light modulation and byte 3 is globally `0x80`; exact Spartan routing remains unconfirmed. They are absent by default and available only through opt-in diagnostic `COLOR_0`.
- Exact native MTL sampler/render equations remain unknown. Raw mode retains conservative materials; an opt-in experimental mapping is available for bounded culling/alpha validation.
- The existing full geometry export references textures by provenance only and does not display them; complete strongly bound texture decode is now available for a later full textured export.
- Source coordinates and source winding are now confirmed for determinant-positive glTF export using descriptor 118.
- Source V is confirmed by descriptor 5's upright lower-banner lambda.
- Exact repeat-versus-mirror semantics remain unresolved; both modes are explicit.
- The MODELS geometry/UV/image pipeline is VISUALLY VALIDATED and all strongly bound geometry TIM2 variants decode faithfully. Full material fidelity still requires broader MTL and sampler semantics.
- glTF's default single-sided materials produce widespread culling holes. The PS2 GS has no face-cull field, and opt-in all-double-sided output restores coherent surfaces; Spartan pre-GS CPU/VU culling remains unknown.
- The level-scale `CLOUD` shell occludes the scene under conservative `OPAQUE` rendering. Its decoded texture alpha is fully opaque, correcting the earlier partial-alpha description. Standard source-alpha blend cannot reproduce its native effect.

## Complete textured assembly gate

`LEVEL00_TEXTURED.gltf` was generated locally with 1,338 meshes, 39 materials, 30 images, and the canonical 46,336 triangles. Blender 5.2.1 LTS reports 1,338 mesh objects, 87,682 referenced vertices, 46,336 polygons, 39 materials, 30 images, and one UV layer on every mesh. All links and dimensions match.

The original export established **TEXTURED ASSEMBLY VALIDATED**. Subsequent R5900/VU1/TEX0 work now establishes **LEVEL00 WORLD RECONSTRUCTION COMPLETE** for the asset-preservation milestone: a faithful preservation profile must include source V4 colour and retain the recovered native GS metadata, especially CLOUD's opaque RGBA/MODULATE path. This does not make standard glTF a complete GS emulator. See [LEVEL00_TEXTURED_RECONSTRUCTION.md](../milestones/LEVEL00_TEXTURED_RECONSTRUCTION.md) and [GS_TEXTURE_ALPHA_PATH.md](GS_TEXTURE_ALPHA_PATH.md).

## Experimental MTL render-semantics gate

`spartan_models.py` retains every unknown numeric MTL child as its property type and raw u32 payload. `models_mtl_render_probe.py` produces a strict ignored matrix for all 55 records and joins the 39 used records to descriptor/triangle totals and decoded alpha classes.

`--mtl-render-semantics raw` remains the default. The explicit `experimental` mode emits `doubleSided=true` for all submitted materials because the PS2 GS primitive state has no cull selector, while documenting that Spartan may cull earlier. It emits standard glTF `BLEND` only when MTL child type 2 is present and a confirmed decoded image has binary/partial alpha. It emits neither `MASK` nor `alphaCutoff`; no threshold has been identified. Opaque type-2 images, including `CLOUD`, remain `OPAQUE`.

The controlled complete export contains 39 double-sided materials, 30 `OPAQUE`, zero `MASK`, and nine `BLEND`. Exact geometry/UV/material round trip remains 1,338 descriptors, 2,128 batches, 88,314 streamed records, and 46,336 triangles. Blender imports all counts and links; the culling holes disappear and alpha vegetation/effect pages improve. `CLOUD` remains an occluder, so this mode is a diagnostic approximation rather than the canonical native material pipeline. Detailed evidence is in [MODELS_MTL_RENDER_SEMANTICS.md](MODELS_MTL_RENDER_SEMANTICS.md).

## Descriptor-118 visual convention gate

Eight controlled variants tested source/`(X,Z,-Y)` coordinates, source/reversed winding, and source/flipped V with the native decoded `002` image. Source coordinates import as terrain with all eight face normals upward in Blender; `(X,Z,-Y)` makes the patch near-vertical. Source winding remains front-facing; reversed winding points all faces downward and is culled from the top view. Both V choices remain plausible. Full evidence and bounds are recorded in [MODELS_VISUAL_CONVENTIONS.md](MODELS_VISUAL_CONVENTIONS.md).

## Descriptor-5 directional V gate

Two otherwise identical variants used descriptor 5 / MTL 1 `L0_FLAGS`: source coordinates, source winding, 84 triangles, and the independently verified native 256×256 decode. Source V places an upright lambda at the banner bottom; flipped V places it inverted at the top. Blender reports identical object/mesh/polygon/material/image counts and identical bounds. Source V is the validated default. A secondary descriptor-361 sampler comparison did not resolve native repeat versus mirrored repeat.

## Commands

Small validation:

```powershell
python tools/conversion/export_models_gltf.py game-extracted/pak/LEVEL00/DATA/ENV/LEVEL00/WORLD temp/exports/level00_validation/descriptor_0118.gltf --descriptor 118 --static-only --coords source --winding source --v-mode source --inventory logs/analysis/LEVEL00_inventory.json --report temp/exports/level00_validation/descriptor_0118_validation.json
```

Full validation:

```powershell
python tools/conversion/export_models_gltf.py game-extracted/pak/LEVEL00/DATA/ENV/LEVEL00/WORLD temp/exports/level00_validation/LEVEL00.gltf --all --coords source --winding source --v-mode source --inventory logs/analysis/LEVEL00_inventory.json --report temp/exports/level00_validation/LEVEL00_validation.json --manifest temp/exports/level00_validation/manifest.json
```

Experimental render-semantic validation adds:

```powershell
--mtl-render-semantics experimental
```
