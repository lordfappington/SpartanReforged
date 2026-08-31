# CLOUD GS Texture/Alpha Path

## Scope and result

This bounded investigation follows only LEVEL00 `CLOUD` (MTL index 31) from its MTL resource binding through context-2 `TEX0`, texture-function alpha, alpha test, blending, and depth behavior. The canonical executable is SHA-256 `55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d`; `CLOUD.TM2` is SHA-256 `694a16e09560cc0bbb3eb2469050541fdd092575333f6cb1ca0566459855b58e`.

The former assumption that CLOUD should be translucent is rejected. Its source-derived state produces an opaque, vertex-coloured sky/cloud dome. The white diagnostic shell was caused by omitting the confirmed V4 RGB modulation, not by a missing alpha source.

## Binding and packet path

```text
MODELS.MTL record 31 / resource CLOUD
  -> FUN_0026d2d0 (record/resource parse)
  -> FUN_0026f0e0 or FUN_0026f730
  -> FUN_0025eed0 (TIM2 load and TCC promotion)
  -> FUN_0025fd10 (runtime TEX0 fields and VRAM addresses)
  -> FUN_0026f530 or FUN_0026f3e0
  -> FUN_00258690 (copy selected texture TEX0 to material +0x40)
  -> FUN_00258970 (nine-entry material packet, TEX0_2 destination 0x07)
  -> FUN_0026e700 (material and queued geometry submission)
```

`FUN_00258690` reads the prebuilt 64-bit texture state from the selected loaded-texture record at `texture_table + index * 0x30 + 0x18`. This establishes the MTL-resource-to-TEX0 data flow; the result is not inferred from the material name alone.

## CLOUD texture and TEX0

`CLOUD.TM2` is 256x256 IDTEX8. Its GS runtime storage is PSMT8H (`PSM=0x1b`) with a 256-entry PSMCT32/RGBA8888 CLUT. Every image byte is palette index 255 and every CLUT entry is the same PS2 value `(255,255,255,128)`. Desktop decode expands the PS2 full-scale alpha `0x80` to PNG alpha 255.

The TIM2 header carries TEX0 `0x0000000221b00000`. The loader then assigns dynamic VRAM addresses and changes the address-independent fields. Because `TBP0` and `CBP` are allocator results, there is no single canonical full runtime raw value. Its address-independent form is:

```text
0x2000000621b10000 | TBP0 | (CBP << 37)
```

| TEX0 field | CLOUD value | Confidence |
|---|---:|---|
| TBP0 | dynamic VRAM allocation | CONFIRMED |
| TBW | 4 | CONFIRMED |
| PSM | `0x1b` / PSMT8H | CONFIRMED |
| TW / TH | 8 / 8 (256x256) | CONFIRMED |
| TCC | 1 / RGBA | CONFIRMED |
| TFX | 0 / MODULATE | CONFIRMED |
| CBP | dynamic VRAM allocation | CONFIRMED |
| CPSM | 0 / PSMCT32 | CONFIRMED |
| CSM | 0 / CSM1 | CONFIRMED |
| CSA | 0 | CONFIRMED |
| CLD | 1 | CONFIRMED |

`FUN_0025eed0` explicitly sets TEX0 bit 34 (`TCC=RGBA`). `FUN_0025fd10` sets TBW/TW/TH and CLUT fields, clears TFX to MODULATE, and selects CLD 1.

## Texture function and alpha scale

For TCC=RGBA and TFX=MODULATE, the relevant GS channel operation is the PS2 fixed-point modulation:

```text
Cfragment.rgb = min((Cvertex.rgb * Ctexture.rgb) >> 7, 0xff)
Afragment     = min((Avertex     * Atexture)     >> 7, 0xff)
```

The PS2 conventional full-scale alpha is `0x80`, not desktop `0xff`. For CLOUD:

```text
Avertex  = 0x80       (confirmed V4 -> RGBAQ)
Atexture = 0x80       (PSMCT32 CLUT alpha)
Afragment = (0x80 * 0x80) >> 7 = 0x80
```

The all-white texture also means its RGB is a modulation carrier for the structured V4 RGB/light gradient. A texture-only desktop material necessarily renders white and loses that authored gradient.

## TEXA applicability

