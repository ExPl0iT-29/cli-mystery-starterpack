# Engineering Study

## What The “Runtime” Actually Is

From an engineering point of view, this repo has no conventional runtime. The effective runtime is:

- the user’s shell
- the filesystem
- a set of plain-text records

That means the engineering quality bar is different from a normal app. You are not optimizing service uptime or component boundaries. You are optimizing solvability, consistency, portability, and content integrity.

## Actual Architecture

The architecture is content-first.

```text
root onboarding files
  -> primary evidence folder
  -> related record families
  -> hints
  -> answer verification
```

This can be treated as a data graph rather than an executable system.

## Effective Modules In `clmystery`

Even without code, the repo has clear modules:

- onboarding module: `README.md`, `instructions`, `cheatsheet.*`
- clue ingress module: `crimescene`
- identity module: `people`
- location module: `streets/*`
- witness module: `interviews/*`
- filtering module: `memberships/*`
- late-stage corroboration module: `vehicles`
- assistance module: `hint*`
- verification module: `solution`, `encoded`

That modularity is worth preserving in future projects.

## Data Integrity Lessons

Because the game is data-driven, integrity failures are fatal.

Examples of dangerous failures:

- a referenced person does not exist
- a street line points to the wrong file or wrong line
- a name appears with different spelling across files
- a generated roster accidentally includes or excludes a key suspect
- multiple candidates satisfy the final evidence set

In this genre, content consistency is the equivalent of program correctness.

## Why Fixed Shapes Matter

The repo uses stable, repeated shapes:

- all street files are 300 lines
- membership files are large flat name lists
- vehicles use repeated multi-line record blocks

This is good engineering for content because:

- the player can infer format quickly
- authoring becomes easier to validate
- generation scripts are simpler if added later
- hint writing becomes more predictable

## Optional Tooling You Should Add In Future Projects

If you use this repo as a base for originals, add author tooling instead of gameplay code first.

Recommended tooling:

- canonical truth file
- entity registry generator
- cross-reference validator
- clue-path validator
- answer verifier builder
- packaging script

## Suggested Authoring Architecture

```text
project/
├─ game/
│  ├─ incident
│  ├─ people
│  ├─ locations/
│  ├─ interviews/
│  ├─ memberships/
│  ├─ logs/
│  └─ vehicles_or_assets/
├─ tools/
│  ├─ generate_entities.py
│  ├─ generate_noise.py
│  ├─ verify_integrity.py
│  ├─ verify_unique_solution.py
│  └─ build_release.py
├─ design_rules_cli/
├─ docs/
├─ instructions
├─ hints/
└─ README.md
```

## Engineering Rules For File Naming

- Prefer ASCII names.
- Use stable separators like `_` for machine-oriented files.
- Keep names grep-friendly.
- Avoid files whose names differ only by case.
- Avoid punctuation that complicates shell usage.
- Only introduce spaces when that is part of the intended player challenge.

## Portability Considerations

If you want the game to work well across environments:

- avoid shell-specific syntax in the core solve path when possible
- provide platform-specific answer verification if needed
- keep text encodings simple
- test on common shells
- avoid requiring nonstandard CLI tools

`clmystery` handles this reasonably well by centering the puzzle around generic commands and isolating the more platform-sensitive logic in the solution path.

## Engineering Takeaway

The best engineering move in this genre is to treat the game as a validated content graph with optional build tooling, not as an app that needs more runtime code.
