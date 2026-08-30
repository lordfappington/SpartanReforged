# MODELS Geometry Export Pipeline

The first LEVEL00 world-geometry reconstruction was completed on 2026-08-30 using only the existing isolated LEVEL00 extraction. This pipeline reconstructs confirmed source geometry outside the PS2 runtime; it does not reproduce native game rendering.

## Source and derived-data boundary

**SOURCE DATA** are the ignored, read-only `MODELS.BIN`, `MODELS.AAB`, `MODELS.MTL`, and referenced TIM2 files beneath the LEVEL00 extraction. The exporter verifies the three MODELS hashes against canonical constants and can verify all 58 TIM2 hashes against the local LEVEL00 inventory.

**GENERATED/DERIVED DATA** are glTF JSON, external glTF binary buffers, validation reports, and manifests. They are written only beneath `temp`, remain ignored, and must not be committed. No source resource is modified.

## Tools and architecture

- `tools/conversion/spartan_models.py` is target-neutral. It parses MODELS.BIN/MTL/AAB, validates boundaries and cross-references, reconstructs ADC topology, decodes Q4.12 UVs, exposes selection, and implements explicit coordinate transforms.
- `tools/conversion/export_models_gltf.py` builds glTF 2.0 buffers/accessors, creates traceable descriptor meshes and placeholder materials, validates the serialized glTF, and performs an exact source-to-accessor consistency check.
- `tests/formats/test_spartan_models.py` uses synthetic, non-copyrighted inputs only.

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

The `gltf` name denotes a documented modern-target alternative, not a claim about otherwise unknown source handedness. The exporter never automatically changes winding.

## Winding and UV options

- `--winding source` emits the confirmed relative strip winding.
- `--winding reverse` swaps the second and third index of every emitted triangle.
- `--v-mode source` exports `v = int16(raw_v) / 4096`.
- `--v-mode flip` exports `v = 1 - int16(raw_v) / 4096`.

U is always `int16(raw_u) / 4096`. Negative and greater-than-one coordinates are preserved. Neither V mode clamps or wraps coordinates. Every selected option and exact coordinate mapping is recorded in glTF asset extras, the report, and the manifest.

## Normals, materials, and textures

Normals are omitted by default and no normal-generation option is used in this first pipeline. V4-8 remains retained in the parser but is not exported or interpreted.

One placeholder glTF material is created for every selected, geometry-used MTL record. Names retain the source MTL index and name. No metallic, roughness, alpha, blend, emissive, or sampler property is assigned by the exporter. These remain glTF defaults rather than claims about Spartan materials.

Strongly resolved TIM2 references are recorded in material extras with their source-relative paths and SHA-256 values. No TIM2 is converted, embedded, filtered, or modified. The full export resolves 32 of 39 used material records to one TIM2 reference.

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
- V4-8 semantics are unknown and absent from glTF.
- Exact MTL sampler/render properties are unknown; materials are placeholders.
- Textures are referenced by provenance only and are not displayed.
- Absolute native front-face and V orientation are not claimed.
- The source-mode export is suitable for structural inspection; faithful rendered appearance requires later convention and material validation.

## Commands

Small validation:

```powershell
python tools/conversion/export_models_gltf.py game-extracted/pak/LEVEL00/DATA/ENV/LEVEL00/WORLD temp/exports/level00_validation/descriptor_0118.gltf --descriptor 118 --static-only --coords source --winding source --v-mode source --inventory logs/analysis/LEVEL00_inventory.json --report temp/exports/level00_validation/descriptor_0118_validation.json
```

Full validation:

```powershell
python tools/conversion/export_models_gltf.py game-extracted/pak/LEVEL00/DATA/ENV/LEVEL00/WORLD temp/exports/level00_validation/LEVEL00.gltf --all --coords source --winding source --v-mode source --inventory logs/analysis/LEVEL00_inventory.json --report temp/exports/level00_validation/LEVEL00_validation.json --manifest temp/exports/level00_validation/manifest.json
```
