# Main-menu state notes

- Entry resets selected text colour, starts main-menu music, enables four procedural emitters, applies padlock state, and selects New Game.
- Selection hides the normal text object for one option and shows its matching FONT18G object at the same coordinates.
- A selection event runs `icon_shaker`: +16 then -16 logical X over ten ticks, followed by a position reset. It is not a persistent selection-bar animation.
- Confirmation flashes the selected text between bright and transparent three times before transitioning.
- Single Mission Replay shows a padlock while `maxlevel == 0`. Confirming it plays the locked sound and flashes the lock from white back to neutral; no transition occurs.
- Smoke and logo glows are script emitters. The deterministic still deliberately represents the zero-particle static composition rather than inventing a runtime particle frame.
- `ATTRACT.PSS`/`ATTRACT_PAL.PSS` belong to the preceding title-screen idle flow and are not part of `main_start`.
