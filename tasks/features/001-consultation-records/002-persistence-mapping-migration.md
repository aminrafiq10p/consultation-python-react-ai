# CR-002: Add Consultation Persistence Mapping and Migration

**Task ID:** CR-002  
**Title:** Add Consultation Persistence Mapping and Migration

## Purpose

Introduce the approved, PostgreSQL-backed consultation storage required for
read-only record and detail retrieval.

## Traceability

- Feature specification: §§5, 7, 10–12.
- Implementation plan: §§3, 5, 12, 14.2, 16–18.

## Scope

- Add one reviewable Alembic migration and SQLAlchemy infrastructure mapping
  for consultations only.
- Persist exactly `id`, `patient_name`, `primary_concern`,
  `recommended_procedure`, and `status`.
- Enforce required fields and the approved `PENDING`, `BOOKED`, `COMPLETED`
  status value set where consistent with foundation conventions.

## Expected files/areas affected

- `backend/app/infrastructure/` SQLAlchemy mapping/metadata area.
- `backend/migrations/` Alembic revision area.
- Backend persistence test fixtures/support and focused persistence tests.

## Implementation requirements

- Use the project-managed SQLAlchemy engine and session lifecycle.
- Keep SQLAlchemy details within infrastructure; do not expose them to routes
  or application services.
- Do not add tables, relationships, fields, seed data mechanisms, or lifecycle
  rules for messages, recommendations, appointments, summaries, or AI output.

## Dependencies

- CR-001.

## Acceptance criteria

- PostgreSQL can store and retrieve the five approved consultation values.
- The migration is versioned, reviewable, and compatible with the existing
  Docker Compose runtime.
- Persistence introduces no unapproved schema or technology.

## Testing requirements

- Add deterministic PostgreSQL-backed coverage that applies the migration and
  verifies required consultation persistence and accepted status values.
- Tests must not require external AI services or credentials.

## Definition of Done

- Migration, mapping, and focused tests pass; architecture boundaries and
  Docker Compose compatibility are preserved.
