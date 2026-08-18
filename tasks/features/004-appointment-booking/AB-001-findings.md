# AB-001 Integration Boundary Findings

Verified against the approved Feature 004 specification and implementation
plan, the AB-001 task definition, completed Features 001–003, current tests,
and the Docker Compose runtime. These findings describe the repository before
appointment implementation; no appointment product code exists yet.

## Persistence and Alembic

- The linear Alembic head is
  `backend/migrations/versions/20260817_03_create_consultation_summaries.py`,
  with `revision = "20260817_03"` and
  `down_revision = "20260813_02"`. Existing filenames use
  `YYYYMMDD_NN_<description>.py`, and revision values use `YYYYMMDD_NN`.
  AB-002 must add one revision whose `down_revision` is exactly
  `20260817_03`.
- The infrastructure-owned declarative `Base` and all current mappings are in
  `backend/app/infrastructure/consultation_models.py`; Alembic imports that
  metadata from `backend/migrations/env.py`.
- IDs use PostgreSQL `UUID(as_uuid=True)`, Python `UUID`, and mapping defaults
  of `uuid4`. UUIDs become strings only through Pydantic JSON mode and frontend
  representations.
- Timestamps use `DateTime(timezone=True)`, `nullable=False`, and server
  `CURRENT_TIMESTAMP`. PostgreSQL persistence tests verify timezone-aware
  reloads through fresh sessions.
- Constraints and indexes are explicitly named in mapping/migration pairs.
  Foreign keys have no delete cascade. Text that must be nonblank uses named
  PostgreSQL `btrim(...) <> ''` checks.
- `ConsultationStatus` is a Python `str, Enum` mapped to the named native
  PostgreSQL enum `consultation_status` with `validate_strings=True`. Its exact
  values are `PENDING`, `BOOKED`, and `COMPLETED`; Feature 004 needs no enum
  migration.

## Summary and Recommendation Lineage

- The persisted parent is `ConsultationSummary`, table
  `consultation_summaries`. Its ownership field is
  `ConsultationSummary.consultation_id`, a required UUID foreign key to
  `consultations.id`, protected by
  `uq_consultation_summaries_consultation_id`.
- The persisted child is `ConsultationRecommendation`, table
  `consultation_recommendations`. Its stable identity is
  `ConsultationRecommendation.id`; its exact ownership field is
  `ConsultationRecommendation.summary_id`, a required UUID foreign key to
  `consultation_summaries.id`. Its authoritative display fields are
  `treatment` and `position`.
- The mappings define no ORM `relationship()` properties. `SummaryRepository`
  explicitly loads the summary by `consultation_id`, then recommendations by
  `summary_id`, ordered by `(position, id)`, and returns frozen
  `SummaryAggregate(summary, recommendations)`.
- Appointment ownership must therefore be proven with the explicit chain
  `recommendation.summary_id == summary.id` and
  `summary.consultation_id == locked consultation.id`. Matching treatment text
  is irrelevant, and the appointment must not copy treatment.

## Repository and Transaction Conventions

- Focused repositories live in `backend/app/repositories/`, accept one
  SQLAlchemy `Session` in `__init__`, use SQLAlchemy 2 `select` plus
  `Session.scalar/scalars`, and return mapped rows, collections, or small
  frozen dataclasses.
- Write repositories own their transaction mechanics. The simple pattern in
  `ConsultationRepository` and `MessageRepository` is
  `add → commit → refresh`, with `rollback → re-raise` on any failure.
- The closest atomic/race precedent is
  `SummaryRepository.complete_consultation`: add parent, flush for its ID, add
  children, mutate the consultation, commit once, and reload the persisted
  aggregate. Any general failure rolls back. An `IntegrityError` is rolled
  back before classification; only
  `error.orig.diag.constraint_name` matching the named expected unique
  constraint is reconciled, followed by an authoritative winner reload.
  Missing winner state or any other constraint is re-raised.
- `create_session_factory` sets `expire_on_commit=False` and documents that a
  failed unit must be rolled back before reuse. Existing tests prove a
  repository-managed rollback leaves the session usable.
- There is currently no `SELECT FOR UPDATE` use and no generic unit-of-work
  class. For AB-003, the smallest repository-consistent design is a focused
  `AppointmentRepository` using `select(Consultation).with_for_update()` as
  the first coordinated load, with all subsequent appointment/status,
  summary/recommendation, insert, and update work in that same session and
  transaction.
- The booking repository must expose an explicit rollback/abort operation for
  typed eligibility exits after the lock. The successful path is
  locked consultation load → existing appointment/status reads → lineage
  reads → add/flush appointment → set only status to `BOOKED` → one commit →
  persisted appointment/recommendation reload. A duplicate constraint path is
  rollback → exact named-constraint check → fresh authoritative appointment
  lookup. This extends the summary precedent; it does not require an
  architecture redesign.
- A post-commit reload failure cannot undo the committed transaction. It must
  remain an unexpected safe failure, with a later POST reconciling against the
  authoritative appointment/`BOOKED` state.

## Session Composition and Application Conventions

