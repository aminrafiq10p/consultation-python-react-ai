# Dashboard and Navigation Implementation Plan

## 1. Objective

Implement the approved Dashboard and Navigation vertical slice on top of
completed Features 001–004:

```text
PostgreSQL consultations + appointments
        ↓ independent aggregate scalar subqueries
DashboardRepository
        ↓ one count-pair operation
DashboardApplicationService
        ↓ Decimal percentage calculation
GET /api/v1/dashboard
        ↓ exact runtime-validated response
Dashboard metric cards
        ↓ shared responsive AppLayout navigation
Dashboard and existing consultation routes
```

The implementation will add one read-only dashboard endpoint, three MUI metric
cards, a `/dashboard` route, a new root redirect, and reusable desktop/mobile
navigation. PostgreSQL remains authoritative. No dashboard persistence,
migration, state-changing workflow, AI behavior, chart, filter, infrastructure
service, or routing redesign will be introduced.

## 2. Current-System Alignment

Feature 005 will extend these implemented conventions:

- `backend/app/__init__.py:create_app` is the composition boundary. Production
  requests receive one request-scoped SQLAlchemy `Session`, and the current
  consultation repositories share it. Tests inject an application-service
  double through `app.extensions` without constructing production dependencies.
- SQLAlchemy mappings share the infrastructure-owned `Base` in
  `backend/app/infrastructure/consultation_models.py`. The existing
  `Consultation` and `Appointment` mappings already represent the two
  authoritative tables; `appointments.consultation_id` is required and unique.
- Focused repositories live in `backend/app/repositories/`, accept a `Session`,
  and own SQLAlchemy statements. Application workflows live in
  `backend/app/application/` and remain independent of Flask and React.
- The existing consultation API uses a blueprint registered at `/api/v1`,
  explicit Pydantic response DTOs, `extra="forbid"` request/query validation,
  and the application-wide safe unexpected-error handler.
- PostgreSQL tests use a temporary PostgreSQL 16 container, run Alembic to
  `head`, clean tables in foreign-key order, and use real SQLAlchemy sessions.
- `frontend/src/app/core/App.tsx` owns one nested React Router tree under
  `AppLayout`. The four approved consultation routes are already direct-link
  reachable and the root index currently redirects with replacement to
  `/consultations`.
- `frontend/src/app/layout/AppLayout.tsx` currently retains the title, an
  application bar, a consultation link, a `main` container, and `Outlet`. It is
  the shell to extend; no second layout is necessary.
- Consultation frontend code uses MUI, feature-local service interfaces for
  screen tests, injected `fetch` transports for API tests, explicit runtime
  validation, safe typed errors, and React state for loading/success/error.
- Vitest, React Testing Library, `MemoryRouter`, and `user-event` cover screens
  and direct routes. There is currently no responsive-navigation test helper,
  so AppLayout tests will provide a deterministic `matchMedia` setup.
- `compose.yaml` already runs PostgreSQL 16, Flask, and Vite with the required
  API URL and CORS origin. The dashboard needs no new dependency or service.

Existing unrelated working-tree changes to `README.md` and the approved
`specs/features/005-dashboard-navigation.md` are user-owned and must be
preserved.

## 3. Specification Traceability

