# AI-002: Add Persistent Consultation Messages

**Task ID:** AI-002  
**Title:** Add Persistent Consultation Messages

## Purpose

Introduce the approved PostgreSQL message schema and SQLAlchemy mapping without adding AI behavior.

## Traceability

- Feature specification: §§5, 12, 14.
- Implementation plan: §§3–5, 11, 12.2, 13–14.

## Scope

- Add the `Message` mapping, `MessageRole`, one Alembic revision directly after `20260813_01`, and persistence-focused PostgreSQL tests.

## Expected files/areas affected

- `backend/app/infrastructure/consultation_models.py` (or AI-001-confirmed mapping area) and exports.
- `backend/migrations/versions/` and backend persistence tests/fixtures.

## Implementation requirements

- Map UUID `id` generated with `uuid4`; required UUID `consultation_id`; native enum `USER`/`ASSISTANT`; required `TEXT` content; nullable `JSONB` payload; required time-zone-aware `created_at` with `CURRENT_TIMESTAMP` server default.
- Reference `consultations.id` with no delete cascade or Feature 001 relationship/read changes.
- Add `role != 'USER' OR structured_payload IS NULL` and a B-tree index on `(consultation_id, created_at, id)`.
- Downgrade in safe reverse order. Add no summary, recommendation, appointment, sequence, edit, or deletion fields.

## Dependencies

- AI-001.

## Acceptance criteria

- Full Alembic upgrade and Feature 002 downgrade work; PostgreSQL enforces the approved types, linkage, constraints, and index.
- Assistant JSONB persists and equal timestamps can be deterministically ordered by UUID.
- Feature 001 persistence remains unchanged.

## Testing requirements

- Test migration upgrade/downgrade, UUID/FK, enum, JSONB, user-payload constraint, timestamps, index, and tied-timestamp ordering support against PostgreSQL.
- No AI or network access.

## Definition of Done

- Mapping, single migration, and focused tests pass with only the approved persistence foundation.
