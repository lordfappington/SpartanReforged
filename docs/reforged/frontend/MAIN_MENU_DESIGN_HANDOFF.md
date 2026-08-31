# Original Main Menu Design Handoff

## Purpose and boundary

This handoff describes the first primary navigation screen after the FE_MAIN title/boot transition: script menu `main_start`. It is a factual reference reconstruction for later SpartanReforged design work, not replacement art. Original extracted files, decoders, FE semantics, preservation exporters, executable data, and the frozen LEVEL00 baseline remain unchanged.

Only already-extracted `FE_MAIN.PAK` resources were used. The preceding `titles` screen and its attract video are outside the target except where they establish inherited state such as the background colour modulation. No other PAK was opened.

## What the original screen contains

The target is a layered 2D screen, not a video or 3D scene:

1. `GRAB_05.TM2` static cloudy blue background, overscanned and slightly brightened;
2. two procedural smoke emitters using `SMOKE.TM2`;
3. four clipped border sprites using the upper band from `BANDS.TM2`;
4. contextual information text using `FONT14`;
5. six localized menu labels using `FONT18`, with only the selected label replaced by `FONT18G`;
6. a flare and small title crop from `SPARTAN_LOGO.TM2`;
7. two procedural glow emitters around the logo using `GLOWS.TM2`;
8. Triangle/Back and Cross/OK prompts from `ICONS.TM2` plus `FONT14`;
9. a conditional replay padlock from `MISSION_BUILDER.TM2`;
10. `BLACKBOX.TM2` PAL/overscan bars at the safe-area boundaries.

`ATTRACT.PSS` and `ATTRACT_PAL.PSS` are not target-screen backgrounds. They are invoked only after the preceding title screen idles.

## Coordinate system and aspect

The recovered layout uses a 512×448 logical safe area with top-left origin, positive X to the right, and positive Y downward. It is displayed as 4:3 using non-square pixels; the corresponding pixel aspect is 7:6 because `(512 × 7/6) / 448 = 4/3`.

Several source sprites intentionally extend outside this area. The background is a 640×480 sprite at `(-64,-16)`. Border halves begin at X `-256` and `256`. PAL bars occupy Y `-64..0` and `448..512`. These are overscan/clipping evidence, not reasons to enlarge the logical UI canvas.

### Principal positions

| Element | Logical bounds |
|---|---|
| Small logo | X 64, Y 16, 192×64 |
| Logo flare | X 64, Y 48, 192×16 |
| New Game | X 64, Y 128, 320×32 text field |
| Load Game | X 64, Y 160, 320×32 |
| Options | X 64, Y 192, 320×32 |
| Arena Challenge Mode | X 64, Y 224, 320×32 |
| Single Mission Replay | X 64, Y 256, 320×32 |
| Extras | X 64, Y 288, 320×32 |
| Replay padlock | X 32, Y 256, 32×32 |
| Context information | X 24, Y 384, 432×32 |
| Triangle glyph / Back | X 336/Y 385 glyph; X 368/Y 384 text |
| Cross glyph / OK | X 432/Y 385 glyph; X 464/Y 384 text |
| Top border halves | X -256 and 256, Y 32, each 512×32 |
| Bottom border halves | X -256 and 256, Y 384, each 512×32 |

There is no separate menu panel, backing plate, or persistent selection bar. Buttons with four-pixel-high logical hit regions provide focus/input behavior but are not members of the target menu's visible draw list.

## Draw order

The script declares this top-level order:

```text
background
smoke emitter 2
smoke emitter 4
borders
information text
normal menu text
logo flare
selected/glow menu text
small logo
two logo glow emitters
Triangle/Back prompt
Cross/OK prompt
padlock
PAL bars
```

The machine-readable expanded order and exact source line references are in `assets/reforged/frontend/design-kit/main-menu/layout.json`.

## Text and font system

The six option labels are localized strings, not raster label sprites. English sources are:

| Script label | English `UI.TXT` value |
|---|---|
| `la_new_game` | New Game |
| `la_load_game` | Load Game |
| `la_options` | Options |
| `la_arena_mode` | Arena Challenge Mode |
| `la_replay_mission` | Single Mission Replay |
| `la_bonus` | Extras |

Unselected labels use `FONT18.TM2`; selected labels use `FONT18G.TM2`. Both are 512×512, contain a 16×16 grid of 32×32 cells, and use byte-identical DIM advances. The selected glow/outline is authored in the `FONT18G` pixels. Information and controller-prompt text uses the 256×256 `FONT14` atlas with 16×16 cells.

