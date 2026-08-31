# Executable Render-State Investigation

## Scope and outcome

This investigation is limited to the canonical PAL executable's LEVEL00 `MODELS.MTL` material-to-GS path. It does not cover gameplay, AI, characters, saves, general executable reconstruction, or PS2Recomp.

Validated R5900 analysis recovered the required native join:

```text
MTL numeric child type 2
  -> parsed material byte at +0x04
  -> FUN_00257cb0 switch
  -> material TEST_2 and ZBUF_2 packet payloads

MTL numeric child type 16
  -> parsed material byte at +0x12
  -> FUN_00257cb0 switch
  -> material ALPHA_2 packet payload
```

The trace is **CONFIRMED**. Child type 2 is an alpha/depth-test family selector, not the blend-equation selector. Child type 16 selects the recovered `ALPHA_2` construction. CLOUD's material state is consequently source-derived, but its opaque-shell artifact is not yet explained because `PRIM.ABE`, draw ordering, and the final submission context remain unknown. Readiness remains **TEXTURED ASSEMBLY VALIDATED; WORLD RECONSTRUCTION NOT COMPLETE**.

## Executable identity

| Property | Value |
|---|---|
| File | `SLES_533.93` |
| Size | 3,656,280 bytes |
| SHA-256 | `55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d` |
| Format | ELF32, little-endian, machine 8 (`EM_MIPS`), executable |
| Entry point | `0x00200008` |
| ELF flags | `0x20924000` |
| Executable segment | `0x00200000..0x0057c77f` |

The source executable was read only and its hash exactly matches the documented SLES-53393 revision 1.01 build.

## R5900 language installation and reproducibility

The unmodified upstream `chaoticgd/ghidra-emotionengine-reloaded` source was cloned on 2026-08-31 and pinned at commit `ae013ee1475dc970db4fdeba3ec88def6b933d43` (upstream commit date 2026-08-25). It was built against installed Ghidra 12.1.3 using the already-cached Gradle 8.14.3 and JDK 21. The build completed successfully without patching upstream source.

| Setting | Value |
|---|---|
| Ghidra | 12.1.3 |
| Extension source | `https://github.com/chaoticgd/ghidra-emotionengine-reloaded` |
| Extension commit | `ae013ee1475dc970db4fdeba3ec88def6b933d43` |
| Built ZIP | `ghidra_12.1.3_PUBLIC_20260831_ghidra-emotionengine-reloaded.zip` |
| Language ID | `r5900:LE:32:default` |
| Compiler specification | `default` |
| Processor / variant | `MIPS-R5900` / `PS2` |
| Language version | 1.4.0 |
| Project | fresh ignored project under `temp/ghidra/SpartanRenderR5900` |
| Analysis override | `Decompiler Parameter ID=false` |

The first per-user extension-directory attempt was not discovered by headless Ghidra and failed safely before import with `Unsupported language: r5900:LE:32:default`. Installing the same built extension in Ghidra's supported `Ghidra/Extensions` directory succeeded; no stock Ghidra file was overwritten. External source, build output, Ghidra projects, and generated reports remain ignored.

Fresh ELF import reported only bounded layout warnings: zero-length segments at `0x00100000` and `0x00618f80`, zero-size symbol/string sections, and a conflicting synthetic `rom0` block. The executable segment imported and analyzed. The extension's constant-reference and unaligned-instruction analyzers ran; auto-analysis found 7,749 functions in 87 seconds. The SLEIGH compiler logged eight non-fatal NOP-constructor warnings.

Reproduction helpers are:

- `tools/analysis/ghidra/SpartanConfigureR5900Analysis.java` — applies the extension-recommended analyzer override before auto-analysis;
- `tools/analysis/ghidra/SpartanR5900Validation.java` — counts and samples R5900-only instruction families program-wide;
- the existing bounded instruction-window, function-seeding, decompile, and render-survey scripts in the same directory.

## Decoder validation

The fresh program decodes all required instruction families:

| Family | Program-wide decoded count | Representative evidence |
|---|---:|---|
| `LQ` | 15,481 | `0x0026d4d4` in the MTL parser |
| `SQ` | 15,192 | `0x002490d0`, `sq zero,0xc0(a0)`; nine coherent saves at the parser prologue |
| R5900 multimedia/MMI | 501 | `0x00249100`, `pcpyld a1,a1,v0` |
| COP2/VU macro | 3,080 | `qmtc2`, `lqc2`, `vmulax`, `vmadday`, and `sqc2` near `0x00203c1c..0x00203dc0` |

