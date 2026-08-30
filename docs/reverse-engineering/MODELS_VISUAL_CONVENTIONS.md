# MODELS Visual Conventions — Descriptor 118 Validation

Descriptor 118 was tested as an isolated, texture-bound LEVEL00 terrain patch. This validation establishes coordinate and front-face conventions, native TIM2 decoding, material/image linkage, and periodic UV use. It does **not** establish V orientation because the `002` stone texture has no unambiguous directional landmark.

## Controlled input

| Property | Value |
|---|---|
| Descriptor | 118, AAB-indexed |
| MTL binding | index 5, name/resource stem `002` |
| Texture | `DATA/ENV/LEVEL00/WORLD/002.TM2` |
| Streamed vertices / triangles | 12 / 8 |
| Source bounds | `(-152.000015, 20.325733, -136.000015)` to `(-136.000015, 32.828007, -120.000031)` |
| UV range | U `-2.5..-0.5`; V `-0.500244140625..1.499755859375` |

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

Both `v_target = v_source` and `v_target = 1-v_source` produce coherent, seam-free mappings; they are vertical mirrors of one another. The decoded `002` image is an approximately stochastic stone surface with no known top, text, logo, lighting cue, or local PCSX2 reference. Neither appearance can be selected without aesthetic guesswork.

Consequently:

- source V remains the exporter default for forensic fidelity;
- `--v-mode flip` remains explicit and lossless;
- target V orientation is **UNKNOWN**, not locked;
- texture orientation is **not confirmed** by descriptor 118.

glTF defines `(0,0)` at the upper-left image pixel, matching the project's preserved PNG row order: [Khronos glTF wrapping rules](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#wrapping). This makes source V plausible, but it is not proof of Spartan's native convention.

## Sampling and material result

The two-period U and approximately two-period V ranges demonstrably require periodic sampling for the shown mapping. glTF `REPEAT` preserves every out-of-range Q4.12 value and produces four coherent tiles. This confirms **periodic/wrapping behavior is required for descriptor 118**. The unresolved MTL properties do not yet distinguish native ordinary repeat from mirrored repeat, so `REPEAT` is a conservative validation sampler rather than a decoded MTL claim.

The attached material uses `KHR_materials_unlit`, neutral base color, one base-color image, and `REPEAT` S/T. This avoids invented lighting, metallic, roughness, alpha, normal, and emissive interpretations. Blender 5.2.1 LTS imports every variant as one object, one mesh, 12 vertices, eight polygons, one material, one image, and one UV layer, with the material linked to image `002`.

## Readiness decision

The pipeline remains **GEOMETRY READY**, with coordinate and winding now visually validated and native decoding/material linkage operational. It does not advance to **VISUALLY VALIDATED** because descriptor 118 cannot prove V orientation or the exact native repeat-versus-mirror sampler. A full textured LEVEL00 export is therefore not yet justified as a faithful visual reconstruction.

The single next gate is a controlled validation using an already-extracted LEVEL00 descriptor whose bound TIM2 has an unmistakable directional feature (text, arrow, logo, or asymmetric page layout), testing source versus flipped V without opening another archive.

