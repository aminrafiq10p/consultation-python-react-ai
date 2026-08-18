# DN-001 Integration Boundary Findings

**Task:** DN-001 — Confirm Feature 005 Integration Boundaries

**Evidence date:** 2026-08-18

**Scope:** Repository discovery and boundary confirmation only

## 1. Evidence inspected

- Approved Feature 005 specification, plan, and DN-001 through DN-008 task
  definitions under `specs/features/`, `plans/features/`, and
  `tasks/features/005-dashboard-navigation/`.
- Flask composition and infrastructure: `backend/app/__init__.py`,
  `backend/app/infrastructure/database.py`, and
  `backend/app/infrastructure/consultation_models.py`.
- Existing repositories and application/API boundaries under
  `backend/app/repositories/`, `backend/app/application/`, and
  `backend/app/api/`.
- Alembic environment and every revision under `backend/migrations/`.
- PostgreSQL fixtures and representative repository, persistence, application,
  API, and vertical-slice tests under `backend/tests/`.
- AI composition under `backend/app/ai/` and environment coverage in
  `backend/tests/test_environment_configuration.py`.
- Frontend router, layout, feature services/types/screens, and tests under
  `frontend/src/`, plus `frontend/package.json` and `frontend/vite.config.ts`.
- `compose.yaml`, both Dockerfiles, all three environment examples, and runtime
  commands in `README.md` and `backend/README.md`.

## 2. Backend composition boundary

`backend/app/__init__.py:create_app` currently has the exact signature
`create_app(consultation_service: ConsultationApplicationService | None = None)
-> Flask`. It calls `load_dotenv(BACKEND_ENV_FILE, override=False)`, where
`BACKEND_ENV_FILE` resolves to `backend/.env`, before creating the Flask app.
It configures CORS for `/api/v1/*` from `FRONTEND_ORIGIN` (default
`http://localhost:3000`) and stores only the boolean
`OPENAI_API_KEY_CONFIGURED` in Flask configuration.

When no service is injected, `create_app` obtains the PostgreSQL URL through
`database_url_from_environment()`, calls `create_database_engine()` and
`create_session_factory()`, creates one provider-neutral `AIService`, and
stores the engine at `app.extensions["database_engine"]`. The registered
`before_request` callback creates exactly one SQLAlchemy `Session`, stores it
as `app.extensions["consultation_session"]`, constructs
`ConsultationRepository`, `MessageRepository`, `SummaryRepository`, and
`AppointmentRepository` with that same session object, and composes one
`ConsultationApplicationService` under the `consultation_service` extension
key. The `teardown_request` callback pops the session and service keys and
closes the shared session; it does not commit.

When `consultation_service` is supplied, it is stored directly under
`app.extensions["consultation_service"]`; engine, session factory, request
hooks, repositories, and AI are not constructed. Existing API tests rely on
both positional `create_app(service)` and named
`create_app(consultation_service=...)` injection.

Only `consultation_blueprint` is registered today, with the application factory
owning the `/api/v1` prefix through
`app.register_blueprint(consultation_blueprint, url_prefix="/api/v1")`.
The global `Exception` handler passes through Werkzeug `HTTPException` values
and maps every other uncaught exception to the exact safe response
`{"error": "Internal server error"}` with status 500.

### Confirmed later Dashboard seam

DN-004 should extend the signature without changing the first argument:

```python
def create_app(
    consultation_service: ConsultationApplicationService | None = None,
    dashboard_service: DashboardApplicationService | None = None,
) -> Flask:
```

The compatibility rule is material: production engine/session/AI composition
occurs only when **neither** service is injected. If either focused service is
injected, install only the non-`None` supplied extension(s) and do not
synthesize unrelated production dependencies. This preserves existing
consultation API tests and lets dashboard API tests use
`create_app(dashboard_service=double)` without requiring PostgreSQL or AI.
Production `before_request` should create `DashboardRepository(session)` and
`DashboardApplicationService(...)` from the already-open session and store it
as `app.extensions["dashboard_service"]`. Teardown should pop that request
service and still close the single `consultation_session`; renaming the session
key is unnecessary and risks existing assumptions. Missing extension access
is safely covered by the global 500 handler.

