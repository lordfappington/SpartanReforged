# MODELS.BIN Structural Format

Analysis completed on 2026-08-30 against the already-extracted canonical PS2 PAL LEVEL00 resource. No archive was opened during this task. All inputs were read-only, no geometry was exported or rendered, and this document describes evidence rather than a production parser.

## File identity

| Property | Value |
|---|---|
| Path | `DATA/ENV/LEVEL00/WORLD/MODELS.BIN` |
| Size | 2,293,536 bytes (`0x22ff20`) |
| SHA-256 | `8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3` |
| Byte order | Little-endian, **CONFIRMED** by the exact-size field, coherent descriptor table, float ranges, and VIF words |
| Standalone magic | None |
| Git state | Ignored/untracked game data |

The full first and final `0x100` bytes are captured locally by `models_family_probe.py`. Concise samples are used here:

```text
000000: 20 ff 22 00  0f 00 00 00  3a 05 00 00  30 00 00 00
000010: 1e 00 00 00  00 00 00 00  00 00 00 00  00 00 00 00
000020: c0 53 00 00  80 06 00 00  ff ff 00 00  0b 00 00 00
000030: 40 5a 00 00  a0 04 00 00  ff ff 00 00  0b 00 00 00
...
22ff00: 7e 79 65 80  7f 7c 66 80  7a 75 5f 80  7c 76 60 80
22ff10: 7c 76 60 80  7c 76 61 80  7f 7c 66 80  00 00 00 15
```

The final word is the last batch's `MSCALF 0` command, not a separate footer.

## Global header

| Offset | Size | Type | Meaning | Confidence | Evidence |
|---:|---:|---|---|---|---|
| `0x00` | 4 | u32 LE | File size (`0x22ff20`) | **CONFIRMED** | Equals physical file size exactly |
| `0x04` | 4 | u32 LE | Value 15 | **UNKNOWN** | No independent count correlation established |
| `0x08` | 4 | u32 LE | Descriptor count (1,338) | **CONFIRMED** | `0x20 + 1338 × 16 = 0x53c0`, exactly the first payload offset |
| `0x0c` | 4 | u32 LE | Value 48 | **UNKNOWN** | Does not equal the 55 MTL records or 39 used material IDs |
| `0x10` | 4 | u32 LE | Value 30 | **UNKNOWN** | No safe cross-file interpretation |
| `0x14` | 12 | bytes | Zero/reserved | **CONFIRMED value; UNKNOWN purpose** | All zero in LEVEL00 |
| `0x20` | `0x53a0` | 1,338 × 16 | Descriptor table | **CONFIRMED** | Every descriptor resolves to a bounded, aligned VIF block |

## Descriptor record

| Relative offset | Size | Type | Meaning | Confidence | Evidence |
|---:|---:|---|---|---|---|
| `+0x00` | 4 | u32 LE | Absolute block offset | **CONFIRMED** | Monotonic, 16-byte aligned, first equals table end |
| `+0x04` | 4 | u32 LE | Block byte size | **CONFIRMED** | All extents are 16-byte aligned, contiguous, non-overlapping, and end at EOF |
| `+0x08` low | 2 | u16 LE | Secondary/group ID or `0xffff` sentinel | **LIKELY ID; semantics UNKNOWN** | 1,273 sentinels; 65 numbered values occur in the unindexed partition |
| `+0x0a` | 2 | u16 LE | Ordered MTL record index | **CONFIRMED relationship** | Values map directly to meaningful `MODELS.MTL` names; independently reinforced by STL's MTL indices |
| `+0x0c` | 4 | u32 LE | Value 11 or 0 | **UNKNOWN** | 1,313 records use 11 and 25 use 0; no safe render-state meaning yet |

All 1,338 descriptor extents are contiguous. There is no separate unreferenced data region after the table.

## Supported segment map

| Range | Size | Contents | Confidence |
|---|---:|---|---|
| `0x000000–0x000020` | 32 | Global header | **CONFIRMED** |
| `0x000020–0x0053c0` | 21,408 | 1,338 fixed 16-byte descriptors | **CONFIRMED** |
| `0x0053c0–0x0776e0` | 467,744 | 114 VIF blocks not indexed by AAB | **CONFIRMED partition; role LIKELY special/dynamic/effect geometry** |
| `0x0776e0–0x22ff20` | 1,804,352 | 1,224 VIF blocks indexed exactly once by AAB | **CONFIRMED partition; role LIKELY static world geometry** |

The two payload partitions differ independently:

- descriptors 0–113 have block-header flag `0x00010000`, use MTL IDs 0–4, 22–32, 37–39, and 49, and are absent from AAB;
- descriptors 114–1337 have block-header flag zero, use MTL IDs 5–20 and 33–35, and are enumerated exactly once by AAB leaf lists.

