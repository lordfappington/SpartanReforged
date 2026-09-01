# Reforged Main Menu Art Asset Contract

## General requirements

This contract describes future approved art inputs. It does not authorize final art production. Original/extracted assets are never replacement fallbacks. All raster masters use tagged sRGB colour with straight alpha unless a reviewed asset explicitly requires linear data. Runtime builds may derive optimized formats without overwriting masters.

Critical UI content must remain separate from background/foreground environment layers. Asset filenames are implementation details; stable asset IDs are the contract.

| Asset ID | Purpose | Preferred master | Recommended master size | Alpha | Padding | Anchor / scaling | Motion / tiling | Fallback |
|---|---|---|---|---|---|---|---|---|
| `logo` | Faithful SPARTAN / TOTAL WARRIOR mark | lossless PNG or layered source + exported PNG | 2048×768 canvas, artwork within safe padding | straight, clean translucent edges | ≥64 px all sides | top-left; preserve aspect; max token width | static | labelled vector box |
| `logoFlare` | Optional warm glint crossing logo | transparent PNG sequence, sprite sheet, or reviewed runtime effect | 2048×512 | straight | enough for bloom tail, ≥96 px | logo-local; never changes logo bounds | optional one-shot/subtle loop | omitted |
| `background` | Cinematic environment plate without UI | layered 16-bit source; exported AVIF/WebP/PNG as pipeline permits | minimum 7680×2160 working canvas with central 3840×2160 composition | opaque | ultrawide environment bleed ≥1920 px each side | viewport cover; preserve central 16:9 composition | not tiled; optional shallow parallax | dark gradient/zone guide |
| `foregroundEnvironment` | Right-side equipment/banner/debris depth | layered source + transparent lossless export | 4096×2160 | straight | ≥128 px around silhouettes | right/bottom; environment-only ultrawide rules | optional shallow parallax | omitted/geometric wedge |
| `topFrieze` | Upper Greek/Roman ornamental band | SVG where practical, otherwise lossless PNG set | 512 px-high master components | straight | 32 px | top stretch axis via caps + repeatable centre | centre tiled/nine-slice | procedural diagonal band |
| `bottomFrieze` | Lower ornamental band | SVG where practical, otherwise lossless PNG set | 512 px-high master components | straight | 32 px | bottom; same rules as top | centre tiled/nine-slice | procedural diagonal band |
| `selectionMarker` | Small spear/weapon-like selected marker | SVG/SDF or equivalent vector source | 512×192 artboard | straight | 32 px | left of selected baseline; uniform scale | short slide/fade/impulse | simple triangle |
| `padlock` | Locked replay status | SVG/SDF or equivalent vector source | 512×512 artboard | straight | 40 px | item/status anchor; uniform scale | restrained rejection pulse | procedural outline lock |
| `glyphCross` | PlayStation-style Cross prompt | SVG/SDF: symbol and metallic housing separable | 512×512 | straight | 32 px | prompt baseline; uniform scale | static/subtle focus response | labelled circular glyph |
| `glyphTriangle` | PlayStation-style Triangle prompt | SVG/SDF | 512×512 | straight | 32 px | prompt baseline | as above | labelled circular glyph |
| `glyphCircle` | Reserved Circle prompt | SVG/SDF | 512×512 | straight | 32 px | prompt baseline | as above | labelled circular glyph |
| `glyphSquare` | Reserved Square prompt | SVG/SDF | 512×512 | straight | 32 px | prompt baseline | as above | labelled circular glyph |
| `smoke` | Back/front atmospheric smoke | grayscale/colour flipbook or reviewed procedural texture | 1024×1024 per unique source frame | straight | ≥32 px soft edge | environment space; text exclusion mask | animated; no tiling unless seamless | omitted/soft geometric haze |
| `embers` | Sparse warm particles | sprite atlas or reviewed procedural primitive | 512×512 atlas | straight/additive intent documented | ≥16 px per sprite | environment space | animated, sparse | omitted |

## Current logo implementation

Pass 1 and Pass 2 remain under `assets/reforged/frontend/main-menu/logo` as rejected experimental/research history. The human-approved 2172×724 RGBA artwork is archived and bound from `logo/approved`; its runtime PNG is byte-identical to the supplied source. It remains a complete static raster because destructive divider/flare separation was not justified.

## Logo-specific acceptance criteria

- Preserve the original two-line identity and proportions; do not redesign it into an unrelated wordmark.
- Aged metallic gold, restrained bevel/depth, subtle weathering, and warm highlights are allowed.
- Transparent pixels must be colour-matted to avoid dark/bright fringes.
- The optional glint remains separate so reduced motion can disable it.
- Review at native master, 4K output size, 1080p output size, and against the quiet upper-left safe zone.
- A 4K-quality master is required even though runtime display is much smaller; the runtime never simply scales a captured 1080p framebuffer to 4K.

## Background composition zones

- Left: low-frequency, low-contrast visual field behind navigation.
- Centre: mist/depth and distant ancient architecture.
- Right: richer environmental focal composition and optional foreground Spartan equipment/banner.
- Top-left: quiet logo silhouette and glint clearance.
- Bottom-right: prompt contrast and clearance.
- No logo, text, prompts, marker, padlock, or labels may be baked into the background.

The committed safe-area SVG is the authoring overlay. Artwork should be previewed with it but exported without it.

## Colour, alpha, and animation delivery

All colour assets declare their colour profile. Straight-alpha deliverables must retain RGB in translucent edge pixels. Animated deliverables include frame rate, loop mode, pivot, blend intent, and reduced-motion behavior. Additive or premultiplied assets require an explicit exception because those semantics cannot be inferred from pixels alone.

## Resolution policy

Vector/SDF components are resolution-independent. Raster masters target native 4K quality or better. Runtime derivatives may be generated for performance tiers, but originals remain immutable. The central 16:9 composition must stand alone at 1920×1080 through 3840×2160; 21:9 and 32:9 reveal environment-only side regions rather than stretching or relocating critical UI.
