# AB-008 Verification — Appointment Booking Vertical Slice

Verified on 2026-08-18 against the approved Feature 004 specification, plan,
AB-001 findings, implementation tasks, PostgreSQL 16, Flask API, React UI, and
the existing Docker Compose stack. No live AI, OpenAI, calendar, or other
external-service call was made.

## Acceptance-Criteria Matrix

| Acceptance criterion | Implementation area | Evidence | Result |
| --- | --- | --- | --- |
| Summary selection opens booking with stable consultation/recommendation IDs | `ConsultationSummaryScreen`, router | Summary screen and `App` route tests | PASS |
| Direct booking load retrieves persisted selected treatment | `AppointmentBookingScreen`, `consultationApi.summary` | Booking screen tests; runtime summary GET | PASS |
| Future datetime and normalized nonblank location can be submitted | Booking screen/service, request DTO, application workflow | Frontend, DTO, application, and runtime `201` checks | PASS |
| Backend independently validates consultation, status, summary, recommendation, and ownership | `ConsultationApplicationService` | Application precedence tests; cross-owner persisted API test | PASS |
| Appointment and `COMPLETED -> BOOKED` commit atomically | `AppointmentRepository`, PostgreSQL | Failure-injection/repository tests; runtime fresh database query | PASS |
| Success returns persisted appointment and records reload `BOOKED` | Flask API, records API/UI | Persisted API test; runtime detail GET and PostgreSQL query | PASS |
| Invalid, repeated, mismatched, concurrent, and failed requests leave no partial/duplicate state | DTO/API/application/repository | Focused API matrix, rollback tests, two-session concurrency test, runtime repeat `409` | PASS |
| PostgreSQL is authoritative; React does not synthesize `BOOKED` | Repository/API and replacement navigation | Persisted API test; booking screen/service tests; runtime records GET | PASS |
| Messages, summary, recommendations, order/treatment, and projection remain unchanged | Focused repository write set | Repository and persisted API immutability tests; runtime GET/database checks | PASS |
| Tests are deterministic and booking invokes no AI/external calendar | Clock injection and strict AI doubles | Application/persisted API no-AI assertions; mock-provider Compose runtime | PASS |

## Migration and Persistence

- Alembic is linear: `20260817_03 -> 20260817_04`; Compose reported the upgrade
  and `alembic_version` returned `20260817_04`.
- Focused PostgreSQL tests passed upgrade, downgrade, and re-upgrade checks.
- Runtime inspection confirmed native UUID primary/foreign keys, required
  timezone-aware `scheduled_at`/`created_at`, `CURRENT_TIMESTAMP`, required
  `VARCHAR(200)` location, named nonblank/max-length checks, and unique
  `consultation_id`.
- Both foreign keys have no delete cascade. The table has no treatment copy or
  lifecycle/status column. Existing tables survive the migration round trip.

## Repository, Application, Concurrency, and API

- `AppointmentRepository` uses `SELECT ... FOR UPDATE`, exact existing-state
  and lineage reads, one insert/status commit, rollback/abort, persisted reload,
  and exact named unique-constraint reconciliation. Unrelated integrity errors
  propagate and are not classified as duplicates.
- Application tests cover fixed-clock future/equivalent-offset success,
  naive/exact-now/past failures, trimming, blank and 200/201 boundaries, UUID
  identity, all approved eligibility outcomes and precedence, abort behavior,
  duplicate reconciliation, unexpected failures, and strict no-AI behavior.
- The controlled independent-session concurrency test produces one committed
  appointment/`BOOKED` winner and one stable duplicate loser.
- The only appointment route is
  `POST /api/v1/consultations/{consultation_id}/appointments`. Route/DTO tests
  cover exact `201`, safe `400`, both `404`, all coded `409`, safe `500`, exact
  response shape/offsets, single delegation, and absence of internal leakage.

## Frontend

- `consultationApi` sends the exact three-field POST once, performs strict
  runtime linkage/value validation, maps only approved errors safely, does not
  retry ambiguous failures, and does not mutate consultation status.
- `AppointmentBookingScreen` owns the Feature 003 route, validates route/query
  context, loads the summary, resolves the selected stable recommendation,
  displays treatment read-only, validates and normalizes date/location input,
  prevents duplicate pending submission, preserves recoverable form state,
  handles coded/ambiguous errors safely, and uses replacement navigation to
  `/consultations` after confirmed success.

## Runtime Compose Slice

The existing stack built successfully. An unrelated running Docker project
already owned host port `5432`, so runtime verification used only supported
host-port overrides: `POSTGRES_PORT=55432`, `BACKEND_PORT=5500`, and
`FRONTEND_PORT=3300`. No Compose file was changed.

All three services started; PostgreSQL was healthy, Flask reached PostgreSQL
and migrated to `20260817_04`, and the frontend/backend were reachable. Using
an existing deterministic completed consultation, persisted summary, and
persisted recommendation:

- POST returned `201` with the persisted recommendation treatment;
- `scheduled_at` persisted as `2030-08-20 14:30:00+00`;
- location persisted normalized as `Runtime Downtown Clinic`;
- exactly one appointment linked the expected consultation/recommendation;
- consultation detail/records returned `BOOKED` from PostgreSQL;
- messages, summary, recommendation treatment/order, and
  `recommended_procedure` remained unchanged; and
- a second POST returned `409 APPOINTMENT_ALREADY_EXISTS` without overwriting
  the appointment.

## Commands and Results

- Backend focused:
  `.venv/bin/pytest -q tests/test_appointment_persistence.py tests/test_appointment_repository.py tests/application/test_appointment_booking_service.py tests/api/test_consultation_dtos.py tests/api/test_appointment_booking_routes.py tests/api/test_consultation_persistence_api.py`
  — **91 passed**, 0 failed/skipped, 11 Alembic configuration deprecation warnings.
- Backend complete: `.venv/bin/pytest -q tests` — **280 passed**, 0
  failed/skipped, 25 Alembic configuration deprecation warnings.
- Frontend complete: `npm test` — **181 passed** across 7 files, 0
  failed/skipped.
- `npm run typecheck`, `npm run lint`, and `npm run build` — PASS; production
  build transformed 940 modules.
- `docker compose config --quiet` and `docker compose build` — PASS.
- Compose `up`, `ps`, logs, HTTP probes, booking/repeat POSTs, and direct
  PostgreSQL schema/data queries — PASS with the host-port overrides above.
- `git diff --check` — PASS.

## Architecture, Secrets, and Scope

Final booking flow remains React -> `consultationApi` -> Flask consultation API
-> `ConsultationApplicationService` -> `AppointmentRepository` -> PostgreSQL.
The route imports no repository/session, the application imports no Flask, the
repository exposes no HTTP, and booking has no AI dependency. PostgreSQL owns
identity, linkage, uniqueness, values, and status; React owns no authorization
or local `BOOKED` transition.

Review found no Feature 004 secret exposure, `VITE_OPENAI_API_KEY`, live AI
booking, appointment GET/update/delete, multiple appointment behavior,
lifecycle status, reschedule/cancel, availability/conflict/hours, calendar,
notification, email/SMS, payment, authentication, dashboard, RAG, Redis,
vector database, LangGraph, WebSocket, streaming, or infrastructure redesign.

## Defects and Changes During AB-008

No approved Feature 004 behavior defect was found and no product code was
changed. AB-008 added this verification record and marked only AB-008 complete.
The initial default-port Compose start was interrupted by an unrelated
container owning port `5432`; supported environment overrides resolved it
without changing project configuration or stopping the other project.

Feature 004 — Appointment Booking is complete and verified.
