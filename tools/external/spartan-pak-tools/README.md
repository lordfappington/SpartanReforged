# Spartan PAK Tooling

This directory contains Luigi Auriemma's QuickBMS 0.12.0 and the game-specific `spartan_total_war.bms` script 0.1.1, retrieved from the author's mirror on 2026-08-28.

- QuickBMS source: https://mirror.aluigi.org/papers/quickbms.zip
- Script source: https://mirror.aluigi.org/bms/spartan_total_war.bms
- Script SHA-256: `e77b5ad9ab7289f11ec72364dd70fccac392b446b45455fc6bb1c6bdfdeda7c4`
- Supported by the script: listing/extracting Spartan: Total Warrior PS2 `PAK0` and `PAK1` archives.
- Known limitations: unsupported PAK version values terminate cleanly; no compression handler is declared; filenames are read directly from the archive. Generic QuickBMS reimport modes exist, but safe rebuilding of Spartan archives has not been verified and must not be assumed.

The downloaded QuickBMS archive and executables are retained locally but ignored by the parent Git repository. The small game-specific BMS script and this provenance file are tracked.

Do not run this tooling against original media. Later tests should use a verified working copy and a disposable output directory.