This corrects the stock-MIPS truncation after `0x002491b0`: the graphics-context builder now remains coherent through `0x0024931c`. The result is **VALIDATED R5900 decoding**, not merely improved generic MIPS coverage.

## Relevant function map

| Address | Evidence-backed role | Confidence |
|---|---|---|
| `0x002c3400`, `0x002c345c` | construct/load `\\MODELS.MTL`, then report completion | CONFIRMED |
| `0x002605d0` | calls the MTL-aware parser at `0x0026d2d0` | CONFIRMED |
| `0x0026d2d0` | parses MTL records/children; type 2 is read into the parsed-material byte at `+0x04` | CONFIRMED |
| `0x0026fdc0` | bounded one-byte stream read used for the type-2 value | CONFIRMED |
| `0x0026ce60`, `0x0026d150` | initialize 66 runtime material slots, each `0x430` bytes | CONFIRMED structure/count |
| `0x00258970` | constructs a nine-entry context-2 material GS packet | CONFIRMED |
| `0x00257cb0` | maps parsed type 2 to runtime `TEST_2`/`ZBUF_2` and type 16 to `ALPHA_2` | CONFIRMED |
| `0x002490c0` | generic paired graphics-context GS packet initializer | CONFIRMED; supersedes the earlier material-builder label |

`FUN_00258970` creates A+D destinations for `TEX1_2` (`0x15`), `TEX0_2` (`0x07`), `TEST_2` (`0x48`), `ZBUF_2` (`0x4f`), `ALPHA_2` (`0x43`), `PRMODECONT` (`0x1a`), and `PRMODE` (`0x1b`). `FUN_00257cb0` writes packed payloads at runtime-material offsets `+0x50` (`TEST_2`), `+0x60` (`ZBUF_2`), and `+0x70` (`ALPHA_2`).