| Approved requirement | Planned responsibility | Verification focus |
| --- | --- | --- |
| Count every consultation row | Dashboard repository consultation scalar count | Empty and all-status PostgreSQL tests |
| Count appointment rows, not `BOOKED` text | Dashboard repository appointment scalar count | Inconsistent-status and linked-booking tests |
| One coherent repository read without row loading | One repository method and one `SELECT` containing two independent scalar subqueries | Statement/result and no-mutation tests |
| Zero-safe half-up percentage | Dashboard application service with `Decimal` and `ROUND_HALF_UP` | `0/0`, `1/3`, `1/32`, zero numerator, and full conversion |
| Exact safe GET contract | Focused dashboard blueprint and Pydantic response DTO | Exact `200`, numeric JSON, `400`, and safe `500` tests |
| Request-scoped composition | `create_app` constructs dashboard repository/service from the existing session | Composition identity and teardown tests |
| Dedicated frontend boundary | Feature-local dashboard types/API with exact runtime validation | Transport, malformed response, and no-retry tests |
| Loading/success/zero/error/retry UI | Dashboard screen state machine | React Testing Library state and retry tests |
| Root lands on Dashboard | Nested index `Navigate` target change | Location-aware replacement test |
| Shared responsive navigation | Existing AppLayout, one navigation definition, permanent/temporary drawers | Desktop/mobile, active, close, keyboard, and landmark tests |
| Existing routes remain unchanged | Preserve all consultation route declarations | Direct records/detail/summary/booking regression tests |
| No AI, mutation, or external call | Focused dependency graph and strict doubles | Application/API/vertical-slice assertions |

## 4. Backend Dashboard Repository

Add `backend/app/repositories/dashboard_repository.py` with a small immutable
count value (for example `DashboardCounts`) and `DashboardRepository`. The
repository accepts the existing request-scoped SQLAlchemy `Session` and exposes
one method, likely `get_counts() -> DashboardCounts`.

### 4.1 Query strategy

Build two independent aggregate subqueries:

```text
SELECT
  (SELECT count(consultations.id) FROM consultations),
  (SELECT count(appointments.id) FROM appointments)
```

Express this through SQLAlchemy `select(func.count(...)).scalar_subquery()` and
execute the enclosing statement once. This strategy:

- counts all `Consultation` rows without a status predicate;
- counts `Appointment` rows directly without inferring from consultation
  status;
- cannot multiply either count because there is no consultation/appointment
  join;
- returns only two scalar values and loads no mapped entity collection;
- observes both values as one PostgreSQL statement under the request session's
  normal transaction visibility;
- acquires no write or explicit row lock; and
- performs no add, flush, commit, rollback, mutation, or AI/external call.

Normalize the database scalar results to Python integers in the repository.
The application layer remains responsible for the specification's defensive
nonnegative invariant rather than silently repairing impossible repository
output.

Expected files:

- new `backend/app/repositories/dashboard_repository.py`
- `backend/app/repositories/__init__.py` only if an export is useful under the
  existing lightweight export convention
- new `backend/tests/test_dashboard_repository.py`

No mapping or Alembic file changes are required.

## 5. Dashboard Application Workflow

Add `backend/app/application/dashboard_service.py` rather than expanding the
already multi-workflow `ConsultationApplicationService`. Define a provider-
neutral immutable metrics value, likely `DashboardMetrics`, and a focused
`DashboardApplicationService` injected with `DashboardRepository` (or a narrow
repository protocol if useful for strict unit doubles).

One method, likely `get_metrics()`, will:

1. call the repository count operation exactly once;
2. reject either count when it is not an integer or is negative, raising an
   internal application failure rather than returning impossible metrics;
3. return `Decimal("0.00")` when `total_consultations == 0`;
4. otherwise calculate
   `Decimal(booked_appointments) / Decimal(total_consultations) * Decimal(100)`;
5. quantize once to `Decimal("0.01")` with `rounding=ROUND_HALF_UP`; and
6. return the two integer counts and quantized percentage without depending on
   Flask, Pydantic, SQLAlchemy mappings, React, AI, or provider SDKs.

Constructing `Decimal` directly from integers avoids binary floating-point
input. The service does not clamp a value, recompute either count, or repair
inconsistent persisted state. Negative values fail defensively. Counts that
would imply a rate above 100 are impossible under valid Feature 004 database
constraints; the response DTO's approved range remains a final safe boundary
if an impossible application value nevertheless reaches the Flask layer.

The boundary preserves two-decimal semantic precision internally. The API DTO
will deliberately convert that finite quantized `Decimal` to a JSON numeric
value; React will only format the received number with `toFixed(2)`.

Expected files:

- new `backend/app/application/dashboard_service.py`
- new `backend/tests/application/test_dashboard_service.py`

