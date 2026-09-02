# Reforged Main Menu Technical Specification

## Status and boundary

This specification defines the additive Reforged presentation for the recovered FE_MAIN `main_start` semantics. It does not replace or modify the frozen preservation implementation, extracted assets, scripts, decoders, or original reference reconstruction.

```text
MainStart semantic state
├── OriginalMainStartView  -> frozen preservation/reference presentation
└── ReforgedMainStartView  -> scalable modern presentation
```

The implementation foundation is `tools/reforged/frontend/main_menu_reforged.py`. It intentionally does not import `main_menu_design_kit.py` or read FE_MAIN. Presentation mode is explicit; the Reforged wireframe refuses an `ORIGINAL` state rather than silently approximating it.

## Semantic architecture

`MenuScreen` owns ordered `MenuItem` and `MenuPrompt` values. `MenuState` owns selection and presentation mode. `MenuAction` identifies destination behavior independently of labels, while `InputAction` identifies navigation intent independently of physical devices.

The stable `main_start` IDs are:

| ID | Action | Original order |
|---|---|---:|
| `new_game` | `NEW_GAME` | 0 |
| `load_game` | `LOAD_GAME` | 1 |
| `options` | `OPTIONS` | 2 |
| `arena_challenge` | `ARENA_CHALLENGE` | 3 |
| `single_mission_replay` | `SINGLE_MISSION_REPLAY` | 4 |
| `extras` | `EXTRAS` | 5 |

Each item carries localization keys, action, enabled/locked state, lock condition, and explicit up/down relationships. Selection wraps at the ends as the original menu does. `single_mission_replay` remains locked when `maxlevel == 0`; a failed confirmation returns no action and must not transition.

Localized text is loaded from external locale resources. The English development locale records only recovered wording. Empty body fields are intentional: no replacement prose was invented. Rendering logic contains localization keys, not English menu copy.

## Input abstraction

Semantic actions are `CONFIRM`, `BACK`, `UP`, and `DOWN`. Initial presentation mappings are:

| Action | PlayStation | Xbox | Keyboard |
|---|---|---|---|
| `CONFIRM` | Cross | A | Enter |
| `BACK` | Triangle | B | Escape |
| `UP` | D-pad Up | D-pad Up | Up Arrow |
| `DOWN` | D-pad Down | D-pad Down | Down Arrow |

These are front-end display bindings, not gameplay remapping. The eventual input service should supply the active profile and configured key names.

## Coordinate and scaling model

The authoring space is 1920×1080 with a top-left origin and square pixels. All positions and sizes are design tokens. A viewport computes one uniform scale:

`scale = min(viewportWidth / 1920, viewportHeight / 1080)`

The central 16:9 composition is centered. At 16:9 this fills the viewport. Wider outputs keep the central composition unchanged and reveal environment-only extensions on both sides. Narrower outputs, including 4:3, fit the complete composition and may expose background-only space above and below. Critical UI stays inside the composition's safe rectangle.

| Output | Scale | Central composition | Extension |
|---|---:|---:|---:|
| 1920×1080 | 1 | 1920×1080 | none |
| 2560×1440 | 4/3 | 2560×1440 | none |
| 3840×2160 | 2 | 3840×2160 | none |
| 2560×1080 (21:9 diagnostic) | 1 | 1920×1080 | 320 px each side |
| 3840×1080 (32:9 policy) | 1 | 1920×1080 | 960 px each side |
| 1440×1080 (4:3 fallback) | 0.75 | 1440×810 | 135 px background above/below |

This is logical scaling, not a requirement to raster-upscale a 1080p framebuffer. Raster art follows the source requirements in the asset contract; typography and glyphs remain scalable.

## Safe areas and anchors

The initial 16:9 action-safe inset is 96 horizontal and 54 vertical design pixels. Logo, menu, context, status, and prompts anchor within that rectangle. The background and atmosphere may fill the physical viewport. Only environmental background/foreground art may occupy ultrawide extensions; logo, labels, prompts, marker, padlock, and friezes retain safe anchors.

The committed `main-menu-safe-area-template.svg` contains quiet logo/navigation/context regions, a right-side environment focal region, prompt clearance, and ornamental edges. It contains no game imagery.

## Rendering layers

The logical layer order is retained even if a renderer batches compatible draws:

1. `00_BACKGROUND_ENVIRONMENT`
2. `01_ATMOSPHERE_BACK`
3. `02_ORNAMENTAL_FRAME`
4. `03_FOREGROUND_ENVIRONMENT`
5. `04_LOGO`
6. `05_MENU_NAVIGATION`
7. `06_CONTEXT_DESCRIPTION`
8. `07_STATUS`
9. `08_INPUT_PROMPTS`
10. `09_FRONT_ATMOSPHERE`
11. `10_TRANSITIONS`

UI is never baked into the background. Foreground environment is independently hideable/croppable so localization, aspect changes, controller changes, and the future Original/Reforged toggle do not require background regeneration.

## Components

### Logo

`Logo` accepts an independent transparent logo and optional glint/flare layer. Rejected Pass 1/Pass 2 experiments remain retained, while the human-approved 2172×724 straight-alpha raster is the Reforged runtime binding. Its baked divider/flare are preserved intact and no rejected experimental overlay is applied. Runtime scaling preserves aspect ratio, respects `maxWidth`, and never enlarges beyond the available safe zone. Missing assets still fall back to a labelled rectangle rather than original copyrighted imagery. Source and review details live in `MAIN_MENU_LOGO.md` and the asset contract.