The generic GS layouts below were cross-checked against [gsKit packing macros](https://github.com/ps2dev/gsKit/blob/master/ee/gs/include/gsInit.h) and [PCSX2 GS register definitions](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSRegs.h). Those sources establish generic register meanings; the executable trace establishes Spartan's values.

## Recovered TEST and depth families

`TEST` fields are ATE bit 0, ATST bits 1–3, AREF bits 4–11, AFAIL bits 12–13, DATE/DATM bits 14/15, ZTE bit 16, and ZTST bits 17–18. `ZBUF.ZMSK` is bit 32. `DATE=0` and `DATM=0` in every recovered branch.

| Type 2 | Raw `TEST_2` | Alpha test | Failure action | Depth test | Depth write | Confidence |
|---:|---:|---|---|---|---|---|
| absent / 0 | `0x5050a` | disabled; encoded ATST `GEQUAL`, AREF `0x50` | `KEEP` | enabled, `GEQUAL` | enabled | CONFIRMED |
| 1 | `0x50809` | `EQUAL`, AREF `0x80` | `KEEP` | enabled, `GEQUAL` | enabled | CONFIRMED |
| 2 | `0x5050b` | `GEQUAL`, AREF `0x50` | `KEEP` | enabled, `GEQUAL` | enabled | CONFIRMED |
| 3 | `0x53001` | `NEVER`, AREF `0x00` | `RGB_ONLY` | enabled, `GEQUAL` | **disabled** (`ZMSK=1`) | CONFIRMED for LEVEL00 child-17 value 0 |
| 4 | `0x33001` | `NEVER`, AREF `0x00` | `RGB_ONLY` | enabled, `ALWAYS` | **disabled** (`ZMSK=1`) | CONFIRMED |
| 5 | `0x5380b` | `GEQUAL`, AREF `0x80` | `RGB_ONLY` | enabled, `GEQUAL` | enabled | CONFIRMED |

Type 3 also contains a child-type-17-controlled alternate (`ATST=GREATER`, AREF `0x32`, `AFAIL=RGB_ONLY`), but the reviewed LEVEL00 type-17 values are zero. `ZBUF` base pointer and pixel storage mode come from runtime graphics globals, so only `ZMSK` is material-family-derived here.

## Recovered ALPHA families

`ALPHA` packs A/B/C/D in bits 0–7 and FIX in bits 32–39. For A, B, and D, selectors 0/1/2 mean `Cs`/`Cd`/zero; for C they mean `As`/`Ad`/`FIX`.

| MTL child type 16 | Raw `ALPHA_2` | Symbolic equation | Confidence |
|---:|---:|---|---|
| absent or 0 | `0x0000008000000044` | A=`Cs`, B=`Cd`, C=`As`, D=`Cd`: `(Cs-Cd)*As+Cd` | CONFIRMED |
| 1 | `0x0000008000000048` | A=`Cs`, B=zero, C=`As`, D=`Cd`: `Cs*As+Cd` | CONFIRMED |
| 2 | inherited payload retained | exact inherited equation not classified | UNKNOWN |

FIX is `0x80` in both explicitly constructed modes, but C selects `As`, so FIX is not used by either recovered equation. This directly disproves the earlier hypothesis that child type 2 alone selects additive blending.

## Material-state anchors

| Material/family | Child 2 | Child 16 | Native state recovered |
|---|---:|---:|---|
| `GRKTREE` | 2 | absent | TEST `0x5050b`; depth write enabled; standard-alpha ALPHA payload |
| `APP_BLOOD_02` | 3 | 0 | TEST `0x53001`; depth writes disabled; standard-alpha equation |
| `APP_FIRE_BASE` | 3 | 1 | TEST `0x53001`; depth writes disabled; additive/source-alpha equation |
| `RING_GLOW` | 3 | absent | TEST `0x53001`; depth writes disabled; standard-alpha equation |
| `FLARE_NOZREAD` | 4 | 1 | TEST `0x33001`; depth test `ALWAYS`; depth writes disabled; additive/source-alpha equation |
| `GREENERY` | 5 | absent | TEST `0x5380b`; depth writes enabled; standard-alpha equation |
| `CLOUD` | 5 | absent | TEST `0x5380b`; depth writes enabled; standard-alpha equation |

Type 2 therefore determines only part of the state. Type 16 independently refines the blend equation, and type 17 refines one type-3 alpha-test branch.

## CLOUD result

CLOUD (MTL index 31) takes the type-2=5/type-16-default path:

- `ALPHA_2`: A=`Cs`, B=`Cd`, C=`As`, D=`Cd`, FIX=`0x80` (FIX unused);
- `TEST_2`: ATE on, ATST `GEQUAL`, AREF `0x80`, AFAIL `RGB_ONLY`, ZTE on, ZTST `GEQUAL`;
- `ZBUF_2`: depth writes enabled (`ZMSK=0`);
- `PRIM.ABE`: UNKNOWN;
- `TEXA`, `PABE`, `FBA`: not recovered on this bounded path;
- draw bucket/order: UNKNOWN.

The material packet does **not** select additive blending for CLOUD. Its source texture and likely vertex alpha are both full, so this state alone does not explain the opaque shell. The remaining explanation must be sought in `PRIM.ABE`, ordering/submission context, camera/effect usage, or another state outside the recovered material payload. No speculative glTF mapping or Blender validation was added.

## V4 and VU boundary

The trace did not naturally establish V4 routing into GS `RGBAQ`; V4 remains **LIKELY** vertex colour/light modulation. R5900 COP2/VU macro decoding is validated, but no VU microprogram analysis was necessary to recover the material-to-GS state and none was started. There is therefore no unavoidable VU boundary or program region to report for this completed join.

## Confidence and readiness

| Question | Classification |
|---|---|
| MTL type-2 data flow | **CONFIRMED** |
| V4 -> GS RGBAQ | **LIKELY** |
| type-2 = 2 state | **CONFIRMED TEST/ZMSK; ABE/order UNKNOWN** |
| type-2 = 3 state | **CONFIRMED TEST/ZMSK; ALPHA depends on type 16** |
| type-2 = 4 state | **CONFIRMED TEST/ZMSK; ALPHA depends on type 16** |
| type-2 = 5 state | **CONFIRMED TEST/ZMSK; not a unique blend family** |
| CLOUD native blend payload | **CONFIRMED standard-alpha ALPHA payload; ABE UNKNOWN** |
| CLOUD depth behavior | **CONFIRMED depth test GEQUAL and depth writes enabled** |
| alpha-test thresholds | **CONFIRMED per recovered TEST family** |

Readiness stays **TEXTURED ASSEMBLY VALIDATED**. `LEVEL00 WORLD RECONSTRUCTION COMPLETE` is not justified because the source-derived state still does not explain CLOUD's opaque shell and per-submission blend enable/order remain unknown.

The single next task should trace only the runtime material packet from `FUN_00257cb0`/`FUN_00258970` into geometry submission far enough to recover `PRIM.ABE` and CLOUD's draw bucket/order. Stop at a bounded VU program if those controls are delegated there.
