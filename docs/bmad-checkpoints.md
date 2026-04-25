# BMAD Checkpoints

## 2026-04-15 - Documentation Pass

### Checkpoint 1

- Role: `tech-writer`
- Phase: `analysis`
- Workflow: `bmad-document-project / initial_scan`
- Artifact created or updated: repo understanding captured in working notes and documentation plan
- Blockers: none
- Decisions: treat repo as a static CLI learning game, not an application codebase
- Handoff target: `tech-writer`
- Completion state: complete

### Checkpoint 2

- Role: `tech-writer`
- Phase: `planning`
- Workflow: `bmad-document-project / initial_scan`
- Artifact created or updated: documentation set definition
- Blockers: none
- Decisions: create `docs/index.md`, `docs/project-overview.md`, `docs/data-model.md`, and refresh root `README.md`
- Handoff target: `tech-writer`
- Completion state: complete

### Checkpoint 3

- Role: `tech-writer`
- Phase: `validation`
- Workflow: `bmad-document-project / initial_scan`
- Artifact created or updated: finalized documentation set and checkpoint log
- Blockers: none
- Decisions: keep docs focused on repository purpose, puzzle structure, and data relationships; avoid revealing the actual killer
- Handoff target: `complete`
- Completion state: complete

## 2026-04-15 - CLI Game Design Guide

### Checkpoint 4

- Role: `tech-writer`
- Phase: `planning`
- Workflow: `documentation extension`
- Artifact created or updated: guide definition for creating original games in this style
- Blockers: none
- Decisions: add a practical design guide covering story, characters, incidents, schemas, tooling, testing, and packaging
- Handoff target: `tech-writer`
- Completion state: complete

### Checkpoint 5

- Role: `tech-writer`
- Phase: `validation`
- Workflow: `documentation extension`
- Artifact created or updated: `docs/designing-cli-mystery-games.md` and updated docs index
- Blockers: none
- Decisions: keep the guide implementation-oriented, emphasize clue-graph-first design, and frame code as author tooling rather than mandatory runtime
- Handoff target: `complete`
- Completion state: complete

## 2026-04-15 - Design Rules CLI Pack

### Checkpoint 6

- Role: `tech-writer`
- Phase: `analysis`
- Workflow: `repo study and reusable design extraction`
- Artifact created or updated: repo-level study across game design, engineering, and writing perspectives
- Blockers: none
- Decisions: derive reusable principles from content scale, file schemas, pacing, hint design, and answer verification rather than only from theme
- Handoff target: `tech-writer`
- Completion state: complete

### Checkpoint 7

- Role: `tech-writer`
- Phase: `validation`
- Workflow: `repo study and reusable design extraction`
- Artifact created or updated: standalone `design_rules_cli/` study pack
- Blockers: none
- Decisions: make the pack reusable as a foundation for future CLI mystery repos
- Handoff target: `complete`
- Completion state: complete

## 2026-04-15 - Docs Conversion For Starter Pack

### Checkpoint 8

- Role: `dev`
- Phase: `analysis`
- Workflow: `docs normalization / repo alignment`
- Artifact created or updated: documentation gap analysis for `docs/`
- Blockers: none
- Decisions: treat current docs as misaligned because they describe the original `clmystery` pattern instead of the `cli-mystery-starter` package in this workspace
- Handoff target: `tech-writer`
- Completion state: complete

### Checkpoint 9

- Role: `tech-writer`
- Phase: `planning`
- Workflow: `docs normalization / structure rewrite`
- Artifact created or updated: target documentation structure for starter-pack docs
- Blockers: none
- Decisions: keep the existing `docs/` filenames but rewrite them around starter-pack overview, scaffold contract, and authoring workflow
- Handoff target: `tech-writer`
- Completion state: complete

### Checkpoint 10

- Role: `tech-writer`
- Phase: `validation`
- Workflow: `docs normalization / structure rewrite`
- Artifact created or updated: `docs/index.md`, `docs/project-overview.md`, `docs/data-model.md`, and `docs/designing-cli-mystery-games.md`
- Blockers: none
- Decisions: position the starter pack as an authoring tool, separate package docs from authoring guidance, and preserve BMAD evidence in this ledger
- Handoff target: `complete`
- Completion state: complete

## 2026-04-15 - Ruflo MCP Debug

### Checkpoint 11

- Role: `dev`
- Phase: `analysis`
- Workflow: `investigate / mcp startup failure`
- Artifact created or updated: root-cause notes for Ruflo MCP startup path
- Blockers: Ruflo MCP tools were not registered in-session because the configured launcher failed before server startup
- Decisions: confirm Codex was configured with `npx -y ruflo@latest`; isolate `latest` as `3.5.80`; verify `3.5.80` fails under local npm `11.6.2` with `Invalid Version`; verify `3.5.51` launches successfully
- Handoff target: `dev`
- Completion state: complete

### Checkpoint 12

- Role: `dev`
- Phase: `validation`
- Workflow: `investigate / mcp startup failure`
- Artifact created or updated: Codex MCP config fix and BMAD ledger update
- Blockers: current session will still lack `mcp__ruflo__*` tools until Codex reloads MCP servers
- Decisions: pin Ruflo MCP server registration to `ruflo@3.5.51` as the last locally verified working version instead of broken `latest`
- Handoff target: `complete`
- Completion state: complete
