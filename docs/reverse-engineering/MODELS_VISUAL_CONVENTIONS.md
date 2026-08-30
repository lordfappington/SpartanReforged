# MODELS Visual Conventions — Descriptors 118 and 5

Descriptor 118 established coordinate and front-face conventions, native TIM2 decoding, material/image linkage, and periodic UV use. Descriptor 5 then established V orientation using a directionally unambiguous banner. Together they satisfy the visual-convention gates for the tested materials without claiming complete MTL semantics.

## Controlled input

| Property | Value |
|---|---|
| Descriptor | 118, AAB-indexed |
| MTL binding | index 5, name/resource stem `002` |
| Texture | `DATA/ENV/LEVEL00/WORLD/002.TM2` |
| Streamed vertices / triangles | 12 / 8 |
| Source bounds | `(-152.000015, 20.325733, -136.000015)` to `(-136.000015, 32.828007, -120.000031)` |
| UV range | U `-2.5..-0.5`; V `-0.500244140625..1.499755859375` |

## Directional candidate ranking

Only geometry-used resources in the existing LEVEL00 extraction were considered.

| Rank | Descriptor(s) | MTL / texture | Dimensions | Triangles | UV range | Directional evidence | Confidence |
|---:|---|---|---:|---:|---|---|---|
| 1 | 5–47; selected 5 | 1 `L0_FLAGS` / `L0_FLAGS.TM2` | 256×256 | 84 each | U `0.00415..0.35889`, V `0.00415..1.0` | Upright lambda emblem occupies the lower-left texture region; descriptor is a vertical hanging banner | **Very high** |
| 2 | 243 representative | 33 `GRKTREE` / `GRKTREE.TM2` | 256×256 | 6 | U `0.33691..1.0`, V `0..0.625` | Tree atlas has trunks/bases and foliage tops | Medium; atlas segmentation and unsupported CLUT type complicate isolation |
| 3 | 361 representative | 34 `MEDUSA_TOWER` / `MEDUSA_TOWER.TM2` | 256×256 | 8 | U `-7.60742..7.89258`, V `2.31519..2.55957` | Architectural lintels/bases have top/bottom; extensive U tiling also tests sampler modes | Medium for V; useful but inconclusive for sampler choice |
| 4 | 49/50 | 2 `ARROW` / `ARROW.TM2` | 32×32 | 16 each | U `0.00684..0.96191`, V `0.00708..0.96411` | Arrow is directional, but its principal direction is horizontal and the geometry has negligible height | Low for vertical V |

`TEMPLE_FLAGS` and `GREEK_PATERN` were inspected but rejected: the former is a generic square tile page and the latter is an approximately symmetric meander motif. Generic stone/wall/noise resources were also rejected.

## Tested matrix

Eight glTF variants were generated: two coordinate modes × two winding modes × two V modes. Every file retained the same 12 POSITION values, 12 UV values, eight confirmed triangles, one material, and one native 256×256 image.

| Dimension | Variants |
|---|---|
| Coordinates | source `(X,Y,Z)`; proper rotation `(X,Z,-Y)` |
| Winding | confirmed source triangle order; reversed second/third indices |
| V | `v`; `1-v` |
| Sampler | glTF `REPEAT` on S/T for the validation material |

`(X,Z,Y)` was considered but not exported: it is the tested axis exchange plus a reflection, so it confounds the coordinate question with the already isolated winding question. `(X,-Z,Y)` similarly adds a sign choice without evidence. The minimal proper rotation is sufficient to test whether source Y or source Z is vertical.

## Coordinate result

**Selected for glTF: source `(X,Y,Z) -> (X,Y,Z)`; determinant +1.**

Existing AAB/geometry evidence establishes source Y as vertical and X/Z as the horizontal plane. glTF also defines +Y as up. Blender's glTF importer converts that glTF Y-up data to its internal Z-up representation. With source coordinates, Blender reports bounds X `-152..-136`, Y `120..136`, Z `20.326..32.828`: the source height range becomes Blender Z. With `(X,Z,-Y)`, the broad source Z range becomes Blender Z and the terrain normals point primarily along Blender Y, making the terrain patch near-vertical. The source transform is therefore **CONFIRMED for glTF/Blender**.

