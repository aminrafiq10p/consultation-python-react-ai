# NC-003: Expose Consultation Creation API and Verify Persistence

**Task ID:** NC-003  
**Title:** Expose Consultation Creation API and Verify Persistence

## Purpose

Expose `POST /api/v1/consultations` through the existing consultation blueprint
and prove the existing repository/session produces the authoritative persisted
`201` representation safely.

## Traceability

- Feature specification: §§6–8, §§12–15, and §17.
- Implementation plan: §§3 and 6, §§12.2–12.3, 14–16, and §§17–18.

## Scope

- Verify rather than replace the existing consultation creation unit of work.
- Add the creation route, exact boundary/error behavior, route tests, and
  production-composition/PostgreSQL persistence coverage.
- Change repository or composition code only if a focused test proves a small
  approved invariant is missing.

## Expected files/areas affected

- `backend/app/api/consultation_routes.py`.
- Consultation repository, route, and persisted API test modules identified by
  NC-001.
- `backend/app/repositories/consultation_repository.py` and
  `backend/app/__init__.py` only for a proven minimal correction/wiring seam.
- Existing fixtures only for additive FK-safe cleanup or side-effect evidence.

## Implementation requirements

- Add exactly `POST /api/v1/consultations`; reject every query parameter before
  delegation.
- Require JSON content type and exactly one JSON object; safely reject absent,
  empty, malformed, null, scalar, array, missing, wrong-type, blank, overlong,
  and extra/server-controlled fields as exact
  `400 {"error":"Invalid request"}` with zero service calls.
- Validate through the NC-002 DTO, call the existing application service once
  with normalized values, serialize through the existing
  `ConsultationResponse`, and return exact `201` only after confirmed creation.
- Add no `Location` header requirement and expose no raw database, exception,
  environment, credential, SQL, or stack detail.
- Let unexpected application/repository/refresh/serialization failures reach
  the existing exact safe `500` handler; map only an approved defensive input
  outcome to `400` if NC-002 introduced one.
- Verify repository add → commit → refresh → return and rollback/re-raise on
  add/commit/refresh exceptions. Explicitly document that rollback cannot undo
  a commit already durable before refresh failure.
- Prove the returned UUID and values reload through a fresh session and the
  existing detail/list APIs, with exactly one consultation row and no child
  rows or AI calls.

## Dependencies

- NC-002.

## Acceptance criteria

- Valid input yields the exact five-key `201` record after one normalized
  service call; all invalid boundaries produce exact safe `400` and no call.
- Unexpected failure produces only the generic safe `500` and no fabricated ID
  or success representation.
- Real PostgreSQL evidence reloads the returned UUID with normalized fields,
  empty recommendation, and `PENDING` using production composition.
- Repository tests establish successful unit-of-work order and failure
  rollback/re-raise while preserving restart behavior.
- No migration, second session/service, AI call, child aggregate, or GET/
  restart semantic change is present.

## Testing requirements

- Add exhaustive injected-service route tests for parsing, exact response,
  zero-call invalid cases, safe errors, and leakage prevention.
- Add repository success/failure tests and migrated-PostgreSQL tests for fresh-
  session visibility, same-ID list/detail retrieval, exact row deltas, and no
  child-table deltas.
- Use a strict AI double/call count and run relevant Feature 001–003 creation/
  restart regressions plus focused backend checks from NC-001.

## Architecture and scope guards

- Keep Flask parsing/serialization, application orchestration, repository unit
  of work, and request-session composition in their existing layers.
- Do not create a route hierarchy, repository, session, engine, unit-of-work
  framework, migration, dashboard write, AI workflow, or child insert.
- Do not change existing GET, conversation, summary, restart, or booking
  response semantics.

## Definition of Done

- Focused and PostgreSQL tests prove the exact safe POST contract returns and
  retrieves one database-confirmed pending consultation through existing
  architecture with no migration, AI, child effect, or regression.
