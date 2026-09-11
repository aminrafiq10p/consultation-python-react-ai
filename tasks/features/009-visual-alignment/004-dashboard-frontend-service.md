# VA-004 — Extend Frontend Dashboard Types and Runtime Validation

**Task ID:** VA-004

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Extend the existing Dashboard frontend service/types to validate the enriched response.

Validate:
- existing metrics;
- trend date/count buckets;
- activity type/consultation/timestamp/target;
- pending review fields/status;
- malformed/extra data per established conventions.

No frontend-derived authoritative values.
No screen redesign in this task.
Add deterministic service tests.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
