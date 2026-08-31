# Executable Render-State Investigation

## Scope and result

This is a bounded investigation of the canonical PAL executable's LEVEL00 material-loading and PS2 GS-state paths. It does not cover gameplay, AI, characters, saves, or general executable reconstruction.

The investigation found two reproducible native anchors:

1. the LEVEL00 `MODELS.MTL` load/deserialization path; and
2. a low-level paired-context packet builder containing `TEST_1/2`, `ALPHA_1/2`, and `ZBUF_1/2` register destinations.

It did **not** recover the required material-child-to-GS-state join. Consequently no type-2 value, CLOUD blend equation, fixed alpha, alpha-test threshold, depth state, or draw bucket is promoted from correlation to native fact. Readiness remains **TEXTURED ASSEMBLY VALIDATED; WORLD RECONSTRUCTION NOT COMPLETE**.

## Executable identity

| Property | Value |
|---|---|
| File | `SLES_533.93` |
| Size | 3,656,280 bytes |
| SHA-256 | `55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d` |
| Format | ELF32, little-endian, machine 8 (`EM_MIPS`), executable |
| Entry point | `0x00200008` |
| ELF flags | `0x20924000` |
| Loaded segment | `0x00200000..0x0057c77f`, 3,655,552 file bytes, RWX |

The file hash exactly matches the documented SLES-53393 revision 1.01 executable. The source file was read only and remained unchanged.

## Ghidra import and limitations

Ghidra 12.1.3 was run headlessly in an ignored project beneath `temp/ghidra`. The closest stock processor configuration was:

- language: `MIPS:LE:64:64-32addr`;
- compiler specification: `o32`;
- image base: `0x00100000` as imported, with the executable segment at `0x00200000`;
- bounded analyzers: instruction/function discovery, references, constants, strings, call graph, switches, and decompiler.

Auto-analysis identified 6,963 functions over the executable segment. A preliminary `MIPS:LE:32:default` import was discarded for analysis because it decoded substantially less of the R5900 program.

Stock Ghidra has no Emotion Engine/R5900 language in this installation. Its MIPS specification explicitly does not support COP2, and it does not decode the R5900 `LQ`, `SQ`, and multimedia instructions that occur at the critical boundaries. Those gaps split real functions, truncate control flow, lose live register/stack state, and make the decompiler unsuitable for the required end-to-end proof. This is visible in both the MTL deserializer around `0x0026d2d0` and the GS packet writer after `0x002491b0`.

Small reproducible Ghidra scripts live under `tools/analysis/ghidra`. Generated projects, listings, candidate tables, and decompiler output remain ignored under `temp`.

## Relevant function and address map

| Address | Stock name / bounded label | Evidence-backed role | Confidence |
|---|---|---|---|
| `0x002c3400` | seeded loader chunk | constructs the `\\MODELS.MTL` path at `0x002c3414/0x002c341c` | CONFIRMED |
| `0x002c345c` | seeded loader continuation | builds localized `DATA\\TEXT\\%s`, calls `0x002605d0`, then logs `after loading MODELS.MTL` at `0x002c34a8/0x002c34b4` | CONFIRMED |
| `0x002605d0` | seeded deserialization entry | calls `FUN_0026d2d0(param+0x150)`, then reads a u16 through `FUN_0026ce40` | CONFIRMED call path; object semantics UNKNOWN |
| `0x0026ce40` | `FUN_0026ce40` | returns `u16[param + 0x1160c + index*2]` | CONFIRMED access; field meaning UNKNOWN |
| `0x0026d2d0` | `FUN_0026d2d0` | large stream/deserialization routine using bounded reads and indirect callbacks | LIKELY generic asset deserializer |
| `0x002490c0` | `FUN_002490c0` | constructs paired GS-context state packet slots including TEST, ALPHA, and ZBUF destinations | CONFIRMED low-level GS packet builder |
| `0x00249b40` | `FUN_00249b40` | calls `0x002490c0`, `0x00249680`, and `0x002498e0` during graphics-context setup | CONFIRMED setup path; material role not shown |
| `0x00260680` | `FUN_00260680` | only identified caller of `0x00249b40`; initializes graphics state | CONFIRMED |
| `0x00553680` | profiler-label initializer | materializes `vu1 render` at `0x005536ac/0x005536bc` | CONFIRMED label use; no material data flow |

The executable strings `\\MODELS.MTL` (`0x005103e8`), `after loading MODELS.MTL` (`0x0052bf15`), and `vu1 render` (`0x00532fba`) support these anchors. Ghidra did not create all string references automatically; the MIPS `LUI`/low-half materializations were checked directly.

## GS packet evidence

`FUN_002490c0` writes the following immediate A+D register identifiers into paired packet slots:

| Instruction | Register ID | Symbolic register |
|---|---:|---|
| `0x00249124` | `0x47` | `TEST_1` |
| `0x00249128` | `0x42` | `ALPHA_1` |
| `0x0024912c` | `0x4e` | `ZBUF_1` |
| `0x00249130` | `0x48` | `TEST_2` |
| `0x00249134` | `0x43` | `ALPHA_2` |
| `0x00249138` | `0x4f` | `ZBUF_2` |

The identifiers and bit layouts agree with the primary ps2sdk/gsKit and PCSX2 GS definitions. Generic GS `ALPHA` is packed as selectors A/B/C/D plus `FIX`; `TEST` contains ATE/ATST/AREF/AFAIL and ZTE/ZTST; `ZBUF` contains ZMSK. This establishes the function's register family, but not the material-specific values placed in those registers. The first undecoded R5900 store occurs immediately after the visible `ALPHA_1` destination at `0x002491b0`, so interpreting subsequent payloads from truncated decompiler output would be unsafe.

References used for generic PS2 meanings:

- [ps2sdk libgs register IDs and test enums](https://github.com/ps2dev/ps2sdk/blob/master/ee/libgs/include/libgs.h)
- [ps2sdk draw packet construction](https://github.com/ps2dev/ps2sdk/blob/master/ee/draw/src/draw.c)
- [gsKit GS ALPHA/TEST/ZBUF packing macros](https://github.com/ps2dev/gsKit/blob/master/ee/gs/include/gsInit.h)
- [PCSX2 GS register definitions](https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSRegs.h)

These references describe generic PS2 state only. They do not establish Spartan's material mapping.

## MTL type-2 data flow

The required proof standard was:

```text
MTL numeric child type 2
  -> runtime material field
  -> render branch or preset
  -> GS state payload/write
```

Only the first and final regions can currently be anchored. The path between them crosses the unsupported R5900-heavy deserializer and later VU/packet submission code. No comparison or switch on values 2, 3, 4, or 5 was accepted as material-related without runtime-object data flow. The GS builder's only observed caller chain leads through graphics-context initialization, so it cannot itself be assigned to CLOUD or a type-2 family.

The u16 table access at `0x0026ce40` is not labelled as type 2: its index argument is one, and no evidence joins its returned value to a MODELS.MTL child type or GS state.

## Material-state table

| MTL family | ABE | ALPHA A/B/C/D/FIX | Alpha test / AREF | Depth test | Depth write | Draw bucket | Confidence |
|---|---|---|---|---|---|---|---|
| type-2 = 2 (`GRKTREE`) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | asset correlation only |
| type-2 = 3 (blood/fire/ring glow) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | asset correlation only |
| type-2 = 4 (`FLARE_NOZREAD`) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | name is a clue, not code proof |
| type-2 = 5 broad family | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | mixed asset family |
| type-2 = 5 / `CLOUD` | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | no native branch/preset recovered |

No additional MTL field was proven to refine type 2. `PRIM.ABE`, `TEXA`, `PABE`, `FBA`, alpha threshold, ZMSK, and ordering remain unknown for these materials.

## CLOUD and V4 conclusions

No executable-level CLOUD-specific branch was recovered. The prior asset evidence remains valid: CLOUD's image alpha is opaque, V4 byte 3 is full-scale `0x80`, and bytes 0–2 supply a structured intensity/color gradient. The executable investigation does not yet prove that V4 reaches GS `RGBAQ`; that routing remains **LIKELY**, not confirmed.

An additive-family diagnostic can remove the shell, but no native `ALPHA` operands or `FIX` value were recovered. Therefore no Blender validation, target-neutral `SpartanRenderState`, or glTF mapping was added in this task. Existing experimental exports remain explicitly non-native diagnostics.

## Confidence and readiness

| Question | Classification |
|---|---|
| MTL type-2 data flow | UNKNOWN |
| V4 -> GS RGBAQ | LIKELY from asset behavior; not executable-confirmed |
| type-2 = 2 native state | UNKNOWN |
| type-2 = 3 native state | UNKNOWN |
| type-2 = 4 native state | UNKNOWN |
| type-2 = 5 native state | UNKNOWN |
| CLOUD native blend | UNKNOWN |
| CLOUD depth behavior | UNKNOWN |
| alpha-test threshold | UNKNOWN |

Readiness stays **TEXTURED ASSEMBLY VALIDATED**. `LEVEL00 WORLD RECONSTRUCTION COMPLETE` is not justified.

## Exact blocker and next task

The exact blocker is the absence of a validated R5900/Emotion Engine Ghidra language covering `LQ`, `SQ`, multimedia instructions, and the relevant COP2/VU transfers. Stock MIPS64 recovers useful address anchors but cannot preserve the data flow needed for native state claims.

The single next task should add or validate R5900 instruction-language support for this executable and repeat only the bounded trace from `0x0026d2d0` through runtime material storage to the draw packet. If the recovered CPU path delegates the final state selection to a VU1 microprogram, that task should stop and identify the exact upload address and bounded microprogram region for a subsequent VU-only investigation.