Application tests will use a strict repository double with no consultation or
AI methods, proving that dashboard retrieval has only the approved dependency.

## 6. Dashboard API, DTO, and Error Mapping

Add a focused API boundary instead of placing dashboard behavior in the
consultation blueprint:

- new `backend/app/api/dashboard_dtos.py`
- new `backend/app/api/dashboard_routes.py`
- focused tests under `backend/tests/api/`

### 6.1 Response DTO

Define `DashboardResponse` with exactly:

- `total_consultations`: nonnegative integer;
- `booked_appointments`: nonnegative integer; and
- `conversion_rate`: finite float constrained to `0.0..100.0`.

The route constructs this explicit response from application metrics and
serializes `model_dump(mode="json")`. Convert the already quantized application
`Decimal` deliberately to `float` at this transport boundary so Flask emits a
JSON number, not Pydantic's JSON string representation for `Decimal`. This
conversion is representation only and does not redo or alter the percentage
formula. Tests require `int` (and not `bool`) count values and a JSON numeric
conversion value.

### 6.2 Route behavior

Register only:

```text
GET /api/v1/dashboard
```

Before delegation, reject `request.args` when any query key exists and reject
`request.get_data(cache=True)` when any body byte exists. A body such as `{}`
is non-empty and therefore invalid. Rejection returns exactly:

```json
{"error": "Invalid request"}
```

with `400` and does not invoke the service. A valid request gets the service
from `current_app.extensions["dashboard_service"]`, invokes `get_metrics()`
once, maps the DTO, and returns `200`. It does not access SQLAlchemy, another
repository/service, or AI. There is no dashboard `404` or `409` branch.

Unexpected repository, application invariant, DTO, or serialization failures
flow to the existing application-wide error handler and return only:

```json
{"error": "Internal server error"}
```

with `500`. Tests will assert that exception, SQL, connection, constraint,
environment, patient, and AI-provider detail is absent.

Register `dashboard_blueprint` beside `consultation_blueprint` with the same
`/api/v1` prefix. Do not broaden or modify existing consultation error
translations.

## 7. Flask Composition and Request Scope

Extend `backend/app/__init__.py:create_app` with an optional focused
`dashboard_service` injection while preserving the positional/named
`consultation_service` seam used by Features 001–004.

Production `create_app()` will continue to:

1. create one engine and session factory;
2. open one SQLAlchemy session in `before_request`;
3. create the existing consultation repositories/service from that session;
4. create `DashboardRepository(session)` and
   `DashboardApplicationService(...)` from the same session;
5. expose both services through distinct `app.extensions` keys; and
6. remove both request services and close that one session during teardown.

For unit API tests, explicitly supplied services are installed in extensions
and production database/AI dependencies are not constructed, matching the
current isolated-test behavior. Existing calls such as
`create_app(consultation_service=double)` must remain valid. Dashboard route
tests use `create_app(dashboard_service=double)`; composition tests use
`create_app()` with database/environment factories patched and assert both
repositories share the opened session. If only one service is injected, the
test application need not synthesize the unrelated production service; tests
must only exercise routes whose service was supplied. Missing-extension access
still resolves through the safe `500` handler rather than leaking internals.

Keep `create_app`, the current session lifecycle, and the existing error
handler; do not introduce a unit-of-work abstraction, second session, global
session, or separate dashboard application factory.

Expected composition coverage belongs in a focused new
`backend/tests/api/test_dashboard_routes.py` and/or
`backend/tests/test_dashboard_composition.py`, with existing consultation API
tests retained unchanged where possible.

## 8. Frontend Dashboard Service and Runtime Types

Create a separate feature root because dashboard concerns are not consultation
records concerns:

- new `frontend/src/app/features/dashboard/dashboardTypes.ts`
- new `frontend/src/app/features/dashboard/dashboardApi.ts`
- new `frontend/src/app/features/dashboard/dashboardApi.test.ts`

