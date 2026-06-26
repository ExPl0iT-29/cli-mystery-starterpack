# CLI Mystery Starter Documentation

## Overview

This `docs/` folder documents the starter pack in this workspace, not a shipped mystery game.
The package under `cli_mystery_starter/` is a Python scaffolder and validator for
filesystem-based CLI mystery projects.

Use this documentation set in the following order:

1. [project-overview.md](./project-overview.md)
2. [developer-guide.md](./developer-guide.md) — practical guide for building a new game
3. [data-model.md](./data-model.md)
4. [designing-cli-mystery-games.md](./designing-cli-mystery-games.md)
5. [bmad-checkpoints.md](./bmad-checkpoints.md)

## Audience

These docs are written for:

- maintainers of the starter pack
- authors creating new mystery games from the scaffold
- reviewers who need to understand what the package generates and validates

## Documentation Map

- [project-overview.md](./project-overview.md): product scope, repository layout, CLI commands, and usage flows
- [data-model.md](./data-model.md): scaffold structure, generated artifacts, configuration fields, and validation rules
- [designing-cli-mystery-games.md](./designing-cli-mystery-games.md): authoring guidance for turning the scaffold into a playable CLI mystery
- [bmad-checkpoints.md](./bmad-checkpoints.md): BMAD checkpoint ledger for the documentation work

## Quick Facts

- Package name: `cli-mystery-starter`
- Python requirement: `>=3.10`
- Runtime model: local CLI only
- Core commands: `init`, `validate`, `play`, `check-answer`, `check-solve`
- Generated project shape: text-first mystery repo with `game/`, `design/`, `docs/`, `hints/`, and `tools/`

## Key Distinction

The starter pack is not itself the mystery game. It provides:

- a CLI to scaffold, validate, playtest, and uniqueness-check a project
- starter templates for the game files
- a strict validator driven by a single project contract
- an investigation shell with a documented event bus
- four data-driven optional subsystems (clues, multi-ending
  solutions, NPC dialogue, scene/beat engine)
- a reference authoring shape for filesystem-based mystery design