This is stronger than a naming-only model: it is an explicit numerical split between special/dynamic resources and spatially indexed world resources.

## Block and VIF batch structure

Each descriptor block starts with a 16-byte wrapper:

| Relative offset | Size | Type | Meaning | Confidence |
|---:|---:|---|---|---|
| `+0x00` | 4 | u32 LE | VIF batch count, 1–27 | **CONFIRMED**; equals parsed batch count in every block |
| `+0x04` | 4 | u32 LE | Partition flag: `0x00010000` or 0 | **CONFIRMED value; LIKELY special/static discriminator** |
| `+0x08` | 4 | u32 LE | Constant 69 (`0x45`) | **UNKNOWN** |
| `+0x0c` | 4 | u32 LE | Constant 69 (`0x45`) | **UNKNOWN** |

The remainder parses end-to-end as 2,128 repeated PS2 VIF batches. No recovery scan or guessed boundary is needed.

| Order | VIF command | Payload | Supported interpretation | Confidence |
|---:|---|---|---|---|
| 1 | `STCYCL 1,1` | none | One-to-one source/destination vector cycle | **CONFIRMED command** |
| 2 | `UNPACK V4-32`, NUM=2 | 32 bytes | Two identical control vectors: packet span, vertex count, `0x8000`, zero | **CONFIRMED layout; field semantics LIKELY** |
| 3 | `UNPACK V4-32`, NUM=N | `16N` bytes | XYZ float positions plus u32 control value | **CONFIRMED layout; position role LIKELY/strong** |
| 4 | `UNPACK V2-16`, NUM=N | `4N` bytes | Signed Q4.12 normalized UV pair | **CONFIRMED for LEVEL00** |
| 5 | `UNPACK V4-8`, NUM=N | `4N` bytes | Unsigned packed four-component attribute; fourth byte is always `0x80` | **CONFIRMED layout; semantic role UNKNOWN** |
| 6 | `MSCALF 0` | none | Execute/continue VU microprogram at address zero with flush | **CONFIRMED command and VU relationship** |
| 7 | zero to two `NOP` words | none | 16-byte batch/block padding | **CONFIRMED** |

Every batch uses the same N for positions, V2-16 values, and V4-8 values. The 2,128 block-preamble counts all agree with the subsequent position UNPACK count.

### Position/control W field

Within each 16-byte V4-32 streamed position record, XYZ occupy relative offsets `+0x00`, `+0x04`, and `+0x08`; the u32 control word is at `+0x0c` (**CONFIRMED layout**). Across 88,314 records it has only two values: zero 46,336 times and `0x00008000` 41,978 times (**CONFIRMED values/frequency**). Every batch's first two records are `0x8000`. Of 37,722 later flags, 37,588 occur in 18,794 two-record runs and 134 occur singly.

Pinned PCSX2 GS source defines packed XYZ ADC through the `0x8000` bit and shows that it suppresses the primitive ending at the current vertex while retaining and advancing triangle-strip history. Spartan's field produces precisely the control patterns and coherent connectivity expected from that behavior. The literal routing from this VU input record to GIF XYZ ADC is **LIKELY with strong evidence**, because the responsible VU microprogram is not embedded here. Its topology effect in LEVEL00 is **CONFIRMED operationally**: `0x8000` suppresses only the current triangle, does not restart, and still advances source parity/history; zero emits.

## Geometry and topology control

- Total streamed vertex instances: **88,314** across 2,128 batches.
- Batch size: **3–74** vertices.
- XYZ ranges: X `-176.0..175.999954`, Y `-12.383148..156.970108`, Z `-176.0..175.999954`.
- The position W word is always either zero or `0x8000`.
- The first two vertices of every batch carry `0x8000`; additional `0x8000` values occur inside batches.
- Counts are 46,336 zero control words and 41,978 `0x8000` control words.
- Signed V2-16 ranges are U `-32763..32734` and V `-32758..32757`. They decode as signed Q4.12 normalized coordinates: `u = int16(raw_u) / 4096`, `v = int16(raw_v) / 4096`. Texture-space coordinates are obtained by multiplying by the bound TIM2 width/height. There is no global half-texel bias. Values outside `0..1` are intentional and must be preserved for material sampler handling. Full evidence is in [MODELS_UV_FORMAT.md](MODELS_UV_FORMAT.md).
- V4-8's fourth component is `0x80` for all 88,314 vertices; the first three components remain semantically unresolved.