Define `DashboardMetrics` with the three snake-case API fields and a safe
`DashboardApiError` (or a single retrieval error kind). Follow the existing
injected transport and `VITE_API_BASE_URL` convention, but do not import or
extend `consultationApi`.

`getMetrics()` will make exactly one call to `/api/v1/dashboard` with GET
semantics and no body, query, or automatic retry. It will accept only status
`200`, parse JSON inside a safe boundary, and validate:

- a non-null, non-array object;
- exactly the three approved own keys, with no missing or additional key;
- counts whose runtime type is `number`, which are finite, integer,
  nonnegative, and within JavaScript's safe-integer range;
- `conversion_rate` whose runtime type is `number`, finite, and between `0`
  and `100` inclusive; and
- coherence constraints supported by the authoritative schema, including
  `booked_appointments <= total_consultations`, zero total requiring all-zero
  metrics, and the returned rounded percentage matching the counts only if
  enforcing that check does not cause React to become a second authoritative
  calculator.

The last point will be resolved conservatively in implementation: validate the
specified value/range and zero-state invariants, but do not recalculate a
nonzero conversion rate in React. The backend owns the formula. A malformed
success, invalid JSON, non-`200`, or transport rejection becomes the same safe
retrieval error without exposing response/transport detail. No automatic retry
occurs; only the screen's explicit Retry starts another call.

## 9. Dashboard Screen and State Machine

Add:

- new `frontend/src/app/features/dashboard/DashboardScreen.tsx`
- new `frontend/src/app/features/dashboard/DashboardScreen.test.tsx`

The screen accepts an optional narrow dashboard service for deterministic
tests and defaults to `dashboardApi`. It uses one explicit discriminated state:

```text
loading
  ├─ valid response → success(metrics)
  └─ any failure    → error
error --Retry--> loading --one GET--> success | error
```

On mount, request metrics once. Use an effect cleanup flag (or equivalent) so
an obsolete resolution cannot update an unmounted/replaced screen. Every new
load first sets `loading` and removes prior metrics; an error stores no metrics.
Thus stale values are never presented as current after failure. Retry calls the
same load function exactly once and introduces no loop or background refresh.

Use MUI `Box`, `Typography`, `Grid` (or responsive CSS grid), `Card`,
`CardContent`, `CircularProgress`, `Alert`, and `Button` as appropriate:

- an `h1` Dashboard heading;
- an accessible `role="status"` loading announcement;
- three clearly labelled cards in this order: `Total consultations`,
  `Booked appointments`, `Conversion rate`;
- integer count rendering and `conversion_rate.toFixed(2) + "%"` formatting;
- zero values rendered as `0`, `0`, and `0.00%`, optionally accompanied by a
  concise no-consultations message;
- one safe error message with a labelled `Retry` button; and
- no charts, record fetch, local percentage formula, mutation, or AI call.

Frontend tests use deferred promises to prove loading, valid and zero metrics
to prove rendering/formatting, a rejected service call to prove safe error
copy, and sequenced rejected/resolved promises to prove one-call Retry recovery
without stale cards.

## 10. Routing Changes and Compatibility

Update `frontend/src/app/core/App.tsx` minimally:

- import and add `<Route path="dashboard" element={<DashboardScreen />} />`
  inside the existing layout route;
- change only the index redirect from `/consultations` to `/dashboard`; and
- retain `replace` on `Navigate`.

Keep these route declarations and paths unchanged:

```text
/consultations
/consultations/:consultationId
/consultations/:consultationId/summary
/consultations/:consultationId/appointments/new
```

React Router continues to own location and nesting. The layout must not parse,
forward, or discard the booking route's `recommendation_id` query. Existing
detail, summary, booking, back, restart, and success navigation behavior stays
inside the same `Outlet`.

Expand `frontend/src/app/core/App.test.tsx` with a small location observer or
history-aware test harness to prove `/` ends at `/dashboard` through a
replacement redirect and direct `/dashboard` renders the screen/layout. Keep
focused deep-route screen tests rather than mocking those screens away.