## 3. Repository conventions and DN-002 boundary

Focused repositories live in `backend/app/repositories/<subject>_repository.py`,
use PascalCase `<Subject>Repository`, accept `sqlalchemy.orm.Session` in
`__init__`, and retain it as `_session`. SQLAlchemy 2.x `select()` with
`session.scalar()`, `session.scalars()`, or `session.execute()` is the current
query style. Immutable multi-value results use `@dataclass(frozen=True)`, as in
`SummaryAggregate`, `SummaryCompletion`, `AppointmentAggregate`, and
`AppointmentCreation`.

Read methods do not commit or mutate. Write repositories explicitly own
`add`/`flush`/`commit`, roll back failures, and refresh or reload persisted
results. The dashboard read is therefore a focused read-only repository
operation, not a consultation-service or unit-of-work extension.

DN-002 has the following exact owner and imports:

- file: `backend/app/repositories/dashboard_repository.py`;
- classes: immutable `DashboardCounts` and `DashboardRepository`;
- model imports: `Consultation` and `Appointment` from
  `app.infrastructure.consultation_models`;
- one public `get_counts()` operation;
- one outer `select` containing independent
  `select(func.count(Consultation.id)).scalar_subquery()` and
  `select(func.count(Appointment.id)).scalar_subquery()` expressions;
- one session execution, two scalar integer values, and no mapped collection,
  join, status predicate, lock, add, flush, commit, rollback, or mutation.

The independent scalar subqueries avoid appointment/consultation row
multiplication while satisfying the one-repository-operation and one-statement
read-consistency requirement. `backend/app/repositories/__init__.py` has a
lightweight explicit export list, but direct module imports are common; adding
an export is optional rather than required architecture.

## 4. Authoritative persistence and Alembic state

All mappings share `Base` in
`backend/app/infrastructure/consultation_models.py`, which Alembic imports as
`target_metadata` in `backend/migrations/env.py`.

- `Consultation` is the authoritative `consultations` mapping. Its status is
  the native PostgreSQL `consultation_status` enum with `PENDING`, `BOOKED`, and
  `COMPLETED`; DN-002 must count every row without a status condition.
- `Appointment` is the authoritative `appointments` mapping. Its required
  `consultation_id` foreign key targets `consultations.id`; its required
  `recommendation_id` targets `consultation_recommendations.id`; and
  `uq_appointments_consultation_id` enforces at most one appointment per
  consultation. DN-002 must count these rows directly, not infer them from
  consultation status.

The linear migration chain ends at revision/head **`20260817_04`** in
`backend/migrations/versions/20260817_04_create_appointments.py`, whose
`down_revision` is `20260817_03`. Existing tables, foreign keys, and uniqueness
fully support both counts. Feature 005 needs no table, column, index,
constraint, enum, or Alembic revision.

## 5. PostgreSQL test infrastructure

The session-scoped `postgresql_url` fixture in `backend/tests/conftest.py`
starts an isolated `postgres:16-alpine` Docker container on a random published
localhost port, waits with `pg_isready` and a real SQLAlchemy connection, yields
a `postgresql+psycopg` URL, and force-removes the temporary container during
fixture cleanup. These tests therefore require a working local Docker daemon;
they do not use the project's long-running Compose PostgreSQL service.

Repository suites define module-scoped `migrated_database_url(postgresql_url)`,
configure `backend/alembic.ini` plus the absolute `backend/migrations` script
location, and run `command.upgrade(config, "head")`. They build engines and
session factories with either the infrastructure helpers or equivalent
SQLAlchemy calls. Cleanup deletes in foreign-key order:

1. `appointments`;
2. `consultation_recommendations`;
3. `consultation_summaries`;
4. `messages`;
5. `consultations`.

`backend/tests/test_appointment_repository.py` provides the most current
`migrated_database_url`, `database`, `_clean`, and `_persist_lineage` patterns.
`backend/tests/test_consultation_repository.py` provides the direct `db_session`
pattern and mixed-status consultation seeding. DN-002 should reuse
`postgresql_url` and these local fixture conventions rather than add global
database infrastructure. DN-008 can follow
`backend/tests/api/test_consultation_persistence_api.py:persisted_client` for a
real repository/service/API slice, explicit child-first cleanup, session close,
and engine disposal.

