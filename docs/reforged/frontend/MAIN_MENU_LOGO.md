# Reforged Main-Menu Logo

## Status

Three production candidates share one custom outline reconstruction. Variant A is the current **TECHNICAL PREFERENCE ONLY — PENDING HUMAN ART REVIEW**. No candidate is human-approved, and no other menu artwork was changed.

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