## 11. Reusable Responsive AppLayout Navigation

Extend only `frontend/src/app/layout/AppLayout.tsx` and add focused
`frontend/src/app/layout/AppLayout.test.tsx` coverage.

Define one module-level navigation collection in approved order:

```text
Dashboard      /dashboard
Consultations  /consultations
```

Render both responsive surfaces from that one collection/helper so labels,
destinations, and active rules cannot drift. Use React Router `Link`/`NavLink`
and `useLocation`; do not introduce another router or manually change browser
history.

### 11.1 Structure and responsiveness

- Preserve the application title in the AppBar and preserve one `main` content
  area containing `Outlet`.
- At MUI `md` and above, render a visible permanent Drawer/sidebar beside the
  main content.
- Below `md`, hide the permanent drawer and expose an icon/button with an
  accessible name such as `Open navigation`; it opens a temporary MUI Drawer.
- Give the links a `nav` landmark with a meaningful accessible label.
- Close temporary navigation after either destination is selected. Permanent
  navigation does not use mobile open/close state.
- Use normal focusable router links and MUI keyboard-operable controls. The
  menu button, close behavior, visible labels, and focus order require no
  pointer-only interaction.

Exact drawer width, icons, spacing, colors, and decoration remain
implementation decisions and must not create another navigation contract.

### 11.2 Active state

Derive active state only from the canonical `location.pathname`:

- Dashboard is selected/current only when pathname is exactly `/dashboard`.
- Consultations is selected/current when pathname is exactly
  `/consultations` or begins with `/consultations/`.

Apply MUI selected styling and accessible current-page semantics
(`aria-current="page"`) to the active link. Do not use substring rules that
would select unrelated paths, and do not change data loading based on active
state.

AppLayout tests run at deterministic desktop/mobile media-query widths and
cover both destinations, approved ordering, navigation landmark, active state
on dashboard/records/detail/summary/booking paths, menu accessibility, and
temporary-drawer closure after link activation.

## 12. Deterministic Backend Testing Strategy

### 12.1 Repository and PostgreSQL

`backend/tests/test_dashboard_repository.py` will run against migrated
PostgreSQL using the existing container/Alembic/session conventions. Clean
appointments before consultations and persist only the lineage required by
the existing FKs.

Cover:

- empty database returns exactly `0, 0`;
- `PENDING`, `COMPLETED`, and `BOOKED` rows each contribute to total;
- a `BOOKED` consultation without an appointment does not increment booked;
- appointment rows determine booked regardless of status-oriented assumptions;
- an appointment-linked `BOOKED` consultation contributes once to each count;
- extra messages, summary/recommendation rows, and multiple related rows do not
  multiply either aggregate;
- the repository executes focused scalar aggregates rather than loading model
  collections; and
- snapshots before/after a read show no consultation, appointment, message,
  summary, recommendation, or projection mutation and no commit.

### 12.2 Application

`backend/tests/application/test_dashboard_service.py` will use strict count
doubles and cover:

- `0 / 0 -> Decimal("0.00")` and API-equivalent `0.0` representation;
- nonzero consultations with zero appointments;
- representative exact percentages such as `1/4 -> 25.00`;
- repeating `1/3 -> 33.33`;
- a half-up boundary such as `1/32 -> 3.13` (exactly `3.125` before
  quantization);
- full `n/n -> 100.00`;
- negative total or appointment counts rejected;
- one repository call; and
- no consultation mutation, AI, LangChain, provider, or network collaborator.

### 12.3 API and composition

`backend/tests/api/test_dashboard_routes.py` will inject a strict service
double and cover:

- exact populated `200` keys/values and numeric JSON types;
- exact empty response `{0, 0, 0.0}`;
- every query parameter, including unknown/blank values, returns exact safe
  `400` without delegation;
- every non-empty body, including `{}`, JSON, text, or malformed bytes,
  returns exact safe `400` without delegation;
- service/repository/invariant failures become exact safe `500`;
- secrets, SQL, connection strings, constraints, patient data, stack and
  provider detail never appear; and
