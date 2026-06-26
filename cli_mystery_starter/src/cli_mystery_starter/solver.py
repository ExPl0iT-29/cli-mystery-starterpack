"""Heuristic uniqueness solver for declared clue + solution sets.

A common authoring failure mode is shipping a case whose clue graph
does not actually narrow to a single suspect. The runtime cannot
detect this on its own, so this module provides an opinionated check
authors can run before validating that their evidence trail is fair.

How it works
------------

Authors annotate each entry in `game/clues.json` with one or more
**directional tags** of the form:

    "points:<suspect-key>"     this clue incriminates <suspect-key>
    "exonerates:<suspect-key>" this clue clears <suspect-key>

Where `<suspect-key>` is a slug derived from the canonical name
(lowercased, spaces collapsed to underscores, e.g. `maria_ortega`).
Both the canonical name and any aliases declared in `solutions.json`
are accepted.

For every suspect listed in `game/people` (column 1 of the data
rows) the solver computes a net score:

    score(suspect) = #points - #exonerates

The case is **UNIQUE** when:

1. exactly one suspect has a strictly highest score
2. that suspect's slug matches the canonical `culprit` field in
   `solutions.json` (or any of its aliases)
3. every clue's `source_path` exists on disk

The check is intentionally a heuristic, not a full constraint
solver. Cases with motive/weapon fields or non-suspect tags are
ignored by this analysis. Authors who need richer guarantees should
layer their own logic on the same tag convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .clues import load_clues
from .solutions import load_solutions


def slugify(name: str) -> str:
    """Normalize a name for tag matching."""
    return "_".join(name.lower().split())


@dataclass
class SolverReport:
    suspects: list[str] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)
    points_by: dict[str, list[str]] = field(default_factory=dict)
    exonerates_by: dict[str, list[str]] = field(default_factory=dict)
    canonical_culprit: str | None = None
    canonical_culprit_slug: str | None = None
    top_suspects: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    verdict: str = "UNKNOWN"  # UNIQUE | AMBIGUOUS | MISMATCH | INSUFFICIENT | ERROR

    @property
    def ok(self) -> bool:
        return self.verdict == "UNIQUE"


def _load_suspects(project_root: Path) -> list[str]:
    people = project_root / "game" / "people"
    if not people.exists():
        return []
    suspects: list[str] = []
    for index, line in enumerate(people.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        if index == 0:
            # Header row
            continue
        first_col = line.split("\t", 1)[0].split("|", 1)[0].strip()
        if first_col:
            suspects.append(first_col)
    return suspects


def analyze(project_root: Path) -> SolverReport:
    report = SolverReport()

    clues, clue_errors = load_clues(project_root)
    if clue_errors:
        report.errors.extend(clue_errors)
        report.verdict = "ERROR"
        return report

    solutions, sol_errors = load_solutions(project_root)
    if sol_errors:
        report.errors.extend(sol_errors)
        report.verdict = "ERROR"
        return report

    if not clues:
        report.info.append("No `game/clues.json` declared; nothing to analyze.")
        report.verdict = "INSUFFICIENT"
        return report

    if solutions is None or "culprit" not in solutions.fields:
        report.info.append(
            "No `solutions.json` with a `culprit` field; cannot verify canonical answer."
        )
        report.verdict = "INSUFFICIENT"
        return report

    suspects = _load_suspects(project_root)
    if not suspects:
        report.errors.append("`game/people` is empty or missing; cannot enumerate suspects.")
        report.verdict = "ERROR"
        return report
    report.suspects = suspects

    suspect_slugs = {slugify(s): s for s in suspects}
    report.scores = {s: 0 for s in suspects}
    report.points_by = {s: [] for s in suspects}
    report.exonerates_by = {s: [] for s in suspects}

    # Validate source paths and tally tags.
    for clue in clues:
        if not (project_root / clue.source_path).exists():
            report.missing_sources.append(clue.source_path)
        for tag in clue.tags:
            kind, _, target = tag.partition(":")
            if not target:
                continue
            target_slug = slugify(target)
            suspect_name = suspect_slugs.get(target_slug)
            if suspect_name is None:
                # Tag references something other than a suspect; ignored.
                continue
            if kind == "points":
                report.scores[suspect_name] += 1
                report.points_by[suspect_name].append(clue.id)
            elif kind == "exonerates":
                report.scores[suspect_name] -= 1
                report.exonerates_by[suspect_name].append(clue.id)

    # Canonical culprit
    culprit_field = solutions.fields["culprit"]
    report.canonical_culprit = culprit_field.value
    canon_candidates = {slugify(culprit_field.value)} | {
        slugify(a) for a in culprit_field.aliases
    }
    matched_canonical = next(
        (suspects[i] for i, s in enumerate(suspects)
         if slugify(s) in canon_candidates),
        None,
    )
    if matched_canonical is None:
        report.errors.append(
            f"Canonical culprit {culprit_field.value!r} (and aliases) "
            f"not found in `game/people`."
        )
        report.verdict = "ERROR"
        return report
    report.canonical_culprit_slug = slugify(matched_canonical)

    # Verdict
    if all(score == 0 for score in report.scores.values()):
        report.info.append(
            "No `points:<suspect>` or `exonerates:<suspect>` tags found in clues; "
            "annotate clues with directional tags to enable uniqueness analysis."
        )
        report.verdict = "INSUFFICIENT"
        return report

    top_score = max(report.scores.values())
    report.top_suspects = sorted(
        s for s, score in report.scores.items() if score == top_score
    )

    if report.missing_sources:
        report.errors.extend(
            f"Clue source missing on disk: {p}" for p in report.missing_sources
        )

    if len(report.top_suspects) > 1:
        report.verdict = "AMBIGUOUS"
        return report

    top = report.top_suspects[0]
    if slugify(top) != report.canonical_culprit_slug:
        report.verdict = "MISMATCH"
        return report

    report.verdict = "UNIQUE" if not report.errors else "ERROR"
    return report


def render(report: SolverReport) -> str:
    lines: list[str] = []
    lines.append(f"Verdict: {report.verdict}")
    if report.canonical_culprit:
        lines.append(f"Canonical culprit: {report.canonical_culprit}")
    if report.suspects:
        lines.append("")
        lines.append("Suspect scores (points - exonerates):")
        for suspect in sorted(report.suspects, key=lambda s: -report.scores.get(s, 0)):
            score = report.scores.get(suspect, 0)
            mark = "  *" if suspect in report.top_suspects else "   "
            lines.append(f"{mark} {suspect:<30} {score:+d}")
    if report.errors:
        lines.append("")
        lines.append("Errors:")
        for err in report.errors:
            lines.append(f"  - {err}")
    if report.info:
        lines.append("")
        lines.append("Notes:")
        for note in report.info:
            lines.append(f"  - {note}")
    if report.verdict == "UNIQUE":
        lines.append("")
        lines.append("OK: evidence narrows to exactly one suspect, "
                     "and that suspect matches the canonical answer.")
    elif report.verdict == "AMBIGUOUS":
        lines.append("")
        lines.append(
            "Ambiguous: multiple suspects share the highest net score: "
            + ", ".join(report.top_suspects)
        )
    elif report.verdict == "MISMATCH":
        top = report.top_suspects[0] if report.top_suspects else "?"
        lines.append("")
        lines.append(
            f"Mismatch: clue tags point most strongly at {top}, "
            f"but the canonical culprit is {report.canonical_culprit}."
        )
    return "\n".join(lines)


def check_solve_command(project_root: Path) -> int:
    report = analyze(project_root)
    print(render(report))
    return 0 if report.verdict in ("UNIQUE", "INSUFFICIENT") else 1
