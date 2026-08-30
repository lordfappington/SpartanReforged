# LEVEL00 Textured Reconstruction Validation

## Outcome

The first complete textured LEVEL00 glTF was assembled from the confirmed MODELS geometry/UV pipeline and the 30 independently verified native TIM2 decodes. Serialization, exact geometry round-trip, external image linkage, and Blender import all pass. The artifact is a valid forensic reconstruction, but **LEVEL00 WORLD RECONSTRUCTION COMPLETE is not yet justified** because unresolved material culling and alpha semantics cause systemic visual occlusion in a normal glTF render.

This task used only the existing isolated LEVEL00 extraction. No PAK was opened, no source asset was modified, and no image or geometry was enhanced or altered.

## Reconstruction totals

| Property | Result |
|---|---:|
| Descriptors / glTF meshes | 1,338 |
| VIF batches represented | 2,128 |
| Source position/UV records | 88,314 |
| Reconstructed triangles | 46,336 |
| Geometry-used materials | 39 |
| Confirmed textured materials | 32 |
| Explicit unresolved placeholders | 7 |
| Unique decoded PNGs/images | 30 |
| Texture decode failures | 0 |

The export uses source coordinates `(X,Y,Z)`, source winding, signed Q4.12 UVs, source V, and unclamped UV ranges. It retains 632 unreferenced strip/history records, three exact geometric degenerates, and 1,463 collapsed-UV triangles. No normals are exported.

## Material and texture policy

Every used MTL record is classified in glTF extras and the ignored manifest as `TEXTURED_CONFIRMED` or `PLACEHOLDER_UNRESOLVED`. Confirmed textures use an unlit neutral validation material and their native decoded base-level PNG. Images shared by aliases are emitted once: 32 materials reference 30 unique images.

The sampler is explicit `REPEAT`, retained as a conservative validation default rather than a confirmed native MTL state. Mirrored repeat remains selectable.

Across the 30 unique images, 22 are fully opaque, one has binary alpha, and seven have partial alpha. Source alpha remains present in every PNG, but all glTF materials remain `OPAQUE`; no blend mode, mask threshold, or emissive behavior was invented.

## Unresolved materials

| MTL | Name | Descriptors | Triangles | Evidence-based role/impact |
|---:|---|---:|---:|---|
| 22 | `HEAD_MARKERS` | 2 | 16 | small marker/billboard-like special geometry at the origin; limited world impact |
| 25 | `LIGHTNING` | 1 | 6 | narrow effect template; limited environment impact |
| 26 | `BEAM` | 1 | 12 | narrow effect template; limited environment impact |
| 28 | `APP_MEDUSA` | 1 | 40 | effect application/template; limited environment impact |
| 29 | `LIGHT_SPHERE01` | 1 | 480 | hemispherical effect template; visible neutral placeholder near origin |
| 30 | `LIGHT_SPHERE02` | 1 | 480 | complementary hemispherical effect template; visible neutral placeholder near origin |
| 37 | `GLOW` | 18 | 2,616 | repeated effect meshes; largest unresolved group, but all are non-AAB special descriptors |

All 26 unresolved descriptors are below descriptor 114 and therefore outside the static AAB-indexed partition. Their small source-space bounds and names support an effect/template role, but no runtime placement or texture substitution is inferred.

## Validation

The built-in written-file validator reports 4,014 buffer views/accessors, 88,314 positions, 88,314 UVs, 139,008 indices, 46,336 triangles, 39 materials, 30 images/textures, and 1,338 meshes/nodes. Exact round-trip validation confirms descriptor/material membership, positions, Q4.12 UVs, and indices.

The output bounds equal the source bounds:

```text
min (-176.0, -12.383148193359375, -176.0)
max (175.9999542236328, 156.97010803222656, 175.9999542236328)
```

The prior AAB audit remains applicable because every exported position matches the source exactly: all 1,224 static descriptor references remain fully contained by their associated AAB cells.

Blender 5.2.1 LTS imports:

| Property | Result |
|---|---:|
| Mesh objects / meshes | 1,338 / 1,338 |
| Imported vertices | 87,682 |
| Polygons | 46,336 |
| Materials | 39 |
| Images | 30 |
| Meshes with UV layers | 1,338 |
| Missing images/materials | 0 / 0 |
| Broken or cross-bound textures | 0 |
| Image-dimension mismatches | 0 |

Blender's bounds are the expected glTF Y-up to Blender Z-up mapping: min `(-176, -175.999954, -12.383148)`, max `(175.999954, 176, 156.970108)`.

## Visual anomaly audit

### Known unresolved semantics

- All 39 imported glTF materials use the format's default single-sided behavior because native MTL culling flags are unknown. The full render consequently contains widespread missing backfaces. A local diagnostic with backface culling disabled reveals a coherent level without those holes. This strongly localizes the visual issue to material culling semantics rather than geometry/topology reconstruction, but it does not prove that every native material is two-sided.
- Descriptor 48 / MTL 31 `CLOUD` is a level-scale shell. A later strict alpha audit corrected this document's original classification: its decoded texture alpha is fully opaque. Conservative `OPAQUE` rendering makes it a large white occluder, and standard source-alpha blend cannot resolve the native effect. See `MODELS_MTL_RENDER_SEMANTICS.md`.
- Binary/partial-alpha vegetation and effect pages render opaquely. Dark fringes or filled transparent regions are expected until MTL alpha modes and thresholds are decoded.
- `REPEAT` appears spatially plausible on terrain, masonry, roofs, and floors, but repeat versus mirrored-repeat remains unresolved.

### Source characteristics / retained data

- The world is split into many descriptor chunks, and some isolated special/effect templates remain near the origin.
- Three geometric degenerates, collapsed UV triangles, and unreferenced streamed records are retained intentionally.

### Not observed

- No texture cross-binding, upside-down systemic texture orientation, axis error, altered bounds, missing confirmed image, index corruption, or impossible global layout was found.
- Architecture, roofs, walls, trees, banners, paths, and the central circular complex align coherently in diagnostic two-sided inspection.

## Local generated artifacts

Ignored outputs are under `temp/exports/level00_textured/`:

- `LEVEL00_TEXTURED.gltf` and `.bin`
- `textures/*.png`
- `manifest.json`, `validation.json`, and `blender_validation.json`
- full-scene `overhead.png`, `wide.png`, and `ground.png`
- supplemental occlusion/culling diagnostic renders

None are committed.

## What this proves

- Complete confirmed MODELS geometry, UVs, material membership, and all strongly bound native textures can be assembled deterministically into one valid glTF.
- Blender preserves all 46,336 polygons and every material/image relationship.
- The remaining major visual defects are render-state semantics rather than missing texture decoder coverage or detected geometry corruption.

## What this does not prove

- Native PS2 culling, alpha, blend, sampler, lighting, fog, effect, or draw-order behavior.
- Resolution of the seven missing texture bindings.
- Native game rendering, a runtime, remastering, or reconstruction of characters/gameplay systems.

## Readiness decision

Classification: **TEXTURED ASSEMBLY VALIDATED; WORLD RECONSTRUCTION NOT COMPLETE**.

The single next task should identify only the MODELS.MTL properties controlling face culling/two-sided rendering and alpha mode/threshold, using the 39 geometry-used records and the visual discriminators established here.
