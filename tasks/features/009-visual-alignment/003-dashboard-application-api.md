# VA-003 — Extend Dashboard Application and API Contract

**Task ID:** VA-003

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Extend the existing Dashboard application service, DTOs, and API response with typed trend/activity/pending-review projections.

Preserve existing metrics exactly.

Requirements:
- reuse current Dashboard endpoint/boundaries;
- no SQLAlchemy in routes;
- exact serialization;
- safe empty projections;
- safe unexpected 500;
- no write behavior;
- no new unrelated endpoint;
- no migration.

Add application/API/composition tests.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
