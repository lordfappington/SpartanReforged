# Approved Reforged selection pointer

The JPEG under `source/` is the exact human-approved production artwork and is
locked by SHA-256 in metadata and tests. It must not be recompressed, redrawn,
recoloured, enhanced, or replaced without a new explicit human approval.

The source contains a black field and no alpha channel. The PNG under
`runtime/` is therefore a deterministic derived copy: the connected pointer
body retains the approved RGB samples, the black field becomes transparency,
and the high-resolution alpha edge is filtered only when the UI scales the
asset for display. `build_approved_pointer.py` reproduces this conversion.

The active Reforged renderer uses the approved runtime raster directly. No
procedural pointer geometry or material layer is active.