- `backend/app/__init__.py:create_app` is the sole production composition
  boundary. Without an injected service it creates one engine/session factory,
  then opens exactly one session in `before_request`. The consultation,
  message, and summary repositories all receive that same request session.
  `teardown_request` removes the request extensions and closes the session.
- Routes resolve the current service from
  `current_app.extensions["consultation_service"]`. Supplying
  `create_app(consultation_service)` bypasses production persistence
  composition and is the API-test injection seam.
- `ConsultationApplicationService` is in
  `backend/app/application/consultation_service.py`. Its constructor is
  positional and progressively optional after the required
  `ConsultationRepository`:
  `repository, message_repository=None, ai_service=None,
  summary_repository=None`. AB-004 can append optional appointment-repository
  and clock parameters without breaking existing one- and four-argument
  construction.
- Application methods own business orchestration and defensive invariants,
  import neither Flask nor provider SDKs, and return mapped objects or frozen
  result dataclasses. Missing dependencies are guarded by focused helper
  methods that raise `RuntimeError`.
- Typed outcomes are application exceptions in the service module:
  `ConsultationNotFoundError` plus focused `ValueError`/`RuntimeError`
  subclasses for invalid or business/recoverable outcomes. Routes translate
  them to HTTP; repositories do not construct HTTP responses. AB-004 should
  place the approved booking outcomes and committed result value here unless a
  later task establishes a separate outcome module (none exists now).

## Flask API and DTO Conventions

- The single `consultation_blueprint` is in
  `backend/app/api/consultation_routes.py` and is registered once at
  `/api/v1`. AB-005 adds only
  `POST /consultations/<consultation_id>/appointments` to this blueprint,
  producing the public path
  `POST /api/v1/consultations/{consultation_id}/appointments`.
- DTOs are in `backend/app/api/consultation_dtos.py`. Inputs use Pydantic v2
  explicit fields and `ConfigDict(extra="forbid")`; mapped responses use
  `ConfigDict(from_attributes=True)` where appropriate. Routes catch
  `ValidationError`, delegate once, build response DTOs, and serialize with
  `model_dump(mode="json")` through `jsonify`.
- Path UUID validation uses `ConsultationDetailPath`. Invalid path/body is the
  exact safe envelope `400 {"error":"Invalid request"}`. Not-found outcomes
  use safe `404` envelopes. Business conflicts use safe `error` text plus an
  exact stable `code`. The app-wide handler preserves Werkzeug errors and maps
  every other exception to `500 {"error":"Internal server error"}`.
- API route tests use `Mock(spec=ConsultationApplicationService)`, inject it
  with `create_app(service)`, enable `TESTING`, and assert exact service calls,
  response bodies, and absence of internal detail. Persisted API tests instead
  construct the real service/repositories over a PostgreSQL session and inject
  that service into `create_app`.
- The approved booking boundary remains the exact three-field request
  (`recommendation_id`, explicit-offset `scheduled_at`, `location`), exact
  nested recommendation success projection, `201`, two safe `404` outcomes,
  three coded `409` outcomes, and safe `400`/`500` outcomes described in the
  specification. No current API convention conflicts with it.

## Frontend Service, Router, and Handoff

- The feature root is
  `frontend/src/app/features/consultation-records/`. Transport-facing types are
  in `consultationTypes.ts`; `consultationApi.ts` is the only HTTP boundary.
- `createConsultationApi` accepts an injectable fetch-compatible transport,
  constructs the base URL from `VITE_API_BASE_URL`, URI-encodes path IDs,
  sends explicit method/header/body options, runtime-validates unknown JSON,
  and maps only known status/code combinations to safe
  `ConsultationApiError` kinds. UUID and explicit-offset timestamp regular
  expressions already exist. Tests use transport doubles and assert requests,
  malformed responses, and safe error mapping.
- Summary runtime validation requires a UUID `id`, a UUID
  `consultation_id` equal to the requested ID, nonblank summary text, at least
  one ordered unique recommendation, valid explicit-offset `created_at`, and
  valid recommendation UUID/treatment/position. The booking screen can reuse
  `consultationApi.summary(consultationId)` and then select by stable ID.
- Routes are centralized as nested `<Route>` elements under `AppLayout` in
  `frontend/src/app/core/App.tsx`; production uses `BrowserRouter`, while tests
  use `MemoryRouter`. Screens use `useParams`, `useNavigate`, injectable
  default service props, discriminated async state, MUI controls/feedback, and
  colocated Vitest/React Testing Library tests.
- Feature 003's exact handoff is implemented in
  `ConsultationSummaryScreen.tsx`: the selected persisted recommendation ID is
  encoded with `URLSearchParams({ recommendation_id: selectedId })` and
  navigation targets
  `/consultations/${encodeURIComponent(consultationId)}/appointments/new?recommendation_id=<encoded UUID>`.
- `App.tsx` already owns the matching route pattern
  `consultations/:consultationId/appointments/new`. Its exact placeholder is
  `frontend/src/app/features/consultation-records/AppointmentUnavailableScreen.tsx`,
  rendered as `<AppointmentUnavailableScreen />`. `App.test.tsx` currently
  asserts the placeholder and no form. AB-007 replaces that component/route
  ownership while preserving the path/query contract and updates that test.

