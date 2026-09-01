# Original Game Data Policy

## Purpose

SpartanReforged publishes original research, tooling, tests, documentation, architecture, and approved/project-created Reforged assets. It does not publish *Spartan: Total Warrior* game data.

## Never commit

Do not commit or redistribute original disc images, BIOS files, executables, PAK archives, extracted files, textures, meshes, skeletons, animations, materials, audio, videos, memory/PCSX2 dumps, or encoded/compressed copies of that content. This includes files such as `SLES_533.93`, `GENERAL.PAK`, `E_DATA.PAK`, `LEVEL00.PAK`, `MODELS.BIN`, TIM2, PSQ, BNS, ANM, and PSS resources.

`.gitignore` is a guardrail, not proof of safety. Before publication, audit both the current tracked tree and all reachable Git history.

## Local inputs

Users provide their own legally obtained game. Original media and extraction output remain in ignored local paths such as:

- `game-original/`
- `game-extracted/`
- `assets/original/`
- `captures/`
- `temp/`
- local analysis/log directories

Tools must read original inputs without modifying them and must not silently copy original assets into tracked directories. Derived geometry, decoded textures, renders, screenshots, manifests containing asset-level data, and raw analysis dumps remain local unless a specific provenance/copyright review establishes that they are safe to publish.

## What may be committed

The repository may contain independently written source code, parsers, converters, synthetic tests, schemas, configuration, bounded factual hashes/offsets, structural descriptions, and reverse-engineering conclusions that do not reproduce substantial copyrighted data. Project-created/generated Reforged artwork and explicitly approved production assets may be committed under `assets/reforged`.

## Preservation and Reforged separation

Preservation research records source-derived facts; it does not make source assets redistributable. Reforged production work is separate and must not overwrite original data or disguise original data as a new project asset.

## Third-party components

Third-party tools are referenced by their official source and pinned version or commit where practical. Do not vendor third-party code without a verified redistribution license. Downloaded applications, external repositories, and game-specific scripts with unconfirmed licensing remain local and ignored.

## Pre-publication history sanitation

Before the repository's first public publication, its unpublished history was rewritten to remove an unlicensed third-party script and unnecessary personal metadata. No preservation conclusions, project-authored tooling, or Reforged assets were intentionally changed by that sanitation.

## Contributor rule

Every contribution must be reviewable without requiring copyrighted fixtures in Git. Use synthetic/non-copyrighted fixtures for tests. If provenance or redistribution rights are uncertain, do not commit the file and request review.