- one service invocation for one valid request.

Composition coverage will prove `create_app()` registers the endpoint and
constructs both focused services over the same request session, teardown closes
it, injected service tests avoid production AI/database setup, and existing
consultation injection remains usable.

## 13. Deterministic Frontend Testing Strategy

### 13.1 Service

`frontend/src/app/features/dashboard/dashboardApi.test.ts` will cover:

- exactly one GET to `/api/v1/dashboard` with no query/body;
- valid populated and zero responses;
- missing/extra fields and non-object/array/null responses;
- negative, fractional, nonnumeric, non-finite, unsafe-integer counts;
- invalid conversion values including string, `NaN`/infinite-equivalent test
  objects, negative, and above 100;
- impossible zero/nonzero combinations and numerator above denominator;
- malformed JSON;
- every non-`200` response mapped safely regardless of body;
- network rejection mapped without raw detail; and
- no automatic retry (`transport` called once).

### 13.2 Dashboard UI

`frontend/src/app/features/dashboard/DashboardScreen.test.tsx` will cover:

- accessible loading state while a promise is pending;
- three labelled cards with integer counts;
- exact `25.00%`, `33.33%`, and `0.00%` presentation from returned numbers;
- successful all-zero state without error/undefined/`NaN`;
- consultations with zero bookings as ordinary success;
- safe error with no transport detail and a Retry button;
- Retry starts exactly one new request, clears stale content, and can recover;
  and
- unmounted/obsolete promises do not overwrite current state.

### 13.3 Navigation and routes

`frontend/src/app/layout/AppLayout.test.tsx` and
`frontend/src/app/core/App.test.tsx` will cover:

- `/` replacement redirect to `/dashboard`;
- direct `/dashboard` and shared layout rendering;
- Dashboard and Consultations canonical destinations;
- Dashboard active only at `/dashboard`;
- Consultations active at records, detail, summary, and appointment booking;
- neither link gains incorrect active state on unrelated locations;
- desktop permanent navigation and mobile menu/drawer access to both entries;
- accessible labels, landmarks, focusable links, selected/current semantics;
- mobile drawer closes after Dashboard or Consultations selection; and
- direct records/detail/summary/booking routes remain functional, including
  booking query handoff.

Use `window.matchMedia` doubles (or MUI-supported deterministic equivalents)
for breakpoint tests; do not assert incidental generated CSS classes.

## 14. PostgreSQL Vertical Slice and Regression Verification

Add a focused PostgreSQL-backed API/vertical-slice test, likely
`backend/tests/api/test_dashboard_persistence_api.py`, using `create_app()` with
the database factories/environment patched to the migrated temporary database
and the existing mock AI provider configuration.

The deterministic scenario will:

1. persist consultations spanning `PENDING`, `COMPLETED`, and `BOOKED` as
   needed, with messages/summary/recommendations;
2. GET dashboard and assert initial counts/rate;
3. book one eligible completed consultation through the existing Feature 004
   application/API workflow (or the same deterministic composed application
   boundary), supplying a future time and owned recommendation;
4. issue a new GET dashboard and assert one added appointment and the correctly
   rounded new conversion rate;
5. prove the booked consultation contributes once to each aggregate; and
6. compare fresh-session snapshots showing dashboard reads changed no
   consultation status, appointment, message, summary, recommendation, or
   `recommended_procedure`; only the explicit booking step has its approved
   appointment/status effects.

Run regression verification after focused tests:

```text
backend:  full pytest suite
frontend: npm test
frontend: npm run lint
frontend: npm run typecheck
frontend: npm run build
```

Also verify Alembic remains at the Feature 004 head with no new revision and
run `docker compose config`, `docker compose build`, and a Compose smoke test
that reaches `/api/v1/dashboard` and the frontend route. The runtime uses the
existing mock AI default and no test needs OpenAI, LangChain execution, an
external service, network credential, or real account.

## 15. Implementation Tasks and Sequence

