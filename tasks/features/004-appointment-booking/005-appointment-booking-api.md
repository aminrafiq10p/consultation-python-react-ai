# AB-005: Expose Appointment Booking API and DTOs

**Task ID:** AB-005  
**Title:** Expose Appointment Booking API and DTOs

## Purpose

Expose the approved appointment booking POST contract through the existing
consultation blueprint and production composition with strict safe DTOs.

## Traceability

- Feature specification: §§9–13, §§15–16, and §19.
- Implementation plan: §§3 and 7, §10.2, §13 AB-005, and §§15–17.

## Scope

- Compose `AppointmentRepository` with the same production request session and
  inject it into `ConsultationApplicationService`.
- Add strict appointment booking request and response DTOs.
- Add only `POST /api/v1/consultations/<consultation_id>/appointments` to the
  existing consultation blueprint.
- Add DTO, route, safe-error, persisted API, and no-AI integration tests.

## Expected files/areas affected

- `backend/app/__init__.py`.
- `backend/app/api/consultation_dtos.py`.
- `backend/app/api/consultation_routes.py`.
- `backend/tests/api/test_consultation_dtos.py` and focused route/API
  integration test locations.

## Implementation requirements

- Define an `extra="forbid"` request accepting only UUID `recommendation_id`,
  strict-string `scheduled_at`, and string `location`.
- Require `scheduled_at` source text to contain `Z` or a numeric UTC offset and
  parse it as an aware valid datetime; reject numeric, date-only, naive,
  malformed, absent, non-object, and extra-field input safely.
- Define a nested recommendation response with only `id` and `treatment`, and
  an appointment response with `id`, `consultation_id`, nested recommendation,
  `scheduled_at`, normalized `location`, and `created_at`.
- Serialize UUIDs at the boundary and both timestamps with explicit offsets;
  expose neither top-level `recommendation_id`, treatment copy, summary
  internals, nor SQLAlchemy state.
- Validate the path/body before one service call and return the persisted DTO
  with exactly HTTP `201` after commit.
- Translate invalid request to `400 {"error":"Invalid request"}`, missing
  consultation/recommendation to their exact safe `404` messages, and the three
  conflict types to safe coded `409` responses using
  `RECOMMENDATION_NOT_BOOKABLE`, `CONSULTATION_NOT_BOOKABLE`, or
  `APPOINTMENT_ALREADY_EXISTS`.
- Preserve the existing generic safe `500` handling and never expose validation
  details, SQL/constraint names, exception text, stack/environment/secrets, or
  another consultation's treatment.
- Keep the route free of direct session/repository access and AI calls.

## Dependencies

- AB-004.

## Acceptance criteria

- The exact endpoint accepts the approved request and returns a runtime-valid
  persisted `201` representation with authoritative treatment and offsets.
- Invalid paths/bodies never call the service; each typed outcome maps to the
  exact approved status/body/code; unexpected failures return only safe `500`.
- API-to-PostgreSQL integration persists one appointment and authoritative
  `BOOKED`, while records and summary GETs reload unchanged source data.
- Repeat and controlled concurrent loser requests return stable coded `409`
  rather than retrieval, raw integrity detail, or automatic retry.

## Testing requirements

- Add strict DTO matrices for UUID, unknown/missing fields, JSON shape,
  datetime type/calendar/offset, normalized location, and explicit-offset
  response serialization.
- Route tests must assert exact service arguments/call count and exact
  `201`/`400`/both `404`/all coded `409`/safe `500` bodies.
- Run a persisted vertical slice through Flask, application, repositories, and
  PostgreSQL, including repeat/race, rollback, records reload, summary reload,
  immutable source data, and a strict no-AI dependency.

## Architecture and scope guards

- Reuse the existing blueprint, application service, shared request session,
  Pydantic conventions, error handler, and Compose services.
- Add no appointment GET, update, delete, lifecycle/status, multiple booking,
  retry/idempotency retrieval, provider/calendar/notification/payment/auth,
  dashboard, AI/RAG, streaming, or infrastructure behavior.

## Definition of Done

- DTO, route, composition, and persisted API tests prove the exact safe contract
  and authoritative atomic result without leaking persistence, adding another
  endpoint, or regressing Features 001–003.
