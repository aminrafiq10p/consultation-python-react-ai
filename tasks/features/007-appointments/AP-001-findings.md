# AP-001 Findings — Feature 007 Integration Boundaries

**Inspection date:** 2026-08-19
**Task:** AP-001, read-only boundary confirmation

## Result

The approved Feature 007 architecture aligns with the repository. No
architecture conflict or blocker was found. Feature 004 remains the only
appointment write system; Feature 007 can add a focused joined read through
the existing appointment repository and consultation application service.

## Boundary map

| Boundary | Confirmed current seam | AP-001 ownership / consequence |
| --- | --- | --- |
| Persistence | `backend/app/infrastructure/consultation_models.py`: `Appointment` stores `id`, `consultation_id`, `recommendation_id`, `scheduled_at`, `location`, `created_at`; `Consultation.patient_name`; recommendation lineage is `ConsultationRecommendation.summary_id -> ConsultationSummary`, whose `consultation_id` identifies the consultation. Appointment consultation identity is unique. | AP-002 may add one explicit joined read. No model, column, constraint, or migration is needed. ORM relationship attributes are not defined, so joins must remain explicit. |
| Repository | `backend/app/repositories/appointment_repository.py`, `AppointmentRepository`, currently owns booking locking, reads, transaction/commit, and post-create `AppointmentAggregate` reload. | Reuse this repository. Keep `AppointmentAggregate` and the Feature 004 booking response unchanged; add a read-specific projection only in AP-002. |
| Application | `backend/app/application/consultation_service.py`, `ConsultationApplicationService`, receives `AppointmentRepository` as an optional dependency and exposes `book_appointment()` through the existing boundary. | AP-003 can delegate one `list_appointments()` read. The service is currently provider-neutral and does not depend on Flask or SQLAlchemy query construction. |
| API / DTOs | `backend/app/api/consultation_routes.py` owns the versioned `consultation_blueprint`, registered at `/api/v1`; `consultation_dtos.py` uses Pydantic DTOs and explicit `model_dump(mode="json")`. The existing booking route is `POST /consultations/<consultation_id>/appointments`; no appointment-list endpoint exists. | AP-004 should add `GET /appointments` to this blueprint with a dedicated envelope/DTO. Existing `_validation_error()` returns `{"error": "Invalid request"}`, 400. Unexpected exceptions are handled by `create_app` as `{"error": "Internal server error"}`, 500. |
| Request shape | Existing no-body read routes validate query/path input; `_has_request_body()` uses cached raw request data. The approved list contract requires rejecting any query parameter or non-empty body before service access. | AP-004 owns exact request-shape validation and zero-call tests. |
| Session composition | `backend/app/__init__.py` creates one engine/session factory and opens one `Session` per request in `before_request`; consultation, message, summary, and appointment repositories share that session. Teardown closes it. Injected services remain supported for tests. | AP-005 must preserve this composition; no new engine, session factory, or repository hierarchy. |
| Dashboard | `backend/app/repositories/dashboard_repository.py` counts `Appointment.id` directly in a scalar subquery; `DashboardApplicationService` and the dashboard API consume that persisted count. | No dashboard change or synchronization callback is required. AP-008 verifies re-reading the same rows. |
| Frontend route shell | `frontend/src/app/core/App.tsx` owns nested routes under `AppLayout`; current routes include dashboard, consultation list/detail/summary, and Feature 004 booking. | AP-010 owns `/appointments`; preserve all existing consultation routes. |
| Frontend navigation | `frontend/src/app/layout/AppLayout.tsx` owns one `navigationItems` array used by both the permanent desktop drawer and temporary mobile drawer. Active state is currently explicit (`/dashboard`, or `/consultations` and descendants), and mobile link activation closes the drawer. | AP-012 owns adding one Appointments item and exact `/appointments` descendant matching. No second navigation system is needed. |
| Frontend transport / validation | Dashboard uses a feature-local `dashboardApi`, injected `FetchTransport`, `VITE_API_BASE_URL`, safe typed errors, one request, exact response-key validation, and tests with Vitest/RTL. Consultation APIs use the same base URL and strict UUID/timestamp/runtime validation patterns. | AP-009 owns a dedicated appointment-list service/types and must not derive data from booking state, dashboard state, consultation records, or browser storage. |
| Fixtures / tests | Backend PostgreSQL fixtures are in `backend/tests/conftest.py`; they create an isolated `postgres:16-alpine` Docker container and cleanup in fixture teardown. Existing appointment coverage is in `test_appointment_persistence.py` and `test_appointment_repository.py`, with application/API tests under `backend/tests/application` and `backend/tests/api`. Frontend tests are colocated `*.test.ts(x)` files using Vitest and React Testing Library. | Later PostgreSQL tests must delete appointments before recommendation/summary/consultation rows and coordinate one fixture owner. |
| Migration / dependencies | Linear Alembic head is `20260817_04`, `backend/migrations/versions/20260817_04_create_appointments.py`; Feature 007 requires no migration. Backend dependencies already include Flask, Pydantic, SQLAlchemy, Alembic, psycopg, and AI packages; frontend package scripts are `test`, `typecheck`, `lint`, and `build`. | No dependency or schema change is required. |
| Docker / runtime | `compose.yaml` defines PostgreSQL 16, backend, and frontend. Backend startup runs `alembic upgrade head` before Flask; frontend uses `VITE_API_BASE_URL`. | Later runtime checks use `docker compose config`, `docker compose build`, and the existing Compose flow. |

## Coordination and safe parallelization

- AP-002 owns `appointment_repository.py`; AP-003 owns the application service;
  AP-004 owns list DTO/API route changes; AP-005 owns composition checks.
- AP-009 is safe to start in parallel with AP-002 because it owns feature-local
  frontend appointment types/service files.
- AP-010 follows AP-009 and the API contract; AP-011 owns appointment item
  presentation/link behavior; AP-012 owns `App.tsx`/`AppLayout.tsx` navigation.
- Do not concurrently edit shared route/service/repository/shell files or
  PostgreSQL fixtures without explicit ownership transfer and reconciliation.

## Checks and commands recorded

The following are the established checks for later Feature 007 stages:

```text
cd backend && .venv/bin/pytest -q tests
cd frontend && npm test
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run build
cd backend && .venv/bin/alembic heads
docker compose config --quiet
docker compose build
docker compose up --build
git status --short
git diff --check
```

In this boundary-only pass, `git diff --check` passed. The local `alembic`
command is not on PATH, so the migration head was confirmed by inspecting the
linear revision chain, ending at `20260817_04`. No product tests or static
checks were changed or required to establish AP-001 boundaries.

## Worktree and deviations

At inspection, the worktree contains only untracked Feature 007 specification,
plan, and task files supplied for this work:

```text
?? plans/features/007-appointments.md
?? specs/features/007-appointments.md
?? tasks/features/007-appointments/
```

These files were preserved. No product source, test, migration, dependency,
Compose file, or Feature 004 implementation was changed. No consultation
service incompatibility was found, and no alternative architecture is needed.
