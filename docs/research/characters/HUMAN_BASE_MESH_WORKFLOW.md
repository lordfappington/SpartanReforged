# Human Base-Mesh Workflow

Roman Grunt Reforged V1 and V2 proved the automated Blender/render/reporting
pipeline, but human review rejected their primitive-built anatomy as a
production character foundation. They remain preserved experiments. Future
characters must start from a continuous anatomical mesh; there is no V3
"block-boy" polish path.

## Candidate review

| Candidate | Source | Exact licence and redistribution | Mesh / workflow assessment | Main drawback |
|---|---|---|---|---|
| Blender Human Base Meshes v1.4.1 | [Official Blender demo asset bundle](https://www.blender.org/download/demo-files/) and [official download index](https://download.blender.org/demo/asset-bundles/human-base-meshes/) | **CC0 1.0 Universal**. Commercial use, modification, and redistribution of original or modified meshes are permitted; attribution is not required. | Native Blender asset collection; realistic male source has 10,582 vertices, 10,590 mostly-quad polygons, 21,160 base triangles, UV map, and three multires levels. Strong anatomy, closed continuous body, sculpt/model/texture/rig intent, good armour-shell source and LOD starting point. Blender 4.2+ requirement is compatible with 5.2.1. Deterministic library append is scriptable. | The realistic sculpt topology is denser than a final crowd mesh and is not a finished deformation/game topology. Retopology, rigging, weights and production LODs remain later stages. |
| MakeHuman / MPFB core assets | [Official licensing](https://static.makehumancommunity.org/about/license.html) and [MPFB FAQ](https://static.makehumancommunity.org/mpfb/faq/can_i_sell_models.html) | Core base mesh, targets, skins and other core assets are **CC0**; generated core-only derivatives may be commercially used, modified and redistributed without attribution. MPFB code is GPL and MakeHuman code AGPL. Third-party add-ons/assets retain their own licences. | Mature parametric human generator, UVs, targets, proxies/topologies, Rigify/Mixamo support and strong automation. Polygon count varies with chosen proxy/subdivision/export. Suitable for armour variants and crowds when a production proxy is selected. | Adds generator/add-on/version complexity. Core-only provenance must be enforced because user-contributed assets may be CC-BY or other licences. A generated mesh still needs art-directed sculpting/retopology. |
| Blender Studio `realistic_human_base.blend` | [Blender Studio workflow page](https://studio.blender.org/training/realistic-human-research/use-of-base-meshes/) | Page labels the file **CC-BY**. Commercial use, modification and redistribution are allowed subject to the applicable Creative Commons attribution terms; the precise version/credit string should be captured with the download before redistribution. | Production-oriented realistic male sculpt base with even quad topology, multires workflow, face sets, UV/UDIM support, A-pose and real-world scale. Strong anatomy and armour/sculpt foundation. Approximate polygon count was not published on the reviewed page and must be inspected from the downloaded file. | Attribution/version metadata must be preserved and the download route is less frictionless than the public CC0 bundle. It is a sculpt base, not automatically an animation/crowd mesh. |
| MB-Lab 1.8.1 | [Archived official repository](https://github.com/animate1978/MB-Lab) and [licence documentation](https://mb-lab-docs.readthedocs.io/en/latest/license.html) | Python is GPL-3.0; database, meshes, images and JSON are **AGPL-3.0**. The project states generated 3D models default to AGPL-3.0 and inherit the database copyright. Commercial use is possible under AGPL, modification is allowed, but redistributed derivatives must remain AGPL with source obligations. | Parametric anatomy, topology, UV/material and rig tooling; published for Blender 4.0+. Output counts vary by model/finalization. Scriptable and useful for crowds/variants in an AGPL-compatible project. | Repository was archived in 2024, Blender 5.2 compatibility is unverified, and AGPL propagation is undesirable for a neutral preservation/remaster asset pipeline. Rejected for this build. |
| CharMorph | [Official repository](https://github.com/Upliner/CharMorph) and [documentation](https://charmorph-docs.readthedocs.io/en/main/Introduction.html) | Add-on code is GPL-3.0. Its character library is a separate submodule and exposes per-character licence metadata; it derives its model ecosystem from ManuelBastioniLAB/MB-Lab. Commercial/modification/redistribution terms therefore depend on the selected character data and must be audited per asset. | Active Blender-native morphing, alternative topology, fitting, Rigify support and automation. Polygon count, UV quality and rig suitability vary by selected library character. | The code licence alone does not clear a chosen mesh. Multi-repository data provenance and per-character licensing are more complex than the official CC0 Blender bundle. Not selected. |

## Selection

**Selected:** Blender Human Base Meshes v1.4.1, collection `Body Male -
Realistic`.

It provides the strongest combination of verified permissive licensing,
credible anatomy, continuous topology, UVs, native Blender compatibility,
future sculpt/rig/LOD usefulness, and deterministic import without installing a
generator. The official bundle archive is kept privately at:

```text
temp/roman-human-base-build1/source/human-base-meshes-bundle-v1.4.1.zip
```

Archive SHA-256:
`811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515`.

The selected mesh is CC0 and could legally be redistributed, but this milestone
keeps the third-party mesh and all derived `.blend`/render output private under
`temp`. Only source-independent workflow code and documentation are public.

## Gated workflow

1. Run `build_roman_grunt_human_base_build1.py -- --phase human`.
2. Review five full-body angles plus head/neck, torso/shoulder,
   arm/elbow/hand and leg/knee/foot close-ups in neutral light.
3. Stop if the body reads as primitive-built, toy-like, or anatomically broken.
4. Only after that technical gate, run the `roman` phase.
5. Build fitted surfaces from the continuous anatomy where appropriate; do not
   replace the body with cubes, cylinders, spheres or capsule limbs.
6. Keep all review output private and stop for human visual approval before
   rigging, animation, LOD creation, export or runtime integration.

Build 1 keeps one multires level for form review: the continuous body evaluates
to 84,680 triangles (86,856 including two eyes) from the 21,160-triangle source
base. This is deliberately not a final runtime budget.

## Current assessment

The anatomy gate passes technically: the foundation reads as a believable adult
male and exposes credible joints, hands and feet from all required angles. The
equipment pass is a **major-form study**, not production character art. It is
substantially closer methodologically because torso and shoulder armour derive
from the anatomical surface, but helmet refinement, shoulder articulation,
pteruges, shield paint, footwear, materials, retopology and posed presentation
still require an artist-led pass.

Status: **AWAITING HUMAN VISUAL APPROVAL**.
