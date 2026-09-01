# Reforged Main-Menu Logo

## Status

Pass 1 and Pass 2 typography/geometry failed human review and remain retained as rejected Reforged experiments. The supplied 2172×724 raster is now the **HUMAN-APPROVED REFORGED ARTWORK** and the active Reforged menu asset. No other menu artwork was changed.

The work is additive beneath `assets/reforged/frontend/main-menu/logo`. The original TIM2, decoded design-kit references, preservation renderer, and FE data remain untouched and independently reproducible.

## Original source and geometry

Canonical source: `DATA/ENV/FE_MAIN/WORLD/SPARTAN_LOGO.TM2`, SHA-256 `755e4dd82ec2d29c1dbc45136f9cbf92a25628a4e6859888ad7c7971b6a3e84c`.

The validated TIM2 decoder produces a 512×512 page. FE_MAIN's normalized declarations resolve to:

- base logo crop: `(0,176)–(192,240)`, displayed 192×64;
- flare crop: `(0,240)–(192,256)`, displayed 192×16.

The prior design-kit `logo-reference.png` composites both layers and remains ignored. Geometry measurements below come from the base crop alone, not the flare.

| Measurement | Source-pixel value | Normalized to 192×64 |
|---|---:|---:|
| full canvas | `(0,0)–(192,64)` | `(0,0)–(1,1)` |
| visible alpha | `(2,1)–(184,64)` | `(0.010417,0.015625)–(0.958333,1)` |
| SPARTAN | `(2,1)–(170,36)` | `(0.010417,0.015625)–(0.885417,0.5625)` |
| TOTAL WARRIOR | `(2,41)–(171,64)` | `(0.010417,0.640625)–(0.890625,1)` |
| TM | `(169,2)–(184,12)` | `(0.880208,0.03125)–(0.958333,0.1875)` |

- Canvas aspect: 3:1.
- Visible-alpha aspect: 182:63, approximately 2.8889:1.
- SPARTAN width/height: 168×35.
- TOTAL WARRIOR width/height: 169×23.
- Lines share the same measured left edge at X=2; the subtitle is one pixel wider.
- Measured high-alpha face baselines: Y=33 and Y=61.
- Measured face-to-face line gap: nine source pixels.
- TM remains small and aligned immediately beyond the upper word.

## Typography and reconstruction

The upper and lower lines resemble classical Roman display lettering but do not match an installed/open font closely enough to justify substitution. The original also uses different proportions for the large title and compressed subtitle. No font is used in the production logo, so there is no runtime font dependency or font license.

The builder decodes the base crop in memory, interpolates its alpha field at 8× for subpixel edge recovery, extracts an alpha=192 iso-contour, simplifies it conservatively, and writes custom SVG paths. All candidates use exactly these paths. This removes source-pixel stair steps while retaining the measured S curvature, narrow P/R bowls, A proportions, R legs, serifs, subtitle compression, spacing, and TM placement.

This is a reconstruction from a 192×64 reference, not a claim to recovered pre-raster source vectors. Subpixel serif detail that never existed in the source remains an unavoidable uncertainty and is a human-review item.

## Master and layers

The vector master is `logo_source/logo_geometry.svg`, a 2520×840 (3:1) custom-path SVG with transparent background. Deterministic runtime PNG derivatives use the same 2520×840 canvas, providing more than 2048 pixels of horizontal working resolution without raster-authoring at 192×64.

Logical authoring layers are:

- `LOGO_BASE`: custom vector silhouette and `logo-base-mask.png`;
- `LOGO_MATERIAL`: candidate A/B/C RGBA outputs;
- `LOGO_GLOW`: `logo-glow.png`, optional and restrained;
- `LOGO_GLINT`: `logo-glint-mask.png`, a travelling-highlight mask only;
- `LOGO_FLARE`: `logo-flare.png`, a deterministic low-intensity representative state.

The runtime may combine these but must retain the option to disable glow/glint/flare, particularly for reduced motion. The current main-menu integration uses the material output only; it does not bake a background into the logo.

