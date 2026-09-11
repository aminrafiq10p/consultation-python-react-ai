# VA-005 — Align Shared Application Shell and Visual Primitives

**Task ID:** VA-005

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Align AppLayout and minimal shared visual primitives with the references.

Cover:
- desktop sidebar;
- branding;
- + New Consult;
- Dashboard/Consultations/Appointments;
- active states;
- content offset/gutters/max-width;
- background;
- page headings;
- cards;
- buttons;
- inputs;
- status chips;
- mobile drawer/top bar;
- focus/disabled/loading styles.

Do not add unsupported screenshot navigation/utilities.
Add focused shell/navigation regressions.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
