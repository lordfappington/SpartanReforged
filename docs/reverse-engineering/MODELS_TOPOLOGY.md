# MODELS.BIN Triangle Topology

This analysis was completed on 2026-08-30 against the already-extracted canonical PS2 PAL LEVEL00 `MODELS.BIN`, `MODELS.AAB`, and `MODELS.MTL`. No PAK was opened. The three inputs were read-only; no geometry was exported, rendered, converted, or modified.

## Result and readiness

**Readiness: TOPOLOGY READY.** The supported reconstruction is an implicit triangle strip per VIF batch. A position W word of `0x8000` suppresses the primitive ending at that vertex while retaining the vertex in the rolling strip history. It does not reset history. A zero W word emits the triangle. Alternating parity follows every submitted source vertex, including suppressed vertices.

This establishes connectivity and relative winding. It does **not** make the format geometry-ready: V2-16 scaling/wrapping and V4-8 semantics remain unresolved, MTL property semantics are partial, and the VU program that routes the field to the GS was not present in these batches. The absolute front-face convention is also not observable from GS behavior because the GS has no conventional back-face culling state; reversing every triangle remains a global convention choice.

## Canonical inputs

| File | Size | SHA-256 |
|---|---:|---|
| `MODELS.BIN` | 2,293,536 | `8d091d4104fa556ccff90d78d3feb9ea1b656356f2fabc667a8457c1382e4cf3` |
| `MODELS.AAB` | 448,048 | `ce46a8c58509d74ceeabedf22d1832dcd365c87d2f8bc583120f1f37797e99d7` |
| `MODELS.MTL` | 5,952 | `57283516fc3cc8589eec4817cf8c25dc3ff0cc2185e4ff99e262fa6f3a4a54b2` |

## Input and VIF batch structure

`MODELS.BIN` has 1,338 fixed 16-byte descriptors, each selecting one MTL record and bounding one VIF block. The blocks contain 2,128 independent batches. Each batch uses `STCYCL 1,1`, a duplicated V4-32 control preamble, N V4-32 records containing float XYZ plus u32 W/control, N V2-16 signed pairs, N V4-8 attributes, and `MSCALF 0` with optional alignment NOPs. All three per-vertex streams agree on N. The W/control word is the fourth dword at position-record offset `+0x0c`.

## Generic PS2 ADC behavior

No local specification/source copy containing the required primitive-state detail was found, so the behavior was checked against the PCSX2 GS implementation pinned at commit `c10a5c9ad951c517dc48b722b5b84eb9bf7fdb42`:

- [`GSRegs.h`](https://github.com/PCSX2/pcsx2/blob/c10a5c9ad951c517dc48b722b5b84eb9bf7fdb42/pcsx2/GS/GSRegs.h#L1041-L1067) defines packed XYZF2/XYZ2 ADC and tests `U32[3] & 0x8000`.
- [`GSState.cpp`](https://github.com/PCSX2/pcsx2/blob/c10a5c9ad951c517dc48b722b5b84eb9bf7fdb42/pcsx2/GS/GSState.cpp#L1438-L1471) passes that result to `VertexKick` as `skip`.
- [`VertexKick`](https://github.com/PCSX2/pcsx2/blob/c10a5c9ad951c517dc48b722b5b84eb9bf7fdb42/pcsx2/GS/GSState.cpp#L5832-L5985) stores the vertex and advances the vertex tail before evaluating `skip`; for a skipped triangle-strip primitive it advances `head` by one and returns.
- The normal triangle-strip path then consumes the rolling `head`, `head+1`, `head+2` window and advances `head` by one ([source](https://github.com/PCSX2/pcsx2/blob/c10a5c9ad951c517dc48b722b5b84eb9bf7fdb42/pcsx2/GS/GSState.cpp#L6004-L6057)).

The generic conclusion is therefore exact: ADC suppresses the primitive that would end at the current vertex; it is not a strip restart, the vertex remains in history, and the rolling window advances by one. Consequently strip parity also advances once. Two consecutive ADC vertices suppress two bridge triangles and seed the next emitted triangle with a new two-vertex history. An isolated ADC advances parity once; a two-ADC run advances it twice and preserves the previous parity phase.

## Spartan evidence

The PS2 rule above is generic. Its application to Spartan is supported independently by the complete LEVEL00 data:

- all 88,314 position W words are exactly zero or `0x8000`;
- all 2,128 batches begin with at least two `0x8000` words;
- there are 46,336 zero words and 41,978 `0x8000` words;
- after removing the mandatory first two per batch, 37,722 internal flags remain;
- 37,588 internal flags form 18,794 exact two-vertex runs; only 134 are isolated;
- the two-flag pattern suppresses bridge triangles while retaining the two new vertices needed to emit the first triangle of the next strip segment;
- 3,517 internal flagged vertices duplicate one of the preceding two positions, consistent with strip stitching;
- 476 adjacent batches within a descriptor repeat the preceding batch's final two positions at the next batch's start;
- the spec model emits exactly 46,336 triangles—one for every zero-W vertex—and has no out-of-range or repeated-index triangle.

The missing VU microprogram means the literal W-to-GIF-register dataflow is not directly visible here. Accordingly, “W is routed to GS ADC” is **LIKELY with very strong convergent evidence**, while the reconstructed topology rule is operationally established across every batch.

## Complete pattern classification

| Pattern class | Batches | Definition |
|---|---:|---|
| Initial flags only | 99 | First two ADC words, no later ADC |
| Consecutive only | 1,895 | Internal ADC occurs only in runs of two |
| Isolated only | 2 | Internal ADC occurs only singly |
| Mixed isolated/consecutive | 132 | Both forms occur |

There are 873 distinct run-length strings across the 2,128 batches. The only internal ADC run lengths are one (134 runs) and two (18,794 runs); the maximum is exactly two. The complete per-batch classification and run-length strings are generated locally in `logs/analysis/MODELS_topology_batches.csv`.

Representative coverage included the 3-vertex minimum, 48-vertex middle sample, 74-vertex maximum, all four control-pattern classes, both the unindexed descriptors 0–113 and AAB-indexed static descriptors 114–1337, and multiple MTL records. Examples include batch 361 (3 vertices, static, initial-only), batch 50 (48, unindexed, paired flags), batch 1999 (74, static, paired flags), batch 291 (isolated-only), and batch 6 (mixed).

## Candidate-model comparison

| Model | Rule | Emitted triangles | Exact zero-area | Assessment |
|---|---|---:|---:|---|
| A | Every source vertex after the first two emits | 84,058 | 5,050 | Disproved; emits 37,722 intended bridge/stitch primitives and produces edges up to 209.89 |
| B | ADC suppresses, history continues, parity follows emitted count | 46,336 | 3 | Connectivity set correct, winding phase wrong for 3,798 triangles |
| C | ADC clears history/restarts | 12,907 | 0 | Disproved; discards the first two valid triangles' vertices after every paired stitch and loses 33,429 spec triangles |
| D | ADC suppresses current primitive; history/source parity continue | 46,336 | 3 | **Selected; matches GS semantics and all Spartan controls** |
| E | ADC suppresses but resets parity phase | 46,336 | 3 | Connectivity set correct, winding phase wrong for 16,135 triangles |

Models B, D, and E have the same unordered triangle connectivity and therefore the same scalar area/edge statistics. They differ in index order. Generic GS behavior resolves that ambiguity in favor of D. Adjacent, non-degenerate triangles under D have a mean normalized face-normal dot of 0.9431; 25,356 of 25,662 pairs are positive, which supports the alternating winding convention locally.

## Reconstruction rule

Each VIF batch is independent. Do not carry history or parity across a batch boundary. Within a batch, submit every vertex to the rolling strip and suppress only the primitive whose newest vertex has `W == 0x8000`.

```text
for each batch:
    for i in 0 .. vertex_count-1:
        if i < 2:
            continue                    # history is not yet three vertices

        if position[i].w == 0x8000:
            continue                    # suppress this primitive only

        if (i & 1) == 0:
            emit(i-2, i-1, i)
        else:
            emit(i-1, i-2, i)           # alternate to consistent winding
```

This ordering uses `(0,1,2)` as the conventional first face. A consumer may globally reverse all faces if its coordinate/front-face convention requires it, but it must not reset or toggle parity based only on emitted triangles. Suppressed source vertices count toward `i`.

## In-memory geometry checks

The selected model produced 46,336 triangles with:

- zero invalid references and zero repeated-index triangles;
- 3 exactly zero-area and 8 at doubled-area `<= 1e-6`;
- median doubled area 2.2500 and 99th percentile 208.1359;
- median edge 2.1045, 99th percentile 18.6450, and maximum 51.3185;
- median aspect proxy `max_edge² / doubled_area` 2.5438 and 99th percentile 51.2637;
- 3,835 repeated position-triple occurrences and 1,463 zero-area UV triangles, neither of which implies an invalid index reference.

The longest edges all belong to unindexed `CLOUD` material geometry, rather than the AAB-indexed static world. The eight near-zero cases are confined to descriptors 535, 536, 557, 849, 921, and 1168 with MTL records 5, 12, or 13. They are retained as authored degenerates/anomalies; the topology probe does not delete them.

## Attributes and winding evidence

V2-16 remains **LIKELY UV** rather than confirmed UV semantics. Its count is exactly one-to-one with positions in all 2,128 batches. Repeated positions frequently carry different V2-16 pairs (13,496 extra position/attribute combinations), consistent with texture seams. The signed ranges nearly span s16, and zero-area V2 triangles exist, so scale, wrapping, and fixed-point interpretation remain unresolved.

V4-8 does not validate winding. Its fourth byte is `0x80` for all 88,314 vertices, while the first three each span 0–255. Signed-int8 decoding has mean magnitude 0.4943; 128-biased decoding has mean 1.2628. Neither clusters tightly at unit length. Correlation with selected-model face normals is effectively absent: mean dot 0.0248 for signed and -0.0113 for biased, with roughly half positive. The field therefore remains **UNKNOWN** and must not be called a normal merely to support winding.

## Batch, descriptor, material, and AAB boundaries

Topology does not cross VIF batch boundaries. Every batch supplies its own first two ADC-marked history vertices. The 476 exact tail/head position repetitions are duplication for continuity, not evidence that history must be carried between packets. Only two descriptor boundaries repeat the same two positions, further arguing against descriptor-spanning state.

Every descriptor selects exactly one ordered `MODELS.MTL` record through descriptor `+0x0a`; no reconstructed triangle crosses a descriptor or material boundary. This remains a confirmed numeric material/resource binding, not proof that every MTL property is a conventional material property.

AAB validation is independent of topology: 484 non-empty cells reference all 1,224 static descriptors exactly once, and every vertex of every referenced descriptor lies within its associated three-dimensional AAB bounds (1,224/1,224). Representative cell comparisons reach the same extrema to float tolerance, strongly validating static-world placement and the decoded AAB origin-plus-extent fields.

## Remaining unknowns

- Direct proof of the VU microprogram's W-to-GIF ADC routing.
- Absolute global front-face choice in a target renderer/coordinate system.
- V2-16 scale, bias, wrap, and texture-coordinate convention.
- V4-8 semantic role.
- Descriptor/block fields not needed for topology and detailed MTL property semantics.
- Whether the same control convention is invariant in other gameplay sections; no other PAK was opened to test that question.

## Tooling

`tools/analysis/models_topology_probe.py` is a standard-library, read-only research probe. It verifies the three canonical hashes, scans all descriptors/batches, compares models A–E, reconstructs triangles only in memory, records geometric/index/winding statistics, validates AAB containment, accepts `--model`, and restricts output to `logs` or temporary directories. Syntax compilation passes and repeated text/CSV outputs are byte-identical.