The proposed decomposition matches the repository and should remain unchanged:

### DN-001 — Confirm Feature 005 Integration Boundaries

- Record exact existing composition, session, DTO, error, frontend service,
  router, AppLayout, fixture, responsive-test, and Compose conventions.
- Finalize names and focused file ownership from §§4–14 without product or
  architecture changes.
- Confirm the Feature 004 Alembic head is reused unchanged.

### DN-002 — Add Dashboard Metrics Repository

- Add the count value/repository and independent scalar-subquery statement.
- Add PostgreSQL coverage for empty, mixed, inconsistent, linked, no-
  multiplication, and no-mutation behavior.

### DN-003 — Add Dashboard Metrics Application Workflow

- Add the focused service/value, invariant checks, zero handling, and exact
  `Decimal`/`ROUND_HALF_UP` calculation.
- Add deterministic strict-double application tests.

### DN-004 — Expose Dashboard API and DTO

- Add response DTO, blueprint, request rejection, safe response/error mapping,
  and `create_app` session composition/injection.
- Add route, numeric-contract, failure, composition, and backend slice tests.

### DN-005 — Add Frontend Dashboard Service

- Add dashboard types, transport, exact runtime validation, and safe no-retry
  failure behavior.
- Add focused service tests.

### DN-006 — Add Dashboard Screen and Route

- Add screen state machine/cards/error/retry and `/dashboard` route.
- Change only the root redirect and add screen/router tests.

### DN-007 — Add Reusable Responsive Application Navigation

- Extend AppLayout with one navigation definition, permanent/temporary drawers,
  exact active rules, and accessible behavior.
- Add responsive, active-state, close, and deep-route compatibility tests.

### DN-008 — Verify Dashboard and Navigation Vertical Slice

- Run composed PostgreSQL booking-to-dashboard verification, all regressions,
  frontend quality gates, scope/file audits, and Docker Compose verification.

No task files are created at planning stage. Each later task file must trace to
the approved specification and this plan before implementation begins.

## 16. Dependencies and Parallel Work

```text
DN-001
├── DN-002 → DN-003 → DN-004 ───────────┐
└── DN-005 → DN-006 → DN-007 ───────────┴→ DN-008
```

- DN-001 is the common boundary confirmation.
- Backend work is sequential because the service consumes repository output
  and the route/composition consumes the service.
- DN-005 can proceed in parallel with DN-002–DN-004 because the approved JSON
  contract is complete and frontend tests inject transport.
- DN-006 follows DN-005 because the screen consumes the dedicated service.
- DN-007 follows DN-006 in this repository: `App.tsx` first establishes the
  new canonical Dashboard destination, then AppLayout navigation can test both
  real destinations and all nested screens. AppLayout coding could be prepared
  in parallel, but integration/route tests and completion depend on DN-006.
- DN-004 and DN-007 do not otherwise depend on each other and may run in
  parallel once their own chains are ready.
- DN-008 waits for both chains and owns full regression/Compose evidence.

This is the preferred dependency structure from the specification. Repository
reality requires no task merge, split, rename, or reordering.

## 17. Risks, Controls, and Planning Assumptions

- **Aggregate multiplication:** never join consultations to appointments for
  the metrics. Two scalar subqueries in one statement retain independent
  cardinalities and one statement-level view.
- **Persisted inconsistency:** count appointment rows exactly as stored. A
  `BOOKED` consultation without an appointment remains in the denominator only;
  dashboard reads neither repair it nor fail because of it.
- **Decimal serialization:** compute and quantize with integer-origin
  `Decimal`; convert to float only while constructing the response DTO so JSON
  remains numeric. React receives the backend result and only formats it.
- **Runtime validation versus recomputation:** frontend validation enforces
  exact keys, types, finiteness, ranges, and structural invariants but does not
  calculate a nonzero percentage to challenge/replace backend authority.
- **Injectable composition:** retain current consultation-service injection and
  add a parallel dashboard seam. Production creates both per request over one
  session; focused tests need not create unrelated database/AI dependencies.
