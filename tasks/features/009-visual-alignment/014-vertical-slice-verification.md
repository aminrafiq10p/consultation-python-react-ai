# VA-014 — Verify Feature 009 Final Vertical Slice

**Task ID:** VA-014

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Perform final Feature 009 verification.

Run focused/full backend and frontend tests, typecheck, lint, frontend build, PostgreSQL integration, migration-head verification, Docker Compose config/build/start/smoke, Features 001–008 regressions, final visual verification, and git diff checks.

Manual flow:
Dashboard → New Consultation → AI Chat → Feature 008 handoff → Summary → Booking → Records → Appointments → Dashboard.

Confirm:
- real Dashboard projections only;
- no fake screenshot data;
- no migration;
- no activity/review subsystem;
- no unsupported screenshot feature leakage;
- Feature 004 remains booking authority;
- Feature 008 handoff remains intact.

Only mark Feature 009 complete after all checks pass.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
