# Approved Reforged PlayStation shield prompts

The JPEG under `source/` is the exact human-approved 2×2 production sheet and
is locked by SHA-256. It must not be recompressed, redrawn, recoloured,
reconstructed, or replaced without explicit human approval.

The source has a black presentation field and no alpha channel. The four RGBA
PNGs under `runtime/` are deterministic derivatives produced by
`build_approved_playstation_prompts.py`. Each shield is isolated from its
quadrant, uniformly normalized to a 416-pixel visible diameter, and centred on
an identical 448×448 transparent canvas. No symbol, shield detail, lighting,
wear, rim, stud, or material treatment is procedurally recreated.

The Reforged renderer selects these assets through semantic PlayStation glyph
IDs. Cross remains Confirm and Triangle remains Back for the current profile;
Circle and Square are retained as production-ready semantic assets.
