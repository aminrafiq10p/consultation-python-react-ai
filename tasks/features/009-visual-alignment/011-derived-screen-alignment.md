# VA-011 — Align New Consultation and Appointments Screens

**Task ID:** VA-011

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Apply the shared visual system to screens without direct references.

New Consultation:
- preserve Feature 006 behavior;
- derive form/card styling from Booking.

Appointments:
- preserve Feature 007 behavior;
- derive table/list styling from Consultation Records.

No new functionality.
No appointment edit/cancel/reschedule.
Add focused regressions as needed.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
