# Spartan PAK Tooling

This directory documents Luigi Auriemma's QuickBMS 0.12.0 and the game-specific `spartan_total_war.bms` script 0.1.1, retrieved locally from the author's mirror on 2026-08-28.

- QuickBMS source: https://mirror.aluigi.org/papers/quickbms.zip
- Script source: https://mirror.aluigi.org/bms/spartan_total_war.bms
- Script SHA-256: `e77b5ad9ab7289f11ec72364dd70fccac392b446b45455fc6bb1c6bdfdeda7c4`
- Supported by the script: listing/extracting Spartan: Total Warrior PS2 `PAK0` and `PAK1` archives.
- Known limitations: unsupported PAK version values terminate cleanly; no compression handler is declared; filenames are read directly from the archive. Generic QuickBMS reimport modes exist, but safe rebuilding of Spartan archives has not been verified and must not be assumed.

The downloaded QuickBMS archive, executables, and game-specific BMS script are retained locally but ignored by the parent Git repository. The upstream page describes QuickBMS as open source and distributes a script collection, but no explicit redistribution license was found for this individual script during the public-release audit. Therefore the public repository tracks only this provenance/integrity note. Obtain the script from the author-operated mirror and verify the SHA-256 above.

Do not run this tooling against original media. Later tests should use a verified working copy and a disposable output directory.
