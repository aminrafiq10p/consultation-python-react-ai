# NC-001 Findings: Feature 006 Integration Boundaries

**Task:** NC-001 — Confirm Feature 006 Integration Boundaries  
**Inspection date:** 2026-08-19  
**Result:** Complete for the read-only boundary investigation. No product code,
tests, migrations, configuration, specification, or plan files were changed.

## 1. Evidence and working-tree boundary

Authoritative inputs inspected:

- `specs/features/006-new-consultation.md`
- `plans/features/006-new-consultation.md`
- `tasks/features/006-new-consultation/001-integration-boundaries.md`

Initial `git status --short` showed the complete Feature 006 specification,
plan, and task directory as untracked (`??`). They are preserved as user-owned
changes. No pre-existing tracked modifications were present in the initial
status output. The only file this task adds is this findings document.

## 2. Persistence boundary

Owner: `backend/app/infrastructure/consultation_models.py`.

`Consultation` maps exactly these five columns: `id` (`PostgreSQLUUID(as_uuid=True)`,
primary key, SQLAlchemy `default=uuid4`), `patient_name` (`Text`, non-null),
`primary_concern` (`Text`, non-null), `recommended_procedure` (`Text`, non-null),
and `status` (native PostgreSQL `consultation_status`, non-null). The Python
`ConsultationStatus` values are `PENDING`, `BOOKED`, and `COMPLETED`. The value
set matches the approved design; only declaration/table ordering differs from
the specification table, which lists `COMPLETED` before `BOOKED`.

The fresh-row convention is already demonstrated by the restart path and
repository tests: explicit `uuid4()`, the two source user values, empty
`recommended_procedure`, and `ConsultationStatus.PENDING`. No timestamp or
additional creation column exists.

Owner for creation transaction: `backend/app/repositories/consultation_repository.py`,
`ConsultationRepository.create_consultation`. It receives the request-scoped
SQLAlchemy `Session`, then performs exactly `add` → `commit` → `refresh`, and
returns the same consultation object. Any exception causes `rollback()` and is
re-raised. The repository owns this unit of work; the application service does
not commit and no new repository/session layer is needed.

## 3. Application boundary

Owner: `backend/app/application/consultation_service.py`,
`ConsultationApplicationService`.

The constructor injects `ConsultationRepository` plus optional message, AI,
summary, appointment, and clock dependencies. `self._repository` is the
creation seam. The existing `restart_consultation` method is the verified
construction convention: it checks the completed source and persisted summary,
constructs `Consultation(id=uuid4(), patient_name=..., primary_concern=...,
recommended_procedure="", status=PENDING)`, delegates once to
`self._repository.create_consultation`, and returns the repository result.

NC-002 should add the narrow creation workflow here, reuse the existing
repository, and keep message/summary/appointment/dashboard/AI dependencies out
of creation behavior. Existing application tests use mocks/strict injected
dependencies and are the seam for exact construction and one repository call.

## 4. API and DTO boundary

Owners:

- `backend/app/api/consultation_dtos.py`
- `backend/app/api/consultation_routes.py`
- `backend/app/__init__.py`

`ConsultationResponse` is the exact five-field response DTO, uses
`ConfigDict(from_attributes=True)`, and routes serialize it with
`model_dump(mode="json")`. Existing request DTOs use Pydantic v2,
`ConfigDict(extra="forbid")`, before validators for trimming, and
`StrictStr` where coercion must be forbidden. `_validation_error()` establishes
the safe exact 400 contract `{ "error": "Invalid request" }`.

The consultation blueprint is registered by `create_app` with
`url_prefix="/api/v1"`; existing collection and detail routes are therefore
`/api/v1/consultations` and `/api/v1/consultations/<consultation_id>`. The
creation route belongs in this same blueprint and resource hierarchy. The
application-wide exception handler returns `{ "error": "Internal server
error" }` with 500 for unexpected non-HTTP exceptions. Injected-service route
tests use `create_app(Mock(spec=ConsultationApplicationService))` and Flask's
test client; these provide the safe-error and no-service-call seam.

NC-003 can extend the existing response serializer and injected service without
loosening existing validators or creating a parallel blueprint.

## 5. Request-scoped database/runtime composition

In production composition (`backend/app/__init__.py`), `create_app` creates one
engine and session factory. `before_request` opens one session, stores it as
`app.extensions["consultation_session"]`, and constructs consultation,
message, summary, appointment, and dashboard repositories around that same
session. It injects `ConsultationApplicationService` and
`DashboardApplicationService` through `app.extensions`. `teardown_request`
removes the services/session and closes that one session. Injected-service mode
is available for API tests and does not create a database session.

`compose.yaml` supplies PostgreSQL 16, Flask, Vite, CORS/API URL, health-check,
volume, and optional AI environment configuration. `backend/Dockerfile` runs
`alembic upgrade head` before Flask. Feature 006 needs no Compose service,
dependency, environment variable, port, volume, or health-check change.

## 6. Migration and PostgreSQL test evidence

Migration chain inspected:

```text
20260813_01_create_consultations  (head ancestor: None)
20260813_02_create_messages       (down: 20260813_01)
20260817_03_create_consultation_summaries (down: 20260813_02)
20260817_04_create_appointments   (down: 20260817_03)  <-- current head
```