### Menu navigation and SelectionMarker

`MenuNavigation` is a floating left-aligned text stack with no button rectangles. `SelectionMarker` uses the locked human-approved raster under `pointer/approved/`; the active Reforged path contains no procedural reconstruction or material overlay. Its derived RGBA runtime copy is scaled from the high-resolution master to a 96×22-design-pixel visible box and placed 17 design pixels left of the selected label using the alpha-visible bounds. It follows the semantic selection at every supported resolution. Unselected and locked labels share a restrained dimensional material construction. The selected label deliberately uses a different, internally illuminated amber treatment rather than imitating the physical bronze title material.

Selection-change timing starts at 160 ms: marker slide/fade, neutral-to-gold interpolation, glow increase, and subtle scale. Confirmation starts a 130 ms warm flare/marker impulse before the original semantic transition. Reduced motion collapses these to an immediate state change. Original mode retains the recovered ±16 logical-pixel behavior through its own view; Reforged does not copy it by default.

### Locked state

`StatusLock` is shown for locked items and uses the locked human-approved raster under `padlock/approved/`. The active Reforged path contains no procedural outline or added glow. The derived RGBA runtime copy preserves the source RGB inside an object-aware, border-connected matte and is rendered at 30 design pixels high, 12 design pixels after the measured visible label bounds. The lock remains driven solely by the existing `maxlevel == 0` semantic condition; unlocked items do not render it. Locked labels reduce emphasis. Confirmation produces restrained feedback, returns no action, and never changes screens.

### Context description

`ContextDescription` accepts heading and body keys, wraps within a tokenized maximum width, and supports empty body text. `Begin your Quest!` is the recovered initial string. Final copy remains localization-owned.

### Prompts and glyphs

`InputPrompts` consumes semantic actions and the active device profile. The PlayStation profile uses the four locked human-approved shield rasters under `prompts/playstation/approved/`: Cross, Triangle, Circle, and Square. Each derived runtime asset is centred on the same 448×448 transparent canvas with a normalized 416-pixel visible diameter. Reforged renders the shield artwork directly at a 52-design-pixel visible diameter—there is no procedural ring, secondary housing, border, or Unicode symbol. Semantic mapping remains profile-driven: Cross is Confirm and Triangle is Back on this screen, while Circle and Square remain available. Non-PlayStation profiles retain replaceable development fallbacks until their own production assets are approved.

### OrnamentalBand

Top and bottom bands expose end-cap and repeatable-center slots. Nine-slice or tiled center rendering is permitted; stretching the detail pattern is not. The wireframe uses a procedural diagonal repeat.

### Atmosphere

Back/front atmosphere exposes smoke, mist, embers, logo glint, and selected glow as independently budgeted effects. Emitters scale in logical space, have exclusion masks for menu/context/prompt safe regions, and must support a later reduced-motion mode. No final particles are included now.

## Typography

Typography roles are `MenuPrimary`, `MenuPrimarySelected`, `ContextHeading`, `ContextBody`, and `PromptLabel`. They are scalable runtime text styles, never rasterized English labels. The Reforged renderer uses Cinzel Regular and Bold, pinned from the upstream Cinzel project and redistributed under SIL Open Font License 1.1. Its first-century Roman inscription influence and classical proportions harmonise with the approved title while remaining an independent UI typeface rather than an imitation of the logo geometry. Locale coverage and fallback remain future review requirements.

Unselected and locked navigation styling is constructed inside the antialiased Cinzel glyph mask: a tonal face gradient, a darker eroded inset band, a pale upper/left-facing bevel, and a grey lower/right-facing bevel. The selected state does **not** use that bronze/inset construction. It combines two differently scaled, label-seeded low-frequency fields with irregular broad cream/white-gold concentrations clipped to the eroded glyph interior. Amber occupies transitions inside a thin darker-gold container; a one-pixel pale rim and minimal opposing-edge response preserve structure. Immediate and broad bloom are derived from the irregular internal light field—not a uniform glyph outline—and remain secondary to the contained illumination. No navigation state uses an external text stroke. The material renderer does not change glyph metrics and supports arbitrary localized labels. Localization must be tested for expansion, missing glyphs, line breaks, and locale-specific font fallback.

## Asset loading and fallback

Every asset slot is optional in the token file. Missing Reforged assets resolve to a named procedural/labelled placeholder. They must never silently fall through to copyrighted original data. Production asset loading must validate asset ID, dimensions, colour space, alpha expectations, and supported format against `MAIN_MENU_ART_ASSET_CONTRACT.md`.

## Wireframe validation

The CLI writes deterministic asset-free previews and a manifest beneath ignored `temp/reforged/main-menu-wireframes`. It validates hierarchy, anchors, safe areas, selection, lock status, prompts, and aspect behavior. It is not concept art, final artwork, or a production renderer.

## Current limitations

- No final artwork, final typeface, production UI framework, audio, or runtime transition integration exists.
- The English locale includes recovered headings but deliberately no invented body copy.
- Pointer/mouse interaction and full remapping are deferred.
- 21:9 is previewed; 32:9 and 4:3 behavior are deterministic and tested but not rendered as requested outputs.
- The semantic actions are stubs until connected to a future front-end runtime.
