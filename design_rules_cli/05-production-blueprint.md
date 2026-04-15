# Production Blueprint

## Goal

This is a recommended workflow for producing a new CLI mystery game from concept to release.

## Phase 1: Story Truth

Create these first:

- final answer definition
- canonical incident summary
- culprit or hidden truth
- motive and method
- key false leads

Deliverable:

- `story-bible.md`

## Phase 2: Puzzle Graph

Define:

- starting clue
- intermediate pivots
- narrowing filters
- final confirmation signals
- hint ladder

Deliverable:

- `clue-graph.md`

## Phase 3: Data Design

Define:

- file families
- schemas
- relationships
- naming rules
- noise strategy

Deliverables:

- `data-schemas.md`
- `entity-map.md`

## Phase 4: Content Authoring

Write:

- instructions
- incident file
- people directory
- rosters, logs, and locations
- key interviews
- hints
- solution verification path

Deliverables:

- playable content tree

## Phase 5: Tooling

Add only the tooling that reduces author error:

- generators
- validators
- release packagers

Deliverables:

- `tools/`

## Phase 6: Validation

Run:

- content consistency checks
- unique-solution checks
- beginner solve tests
- platform sanity checks

Deliverables:

- `validation.md`

## Phase 7: Release

Ship with:

- short README
- clean first-step instructions
- hint ladder
- license
- author credits

## Recommended Folder Template

```text
new-cli-mystery/
├─ game/
│  ├─ incident
│  ├─ people
│  ├─ locations/
│  ├─ interviews/
│  ├─ memberships/
│  ├─ logs/
│  └─ assets_or_registry/
├─ hints/
├─ tools/
├─ docs/
├─ design_rules_cli/
├─ instructions
├─ solution
├─ encoded
├─ README.md
└─ LICENSE.md
```

## Blueprint Takeaway

Build in this order:

truth -> clue graph -> schemas -> content -> tooling -> validation -> release

Do not start with generators. Start with the solve path.
