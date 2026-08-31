# LEVEL00 World Render Submission

## Scope and result

This note covers only the canonical LEVEL00 `MODELS` material/geometry submission path in `SLES_533.93`. CPU ordering and the bounded resident VU1 vertex-output route are now recovered; gameplay, characters, unrelated VU programs, and general renderer code were not investigated.

The normal CPU pass groups materials into three stable ranges. Each MODELS batch dispatches resident VU1 entry 0 with `MSCALF 0`. The MODELS-compatible VU path emits a PACKED GIFtag whose embedded `PRIM` is `0x25c`: triangle strip, Gouraud interpolation, texture enabled, blending enabled, ST coordinates, and GS context 2. The streamed V4 tuple is emitted unchanged as the packed `RGBAQ` item.

## CPU queue and submission chain

```text
geometry object
  -> FUN_0026fe70 (queue by material index)
  -> FUN_0026e700 (material packet, then queued geometry chains)
  -> FUN_0026ea70 (normal three-range pass builder)
  -> FUN_002590d0 (chain terminator)
  -> FUN_00258d40 / FUN_00258c70 (start VIF1 DMA)
  -> MODELS VIF batch, MSCALF 0
  -> resident VU1 entry 0
  -> MODELS route 0x110..0x183
  -> PACKED GIFtag and ST/RGBAQ/XYZF2 stream
```

The runtime material manager has 66 slots of `0x430` bytes. `FUN_00258970` constructs the resident nine-entry context-2 state packet during material construction/reset. `FUN_0026e700` emits that packet once for each non-empty material in a built chain, then appends its queued geometry entries; it is not emitted once per descriptor or batch.

## Pass ordering

The normal frame path `FUN_002e0760` selects `FUN_0026ea70`, which emits ascending material indices in three ranges separated by transition packets:

1. `[0,4)`;
2. `[4,21)`;
3. `[21,total)`.

The second boundary is source-derived: MTL child type 15 is stored at parsed-material `+0x14`, and canonical record 21 `AMBIENT_FOLIAGE` has the value that sets manager boundary `+0x115fe`. CLOUD is material 31, so it is in the third/special range, after ordinary records 4–20 and before GRKTREE 33 and GREENERY 35. The recovered loops preserve material-index order and do not distance/depth sort. This is a confirmed relative submission order, not an inferred engine name for the pass.

## Resident program and MODELS route

`FUN_002595b0`, called from renderer initialization `FUN_00260780`, uploads a contiguous resident VU1 program from executable data beginning at VIF MPG command `0x0050488c`. Seven blocks cover micro-addresses `0x000..0x642` (1,603 instructions): six 256-instruction blocks at destinations `0x000..0x500` and a final 67-instruction block at `0x600`. The upload source occupies `0x0050488c..0x00507ad7`; the subsequent VIF unpack installs 11 static VU data qwords, including the MODELS GIFtag template at executable `0x00507b60` / VU memory qword 8. The program is installed during renderer initialization; MODELS batches invoke it rather than carrying `MPG` commands.

The CPU batch ends in `MSCALF 0`, confirming entry address 0. Entry dispatch reaches the MODELS-compatible route at micro `0x110`; the route reads the batch control value `0x8000`, selects VU qword 8, inserts the dynamic vertex count, emits the tag at `0x128`, loads expanded V4 at `0x12c`, and emits it unchanged at `0x141` as the middle item in each three-qword vertex group.

## GIFtag and PRIM

The template is best recorded as its logically constructed fields rather than a naive serialized 128-bit lane order:

```text
TAG0 = vertex_count | 0x8000
TAG1 = 0x312e4000
REGS = 0x0000000000000412
```

| Field | Value | Confidence |
|---|---:|---|
| `PRE` | 1; embedded PRIM applies | CONFIRMED |
| `FLG` | 0, PACKED | CONFIRMED |
| `NREG` | 3 | CONFIRMED |
| registers | `ST`, `RGBAQ`, `XYZF2` | CONFIRMED |
| `PRIM` | `0x25c` | CONFIRMED |
| primitive | 4, triangle strip | CONFIRMED |
| `IIP` | 1 | CONFIRMED |
| `TME` | 1 | CONFIRMED |
| `FGE` | 0 | CONFIRMED |
| `ABE` | 1, blending enabled | CONFIRMED |
| `AA1` | 0 | CONFIRMED |
| `FST` | 0, ST/Q path | CONFIRMED |
| `CTXT` | 1, GS context 2 | CONFIRMED |
| `FIX` | 0 | CONFIRMED |

