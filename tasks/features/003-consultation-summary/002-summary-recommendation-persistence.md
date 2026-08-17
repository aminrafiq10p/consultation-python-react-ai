# CS-002: Add Summary and Recommendation Persistence

**Task ID:** CS-002  
**Title:** Add Summary and Recommendation Persistence

## Purpose

Introduce the approved PostgreSQL schema and SQLAlchemy mappings for one
immutable consultation summary and its stable ordered recommendations.

## Traceability

- Feature specification: §§5–8, 13–16.
- Implementation plan: §§3–4, 13–16, 18–20.

## Scope

- Add one linear Alembic revision after `20260813_02`.
- Add `ConsultationSummary` and `ConsultationRecommendation` mappings to the
  shared infrastructure metadata.
- Add focused migration/schema persistence coverage.

## Expected files/areas affected

- `backend/app/infrastructure/consultation_models.py`.
- `backend/migrations/versions/` with one Feature 003 revision.
- Focused backend persistence/migration tests and fixtures.

## Implementation requirements

- Use native UUID primary/foreign keys and time-zone-aware summary creation
  timestamp with server default.
- Enforce unique `consultation_id`, nonblank patient summary, nullable-or-
  nonblank rationale, nonblank treatment, positive position, and unique
  `(summary_id, position)` through named constraints.
- Use explicit foreign keys without delete cascades; create tables in summary
  then recommendation order and downgrade in reverse.
- Do not add appointment, version, attempt, audit, lineage, deletion, or new
  consultation-status schema.

## Dependencies

- CS-001.

## Acceptance criteria

- PostgreSQL enforces at most one summary per consultation and stable UUID
  recommendation rows with deterministic valid positions.
- The migration upgrades/downgrades cleanly after Features 001/002.
- Shared metadata represents exactly the approved summary data model.

## Testing requirements

- Test the full migration chain and focused downgrade/upgrade against
  PostgreSQL 16.
- Verify UUID/FK, unique summary, text checks, nullable rationale, positive and
  unique position, timestamp, and no-cascade behavior deterministically.

## Definition of Done

- Migration, mappings, and focused schema tests pass with no repository,
  workflow, API, frontend, appointment, or unrelated infrastructure work.