For target ASCII text, glyph index is `character code - 32`. Each paired 576-byte DIM has a 64-byte prefix followed by 256 little-endian u16 advances. No independent kerning table, baseline table, or per-pair spacing table was found. This is strong enough for the target reference strings; broader legacy-code-page mapping remains outside this handoff.

The initial contextual line is `Begin your Quest!`. Other selected states use `Continue previous game`, `Game Options`, `Arena Challenge`, `Replay a Chapter`, and `Bonus Features`.

## Selection and state behavior

On entry, New Game is selected. The script hides all glow variants, shows all normal variants, hides the selected normal label, and shows the matching glow label at identical bounds. A selection change performs a temporary horizontal shake: +16 then -16 logical pixels over ten ticks, followed by position reset. It is not a persistent motion or highlight bar.

Confirmation flashes the selected glow text between bright and transparent three times before transition. Main-menu music is requested symbolically as `MAIN_MENU_MUSIC`.

Four emitter objects are active: two large tinted smoke fields and two small opposing logo glows. Their source declarations, anchors, and parameters are preserved in `layout.json`. The exact runtime particle instance distribution is stochastic/procedural and was not invented for the deterministic still; the still represents the static zero-particle composition.

## Logo

The visible title is two layers from one 512×512 `SPARTAN_LOGO.TM2` page:

- `tex_spartan_logo_small`: normalized source region `(0,88,96,32)`, resolving to a native 192×64 crop and displayed 1:1 at `(64,16)`;
- `tex_spartan_logo_flare`: normalized source region `(0,120,96,8)`, resolving to 192×16 and displayed 1:1 at `(64,48)`.

The flare is drawn first and the logo over it. No font participates in the title. The main-menu logo is not animated directly, although nearby glow emitters are animated. The same page supplies larger title, credits, SEGA, Creative Assembly, and Total Warrior branding elsewhere, so it is shared.

## Controller glyphs and input assumptions

`ICONS.TM2` is a 64×64 page divided into four native 32×32 glyphs. Script texture coordinates use a normalized 0..256 page space:

| Texture region | Glyph | Native size | Target use |
|---|---|---:|---|
| `tex_icons_button_1` | Cross | 32×32 | `CONFIRM`, visible as Cross/OK |
| `tex_icons_button_2` | Triangle | 32×32 | `BACK`, visible as Triangle/Back |
| `tex_icons_button_3` | Circle | 32×32 | shared global source, not visible on this state |
| `tex_icons_button_4` | Square | 32×32 | shared global source, not visible on this state |

No directional, analog-stick, shoulder, START, or SELECT sprite appears on `main_start`. Directional navigation is embedded as script handlers rather than visible glyphs.

Future input rendering should bind semantic actions first:

| Semantic action | Original PS2 assumption | Later platform examples |
|---|---|---|
| `CONFIRM` | Cross | Xbox A; bound keyboard key |
| `BACK` | Triangle | Xbox B or project-approved mapping; bound keyboard key |
| `OPTIONS` | no visible target-screen glyph | platform menu/options key |

The current PS2-specific assumption is embedded in the `controller_ok` and `controller_back` item groups and in named `CROSS`/`TRIANGLE` handlers. This handoff does not implement alternate platforms.

## Padlock

`tex_padlock` is a native 46×47 crop at `(65,0)` from the 256×256 `MISSION_BUILDER.TM2` page. `spr_padlock_freeplay` scales it to 32×32 at `(32,256)`, immediately left of Single Mission Replay.

It is visible while `maxlevel == 0` and hidden after progress unlocks replay. Attempted confirmation while locked plays `sfx_locked` and flashes the sprite to white for two ticks before returning to neutral over ten ticks. The lock does not move and is not frame-animated. Its source page is shared with many mission/menu construction elements.

## Background and frame construction

The background is not a PSS. `GRAB_05.TM2` is a 512×512 indexed source page. Its normalized near-full-page crop is resized to 640×480 at `(-64,-16)`, producing deliberate viewport cropping. The preceding title state applies RGB modulation `148/128`, and `main_start` does not reset it; the reference therefore retains that inherited value. This inheritance is strongly supported by script state flow but remains part of the pending runtime-capture check.

Two large smoke emitters use `SMOKE.TM2` and receive dark blue modulation. The top and bottom ornamental lines use one 510×32-equivalent normalized crop from `BANDS.TM2`; four wide sprites clip its left/right halves against the 512-pixel viewport.

