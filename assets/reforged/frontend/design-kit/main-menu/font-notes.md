# Main-menu font notes

- English main-menu labels come from `UI.TXT` keys referenced through script `LABEL` declarations.
- Unselected options use `FONT18.TM2` and selected options swap to `FONT18G.TM2`.
- Both atlases use 32x32 cells in a 16x16 grid and share identical 256-entry DIM advances.
- Information/footer and controller-prompt text uses `FONT14`, with 16x16 cells.
- Character index is `codepoint - 32` for the target ASCII strings. DIM stores one little-endian u16 advance per glyph after its 64-byte prefix.
- No independent kerning table was found. The target strings use advances only.
- The selected glow is baked into `FONT18G`; there is no replacement font, generated outline, or added shadow in the reference.