## 6. Application layer and DN-003 seam

Application workflows live in `backend/app/application/<subject>_service.py`.
`ConsultationApplicationService` uses constructor injection, typed application
exceptions, immutable dataclass results, and deterministic injected
dependencies (including a clock where needed). Application unit tests under
`backend/tests/application/` use `Mock(spec=...)` or strict purpose-built
doubles and do not require Flask or PostgreSQL. SQLAlchemy query mechanics stay
in repositories, although the existing broad consultation service necessarily
passes mapped persistence values through its workflows.

DN-003 should add the separate file
`backend/app/application/dashboard_service.py`, with immutable
`DashboardMetrics` and focused `DashboardApplicationService`, instead of
expanding the already multi-workflow `ConsultationApplicationService`. Its
constructor receives only `DashboardRepository` (or a narrow count-repository
protocol), and `get_metrics()` calls `get_counts()` once. A strict unit double
belongs in `backend/tests/application/test_dashboard_service.py` and should
expose no consultation-mutation or AI method.

The conversion definition belongs in this application service, not Flask,
SQLAlchemy, or React: construct `Decimal` values from the integer counts,
calculate `booked / total * Decimal(100)`, and quantize to `Decimal("0.01")`
with `ROUND_HALF_UP`. A zero total returns `Decimal("0.00")`. Non-integer or
negative repository values are internal invariant failures; the service must
not clamp or repair them.

## 7. API/DTO conventions and DN-004 boundary

API files live under `backend/app/api/`; the existing pattern separates
Pydantic models in `consultation_dtos.py` from a focused Blueprint in
`consultation_routes.py`. The project uses Pydantic 2 (`Pydantic>=2,<3`),
`ConfigDict(extra="forbid")`, strict/constrained fields and validators,
`model_validate(...)`, then explicit DTO construction and
`jsonify(dto.model_dump(mode="json"))`. Validation failures use the exact safe
`{"error": "Invalid request"}`, 400 response. Unhandled service, DTO, and
serialization failures fall through to the application-wide safe 500 handler.
API tests inject a `Mock(spec=ConsultationApplicationService)` through
`create_app(service)` and assert exact envelopes plus non-delegation.

DN-004 should add:

- `backend/app/api/dashboard_dtos.py` with explicit `DashboardResponse` and
  exact nonnegative integer/finite percentage constraints;
- `backend/app/api/dashboard_routes.py` with
  `dashboard_blueprint = Blueprint("dashboard", __name__)`;
- registration beside the consultation blueprint using the same factory-owned
  `url_prefix="/api/v1"`;
- only `GET /dashboard`, yielding the public path `GET /api/v1/dashboard`.

The route should reject any `request.args` entry and any raw non-empty body via
`bool(request.get_data(cache=True))` before resolving/delegating. This matches
the existing raw-body helper and ensures `{}`, malformed JSON, and text bodies
are all invalid. It should resolve only
`current_app.extensions["dashboard_service"]`, invoke `get_metrics()` once,
construct the response DTO, deliberately convert the already-quantized Decimal
to `float` at the DTO/transport boundary, and serialize with
`model_dump(mode="json")`. It must not catch unexpected failures locally or
access a session, repository, consultation service, or AI dependency.

## 8. Frontend service boundary and DN-005 files

Frontend features currently live under
`frontend/src/app/features/<feature-name>/`. Consultation code separates
`consultationTypes.ts`, `consultationApi.ts`, screens, and colocated Vitest
tests. `createConsultationApi(transport = globalThis.fetch.bind(globalThis))`
injects a `FetchTransport`, while the exported singleton supplies production
fetch. `apiUrl()` trims trailing slashes from
`import.meta.env.VITE_API_BASE_URL` and appends a versioned `/api/v1/...` path.