## Material variants

All shading is deterministic and procedural. It consists of a three-stop vertical bronze/gold response, shallow upper-edge highlight, darker lower recess, subtle seeded low-frequency surface irregularity, limited pitting, and a small self-shadow. It is not a generic font emboss filter because the input is the custom geometry and each effect is independently controlled.

| Variant | Treatment | Assessment |
|---|---|---|
| A | restrained aged gold; moderate relief; minimal wear | closest to original tonal restraint and best small-scale balance |
| B | darker aged bronze; stronger wear and recess | atmospheric but loses some subtitle energy at 50% |
| C | brighter cinematic gold; stronger upper-edge illumination | strongest contrast, but risks dominating the unfinished menu |

Variant A is the technical preference because it preserves line hierarchy, remains legible at 315×105, avoids the dark subtitle of B, and avoids C's stronger highlight competing with future background lighting. This selection is not art approval.

## Original palette reference

Broad source measurements from high-alpha base pixels are:

- dark visible material P10: approximately sRGB `(63,63,67)`;
- dominant warm-metal median: approximately `(170,140,89)`;
- bright highlight P99: approximately `(255,254,187)`;
- representative original flare warmth: `(255,210,137)`.

These are references, not hard constraints. The new variants extend tonal range while retaining aged warm-gold identity.

## Runtime presentation

Runtime form: straight-alpha sRGB PNG, 2520×840. Alpha masks represent linear coverage; colour is not premultiplied and contains no menu-background matte. The main-menu token points to `logo-preferred.png` and separately identifies flare/glint assets.

Nominal display sizes are:

| Output | Display size | Filter |
|---|---:|---|
| 1920×1080 | 630×210 | Lanczos |
| 2560×1440 | 840×280 | Lanczos |
| 3840×2160 | 1260×420 | Lanczos |

At 21:9 the logo retains the same position relative to the centered 16:9 composition, not the physical left edge. The 3440×1440 diagnostic places the composition at X=440 and the logo anchor at approximately X=613.33.

Review renders cover 100%, 75%, and 50% nominal display sizes. SPARTAN and TOTAL WARRIOR remain readable, TM remains recognizable, and reconstructed curves/serif tips do not exhibit nearest-neighbor pixel stair steps. Fine surface wear appropriately disappears before core letter structure.

## Transparency validation

The preferred asset was composited over black, neutral grey, and the representative dark blue. No background is present in the source PNG, no blue matte is baked into its edge pixels, and the master alpha bounds `(120,66)–(2295,814)` remain inside the 2520×840 canvas. Soft self-shadow is contained within padding.

## Reproducibility

`tools/reforged/frontend/build_main_menu_logo.py` is hash-locked to both the original TM2 and design-kit comparison reference. It fails if either changes, performs in-memory read-only decoding, generates vector/runtime/mask assets, builds the ignored review package, and verifies source hashes afterward.

Required existing Python packages are Pillow, NumPy, and OpenCV. No online service, external logo download, newly installed program, or generative-image model is used.

Machine-readable dimensions, paths, hashes, geometry, palette references, variants, layers, and preference status are in `logo/metadata/logo.json`.

## Human review package

Local ignored path: `assets/reforged/frontend/review/logo`.

It contains original-versus-Reforged, three-variant, 100/75/50% scale, transparency, three 1080p menu integrations, and preferred 1440p/4K/21:9 integrations. The files are review evidence only and are not canonical assets.

## Human-review questions

1. Does the custom tracing remain immediately identifiable as the original mark despite the unavoidable 192×64 source limit?
2. Should the upper title be made slightly lighter/thinner before approval?
3. Is Variant A appropriately restrained, or should C's brighter edge response become the baseline?
4. Is B's wear too strong for the subtitle at actual menu size?
5. Should the flare/glint warmth retain more of the original cool-blue centre?

Do not begin the next main-menu art asset until these candidates are approved or revised.

## Pass 2 — clean geometry and reconstructed bevel

