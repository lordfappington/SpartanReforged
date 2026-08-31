# MODELS Resident VU1 Render Path

## Result and boundary

This is a bounded analysis of the resident VU1 route used by LEVEL00 `MODELS` batches. It recovers only program upload/dispatch, the MODELS vertex-input route, GIFtag/PRIM construction, V4/RGBAQ routing, and effective vertex alpha. It is not a general VU1 disassembly.

The canonical executable is SHA-256 `55424814871ed9174cab99a545f384864ace490fa6af2b816130dc2d5482722d`. Ghidra 12.1.3 used `r5900:LE:32:default` with Emotion Engine Reloaded commit `ae013ee1475dc970db4fdeba3ec88def6b933d43`.

## Upload and dispatch

`FUN_002595b0` uploads the resident program during renderer initialization from VIF MPG data at executable address `0x0050488c`. Seven blocks form one contiguous 1,603-instruction program at VU1 micro-addresses `0x000..0x642`; the upload destination starts at 0. Six blocks contain 256 instructions and the seventh contains 67. Static VU data follows, with the relevant GIFtag template at executable `0x00507b60` / VU qword 8.

MODELS packets contain no `MPG`. Their terminal `MSCALF 0` dispatches entry 0. The bounded reachable route used by the documented input layout is micro `0x110..0x183`.

## Input layout and landmarks

Each MODELS batch begins with two matching V4-32 control qwords containing packet span, vertex count, `0x8000`, and zero. Position V4-32 data begins at TOP+2, UV V2-16 begins at TOP+N+2, and unsigned V4-8 begins at TOP+2N+2. The existing parser's 2,128 batches / 88,314 records agree with this layout.

| Micro address | Bounded role |
|---:|---|
| `0x000` | entry/startup |
| `0x014` | batch dispatch |
| `0x073` | layout route leading to `0x110` |
| `0x110` | transfer MODELS control to integer state |
| `0x114` | load VU qword-8 tag template |
| `0x115` | `0x8000` control retains blended/no-fog template |
| `0x120..0x122` | insert dynamic NLOOP and EOP |
| `0x128` | emit GIFtag |
| `0x12c` | load expanded V4 qword |
| `0x141` | emit V4 unchanged as middle packed vertex item |

## GIFtag / PRIM

The constructed tag is `TAG0 = vertex_count | 0x8000`, `TAG1 = 0x312e4000`, and `REGS = 0x412`. It has EOP 1, PRE 1, PACKED mode, NREG 3, register list ST/RGBAQ/XYZF2, and embedded PRIM `0x25c`.

`PRIM 0x25c` is triangle strip, IIP 1, TME 1, FGE 0, ABE 1, AA1 0, FST 0, CTXT 1 (context 2), FIX 0. Since PRE is set, this is the effective primitive state. The common MODELS control/template means ABE does not vary by MTL type-2 family on this route.

## V4 / RGBAQ / alpha

VIF unsigned V4-8 expands each byte into a 32-bit unsigned VU lane. Micro `0x12c` loads that four-lane qword and `0x141` emits it unchanged as the second item described by ST/RGBAQ/XYZF2. In PACKED RGBAQ form, the low byte of each lane supplies R, G, B, and A; this is not a literal 64-bit GS register image.

Therefore V4-to-GS-RGBAQ, bytes 0–2 to RGB, and byte 3 to A are all **CONFIRMED**. Canonical byte 3 `0x80` is full-scale PS2 vertex alpha. The prior distribution-based colour/light-modulation interpretation is strengthened by this confirmed destination, although the authorship semantics remain an interpretation.

## CLOUD consequence

CLOUD uses ABE 1 and context 2 like the rest of this MODELS route. The downstream texture trace confirms TCC=RGBA and TFX=MODULATE. Its PSMCT32 CLUT alpha and vertex alpha are both full `0x80`, producing full fragment alpha `0x80`; the alpha test passes and `(Cs-Cd)*As+Cd` evaluates to `Cs`. CLOUD is therefore an opaque V4-coloured dome, not a missing translucent blend. See [GS_TEXTURE_ALPHA_PATH.md](GS_TEXTURE_ALPHA_PATH.md).

## Confidence

| Finding | Classification |
|---|---|
| resident program identity/upload | CONFIRMED |
| MODELS `MSCALF 0` entry | CONFIRMED |
| MODELS route `0x110..0x183` | CONFIRMED |
| GIFtag construction / register list | CONFIRMED |
| PRIM source, ABE, CTXT, primitive type | CONFIRMED |
| V4 to RGBAQ and alpha routing | CONFIRMED |
| effective CLOUD vertex alpha | CONFIRMED full scale |
| CLOUD rendering explanation | CONFIRMED opaque V4-coloured dome |
| TEX0 TCC/TFX | CONFIRMED RGBA/MODULATE by downstream loader trace |
| TEXA | CONFIRMED irrelevant to CLOUD's PSMCT32 CLUT alpha |
| PABE, FBA | not required for the recovered CLOUD result |

## Reproducibility and provenance

The committed probe reports only aggregate state and instruction landmarks. Raw executable, raw microcode, full disassembly, Ghidra databases, and external reference source remain ignored. Decoder behavior was checked against [PCSX2's VU1 disassembler](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/DebugTools/DisVU1Micro.cpp) and its [VIF unpack implementation](https://github.com/PCSX2/pcsx2/blob/d073d75010090186b58eb38bfc78dfc2f3acd8c7/pcsx2/Vif_Unpack.cpp).