## PostgreSQL, Concurrency, and Cleanup

- `backend/tests/conftest.py` starts one session-scoped disposable
  `postgres:16-alpine` container, binds it to a random loopback port, waits for
  `pg_isready` and a real SQLAlchemy connection, yields the database URL, and
  force-removes the container in fixture teardown.
- Focused persistence/repository suites programmatically configure Alembic and
  upgrade to `head`, create an engine and sessionmaker with
  `expire_on_commit=False`, clean before and after each test, and verify
  authoritative state through fresh sessions.
- Current FK-safe cleanup is recommendations → summaries → messages →
  consultations, either with `sessionmaker.begin()` plus SQL `DELETE` or ORM
  deletes in API fixtures. Once AB-002 creates appointments, every cleanup
  touching those parents must delete appointments first.
- The existing concurrency precedent is
  `backend/tests/test_summary_repository.py`: `ThreadPoolExecutor(max_workers=2)`,
  `threading.Barrier(2)` with a bounded timeout, and one independently created
  and closed SQLAlchemy session per worker. Results are collected after join,
  then row counts and winner identity are checked in a fresh session. AB-003
  should reuse this pattern; sessions must never be shared between threads and
  sleeps must not coordinate the race.

## Docker and Verification Commands

- Root `compose.yaml` defines `postgres:16-alpine` with healthcheck and named
  volume, a backend depending on healthy PostgreSQL, and a Vite frontend
  depending on the backend. No Compose service, environment variable, port,
  volume, or dependency is needed for booking.
- `backend/Dockerfile` runs
  `alembic upgrade head && flask --app 'app:create_app()' run
  --host=0.0.0.0 --port=5000`; therefore every backend container startup
  migrates before serving. The root runtime command is
  `docker compose up --build`.
- Applicable later-task commands are:
  - from `backend/`: `alembic upgrade head` and explicit downgrade/upgrade
    round trips for AB-002;
  - from `backend/`: focused `pytest -q <test paths>` followed by
    `pytest -q tests` for AB-002 through AB-005/AB-008;
  - from `frontend/`: `npm test`, `npm run typecheck`, `npm run lint`, and
    `npm run build` for AB-006 through AB-008;
  - from the repository root: `docker compose up --build` for AB-008 runtime
    verification.

## Expected Files by Later Task

| Task | Exact expected files/areas |
| --- | --- |
| AB-002 | `backend/app/infrastructure/consultation_models.py`; one new `backend/migrations/versions/<revision>_create_appointments.py`; new `backend/tests/test_appointment_persistence.py`; appointment-first cleanup in PostgreSQL fixtures that delete recommendation/summary/consultation rows |
| AB-003 | new `backend/app/repositories/appointment_repository.py`; `backend/app/repositories/__init__.py` only if exports become necessary (it is currently empty); new focused repository/rollback/concurrency tests, most naturally `backend/tests/test_appointment_repository.py` |
| AB-004 | `backend/app/application/consultation_service.py`; new `backend/tests/application/test_appointment_booking_service.py`; only constructor-compatible adjustments to existing application fixtures if required |
| AB-005 | `backend/app/__init__.py`; `backend/app/api/consultation_dtos.py`; `backend/app/api/consultation_routes.py`; `backend/tests/api/test_consultation_dtos.py`; `backend/tests/api/test_consultation_routes.py` and/or a focused booking route file; `backend/tests/api/test_consultation_persistence_api.py` and/or a focused persisted booking API file |
| AB-006 | `frontend/src/app/features/consultation-records/consultationTypes.ts`; `consultationApi.ts`; `consultationApi.test.ts` (or one colocated focused booking service test) |
| AB-007 | new `frontend/src/app/features/consultation-records/AppointmentBookingScreen.tsx` and `.test.tsx`; `frontend/src/app/core/App.tsx`; `frontend/src/app/core/App.test.tsx`; remove `AppointmentUnavailableScreen.tsx` after replacement; retain/update `ConsultationSummaryScreen.test.tsx` only to preserve handoff coverage |

AB-002 and AB-006 have independent, fully specified integration seams after
this confirmation. AB-003 follows AB-002; AB-004 follows AB-003; AB-005 follows
AB-004; AB-007 follows AB-006.

## Working Tree and Conflict Review

- The pre-task worktree was already dirty: `README.md` was modified, and the
  approved Feature 004 spec, plan, and task directory were untracked. These are
  user-owned changes and were preserved. Generated `.venv`, cache, and
  `__pycache__` artifacts were inspected only and not modified intentionally.
- No repository/specification/plan conflict was found. The plan's current-head,
  mapping, shared-session, service-injection, error, route/query, frontend,
  PostgreSQL concurrency, and Compose assumptions all match repository reality.
- One implementation-precedent gap exists but is not a conflict: current
  repositories do not lock rows. The approved consultation row lock fits the
  existing focused repository/shared-session design via SQLAlchemy
  `with_for_update()` and needs no new architecture.
- No product code, migration, test, dependency, Docker/Compose file, or
  appointment functionality was created or changed by AB-001.

