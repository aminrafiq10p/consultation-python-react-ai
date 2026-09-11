# VA-010 — Align Consultation Records Screen

**Task ID:** VA-010

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Close-match Screen 5 while preserving Feature 001 behavior.

Retain:
- Patient Name;
- Primary Concern;
- Recommended Procedure;
- Status;
- search;
- status filters;
- record-to-detail navigation.

Align heading, search, filter pills, table/card surface, initials/avatar treatment, row height, separators, status chips, and responsive presentation.

Do not fabricate dates, pagination, counts, sorting, or records.
Add focused records tests.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
