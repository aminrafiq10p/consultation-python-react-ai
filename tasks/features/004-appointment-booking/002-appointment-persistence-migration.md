# AB-002: Add Appointment Persistence and Migration

**Task ID:** AB-002  
**Title:** Add Appointment Persistence and Migration

## Purpose

Add the PostgreSQL and SQLAlchemy persistence foundation for exactly one linked
appointment per consultation, without adding booking workflow behavior.

## Traceability

- Feature specification: §§7–11, §13, §16, and §19.
- Implementation plan: §§3–4, §10.1, §§12–13 AB-002, and §§15–17.

## Scope

- Add the `appointments` SQLAlchemy mapping to the infrastructure-owned shared
  metadata.
- Add one linear Alembic revision immediately after the confirmed Feature 003
  head.
- Extend PostgreSQL fixture cleanup in foreign-key-safe order.
- Add focused mapping, migration, constraint, and round-trip persistence tests.

## Expected files/areas affected

- `backend/app/infrastructure/consultation_models.py`.
- One new revision under `backend/migrations/versions/`.
- PostgreSQL fixture cleanup used by backend persistence tests.
- `backend/tests/test_appointment_persistence.py` or the established focused
  persistence/migration test locations.

## Implementation requirements

- Map `id` as a native PostgreSQL UUID primary key generated from `uuid4`.
- Map required native UUID foreign keys `consultation_id` and
  `recommendation_id` to consultations and persisted recommendations, with no
  delete cascade.
- Enforce zero-or-one appointment per consultation with a named unique
  constraint on `consultation_id`; preserve its exact name for AB-003 race
  classification.
- Map required timezone-aware `scheduled_at` and required timezone-aware
  `created_at` with a `CURRENT_TIMESTAMP` server default.
- Map required `location` as `VARCHAR(200)` or the approved equivalent and add
  named checks for nonblank `btrim(location)` and `char_length(location) <= 200`.
- Store no treatment copy and no appointment lifecycle/status column.
- Add only an index justified by foreign-key/recommendation access; the unique
  consultation constraint already supplies consultation lookup support.
- Ensure downgrade drops only the appointment table and upgrade/downgrade does
  not alter existing consultation enum values or rows.
- Delete appointments before recommendations, summaries, and consultations in
  shared test cleanup.

## Dependencies

- AB-001.

## Acceptance criteria

- A full Alembic upgrade creates the exact UUID, FK, unique, check, timezone,
  and default schema, and downgrade/upgrade round trips cleanly.
- Fresh sessions preserve UUID identities, aware instants, consultation and
  recommendation linkage, and valid location values.
- Database constraints reject duplicate consultations, nonexistent foreign
  keys, blank/overlong locations, and missing required fields.
- Existing consultation, message, summary, and recommendation rows remain
  unchanged across migration upgrade.

## Testing requirements

- Run focused PostgreSQL 16 mapping and migration tests against an Alembic-to-
  head database, including schema inspection and downgrade/upgrade.
- Cover aware timestamp round trips, UUID/FK linkage, one-per-consultation,
  location checks, defaults, and fresh-session reload.
- Run applicable prior persistence/migration regressions after cleanup changes.

## Architecture and scope guards

- Persistence checks are defense in depth; offset parsing, future comparison,
  trimming, eligibility, and ownership remain API/application responsibilities.
- Do not add repositories, application workflow, routes, frontend behavior,
  treatment duplication, appointment status, retrieval, lifecycle behavior,
  provider availability, AI, or infrastructure changes.

## Definition of Done

- The mapping, linear migration, cleanup, and focused PostgreSQL tests satisfy
  the approved persistence contract without changing product behavior or
  introducing any out-of-scope schema.
