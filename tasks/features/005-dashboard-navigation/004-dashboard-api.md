# DN-004: Expose Dashboard API and DTO

**Task ID:** DN-004  
**Title:** Expose Dashboard API and DTO

## Purpose

Expose the exact safe read-only dashboard contract and compose its focused
service over the existing request-scoped production session.

## Traceability

- Feature specification: §§7–8, §§12–14, §§16–18.
- Implementation plan: §§3, 6–7, §12.3, §14, §15 DN-004, and §§16–19.

## Scope

- Add the strict dashboard response DTO and focused dashboard blueprint.
- Register only `GET /api/v1/dashboard` and reject query/body input.
- Extend `create_app` with production composition and an isolated dashboard
  service injection seam while preserving consultation injection.
- Add route, DTO, composition, safe-error, and PostgreSQL-backed API tests.

## Expected files/areas affected

- `backend/app/api/dashboard_dtos.py`.
- `backend/app/api/dashboard_routes.py`.
- `backend/app/__init__.py`.
- `backend/tests/api/test_dashboard_routes.py`,
  `backend/tests/test_dashboard_composition.py`, and focused persisted API test
  locations such as `backend/tests/api/test_dashboard_persistence_api.py`.

## Implementation requirements

- Define exactly nonnegative integer `total_consultations`, nonnegative integer
  `booked_appointments`, and finite numeric `conversion_rate` constrained to
  `0..100` in `DashboardResponse`.
- Deliberately convert the quantized application `Decimal` to `float` only at
  DTO construction and serialize with Pydantic JSON-mode output.
- Reject any query key or any non-empty cached raw request body, including
  `{}`, text, JSON, and malformed bytes, as exact
  `400 {"error":"Invalid request"}` without service delegation.
- Resolve `current_app.extensions["dashboard_service"]`, call `get_metrics()`
  once for a valid request, and return the exact three-key numeric `200` JSON.
- Route all unexpected repository, invariant, DTO, or serialization failures
  through the existing exact safe `500` handler without internal details.
- In production, construct dashboard and consultation repositories/services
  over the same request session, remove both service extensions, and close the
  single session at teardown.
- Support `create_app(dashboard_service=double)` without production database or
  AI construction, and preserve existing `consultation_service` injection.

## Dependencies

- DN-003.

## Acceptance criteria

- The application exposes exactly one dashboard endpoint with exact populated
  and zero numeric response shapes and one service call.
- All query/body-bearing requests return the exact safe `400` and never
  delegate; all unexpected failures return only the exact safe `500`.
- Composition proves both production services share one request session and
  teardown closes it, while either focused injection seam remains isolated.
- A persisted request obtains counts from PostgreSQL without AI, mutation,
  another endpoint, or another session.

## Testing requirements

- Assert exact keys, values, statuses, numeric types (`int` but not `bool` for
  counts), empty response, and service call counts.
- Parameterize query and non-empty-body cases; test service/invariant/DTO
  failures and absence of SQL, connection, constraint, environment, patient,
  stack, secret, and AI-provider detail.
- Add composition identity/teardown and injection-isolation tests plus a
  focused migrated-PostgreSQL API slice; retain consultation API regressions.

## Architecture and scope guards

- Keep Flask mapping in a focused blueprint, application calculation in
  DN-003, and SQLAlchemy statements in DN-002.
- Add no mutation route, dashboard persistence/cache, migration, second/global
  session, unit-of-work abstraction, AI, chart, filter, analytics framework,
  external service, or Compose dependency.
- Do not broaden existing consultation error translations or routes.

## Definition of Done

- DTO, route, composition, isolation, safety, and persisted API tests prove the
  exact one-endpoint numeric contract over one shared request session without
  leakage, migration, mutation, AI, or Feature 001–004 regression.