Every canonical MODELS batch has the same `0x8000` control used to retain this template. No material/type-2-dependent ABE branch was found on this route. Type 2 selects CPU-built `TEST_2`/`ZBUF_2`; child 16 selects `ALPHA_2`; ABE and context are route/template state.

Triangle-strip PRIM corroborates the existing ADC reconstruction. The VU output uses `XYZF2`; no contradiction to the confirmed W/ADC suppression rule was found.

## V4 and effective alpha

VIF command `0x6e` unpacks unsigned V4-8 into four unsigned 32-bit VU lanes. The MODELS route loads this qword and emits it unchanged as the packed `RGBAQ` register item. Therefore V4-to-RGBAQ and byte-3-to-GS-alpha routing are **CONFIRMED**. All 88,314 LEVEL00 MODELS tuples carry byte 3 `0x80`, so the effective vertex alpha is the PS2 full-scale value `0x80`.

The route does not emit `TEX0`, `TEXA`, `PABE`, or `FBA`; those states remain outside this bounded result. `TEX0.TCC/TFX` therefore remain unknown here.

## CLOUD result

| Field | Result | Confidence |
|---|---|---|
| MTL / pass | index 31 / third range `[21,total)` | CONFIRMED |
| `TEST_2` | `0x5380b`: ATE GEQUAL, AREF `0x80`, AFAIL RGB_ONLY, depth GEQUAL | CONFIRMED |
| `ZBUF_2.ZMSK` | 0, depth writes enabled | CONFIRMED |
| `ALPHA_2` | `(Cs-Cd)*As+Cd`; FIX `0x80` unused | CONFIRMED |
| `PRIM.ABE` | 1 | CONFIRMED |
| `PRIM.CTXT` | 1, context 2 | CONFIRMED |
| vertex alpha | V4 byte 3 reaches RGBAQ unchanged as `0x80` | CONFIRMED |
| texture alpha | fully opaque decoded source | CONFIRMED |
| sorting | stable material order; no recovered depth sort | CONFIRMED |
| `TEX0.TCC/TFX`, `TEXA`, `PABE`, `FBA` | not recovered on this VU route | UNKNOWN |

With full effective source alpha, `(Cs-Cd)*As+Cd` reduces to `Cs`. Thus ABE is genuinely enabled, but the recovered texture/V4 inputs and equation still do **not** mathematically make CLOUD translucent. The former additive diagnostic is not source-derived. The remaining bounded blocker is the effective texture-alpha/function state (especially `TEX0.TCC/TFX` or `TEXA`) or a mistaken assumption about CLOUD's intended use/visibility; draw ordering and V4 routing no longer explain the discrepancy.

Readiness remains **TEXTURED ASSEMBLY VALIDATED; WORLD RECONSTRUCTION NOT COMPLETE**.

## Reproducibility

- `tools/analysis/vu1_models_probe.py` verifies the executable hash, reconstructs only the seven MPG blocks, validates the MODELS route landmarks, and symbolically decodes the tag/PRIM without dumping microcode.
- `tools/analysis/ghidra/SpartanVu1ModelsTrace.java` and `SpartanVu1MpgSurvey.java` produce bounded Ghidra address/reference reports.
- Instruction decoding was independently checked with PCSX2's VU1 disassembler source at pinned commit `d073d75010090186b58eb38bfc78dfc2f3acd8c7`; the external source and local build remain ignored.
- Generic VIF unpack and GIF/PRIM definitions were checked against [PCSX2 VIF unpack](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/Vif_Unpack.cpp), [PCSX2 GIF definitions](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/Gif_Unit.h), and [ps2sdk draw code](https://github.com/ps2dev/ps2sdk/blob/master/ee/draw/src/draw3d.c).