Responses are treated as `unknown` and validated explicitly at runtime for
object/array shape, UUIDs, enums, timestamps, finite numbers, linkage, and
domain constraints. Network, status, JSON, and malformed-success detail is
collapsed into typed safe `Error` subclasses. Requests execute once; there is
no automatic retry wrapper. API tests inject `vi.fn()` transports, use real
`Response` objects, stub `VITE_API_BASE_URL`, assert exact calls and malformed
responses, and assert a rejected transport was called once.

DN-005 should establish a separate dashboard boundary rather than extend the
large consultation API:

- `frontend/src/app/features/dashboard/dashboardTypes.ts`;
- `frontend/src/app/features/dashboard/dashboardApi.ts`;
- `frontend/src/app/features/dashboard/dashboardApi.test.ts`.

It should expose focused `DashboardMetrics`, `DashboardApiError`,
`createDashboardApi(transport?)`, and `dashboardApi`. Runtime validation must
require exactly the three approved keys, integer/nonnegative counts, a finite
percentage in `0..100`, and the valid-state numerator/denominator constraints,
but must not recompute conversion. One `GET /api/v1/dashboard` (using the
repository's established explicit `{method: "GET"}` convention where applied)
must map every transport, non-200, JSON, or shape failure to one safe retrieval
error without retrying.

## 9. Router and screen boundary

`frontend/src/app/core/App.tsx` owns one `<Routes>` tree with an element-only
parent `<Route element={<AppLayout />}>`. Its index currently renders
`<Navigate to="/consultations" replace />`. The unchanged child paths are:

- `consultations`;
- `consultations/:consultationId`;
- `consultations/:consultationId/summary`;
- `consultations/:consultationId/appointments/new`.

`AppointmentBookingScreen` reads all `recommendation_id` values through
`useSearchParams().getAll(...)`, requires exactly one valid UUID, and the
summary screen creates that query with `URLSearchParams`. `AppLayout` does not
inspect or rewrite the query, so preserving the route declaration preserves
this handoff.

DN-006 should add
`frontend/src/app/features/dashboard/DashboardScreen.tsx` and its colocated
test, import the screen in `App.tsx`, add child path `dashboard`, and change
only the index target to `/dashboard` while retaining `replace`. Existing
MemoryRouter direct-route tests remain the compatibility pattern.

## 10. AppLayout/navigation boundary

`frontend/src/app/layout/AppLayout.tsx` currently owns the full shared shell:
a grey page background, static MUI `AppBar`/`Toolbar`, the
`AI Consultation Platform` title, one `Button` using React Router `Link` to
`/consultations` with label `Consultation Records`, and a `Container` rendered
as `main` that owns `<Outlet />`. There is no Drawer, `useMediaQuery`, active
route state, or responsive navigation helper anywhere in the frontend today.
The installed UI version is MUI `^9.3.1`.

DN-007 should modify only this established shell (plus focused layout tests),
retaining the title, main landmark, and Outlet. One immutable logical
navigation definition should contain `Dashboard -> /dashboard` followed by
`Consultations -> /consultations`; desktop and mobile renderings map that same
definition. Use Router `Link` ownership and `useLocation()` for presentation:
Dashboard is active only when pathname is exactly `/dashboard`; Consultations
is active when pathname equals `/consultations` or begins with
`/consultations/`. At `md+`, render a permanent Drawer beside main content; below
`md`, render an accessible menu button and temporary Drawer, with a `nav`
landmark, focusable labelled links, selected/current-page semantics, and close
the temporary drawer after link selection. No route or data ownership moves
into the layout.

## 11. Deterministic responsive test strategy

Vitest uses `jsdom` and `frontend/src/test/setup.ts`; the setup currently adds
jest-dom and after-test cleanup only. No repository code defines
`window.matchMedia`. Tests use React Testing Library, `MemoryRouter`, and
`@testing-library/user-event` directly.

The smallest evidence-aligned strategy is a focused
`frontend/src/app/layout/AppLayout.test.tsx` helper that stubs
`window.matchMedia` for the desired viewport/breakpoint result and restores it
after each test. There is no need to add a global abstraction. Render
`AppLayout` under `MemoryRouter` with a child route/outlet, exercise the menu
with `userEvent`, and assert accessible roles, link destinations,
`aria-current`/selected state, temporary drawer open/closed state, and both
destinations. Because MUI responsive Drawer visibility may be CSS-driven in
jsdom, assertions should combine the deterministic media-query stub with
accessible state/roles rather than infer a physical viewport from pixels.

## 12. Docker Compose and runtime boundary

`compose.yaml` already defines exactly three services: PostgreSQL 16 Alpine,
Flask backend, and Vite frontend. PostgreSQL has a named `postgres_data` volume,
host port default 5432, and `pg_isready` healthcheck. Backend waits for database
health, receives `postgres:5432`, defaults to `AI_PROVIDER=mock`, exposes host
port 5000, and receives a CORS origin matching the frontend host port. Frontend
receives browser-visible `VITE_API_BASE_URL=http://localhost:<backend-port>` and
exposes host port 3000. The backend image starts with
`alembic upgrade head` followed by Flask; the frontend image runs the Vite dev
server.

Feature 005 requires no new service, port, volume, healthcheck, credential,
environment variable, OpenAI configuration, Dockerfile change, or
infrastructure redesign. DN-008 should use the documented runtime command:

```bash
docker compose up --build
```

and verify the resulting service state with:

```bash
docker compose ps
```

The relevant deterministic project checks are:

```bash
cd backend && pytest -q tests
cd frontend && npm run test
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
docker compose config
```

Compose defaults need no real credential. Runtime verification should retain
the mock provider and may exercise `GET /api/v1/dashboard` plus the frontend
routes once DN-008 exists. Teardown after a temporary smoke run should use
`docker compose down` without `--volumes`, preserving persisted developer data.

## 13. Explicit no-AI boundary

Current consultation composition builds `AIService` through
`create_ai_service`, which selects `MockAIProvider` or `OpenAIProvider`, wraps
it in `ConsultationAgent` and `ConsultationSkill`, and is used by consultation
message/summary workflows. `OPENAI_API_KEY` is read only for the optional
OpenAI provider; Compose defaults to mock.

Dashboard repository, application service, and API modules must import none of
`AIService`, `ConsultationAgent`, `ConsultationSkill`, `OpenAIProvider`,
`MockAIProvider`, LangChain, or provider configuration. Their dependency graph
is only Dashboard route -> Dashboard application service -> Dashboard
repository -> request-scoped SQLAlchemy session/models. Production may still
initialize the existing consultation AI service once per application factory,
but a dashboard read never calls it. Focused API injection must also avoid AI
construction, and strict DN-003/DN-008 doubles should fail if any AI method is
invoked.

## 14. Downstream ownership summary

| Task | Exact primary boundary |
| --- | --- |
| DN-002 | `backend/app/repositories/dashboard_repository.py`; `Consultation` and `Appointment`; PostgreSQL fixtures above |
| DN-003 | `backend/app/application/dashboard_service.py`; strict repository double; Decimal calculation |
| DN-004 | `backend/app/api/dashboard_dtos.py`, `dashboard_routes.py`, and parallel `create_app` injection/composition |
| DN-005 | `frontend/src/app/features/dashboard/dashboardTypes.ts` and `dashboardApi.ts`; injected fetch and exact runtime validation |
| DN-006 | `DashboardScreen.tsx`; `frontend/src/app/core/App.tsx`; index replacement redirect |
| DN-007 | existing `frontend/src/app/layout/AppLayout.tsx`; focused local `matchMedia` test helper |
| DN-008 | PostgreSQL/API vertical slice, full regression/check commands, and unchanged three-service Compose runtime |

## 15. Conflicts, deviations, and scope verification

No product or architecture conflict blocks DN-002 through DN-008. The only
implementation-sensitive finding is the injected-app rule documented in §2:
the current factory treats service injection as a complete production-
composition bypass, so the later dashboard seam must not construct database or
AI dependencies merely because the other service parameter is `None`.

DN-001 added only this findings artifact and updated the approved Feature 005
task checkbox. It changed no backend or frontend product source, test,
migration, dependency, configuration, plan, infrastructure, or Feature 001–004
implementation file. No DashboardRepository, DashboardApplicationService,
dashboard route/DTO, frontend dashboard file, migration, or AppLayout change
was created. DN-002 through DN-008 remain unimplemented and unchecked.