### Why Pass 1 failed review

Human review rejected Pass 1 because its alpha iso-contour made source-pixel staircase, curve, antialiasing, and sampling irregularities permanent vector geometry. Its material also read mainly as colour variation over a flat face instead of the source's bright edge, bevel slope, raised face, opposing dark edge, and recessed perimeter. Pass 1 remains in its original paths and metadata; Pass 2 is entirely separate beneath `logo/pass2`.

### Geometry reconstruction

Pass 2 does **not** trace any raster contour. The 192×64 source provides composition, stroke/proportion evidence, line boxes, baselines, and glyph identity only. The builder defines a reusable custom glyph library for S/P/A/R/T/N/O/L/W/I/M:

- intended stems, crossbars, diagonals, serif edges, and terminals are exact line segments;
- S, P/R bowls, and O/counter geometry use deliberate cubic Bézier curves;
- A uses mirrored straight diagonals, a symmetric apex/counter, one crossbar, and matched foot serifs;
- T uses a horizontal crown, straight central stem, and symmetric crown/foot serifs;
- N uses parallel stems and one mathematically straight diagonal;
- repeated A, R, T, and O instances reference one shared glyph definition rather than independent sampled outlines;
- the title, compressed subtitle, and TM apply separate transforms to the same definitions and retain the measured source boxes.

The availability survey found Georgia, Times New Roman, and Informal Roman on the workstation. They were rejected as production inputs because none establishes the original identity closely enough and their use would introduce either licensing or proportion questions. No reference font supplies Pass 2 geometry and there is no font runtime dependency.

### Downsample validation

The 2520×840 clean mask is Lanczos-downsampled to 192×64 and compared against the decoded original base. The diagnostic shows source coverage, rejected Pass 1, full Pass 2, the downsampled Pass 2, an original-red/Pass-2-cyan edge overlay, and enlarged S/P/R/A/N panels.

The downsample preserves the 192×64 composition, two-line hierarchy, widths, alignment, glyph identities, subtitle compression, TM hierarchy, and approximate stroke locations. It intentionally does not reproduce source staircase edges or irregular edge coverage. A thresholded-interior IoU of approximately 0.266 is recorded for reproducibility but is not treated as the objective function: forcing pixel equality would recreate the failure Pass 2 is intended to remove.

The remaining uncertainty is typographic rather than raster: no pre-raster source vectors exist, so precise original serif profiles and curve tensions remain inferred and require human art review.

### Original bevel/light study

Representative high-alpha source samples yielded:

- deepest shadow P02: approximately `(40,31,22)`;
- dark bevel P15: approximately `(69,70,75)`;
- main face median: approximately `(164,142,96)`;
- light bevel P85: approximately `(253,202,122)`;
- bright highlight P99: approximately `(255,254,187)`;
- brightest original flare sample: approximately `(248,248,249)`.

Repeated bright upper/left edges and dark lower/right edges imply an upper-left/front light direction. The bright bands are narrow and orientation-dependent, while dark bronze edges recur opposite them and around counters. This supports a raised face bounded by a shallow directional bevel, not a vertical fill gradient.

### Pass 2 bevel model

Pass 2 builds material in the required order: clean mask, signed-distance bevel, face gold, dark bronze edge, directional light, restrained variation, specular, then separate glow/glint/flare.

The bevel rises over 20 master pixels from every outer or counter edge to the raised face, equivalent to about five pixels at the nominal 1080p display size. Gradients of the distance field produce surface orientation. A normalized light vector `(-0.48,-0.72,0.50)` shades each slope; a half-vector response adds controlled bevel-only specular. The face retains Pass-1A restraint with a subtle upper-left illumination gradient. Seeded wear is added last at very low amplitude and cannot alter silhouette or conceal construction problems.

### Pass 2 candidates

All candidates use byte-identical geometry and alpha:

| Candidate | Difference |
|---|---|
| Pass 2A | faithful bevel; restrained A-family gold and source-like light/dark edge separation |
| Pass 2B | same bevel geometry with smoother modern bronze/gold response and tighter specular |
| Pass 2C | same geometry and material family with stronger controlled cinematic edge illumination |