Complete control-pattern and geometric analysis now establishes implicit triangle strips. `0x8000` suppresses the primitive ending at that vertex while the vertex remains in the rolling three-vertex history; zero emits. It does not reset the strip. Parity follows every submitted source vertex, including suppressed vertices. This yields exactly **46,336** triangles, equal to the zero-W count, with no bad index references, three exact zero-area triangles, and eight doubled-area values at or below `1e-6`.

Internal control structure is decisive: 37,588 of the 37,722 internal flags occur in 18,794 two-vertex runs. These suppress two bridge triangles while seeding the next face with a new two-vertex history. Only 134 internal flags are isolated. Full evidence, candidate-model comparisons, winding convention, and pseudocode are in [MODELS_TOPOLOGY.md](MODELS_TOPOLOGY.md).

No independent u16/u32 index-buffer segment exists: the entire post-table payload is consumed by valid VIF streams. Any topology is therefore implicit in stream order/control or produced by the VU program.

## PS2-specific evidence

The VIF classification is **CONFIRMED**, not a byte-pattern guess:

- all 1,338 blocks parse from their declared start to declared end;
- all 2,128 batches use coherent STCYCL and UNPACK commands with exact payload sizes;
- corresponding attribute counts agree;
- each batch ends in `MSCALF 0` and optional alignment NOPs;
- no unknown VIF command is needed to complete any block.

This confirms VIF-fed, VU-related world rendering data. No `MPG` command embeds a VU microprogram, and no independently validated DMA tag or GIFtag stream was found. GIF/DMA structure must therefore remain **UNKNOWN/ABSENT FROM CURRENT EVIDENCE**.

## Strings and material references

MODELS.BIN has no string table and contains no exact `MODELS.MTL` name. Apparent short printable runs are accidental interpretations of float/packed data. Material binding is numeric: descriptor `+0x0a` selects an ordered MTL record. Thirty-nine distinct MTL indices from 0 through 49 are used.

This establishes the supported chain:

```text
BIN descriptor
  -> u16 ordered MTL index
    -> MTL resource record / type-0 resource stem
      -> same-named or explicitly aliased TM2/config resource
```

Examples include index 5 → `002`, 7 → `BASEWALL`, 12 → `TEMPLE_FLAGS`, 33 → `GRKTREE`, and 35 → `GREENERY`. The AAB-indexed static partition uses only world-facing records 5–20 and 33–35.

## Entropy, alignment, and zero regions

- Header entropy: 1.5613 bits/byte.
- Descriptor-table entropy: 3.8760 bits/byte.
- VIF payload entropy: 6.4575 bits/byte.
- `0x1000`-window entropy spans 3.6981–6.6509 bits/byte.
- Sixteen zero runs of at least 64 bytes occur, totaling 4,232 bytes; the maximum is 268 bytes. They lie inside declared VIF blocks in the special partition and are payload content, not segment gaps.
- Descriptor offsets, sizes, data boundaries, and whole-file size are all 16-byte coherent.

## Tentative schema status

The global header, descriptor table, block boundaries, VIF command grammar, attribute stream widths, numeric MTL binding, AAB static-descriptor partition, triangle topology, and V2-16 UV decode are established strongly enough for a bounds-checked first geometry exporter.

Readiness is **GEOMETRY READY** for a first read-only export that preserves source coordinates, winding, material groups, and signed normalized UV values. This does not mean the format is complete: V4-8 semantics, exact MTL sampler/property states, target-renderer V orientation/front-face conversion, and the literal VU-to-GS dataflow remain unresolved. V4-8 is not required to export positions, topology, material assignment, and usable UVs.

The first strict parser and glTF reconstruction now validate this readiness operationally. All 1,338 descriptors parse through independent bounds checks and export as traceable descriptor meshes containing 88,314 source records and exactly 46,336 triangles. See [MODELS_EXPORT_PIPELINE.md](MODELS_EXPORT_PIPELINE.md). This is a geometry reconstruction milestone, not proof of native material or rendering fidelity.

## Outstanding questions

- What do global-header values 15, 48, and 30 represent?
- What is the descriptor low-u16 secondary ID, and why is it populated for only 65 special descriptors?
- What does descriptor field `+0x0c` (11/0) control?
- Are the two block constants `0x45` VU layout/program identifiers, and where is the actual VU microprogram supplied?
- Where is the VU microprogram that routes the strongly ADC-like position W field to the GS?
- Which MTL properties select repeat, mirror, or clamp for each material?
- Does the VU program multiply Q4.12 values by texture dimensions and 16 exactly as inferred before writing GS UV, or perform equivalent rounding/offset operations?
- Is V4-8 normal, color/lighting, or another packed attribute?
- How do the unindexed special blocks obtain transforms/instances at runtime?
