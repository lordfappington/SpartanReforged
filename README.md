# SpartanReforged

SpartanReforged is an independent preservation, reverse-engineering, and remaster research project relating to *Spartan: Total Warrior*. It studies the PlayStation 2 release's data formats and rendering architecture, builds reproducible parsers and validation tools, and develops a separate modern Reforged presentation layer.

The repository does **not** distribute the original game, disc images, executables, archives, extracted assets, BIOS files, audio, video, or memory dumps. Users must provide their own legally obtained game data for workflows that require it. See [Original Game Data Policy](docs/ORIGINAL_GAME_DATA_POLICY.md).

SpartanReforged is not affiliated with or endorsed by Creative Assembly, SEGA, or any other rights holder. Product names and trademarks belong to their respective owners. This repository makes no claim that a particular use of third-party game data is lawful in every jurisdiction.

## Project areas

- **Preservation research:** archive, texture, geometry, material, script, and PS2 render-state findings recorded without redistributing source assets.
- **Reverse engineering:** bounds-checked parsers, deterministic decoders, synthetic tests, and documented executable/VU/GS analysis.
- **Reforged development:** independent rendering/UI architecture and project-created or human-approved production assets kept separate from preservation inputs.
- **Static recompilation research:** PS2Recomp compatibility remains exploratory; no working recompiled game or compatibility claim exists.

## Current status

Milestone 0 has reconstructed and validated the LEVEL00 world-geometry/texture pipeline and recovered substantial native render-state behavior. The Reforged frontend foundation now uses a human-approved main-menu logo. This is still research-stage software: there is no complete native runtime or playable release.

See [Project Status](docs/PROJECT_STATUS.md), [Milestone 0](docs/milestones/MILESTONE_0.md), and the [research index](docs/research/RESEARCH_LOG.md).

## Data separation

Original and locally extracted data belongs only in ignored locations such as `game-original`, `game-extracted`, and `assets/original`. Tools must read those inputs in place and write derived validation output to ignored `temp`, `logs`, or review directories. Project-created Reforged assets live under `assets/reforged`.

## Dependencies

External applications and repositories are documented by source and pinned version/commit where practical. They are installed or cloned locally and are not silently vendored. See [Tool Registry](docs/research/TOOL_REGISTRY.md).

## License status

No project-wide open-source license has yet been selected. Until the maintainers choose and add one, no license is granted for reuse of SpartanReforged's original code or project-created assets beyond rights provided by applicable law. Third-party projects and tools remain governed by their own terms.
