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
navigate. A south/primary button confirms. Recognized DualSense, DualShock,
Sony, or PlayStation-named devices use the PlayStation profile (Cross confirms,
Triangle backs); other controllers use the generic/XInput profile (A confirms,
B backs). Keyboard remains available at all times. Prompt presentation follows
the last meaningful input profile.

Navigation moves immediately, repeats after 320 ms, and then repeats every
115 ms. Confirm and Back are edge-triggered. The standalone harness reports
semantic actions in a short development notice; locked confirmation reports
`LOCKED ACTION REJECTED`. The HUD is off by default and shows FPS, physical and
logical sizes, selection, action, device profile, `maxlevel`, and window mode.

## Current limitations

- Controller mappings use SDL/pygame joystick conventions and require physical
  hardware testing across specific controller/driver combinations.
- Campaign screens and gameplay actions are intentionally not connected.
- The existing 160 ms transition token has no executable animation path yet;
  selection state and the approved pointer update immediately.
- Non-PlayStation prompt artwork remains development-grade.
- This harness deliberately adds no audio, particles, parallax, or new effects.
