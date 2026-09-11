# VA-009 — Align Appointment Booking Screen

**Task ID:** VA-009

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Close-match Screen 4 while preserving Feature 004 semantics.

Align:
- back navigation;
- heading/subtitle;
- two-column desktop layout;
- selected treatment/form cards;
- date/time/location;
- right summary card;
- labels/control sizing;
- Confirm Appointment;
- responsive stacking.

Do not add provider, target area, duration, estimated cost, Save as Draft, availability, or clinic-management workflows.
Add focused booking regressions.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