TEXA is **CONFIRMED IRRELEVANT** for this texture. CLOUD's CLUT is PSMCT32 and supplies an explicit eight-bit GS alpha value. TEXA alpha expansion applies to source formats without a full alpha channel; it does not replace this CLUT alpha on the recovered RGBA/MODULATE path. TA0, AEM, and TA1 therefore were not needed and were not recovered in this bounded trace.

This distinction is important: PNG alpha 255 and raw PS2 CLUT alpha `0x80` both denote full scale in their respective representations.

## Alpha test, blend, and depth result

CLOUD uses:

- `PRIM.ABE=1`, context 2;
- `ALPHA_2`: `(Cs - Cd) * As + Cd`;
- `TEST_2=0x5380b`: ATE enabled, GEQUAL, AREF `0x80`, AFAIL RGB_ONLY, depth GEQUAL;
- `ZBUF_2.ZMSK=0`: depth writes enabled;
- special material range `[21,total)`, after ordinary range `[4,21)`, with no recovered depth sort.

Since `As=0x80`, every canonical CLOUD fragment passes `As >= AREF`. AFAIL therefore does not run, and the blend equation reduces to `Cs`. CLOUD writes RGB, framebuffer alpha, and depth subject to the normal frame mask.

For completeness, if a context-2 fragment did fail with AFAIL=RGB_ONLY on a 32-bit framebuffer, GS writes RGB while preserving framebuffer alpha and suppressing the failed fragment's depth write. RGB_ONLY is not a discard mode. This failure behavior matters to GREENERY, but not to CLOUD because all CLOUD fragments pass.

## Bounded comparisons

| Material | Texture state | Texture alpha | TEST behavior | Result |
|---|---|---|---|---|
| CLOUD, type 2=5 | RGBA/MODULATE, indexed PSMCT32 CLUT | constant `0x80` | GEQUAL `0x80`, RGB_ONLY | all pass; opaque V4-coloured dome, depth writes |
| GREENERY, type 2=5 | RGBA/MODULATE, indexed PSMCT32 CLUT | varying `0..0x80` | GEQUAL `0x80`, RGB_ONLY | full-alpha texels pass/depth-write; lower alpha blends RGB but preserves alpha/depth |
| GRKTREE, type 2=2 | RGBA/MODULATE, indexed PSMCT32 CLUT | varying `0..0x80` | GEQUAL `0x50`, KEEP | low-alpha texels discarded; cutout-like foliage |

CLOUD does not use a unique texture-function mode. The difference is its uniform white/full-alpha CLUT and the V4 colour gradient.

## Confidence and preservation decision

| Question | Classification |
|---|---|
| CLOUD texture binding to TEX0_2 | CONFIRMED |
| TEX0.TCC / TEX0.TFX | CONFIRMED RGBA / MODULATE |
| TEXA applicability | CONFIRMED IRRELEVANT |
| CLUT alpha entering GS | CONFIRMED constant `0x80` |
| final fragment alpha | CONFIRMED constant `0x80` |
| CLOUD rendering explanation | CONFIRMED opaque vertex-coloured dome |

The LEVEL00 world preservation baseline is now classified **LEVEL00 WORLD RECONSTRUCTION COMPLETE** for this asset-reconstruction milestone. This does not claim a native runtime, complete MTL semantics, exact modern emulation of every GS failure/blend mode, character/effect reconstruction, or resolution of seven special/template texture bindings.

The baseline is frozen: future Reforged work must preserve the original geometry interpretation, source textures, source-derived material/GS semantics, and a reproducible preservation export. Graphical work may proceed independently, but must not overwrite this baseline.

## Reproducibility

`tools/analysis/gs_texture_state_probe.py` hash-locks the canonical executable and CLOUD input, decodes the address-independent TEX0 fields, verifies aggregate TIM2/CLUT content, and evaluates the fixed-point alpha/test result without emitting copyrighted pixels or executable data.

The texture-function and alpha-failure interpretations were cross-checked against PCSX2's [GS register definitions](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/GS/GSRegs.h), [texture-function shader](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/bin/resources/shaders/opengl/tfx_fs.glsl), [software alpha-test implementation](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/GS/Renderers/SW/GSDrawScanline.cpp), and [texture-alpha expansion paths](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/GS/GSBlock.h).