This uses the normative glTF convention rather than a guessed relabeling: [Khronos glTF 2.0 specification](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#coordinate-system-and-units).

## Winding result

**Selected: source winding, with no index reversal under the selected determinant-positive coordinate transform.**

Before export, all eight source-winding triangle normals have positive source Y (`0.5345..0.9221`). After source-coordinate glTF import, all eight Blender face normals have positive Z; their mean is approximately `(-0.1913, -0.0358, 0.7350)`. Reversed winding sends all eight normals to negative Blender Z and back-face culling removes the patch from the controlled top view. Source winding is therefore **CONFIRMED as the glTF front-face order for this determinant-positive path**.

No normals were exported or generated. Blender's face normals were computed from imported triangle indices solely for validation.

## V orientation result

Descriptor 5 is MTL index 1 `L0_FLAGS`, bound to `DATA/ENV/LEVEL00/WORLD/L0_FLAGS.TM2` (SHA-256 `1dc53a5566f1b0beb27d3717bf7fbad22d95a1e2c60adc0222918257e694b0a3`). It contains three batches, 150 streamed vertices, and 84 triangles. Blender imports 148 referenced vertices, 84 polygons, one material, one image, and one UV layer for both variants; bounds are identical.

The native 256×256 texture has an unmistakable upright lambda emblem in pixels approximately X `10..92`, Y `184..243`, near the image bottom. Source V renders the lambda upright at the lower end of the hanging banner. `1-v` renders the emblem upside-down at the banner top. This is not an aesthetic preference: the symbol orientation and its placement relative to the suspension frame both reverse.

Geometry independently supports the source result. In the main flag batch, V `0.00415` occurs around source Y `9.91..10.08`; successive rows V `0.16895`, `0.33398`, `0.49902`, `0.66382`, and `0.82886` descend monotonically to Y `4.12..4.15`. The image's lower emblem therefore belongs at lower geometry under source V. Flipping V contradicts that mapping.

Consequently:

- **selected modern convention: `v_target = v_source`; CONFIRMED for LEVEL00 glTF/Blender validation**;
- source V is the exporter default for both modern and forensic output;
- `--v-mode flip` remains explicit and lossless;
- texture orientation is now confirmed by descriptor 5.

glTF defines `(0,0)` at the upper-left image pixel, matching the project's preserved PNG row order: [Khronos glTF wrapping rules](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#wrapping).

## Sampling and material result

Descriptor 118 confirms periodic sampling is required. Descriptor 5 stays within one texture extent, so it cannot distinguish wrap modes. A bounded secondary test used descriptor 361 / MTL 34 `MEDUSA_TOWER`, whose U range crosses more than 15 integer periods. Explicit `REPEAT` and `MIRRORED_REPEAT` variants retain identical geometry and continuous seams, but no local runtime reference or directionally repeated text distinguishes which motif sequence is native. Both are mathematically coherent at integer boundaries.

Therefore exact native ordinary-repeat versus mirrored-repeat remains **UNKNOWN**. `--sampler repeat|mirrored-repeat` is explicit and recorded; `REPEAT` remains the conservative validation default, not a decoded MTL property.

The attached material uses `KHR_materials_unlit`, neutral base color, one base-color image, and `REPEAT` S/T. This avoids invented lighting, metallic, roughness, alpha, normal, and emissive interpretations. Blender 5.2.1 LTS imports every variant as one object, one mesh, 12 vertices, eight polygons, one material, one image, and one UV layer, with the material linked to image `002`.

## Readiness decision

The pipeline advances to **VISUALLY VALIDATED** for LEVEL00 MODELS geometry: topology, coordinates, winding, Q4.12 UV decode, source V, native PSMT4 decode, and descriptor material/image mapping have all passed controlled Blender validation. Exact repeat-versus-mirror remains documented but does not prevent faithful validation of descriptor 5 because its UVs remain within one extent.

A full textured LEVEL00 export is now technically justified as a local validation export, but it should remain conservative: only verified TIM2 variants can be decoded, unresolved materials must remain placeholders, and sampler mode must stay explicit rather than claimed from MTL.