Pass 2A is the technical preference because its bevel is evident at 630×210 without overpowering the face, its subtitle remains legible at smaller scales, and its contrast is closest to the measured source structure. This is not human approval.

### Blue-white flare

Pass 2 replaces Pass 1's warm flare with a separate 2520×252 blue-white component. It has a white-blue core, narrow horizontal beam, soft blue bloom, and bounded 150/255 maximum alpha. The deterministic review state composites it between the title and subtitle at the recovered vertical relationship. Runtime logo PNGs do not bake it in; the independent flare file and glint mask preserve future animation/reduced-motion control.

### Quality-gate result

- High-resolution vector edges contain no source-pixel staircase segments.
- Straight strokes are exact; curves are smooth cubics; repeated glyphs share definitions.
- No accidental Pass-1-style wobbly contour is present.
- Serif/counter geometry is deliberate and A's counter is explicitly cut.
- The directional bevel is clearly perceptible at nominal menu size without large extrusion.
- The face remains restrained gold with controlled dark-bronze and bright-edge separation.
- The cool flare is restored as a separate identity layer.
- SPARTAN, TOTAL WARRIOR, and TM remain readable at 1080p/1440p/4K and the 50% diagnostic scale.
- 21:9 retains the central-composition anchor.

Pass 2 completed its technical review but was subsequently rejected for final typography/geometry. Its geometry and bevel study remains research history rather than runtime art.

### Pass 2 paths

- Vector source: `assets/reforged/frontend/main-menu/logo/pass2/logo_source/logo_clean_geometry.svg`
- Runtime candidates: `assets/reforged/frontend/main-menu/logo/pass2/logo_runtime`
- Masks/flare: `assets/reforged/frontend/main-menu/logo/pass2/logo_masks`
- Metadata: `assets/reforged/frontend/main-menu/logo/pass2/metadata/logo-pass2.json`
- Ignored diagnostics/review: `assets/reforged/frontend/review/logo`

## Human-approved raster integration

Human review rejected both procedural reconstruction passes and supplied the final art direction as `spartan-logo-approved.png`. Preservation research still establishes what the original artists were depicting, while Reforged production may reconstruct that intent without inheriting PS2 raster constraints. Automated reconstruction must never override approved art direction.

The approved source is archived byte-for-byte at `assets/reforged/frontend/main-menu/logo/approved/source/spartan-logo-approved.png`. Its SHA-256 is `b57304192c2b811a8f49b3b235617082ab8b5d4319a2867d08b2df671cd1d42d`; it is a 1,542,636-byte, 2172×724 RGBA PNG with straight alpha and a 3:1 aspect ratio. It contains transparent, partial-coverage, and opaque pixels. Inspection against blue-black showed clean readable gold, preserved dark-bronze relief, a legible TM/divider, and a restrained blue-white flare. No cleanup, colour adjustment, sharpening, denoising, resizing, vectorisation, or redesign was applied.

The runtime asset at `assets/reforged/frontend/main-menu/logo/approved/runtime/spartan-logo-approved.png` is byte-identical to the approved source. The complete raster is used because divider/flare extraction could not be guaranteed without changing approved pixels. Consequently `logoFlare` and `logoGlintMask` are disabled for this asset; future independent flare animation requires a human-approved layered source.

The existing 1920×1080 logical placement remains `(130,90)` in a `650×210` fit box, producing a 630×210 presentation at 1080p, 840×280 at 1440p, and 1260×420 at 4K. The same central 16:9 composition remains anchored on ultrawide displays. ORIGINAL presentation and every original extracted asset remain unchanged.

Machine-readable metadata is at `assets/reforged/frontend/main-menu/logo/approved/metadata/spartan-logo-approved.json`. Ignored review renders are under `assets/reforged/frontend/review/logo/approved`. The next gate is human review of the approved logo in the menu composition, not another automated logo pass.