For future widescreen work, only the abstract background field is a technically suitable extension region. The logo, menu text, glyphs, lock, and ornamental bands must retain anchored composition and must not be stretched horizontally.

## 16:9 and future-resolution mapping

The unmodified 4:3 presentation is centred vertically at full output height:

| Output | Central 4:3 area | Side extension each | Logical X scale | Logical Y scale |
|---|---:|---:|---:|---:|
| 1920×1080 | 1440×1080 | 240 px | 2.8125 | 2.410714 |
| 2560×1440 | 1920×1440 | 320 px | 3.75 | 3.214286 |
| 3840×2160 | 2880×2160 | 480 px | 5.625 | 4.821429 |

Different X/Y factors are expected because the logical source pixels are non-square. The provided 1080p reference uses nearest-neighbour sampling and black side regions to expose the original without redesigning it.

Recommended future architecture:

- retain a 1920×1080 design coordinate system for new UI, independent of physical output;
- use aspect-safe anchors and normalized safe-area constraints rather than scaling a 512×448 canvas;
- render scalable typography, vector/SDF symbols, and procedural/nine-slice chrome;
- select resolution-appropriate raster artwork for 1080p, 1440p, and 4K;
- keep the 4:3 preservation renderer and Reforged renderer as independent output paths;
- on ultrawide displays, extend only approved background layers while keeping the authored UI group inside an aspect-safe central region.

## Technical replacement categories

| Original component | Future category | Technical reason |
|---|---|---|
| Cross/Triangle/Circle/Square glyphs | **A — VECTOR / SDF REBUILD CANDIDATE** | simple symbols; current 32×32 raster includes low-resolution bezel/shading |
| Padlock | **A — VECTOR / SDF REBUILD CANDIDATE** | simple silhouette; source is only 46×47 and displayed 32×32 |
| Spartan/Total Warrior logo + flare | **B — HIGH-RES RASTER REBUILD CANDIDATE** | complex authored metallic artwork; visible crop only 192×64 |
| Ornamental top/bottom bands | **C — PROCEDURAL / NINE-SLICE UI CANDIDATE** | long clipped strips must scale without horizontal texture distortion |
| Cloudy background and smoke composition | **D — HIGH-RES BACKGROUND RECONSTRUCTION CANDIDATE** | current base page is 512×512 and must support side extension |
| Typography, spacing, selection swap, prompt semantics | **E — KEEP ORIGINAL SEMANTICS / REDRAW VISUALLY** | preserve hierarchy and states while replacing low-resolution bitmap text later |
| Particle timing/distribution | **F — UNKNOWN / NEEDS DESIGN DECISION** | source emitter parameters are known, but exact Reforged presentation is not selected |

The 32-pixel glyphs, 32-pixel font cells, 46×47 lock, 192×64 logo, 32-pixel bands, and 512×512 background are unsuitable for filtered raster enlargement as final Reforged assets.

## Strict original/Reforged separation

```text
game-extracted/pak/FE_MAIN/...          ignored original extracted inputs
assets/original/...                     original archival namespace (unchanged)
assets/reforged/frontend/design-kit/... factual reference metadata; generated imagery ignored
exports/preservation/...                reproducible source-faithful outputs
exports/reforged/...                    future independent Reforged outputs
```

No original file was moved or copied into the Reforged tree. The design kit contains generated crops/compositions only, and every PNG is Git-ignored. Preservation remains reproducible without any Reforged asset.

## Reference outputs and limitations

Generated locally under `assets/reforged/frontend/design-kit/main-menu/`:

- native 512×448 static reference;
- 2× nearest-neighbour inspection reference;
- centred 1920×1080 mapping reference;
- transparent background/chrome/text/lock layers;
- logo and padlock clean source references;
- glyph and representative-state contact sheets;
- layout, inventory, font, state, and hash manifests.

No existing local gameplay capture of `main_start` was found. Runtime visual validation is therefore **PENDING**. The reconstruction is source-structural, and its explicit limitation is the absence of stochastic particle instances. No web capture was searched for or fabricated.

## Recommended first human review

Review the **logo reconstruction specification first**. It is the screen's dominant identity element, yet the visible original is only 192×64 and combines metallic lettering with a separate flare. Establishing human-approved logo fidelity before panels, glyphs, or background work gives the later UI pass a stable visual anchor without committing to a whole-menu redesign.
