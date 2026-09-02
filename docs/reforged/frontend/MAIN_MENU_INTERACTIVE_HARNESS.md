# Main-menu interactive harness

This is a Windows development harness for hands-on testing of the Reforged
main menu. It is not a native recompilation of Spartan: Total Warrior, and no
campaign or gameplay systems are connected.

## Architecture

`menu_harness.py` is a pygame-ce/SDL adapter around the existing
`main_menu_reforged.py` architecture. It sends semantic `UP`, `DOWN`,
`CONFIRM`, and `BACK` actions to the shared `MenuState`, and caches frames
produced by the same `render_wireframe` function used for public review images.
It does not contain a second menu definition or duplicate asset layout.

The six selection states for the active logical viewport, lock state, and input
profile are pre-rendered as a bounded cache. This adds a short initial warm-up
but keeps ordinary navigation responsive without replacing the shared renderer.

The cached frames contain the approved background, logo, unselected/locked
navigation, context, padlock, and prompts. A small real-time overlay supplies
only the selected Cinzel run, selected-row dust, and approved pointer. The
selected text combines a stable dark-bronze/gold container with two large
low-frequency fields and sparse cream-hot regions clipped to the glyph mask.
Fields advance through 4 Hz keyframes over 7.4–9.2 second cycles and interpolate
every displayed frame, so the material flows slowly without changing the glyph
silhouette or visibly stepping. It does not rasterize or special-case any
localized label.

Selected-row dust uses a bounded 46-instance pool distributed anisotropically
through the actual selected text bounds and a sparse horizontal tail. Most
particles retain low positive-X momentum with drag; mild upward drift and
turbulence increase dispersion as their 2.5–6.0 second lifetimes expire. The
distribution is independent of the pointer position. Existing row dust decays
in place after selection changes while a bounded fresh wake starts at the new
row—particles never travel between rows. The approved pointer raster
moves between exact row anchors over 160 ms with cubic ease-out; its destination
size and 17 px text gap are unchanged. `--reduced-motion` freezes the internal
light, disables particles, and makes the pointer transition immediate while
retaining the static selected treatment.

The repeatable Windows build uses pinned pygame-ce 2.5.8, Pillow 11.3.0, and
PyInstaller 6.22.2 in an ignored local virtual environment. PyInstaller creates a self-contained
one-folder distribution; Python does not need to be installed on the machine
that launches the resulting executable.

## Build and launch

From PowerShell at the repository root:

```powershell
.\tools\build_menu_harness.ps1
```

Double-click:

`build\menu-harness\SpartanReforged-Menu\SpartanReforged-Menu.exe`

## Controls

- Up/Down or W/S: navigate
- Enter or Space: confirm
- Escape: semantic Back (does not immediately exit)
- F6: development-only `maxlevel` 0/1 toggle
- F8: development HUD
- F10: clean immediate exit
- F11 or Alt+Enter: windowed/borderless fullscreen
- F1: 1920×1080 logical viewport
- F2: 2560×1440 logical viewport
- F3: 3840×2160 logical viewport
- F4: 2560×1080 logical viewport

Controllers use SDL joystick hot-plugging. D-pad and left-stick vertical input
navigate. SpartanReforged preserves PlayStation positional face-button semantics
across controller brands: south is Cross, east is Circle, west is Square, and
north is Triangle. Consequently Xbox A maps to Cross, B to Circle, X to Square,
and Y to Triangle. On the current main menu south/Cross/Xbox A confirms and
north/Triangle/Xbox Y backs; Xbox B is not Back.

Physical controller identity is kept separate from semantic mapping and prompt
presentation. Any controller (PlayStation, Xbox/XInput, or generic SDL) displays
the approved Cross and Triangle Spartan shield prompts. Keyboard remains
available at all times and displays the temporary `ENT` and `ESC` development
prompts. The visible prompt set switches with the last meaningful input device.

Navigation moves immediately, repeats after 320 ms, and then repeats every
115 ms. Confirm and Back are edge-triggered. The standalone harness reports
semantic actions in a short development notice; locked confirmation reports
`LOCKED ACTION REJECTED`. The HUD is off by default and shows FPS, physical and
logical sizes, selection, action, device profile, `maxlevel`, and window mode.

## Current limitations

- Controller mappings use SDL/pygame joystick conventions and require physical
  hardware testing across specific controller/driver combinations.
- Campaign screens and gameplay actions are intentionally not connected.
- Selection effects are an initial tuning pass and require human visual review.
- Keyboard prompt artwork remains development-grade.
- This harness deliberately adds no audio, smoke, parallax, logo glints, or
  background motion.