- **GET body detection:** inspect raw cached body bytes so `{}`, malformed JSON,
  and text are all rejected consistently without content-type-specific parsing.
- **Responsive testing:** MUI breakpoints depend on media queries; tests must
  install deterministic `matchMedia` behavior and assert roles/state rather
  than implementation CSS.
- **Active path boundaries:** use equality plus `/consultations/` prefix, not a
  broad `startsWith("/consultations")`, so unrelated names cannot appear active.
- **Drawer duplication:** desktop and mobile renderings may be separate visual
  containers, but both map the same immutable navigation definition and active
  helper; there is one logical route/label source.
- **Route compatibility:** AppLayout owns presentation only. It never rewrites
  nested paths or query parameters and does not become a data-loading owner.
- **No migration:** existing tables and Feature 004 uniqueness/FKs fully
  support the counts. Any generated revision is a scope failure.
- **Working tree preservation:** keep existing user changes to README/specs and
  avoid formatting or rewriting unrelated implementation files.

No product or architecture conflict blocks task generation after this plan is
approved. Exact class/helper names, drawer width, icons, spacing, and card
decoration remain task-local choices within the boundaries above.

## 18. Acceptance-Criteria Validation Matrix

| Feature 005 acceptance criterion | Plan coverage |
| --- | --- |
| `/` replaces to `/dashboard`; direct Dashboard loads API metrics | §§8–10, 13 |
| Exact total, booked, and conversion definitions | §§4–6, 12 |
| Empty database is successful zero data | §§5, 9, 12–13 |
| Retrieval/validation failures recover through explicit Retry | §§8–9, 13 |
| Shared navigation spans dashboard and all consultation screens | §§10–11, 13 |
| Correct active state derives from Router location | §§11, 13.3 |
| Existing consultation direct links and query handoff remain | §§10–11, 13–14 |
| PostgreSQL is authoritative; React does not derive metrics | §§4–5, 8–9, 14 |
| One coherent aggregate operation makes no mutation | §§4, 12.1, 14 |
| API rejects query/body and exposes safe failures only | §6, §12.3 |
| Desktop sidebar and mobile drawer are accessible | §11, §13.3 |
| Tests are deterministic and make no AI/external call | §§12–14 |
| Feature 001–004 and Docker behavior remain intact | §14 |

## 19. Definition of Done

Feature 005 is ready only when:

- a focused repository returns consultation and appointment counts from one
  independent, non-joining aggregate statement over existing tables;
- a focused application service validates counts and computes the zero-safe
  percentage with integer-origin `Decimal`, `ROUND_HALF_UP`, and two-decimal
  semantic precision without Flask, SQLAlchemy-model, React, or AI coupling;
- the focused blueprint exposes only `GET /api/v1/dashboard`, rejects every
  query/non-empty body, delegates once, emits the exact numeric DTO, and keeps
  all unexpected errors safe;
- production composition uses the existing request session for both feature
  services and preserves isolated injectable test seams;
- the dedicated frontend service makes one GET, strictly validates the exact
  contract, safely collapses failures, and never computes conversion;
- `/dashboard` renders accessible loading, three-card success/zero, and
  recoverable Retry states without stale metrics;
- `/` redirects with replacement to Dashboard while every Feature 001–004
  route and booking query handoff remains unchanged;
- AppLayout retains title/main/Outlet and provides one logical Dashboard/
  Consultations navigation definition through permanent desktop and temporary
  mobile drawers with exact active/current semantics;
- focused backend/frontend, PostgreSQL vertical-slice, Features 001–004
  regression, lint, typecheck, build, and Docker Compose checks pass; and
- no product code beyond approved implementation scope, migration, new table,
  dependency, Compose service, chart, filter, analytics history, cache,
  background job, auth, notification, external integration, AI insight,
  OpenAI call, RAG, Redis, vector database, LangGraph, WebSocket, streaming, or
  infrastructure/routing redesign is introduced.