The consultation table and native enum are created by the first revision;
there is no Feature 006 migration and none is required. PostgreSQL fixtures in
`backend/tests/conftest.py` launch an isolated `postgres:16-alpine` container,
wait for readiness, yield a published connection URL, and force-remove the
container during fixture cleanup. Persistence/repository fixtures run Alembic
to `head` and use real SQLAlchemy sessions.

Foreign-key cleanup order is consistently child-to-parent: `appointments`,
`consultation_recommendations`, `consultation_summaries`, `messages`, then
`consultations`. This order must be retained for NC-007/NC-008 PostgreSQL
coverage. Existing persistence tests verify fresh-session reads and rollback
behavior.

## 7. Frontend service/types boundary

Owners:

- `frontend/src/app/features/consultation-records/consultationTypes.ts`
- `frontend/src/app/features/consultation-records/consultationApi.ts`

`ConsultationRecord` already models the authoritative five-field response and
the status union is `PENDING | BOOKED | COMPLETED`. The injectable
`FetchTransport` and `createConsultationApi` factory establish the HTTP seam.
The service constructs URLs from `VITE_API_BASE_URL`, uses `safeRequest`, maps
HTTP outcomes to typed `ConsultationApiError` kinds/messages, requires exact
successful status where operation-specific code does so, parses JSON safely,
and runtime-validates UUIDs, strings, statuses, and response shapes before
returning them. Existing API tests stub transport and assert request/malformed
response/error behavior.

NC-004 should add the creation request/response operation to these existing
modules, preserving injectable transport, one-shot request behavior at screen
level, safe recoverable errors, and runtime validation of the returned record.

## 8. Router, layout, and responsive navigation boundary

`frontend/src/app/core/App.tsx` owns one nested React Router tree beneath
`AppLayout`. Current order is the static `/consultations` route followed by
parameterized `consultations/:consultationId`, summary, and appointment routes.
The static `consultations/new` route must be registered before the parameter
route so `new` is never treated as an ID. Existing detail/summary/appointment
paths must remain unchanged.

`frontend/src/app/layout/AppLayout.tsx` owns `SidebarContent`, shared by the
permanent desktop drawer and temporary mobile drawer. The `+ New Consult`
button is currently a disabled MUI `Button` with no navigation behavior. The
consultations active rule is exactly `pathname === "/consultations" ||
pathname.startsWith("/consultations/")`, so `/consultations/new` remains in
Consultations context. Mobile passes `onNavigate={() => setMobileOpen(false)}`
to `SidebarContent`; desktop does not. NC-005/NC-006 should activate the
shared control and preserve that callback behavior. Existing layout/router
tests use `MemoryRouter`, RTL, and deterministic `matchMedia` setup.

## 9. Downstream task ownership and independence

| Task | Verified seam |
| --- | --- |
| NC-002 | `ConsultationApplicationService` + `ConsultationRepository.create_consultation`; strict construction/injection tests |
| NC-003 | Existing consultation blueprint, Pydantic DTO module, response serializer, `/api/v1` prefix, injected Flask service tests |
| NC-004 | `consultationTypes.ts` and injectable `consultationApi.ts` transport/runtime validation |
| NC-005 | `App.tsx` static route precedence and focused creation screen under `AppLayout` |
| NC-006 | Shared `SidebarContent`, disabled button, active-route rule, mobile close callback |
| NC-007 | Real PostgreSQL/Alembic fixtures, same-session composition, child-first cleanup, dashboard read authority |
| NC-008 | Existing focused/full backend/frontend commands plus Compose/diff/migration checks |

NC-002 and NC-004 can begin independently: the backend application boundary
and frontend HTTP boundary are separate and neither requires the other’s
implementation. No material architecture conflict was found.

## 10. Supported verification commands

Run from the repository root unless noted:

```bash
# Repository/diff validation
git status --short
git diff --check
git diff -- tasks/features/006-new-consultation/NC-001-findings.md
git status --short --untracked-files=all

# Backend (from backend/)
cd backend && pytest -q tests/api/test_consultation_dtos.py tests/api/test_consultation_routes.py tests/application/test_consultation_service.py
cd backend && pytest -q tests
cd backend && alembic upgrade head

# Frontend (from frontend/)
cd frontend && npm test -- --run
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run build

# Runtime/configuration
docker compose config
docker compose up --build
```

NC-001 itself does not run feature tests, per the task’s read-only testing
requirement. The commands above are the repository-supported commands for the
downstream tasks and final verification; `alembic upgrade head` and Compose
operations require a configured PostgreSQL/runtime environment.

## 11. Conclusion

The approved Feature 006 design can proceed unchanged at the architectural
level: PostgreSQL remains authoritative, creation reuses the existing
repository transaction, production requests use one SQLAlchemy session, the
existing consultation API hierarchy is extended, and routing/layout remain
shared. The only noted mismatch is declaration/table ordering of the already
matching status values (`BOOKED` and `COMPLETED`), with no behavioral impact.

**NC-001 acceptance:** satisfied. No tracker file exists for NC-001 outside
the task checklist in the proposed specification; that checklist and all
authoritative inputs were intentionally left unchanged. NC-002 and NC-004 are
safe to start in parallel. This work stops here.
