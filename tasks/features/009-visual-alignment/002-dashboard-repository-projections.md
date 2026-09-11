# VA-002 — Add Dashboard Read Projections

**Task ID:** VA-002

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Extend the existing Dashboard repository with read-only PostgreSQL projections for:
- rolling 30-day Consultation Trends;
- bounded Recent Activity;
- Pending Clinical Reviews from `PENDING` consultations.

Requirements:
- no mutation/commit;
- no synthetic timestamps;
- no hardcoded data;
- deterministic ordering;
- bounded results;
- no N+1;
- request-scoped Session;
- no migration.

Add focused repository tests.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
