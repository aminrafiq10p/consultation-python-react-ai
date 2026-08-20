# Feature 007 — Appointments Implementation Plan

## 1. Objective

Implement the approved, read-oriented Appointments vertical slice on top of
the completed Features 001–006:

```text
Feature 004 POST booking
        ↓ committed Appointment row
AppointmentRepository joined list read
        ↓ existing request-scoped SQLAlchemy Session
ConsultationApplicationService list operation
        ↓ GET /api/v1/appointments
dedicated frontend appointment-list service
        ↓ /appointments in AppLayout
responsive appointment list
        ↓ persisted consultation_id
/consultations/{consultationId}
```

Feature 004 remains the only appointment write flow. Feature 007 adds no
schema, write operation, status, AI behavior, external integration, or second
appointment source. PostgreSQL remains authoritative for every displayed
value and for the Dashboard booked count.

This plan is implementation-ready but is not an implementation task list. No
task files, product code, migration, or Feature 008 work is included.

## 2. Repository Alignment and Boundary Confirmation

### Confirmed existing architecture

- `backend/app/infrastructure/consultation_models.py` already contains the
  `Appointment`, `Consultation`, `ConsultationSummary`, and
  `ConsultationRecommendation` mappings required by the specification.
- `Appointment.consultation_id` is unique; the persisted appointment stores
  `recommendation_id`, `scheduled_at`, `location`, and `created_at`, but not
  patient or treatment text.
- `backend/app/repositories/appointment_repository.py` already owns Feature
  004 booking coordination and atomic creation. It currently exposes booking
  aggregates and a joined post-create reload, so the list read should extend
  this repository rather than introduce another repository hierarchy.
- `ConsultationApplicationService` already receives the appointment repository
  and is the existing application boundary for booking. A focused
  `list_appointments()` operation is the smallest compatible extension.
- `consultation_blueprint` is registered at `/api/v1`, owns request-shape
  validation and DTO serialization, and already maps known outcomes while the
  application-wide handler maps unexpected failures to the safe 500 response.
- `create_app` constructs one `Session`, then composes consultation, message,
  summary, appointment, and Dashboard repositories around that same session.
  The production appointment-list path must use this existing composition.
- `DashboardRepository` counts persisted `Appointment` rows directly. No
  Dashboard code or synchronization callback is needed for Feature 007.
- `frontend/src/app/core/App.tsx` owns the nested route tree under
  `AppLayout`; `frontend/src/app/layout/AppLayout.tsx` owns the single shared
  desktop permanent drawer and mobile temporary drawer navigation definition.
- The frontend already uses feature-local types/services, injected fetch
  transports, runtime response validation, safe typed errors, MUI, and React
  Testing Library. The appointment list should follow these conventions.

### Compatibility detail and smallest solution

The existing Feature 004 `AppointmentAggregate` and
`AppointmentResponse` are booking-oriented and return appointment plus
recommendation data, but do not include `patient_name`. Feature 007 requires a
patient projection and a different list envelope. Do not alter the booking
response contract or make `AppointmentAggregate` depend on consultation data.
Add a provider-neutral list read value/row (or equivalent focused aggregate)
containing the appointment, consultation patient name, and selected
recommendation projection; add a dedicated list response DTO. This is a
read-specific projection over existing tables, not a new persistence model or
appointment system.

### Integration boundary to freeze before implementation

Confirm the exact current names/imports, test fixtures, response-key
strictness, migration head, frontend package scripts, and dirty-worktree
changes immediately before coding. Shared files requiring coordination are:

- `backend/app/repositories/appointment_repository.py`
- `backend/app/application/consultation_service.py`
- `backend/app/api/consultation_dtos.py`
- `backend/app/api/consultation_routes.py`
- `backend/app/__init__.py`
- `frontend/src/app/features/consultation-records/consultationTypes.ts` only if
  the existing booking type is intentionally reused/relocated
- `frontend/src/app/core/App.tsx`
- `frontend/src/app/layout/AppLayout.tsx`
- shared PostgreSQL fixtures and regression tests

No architecture change is currently indicated. If inspection discovers that
the consultation service cannot safely expose a read without coupling to
Flask/SQLAlchemy, document that conflict and the smallest focused read-service
alternative before implementation; do not silently redesign Feature 004.

## 3. Specification Traceability

| Approved requirement | Planned responsibility | Acceptance evidence |
| --- | --- | --- |
| Existing Feature 004 booking remains authoritative | Reuse appointment table, repository, session, and POST flow unchanged | PostgreSQL booking-then-list continuity test |
| `GET /api/v1/appointments` | Extend existing versioned consultation blueprint or its current API boundary | Exact method/path/status tests |
| No query parameters/body | Route rejects `request.args` or non-empty request data before service call | 400 and zero-call tests |
| Exact `{items: [...]}` response | Dedicated list DTO with explicit fields only | Exact JSON shape test |
| Patient from Consultation | Joined repository projection | Patient-name lineage test |
| Treatment/id from selected recommendation lineage | Join recommendation through summary and constrain to appointment consultation | Treatment/recommendation lineage test |
| Deterministic ordering | `scheduled_at ASC`, then `Appointment.id ASC` | Same-time tie-break test |
| No N+1/duplicate rows | One focused joined query with constrained lineage and one row per appointment | SQL statement/load-path and duplicate-row tests |
| Shared request-scoped Session | Existing `create_app` composition | Repository identity/session composition test |
| Safe 500 | Existing unexpected-error boundary plus route operation | No internal error detail test |
| No migration | Use existing Feature 004 schema | Migration diff/head check |
| No AI/external network | Read-only repository/service route and strict doubles | No-AI/no-network tests and dependency review |
| Dedicated frontend service | Feature-local list API with configured base URL | One-request transport tests |
| Runtime validation | Exact object/array/UUID/string/timestamp/lineage checks | Malformed response matrix |
| Loading/populated/empty/error/retry | Appointments screen state machine | RTL state and request-count tests |
| One retry request | Explicit Retry calls service once; no auto retry | Deferred/retry assertion |
| Related consultation navigation | One row/card action using persisted `consultation_id` | MemoryRouter location test |
| Shared responsive navigation | Add one Appointments item to existing navigation array and active helper | Desktop/mobile order, active, close tests |
| Dashboard consistency | Re-read existing Dashboard after booking; no count mutation | Before/after Dashboard persistence test |
| Feature 001–006 compatibility | Existing backend/frontend suites and direct route checks | Regression run and route evidence |
| Feature 008 separation | Use current visual language only; no screenshot matching/polish | Scope/diff review |

## 4. Implementation Stages

Each stage below is a small implementation unit suitable for later task
decomposition. The implementation sequence and safe parallelization appear in
Sections 5 and 6.

### Stage 1 — Confirm integration boundaries and test seams

**Objective:** Freeze the actual Feature 004–006 interfaces before changing
shared backend and shell files.

**Likely files/areas:** approved Feature 007 specification; plans and code for
Features 004–006; appointment/consultation models and migrations; appointment,
consultation, summary, Dashboard repositories/services/routes/DTOs;
`create_app`; frontend `App.tsx`, `AppLayout.tsx`, consultation API/types,
Dashboard API/screen; backend/frontend fixtures and package scripts.

**Dependencies:** Approved specification and current repository state.

**Architecture boundary:** Read-only inspection across persistence,
application, API, frontend service, presentation, composition, and tests.

**Implementation approach:** Confirm that `AppointmentRepository` and
`ConsultationApplicationService` are the reuse points; confirm API error and
request-body conventions; identify fixture cleanup order; confirm the
Dashboard count query; record current migration head and Docker commands.
Inspect `git status --short` and preserve unrelated changes.

**Tests:** No product test changes in this stage. Record the focused commands
to run later, including backend pytest, frontend Vitest, lint/type/build,
migration-head, and Compose checks.

**Acceptance evidence:** A file-level change map and explicit confirmation
that no new table, migration, engine, session factory, AI dependency, or
navigation system is needed.

**Scope guards:** Do not modify product code, create tasks, alter Feature 004
booking, or begin Feature 008.

### Stage 2 — Add the appointment repository joined read query

**Objective:** Return one authoritative appointment list projection in one
focused, deterministic SQLAlchemy query without N+1 lookups or fabricated
related values.

**Likely files/areas:**
`backend/app/repositories/appointment_repository.py`; repository tests in
`backend/tests/test_appointment_repository.py` or a focused new list-read test
module; existing model imports and PostgreSQL fixtures.

**Dependencies:** Stage 1; existing Feature 004 mappings and repository.

**Architecture boundary:** Repository owns SQLAlchemy mechanics only. It does
not serialize JSON, inspect Flask requests, call AI, or apply UI behavior.

**Implementation approach:** Add a narrowly typed `list_appointments()` (name
may follow existing conventions) returning a provider-neutral read projection.
Select appointment columns, `Consultation.patient_name`, and the selected
recommendation `id/treatment`. Join explicitly:

```text
Appointment
  JOIN Consultation
    ON Appointment.consultation_id = Consultation.id
  JOIN ConsultationRecommendation
    ON Appointment.recommendation_id = ConsultationRecommendation.id
  JOIN ConsultationSummary
    ON ConsultationRecommendation.summary_id = ConsultationSummary.id
   AND ConsultationSummary.consultation_id = Appointment.consultation_id
```

Use a single `select(...)`/execute path, no relationship attributes, no
separate consultation/recommendation loads, and no Python-side matching. Order
by `Appointment.scheduled_at.asc(), Appointment.id.asc()`. The constrained
summary join makes selected recommendation lineage explicit. Do not add
`distinct()` as a substitute for correct joins; if the schema could produce
duplicates, resolve the join predicate/design so one appointment yields one
row. Let inconsistent legacy lineage raise to the safe server boundary rather
than omit or invent patient/treatment data. Never commit or mutate.

**Tests:** Empty result; one projection; multiple rows; same-time ID tie-break;
patient-name resolution; recommendation ID/treatment resolution; no duplicate
row; one SQL/load path/no N+1; no commit/mutation; request-scoped session
identity; no AI/external call.

**Acceptance evidence:** Repository tests demonstrate exact projections and
ordering from persisted rows and show that related values are not retrieved by
per-item queries.

**Scope guards:** Do not change `Appointment` columns, constraints, booking
transaction behavior, recommendation text storage, Dashboard query, or add a
new repository hierarchy.

### Stage 3 — Add the application-layer list operation

**Objective:** Expose a provider-neutral read operation through the existing
`ConsultationApplicationService` boundary.

**Likely files/areas:** `backend/app/application/consultation_service.py` and
`backend/tests/application/test_consultation_service.py` (or a focused
appointment-list application test).

**Dependencies:** Stage 2 repository method.

**Architecture boundary:** Application service coordinates the use case and
returns repository values. It remains independent of Flask, Pydantic,
SQLAlchemy query mechanics, React, and AI.

**Implementation approach:** Add `list_appointments()` delegating exactly once
to the configured `AppointmentRepository`. Reuse the existing appointment
dependency guard and do not perform filtering, sorting, enrichment, caching,
counting, mutation, commit, or AI work in the service. Preserve all existing
constructor parameters and booking methods/test seams.

**Tests:** Delegation and return-value identity; missing dependency is an
unexpected internal configuration failure; no commit/mutation; strict AI
double remains unused; repository failure propagates for the API boundary to
handle safely.

**Acceptance evidence:** The application test proves the list use case does
not know about Flask or SQLAlchemy and invokes one repository read.

**Scope guards:** Do not introduce a second appointment application service
unless Stage 1 documents a real boundary conflict. Do not modify booking
eligibility, creation, status transitions, or clocks.

### Stage 4 — Add list DTOs and the Flask API endpoint

**Objective:** Implement the exact safe `GET /api/v1/appointments` contract.

**Likely files/areas:** `backend/app/api/consultation_dtos.py` (or a focused
appointment DTO module if that matches current conventions),
`backend/app/api/consultation_routes.py`, and backend API tests.

**Dependencies:** Stage 3 and existing route/error conventions.

**Architecture boundary:** Flask route owns request-shape rejection and DTO
serialization. It must not access sessions, execute SQL, construct models,
join rows, derive Dashboard data, or call AI.

**Implementation approach:** Add explicit list projection DTOs containing only:
`id`, `consultation_id`, `patient_name`, nested recommendation `id/treatment`,
`scheduled_at`, `location`, and `created_at`; add the exact `{items: [...]}`
envelope. Require aware timestamps and serialize UUIDs/timestamps through
Pydantic JSON mode. Keep the existing booking DTO/response unchanged.

At route entry reject any query parameter or non-empty request body before
calling the application operation, returning exactly `400` and
`{"error":"Invalid request"}`. An empty body/content type remains valid.
Delegate once to the service, map each read projection to the list DTO, and
return `200`. Do not add pagination, filters, date ranges, sorting controls,
status, provider, or other fields. Unexpected repository, mapping, database,
or serialization errors must reach the existing safe `500` handler without
internal details.

**Tests:** Exact successful populated shape and no extra fields; empty
`{items:[]}`; query/body rejection; malformed input does not call service;
UUID and explicit-offset timestamp serialization; unexpected service failure
returns safe 500; no AI/no mutation. Include a test that existing POST
booking response remains unchanged.

**Acceptance evidence:** Flask test client proves valid empty requests make one
application call and invalid request shapes make zero calls.

**Scope guards:** Do not create a new blueprint unless required by existing
conventions; do not change API-wide error semantics or booking endpoint
semantics.

### Stage 5 — Verify `create_app` and request-scoped composition

**Objective:** Ensure the list flow uses the same request-scoped Session and
composition as Feature 004 booking and Feature 005 Dashboard.

**Likely files/areas:** `backend/app/__init__.py`; composition tests such as
`backend/tests/test_dashboard_composition.py`; API persistence fixtures.

**Dependencies:** Stages 2–4.

**Architecture boundary:** Infrastructure composition only; no new session,
engine, repository hierarchy, or transaction boundary.

**Implementation approach:** Prefer no production change: the existing
`AppointmentRepository(session)` already enters
`ConsultationApplicationService`, which is registered per request. Verify the
new route resolves that service and that teardown closes the same session.
If a small composition edit is needed, preserve optional injected service
behavior used by unit/API tests and retain Dashboard repository identity.

**Tests:** Production composition list request against PostgreSQL; injected
service route test; session identity/teardown test; no second engine/session
factory; no commit for list request.

**Acceptance evidence:** A persisted appointment created/read through the
production app is visible from a fresh session and the list request does not
insert or update rows.

**Scope guards:** Do not move composition, alter teardown semantics, or change
Feature 004’s atomic booking unit of work.

### Stage 6 — Backend repository/application/API unit and integration tests

**Objective:** Complete deterministic backend coverage before wiring the live
frontend.

**Likely files/areas:** appointment repository/application/API test modules,
existing PostgreSQL fixtures, booking route tests, and persistence API tests.

**Dependencies:** Stages 2–5.

**Architecture boundary:** Tests may use repository, application, Flask test
client, and real PostgreSQL seams but must not introduce product abstractions.

**Implementation approach:** Use deterministic UUIDs, timestamps, locations,
consultations, summaries, and recommendations. Test exact output and
failure boundaries. Reuse existing fixture cleanup order: appointments before
recommendations/summaries/consultations. Do not seed appointments through a
new Feature 007 write endpoint.

**Tests:** All repository/application/API cases from the approved
specification, including request rejection before repository access and safe
500 sanitization.

**Acceptance evidence:** Focused backend suite passes with no OpenAI
credentials or external network and confirms list reads perform no commits or
row mutations.

**Scope guards:** No migration or test-only alternate data source.

### Stage 7 — Feature 004 booking → Feature 007 retrieval PostgreSQL slice

**Objective:** Prove that the same committed appointment is returned by the
new read path with authoritative identifiers and related values.

**Likely files/areas:** existing Feature 004 booking persistence/API tests,
new Feature 007 PostgreSQL integration test, shared test fixtures.

**Dependencies:** Stages 3–6.

**Architecture boundary:** Real PostgreSQL, existing booking API/application
path, and new list API path; no frontend or AI dependency.

**Implementation approach:** Create a completed consultation, persisted
summary, and selected recommendation using existing deterministic test seams.
Book through the existing `POST /api/v1/consultations/{id}/appointments`
workflow, commit it, then call `GET /api/v1/appointments` in a fresh request
or session. Assert the exact appointment ID, consultation ID,
recommendation ID/treatment, scheduled instant, location, created timestamp,
and patient name. Assert one appointment row and no list-request insert or
status mutation. Include historical/passed appointments in list coverage as
the read contract does not hide them.

**Tests:** Full continuity and fresh-session assertions; recommendation
lineage; no duplicate list item; no AI/network calls.

**Acceptance evidence:** The returned object is demonstrably the same row
created by Feature 004, not a consultation-derived or frontend-created record.

**Scope guards:** Do not create appointments through Feature 007, alter
booking semantics, or add status/calendar behavior.

### Stage 8 — Dashboard consistency verification

**Objective:** Confirm the existing Dashboard continues to count the same
persisted appointment row without synchronization logic.

**Likely files/areas:** `backend/app/repositories/dashboard_repository.py`,
existing Dashboard persistence tests, the Feature 004→007 integration test.

**Dependencies:** Stage 7.

**Architecture boundary:** Read-only verification of the existing Dashboard
aggregate; no Feature 007 count endpoint or frontend count state.

**Implementation approach:** Read Dashboard before booking, perform Feature
004 booking, read Dashboard again, and assert `booked_appointments` increases
according to the existing PostgreSQL count. Call the appointments list and
then Dashboard again to prove the list read has no side effect. Do not modify
Dashboard production code unless a test exposes an actual regression caused
by the list implementation.

**Tests:** Existing dashboard persistence and composition tests plus the
vertical-slice before/after metric assertion.

**Acceptance evidence:** Dashboard count and appointment list refer to the
same authoritative `appointments` row, with no event, callback, local count,
or duplicate metric calculation.

**Scope guards:** No Dashboard redesign, second count, cache, or synchronization
callback.

### Stage 9 — Frontend appointment types, service, and runtime validation

**Objective:** Add a dedicated, one-shot frontend list boundary for the exact
API representation.

**Likely files/areas:** Prefer new
`frontend/src/app/features/appointments/appointmentTypes.ts` and
`appointmentApi.ts`; tests beside them; only reuse the existing consultation
`Appointment` type if doing so does not couple the list feature to booking
screen concerns.

**Dependencies:** Stable backend contract from Stage 4; Stage 1 frontend
conventions.

**Architecture boundary:** Frontend service owns URL/configuration, transport,
status handling, JSON parsing, runtime validation, and safe typed errors. The
screen must not call `fetch` directly and the service must not render UI.

**Implementation approach:** Issue exactly one `GET /api/v1/appointments`
request with no query/body and accept only `200`. Parse and validate an exact
top-level `{items: [...]}` shape and each exact item projection. Validate
canonical UUIDs, non-empty strings, nested recommendation id/treatment,
explicit-offset timestamps with valid calendar/time/offset components, and
duplicate/malformed projections according to the specification. Map all
non-2xx, malformed JSON, validation, and transport failures to a safe
feature-facing retrieval error. Never return `[]` on failure, auto-retry, or
expose raw response/transport/database text. Keep the existing booking service
behavior intact.

**Tests:** Correct GET URL/base URL, method, no body/query; valid populated and
empty response; malformed JSON/shape/extra structure; invalid UUIDs,
timestamps, strings, nested recommendation; duplicate/malformed item; non-2xx
and network errors; exactly one request per service call and no automatic
retry.

**Acceptance evidence:** Service tests return only validated feature types and
safe errors with deterministic transport doubles.

**Scope guards:** No consultation API reuse as the appointment source, no
localStorage/sessionStorage, no polling, and no frontend-created records.

### Stage 10 — `/appointments` screen and state machine

**Objective:** Render the authoritative list with accessible loading,
populated, empty, and recoverable-error states inside the existing shell.

**Likely files/areas:** new feature-local `AppointmentsScreen.tsx` and
component tests; `frontend/src/app/core/App.tsx`; existing MUI theme/layout
conventions.

**Dependencies:** Stage 9 types/service; existing `AppLayout` route boundary.

**Architecture boundary:** Screen owns presentation state and navigation. It
does not fetch directly, derive appointments from consultations/Dashboard,
persist browser data, or create booking records.

**Implementation approach:** Add `/appointments` as a static route nested
under `AppLayout`. On entry and explicit Retry, set loading and replace any
previously displayed data so stale results are not presented as current.
Invoke the service once. Render a clear accessible status while pending; a
clear populated list; `No appointments yet.` for a successful empty result;
and a safe error Alert with exactly one explicit Retry action. Use request
identity/unmount protection consistent with Dashboard to prevent stale
responses from winning. Keep error distinct from empty.

**Tests:** Loading; populated patient/treatment/date-time/location and stable
identity/context; empty; error; failed retrieval does not render empty;
Retry causes one new request; no automatic retry; unmount/stale response
protection; direct route render.

**Acceptance evidence:** RTL tests prove each state and that all data shown
comes from the injected appointment-list service.

**Scope guards:** No booking controls, edit/cancel/status/calendar UI,
dashboard redesign, or new consultation-detail architecture.

### Stage 11 — Responsive table/card presentation and consultation navigation

**Objective:** Make the same appointment data readable on desktop and narrow
screens and provide one unambiguous route to the related consultation.

**Likely files/areas:** `AppointmentsScreen.tsx` and a feature-local table/card
component if useful; screen/router tests.

**Dependencies:** Stage 10 and existing MUI/layout sizing.

**Architecture boundary:** Presentation adaptation only; routing uses the
existing React Router and persisted ID.

**Implementation approach:** Use a restrained MUI table at desktop widths and
a stacked/card/list layout at narrow widths, or a single responsive list that
does not horizontally overflow. Do not create separate data loaders or
navigation models. Choose one clear interaction per item: the entire
keyboard-accessible row/card as a link, or one `View consultation` action.
Navigate exactly to `/consultations/{consultation_id}` using the returned
persisted ID; do not add redundant patient/row/action links.

**Tests:** Desktop content; narrow viewport readability/no required horizontal
overflow; keyboard activation; exact destination; existing consultation detail
route remains reachable.

**Acceptance evidence:** A populated item offers one accessible consultation
navigation interaction and preserves the current route architecture.

**Scope guards:** No screenshot matching, visual alignment pass, shell
redesign, or Feature 008 polish.

### Stage 12 — Shared Appointments navigation and active state

**Objective:** Add Appointments once to the existing shared desktop/mobile
navigation in the specified order and preserve `+ New Consult`.

**Likely files/areas:** `frontend/src/app/layout/AppLayout.tsx`, its tests,
and `frontend/src/app/core/App.tsx` route tests.

**Dependencies:** Stage 10 route exists; existing AppLayout patterns.

**Architecture boundary:** Shared application shell/navigation only.

**Implementation approach:** Extend the single `navigationItems` definition to
Dashboard, Consultations, Appointments, with one icon/label/destination
mapping. Update the active helper so Dashboard is exact, Consultations covers
its existing descendants, and Appointments covers `/appointments` and future
appointment descendants but does not activate on consultation booking routes.
Use the existing permanent desktop Drawer and temporary mobile Drawer. Keep
`+ New Consult` at `/consultations/new`, and preserve mobile close-on-navigation
through the existing callback.

**Tests:** Desktop/mobile same order and destinations; `/appointments` only
marks Appointments; consultation detail/summary/booking descendants still mark
Consultations; lookalike paths do not activate; mobile drawer closes after
Appointments navigation; New Consult remains functional.

**Acceptance evidence:** One shared definition drives both navigation modes and
no router or shell duplication is introduced.

**Scope guards:** No route flattening, navigation redesign, branding change, or
Feature 008 visual alignment.

### Stage 13 — Features 001–006 regression and lifecycle verification

**Objective:** Demonstrate that existing consultation, booking, Dashboard,
root, and shell behavior remains compatible.

**Likely files/areas:** Existing backend pytest modules; frontend App/layout,
consultation-records, Dashboard, route, and API tests; Compose configuration.

**Dependencies:** Stages 7–12.

**Architecture boundary:** Cross-feature verification only; no unrelated
refactor.

**Implementation approach:** Run the complete existing suites and targeted
direct-route checks for `/`, `/dashboard`, `/consultations`, `/consultations/new`,
consultation detail, summary, booking, and `/appointments`. Verify Feature 004
booking still returns its original response and updates `BOOKED`; verify
Dashboard metrics and Feature 006 New Consult remain functional. Confirm the
Appointments list uses only its new endpoint.

**Tests:** Features 001–006 backend/frontend regression; route reachability;
shared navigation and root redirect; booking screen/API; Dashboard read;
new-appointment screen/API.

**Acceptance evidence:** Existing tests pass without loosening assertions or
changing approved behavior.

**Scope guards:** Do not fix unrelated failures by broadening Feature 007 or
altering earlier feature contracts without documenting a separate decision.

### Stage 14 — No-AI, no-migration, Docker, and scope verification

**Objective:** Prove the read feature is deterministic, schema-preserving,
container-compatible, and isolated from Feature 008.

**Likely files/areas:** git diff; migration directory/head; AI imports and
test doubles; `compose.yaml`, backend/frontend Dockerfiles, package/requirements
files; changed tests.

**Dependencies:** All implementation stages.

**Architecture boundary:** Release/scope verification.

**Implementation approach:** Confirm no new migration or model/table change;
run migration-head/schema checks against existing Feature 004 appointments.
Use strict AI/network doubles and inspect the list dependency graph for no
`AIService`, LangChain, provider, or external request. Run backend/frontend
tests without OpenAI credentials. Verify Compose still builds/runs with no
new service, port, environment, or dependency. Review diff for only Feature
007 changes and existing test updates; specifically reject screenshot matching
or screen-by-screen Feature 008 work.

**Tests/evidence:** No-migration diff; no-AI/no-network test; Compose/build and
type/lint checks; dependency review; scope review.

**Scope guards:** Do not add migration “just for indexing,” AI fallback,
external calendar integration, or visual-polish work.

### Stage 15 — Final vertical-slice verification

**Objective:** Validate the full approved Definition of Done from persisted
booking through list, consultation navigation, and Dashboard consistency.

**Likely files/areas:** Full backend/frontend test suites, PostgreSQL
integration fixtures, browser/router tests, Docker runtime, final diff.

**Dependencies:** Stages 1–14.

**Architecture boundary:** End-to-end verification across existing boundaries;
no new implementation scope.

**Implementation approach:** Execute the continuity scenario:

```text
completed consultation + persisted recommendation
  → Feature 004 booking
  → committed Appointment row
  → GET /api/v1/appointments
  → /appointments populated state
  → existing related consultation route
  → Dashboard booked_appointments count
```

Cross-check exact IDs, treatment, patient, timestamp, location, response
shape, ordering, empty/error/retry behavior, desktop/mobile navigation, and
regressions. Collect commands and outcomes for handoff.

**Tests/evidence:** Focused and full pytest/Vitest suites; lint/type/build;
PostgreSQL integration; route/navigation tests; migration/no-AI/Compose
checks; final `git diff --check`.

**Scope guards:** Stop after Feature 007 evidence. Do not create task files or
begin Feature 008.

## 5. Dependency Order / Critical Path

The required dependency order is:

```text
1 boundary confirmation
        ↓
2 repository query
        ↓
3 application operation
        ↓
4 DTO/API
        ↓
5 composition verification
        ↓
6 backend unit/API tests
        ↓
7 booking → list PostgreSQL slice
        ↓
8 Dashboard consistency

1 boundary confirmation
        ↓
9 frontend types/service
        ↓
10 screen + /appointments route
        ↓
11 responsive presentation + consultation link
        ↓
12 shared navigation
        ↓
13 regression
        ↓
14 scope/runtime checks
        ↓
15 final vertical slice
```

The live frontend/API integration requires Stages 4, 9, and 10. The final
vertical slice requires both backend and frontend paths plus the existing
Feature 004 booking and Dashboard reads.

## 6. Safe Parallelization

After Stage 1 boundary confirmation:

- Stages 2 and 9 can proceed in parallel once the exact API projection is
  agreed: repository/backend work and frontend types/service tests are
  separate, with live integration waiting for Stage 4.
- Stage 3 can follow Stage 2 while frontend Stage 9 proceeds.
- Backend repository tests and API/DTO tests can overlap after the application
  method signature and DTO shape are fixed, provided shared PostgreSQL fixture
  edits have one owner.
- Stage 10 screen tests can be developed against an injected appointment
  service while Stages 3–6 finish; route integration waits for the screen
  contract.
- Stage 11 presentation tests and Stage 12 navigation tests can overlap after
  `/appointments` is registered, but coordinate changes to `App.tsx` and
  `AppLayout.tsx`.
- Stage 7 booking/list integration and Stage 8 Dashboard verification can be
  prepared together, but should converge on one committed PostgreSQL fixture
  and avoid duplicate cleanup/transaction assumptions.
- Final backend and frontend focused suites may run in parallel; Compose and
  full vertical-slice checks follow successful builds and integration tests.

Do not parallel-edit `consultation_routes.py`, `consultation_service.py`,
`appointment_repository.py`, `App.tsx`, `AppLayout.tsx`, or shared fixtures
without explicit ownership. Parallelization is by boundary, not merely by
test file.

## 7. Backend Design Summary

The intended backend path is:

```text
GET /api/v1/appointments
  → request-shape guard in existing Flask blueprint
  → ConsultationApplicationService.list_appointments()
  → AppointmentRepository.list_appointments()
  → one joined SELECT on the request-scoped Session
  → list read projection
  → explicit Pydantic DTO serialization
```

The repository query joins Appointment to Consultation, Recommendation, and
Summary with the summary-to-consultation lineage constraint and orders by
`scheduled_at ASC, Appointment.id ASC`. It returns no SQLAlchemy models across
the API boundary, performs no commit, and does not load related records per
item. Unexpected lineage/database/serialization failures use the existing safe
500 boundary.

The booking aggregate and POST response remain unchanged. The list DTO is
separate because `patient_name` is a directly resolved list projection, not a
new Appointment column.

## 8. Frontend Design Summary

Add a feature-local appointment list service and types using the existing API
base URL and injected transport conventions. The service performs exactly one
GET per invocation, validates the exact response shape and values, and maps
all failures to a safe retrieval error. The screen owns only loading,
success/empty, error, retry, and navigation state. It never derives data from
consultations, Dashboard metrics, booking state, or browser storage.

Render the approved fields—patient, selected treatment, date/time, location,
and stable appointment/consultation identity—in a restrained MUI responsive
table/card presentation. Use the existing visual language and layout; defer
screen-by-screen visual alignment to Feature 008.

## 9. Navigation Design Summary

Add one `Appointments` item to the existing shared navigation array after
Consultations, targeting `/appointments`. The active helper must exact-match
Dashboard, match Consultation descendants, and match the Appointments section
without activating Consultation on appointment routes or vice versa. The same
definition drives permanent desktop and temporary mobile drawers. Preserve
`+ New Consult`, all existing routes, accessibility semantics, and mobile
drawer close-on-navigation.

## 10. Feature 004 and Dashboard Strategy

Feature 004 integration is write-then-read, never a second write path. The
integration test books through the existing consultation booking endpoint,
then retrieves through the new list endpoint using a fresh authoritative read.
The test asserts the same persisted appointment ID and all related lineage,
time, location, and creation values.

Dashboard consistency is verified by reading the existing Dashboard metric
before and after Feature 004 booking and again after the list request. The
metric must continue to count `appointments` rows from PostgreSQL. Feature
007 adds no count calculation, synchronization callback, frontend count
mutation, or Dashboard endpoint.

## 11. Testing Strategy

Use the existing deterministic unit, API, PostgreSQL, Vitest, and React
Testing Library seams. Cover repository query correctness and one-load-path
behavior; application delegation; exact request/response/error contracts;
Feature 004 continuity; Dashboard count continuity; service runtime
validation and one-request semantics; screen state transitions and retry
count; responsive rendering; consultation navigation; shared navigation and
all Features 001–006 regressions.

Tests must run without OpenAI credentials, AI calls, or external network.
They must not seed appointments through a new Feature 007 endpoint or use
browser storage as an authority.

## 12. Migration, AI, and Scope Decisions

- **Migration:** None. Feature 004’s `appointments` table and constraints
  already supply every required value, index/uniqueness guarantee, and
  lineage foreign key. The plan must produce no migration file.
- **AI:** None. Listing is deterministic and read-only; no
  `AIService`, provider, LangChain, agent, skill, or external request enters
  the dependency path or tests.
- **Architecture:** Extend `AppointmentRepository` and
  `ConsultationApplicationService`; do not add a parallel appointment system,
  session architecture, or persistence model.
- **Feature 008:** Out of scope. Use current MUI/application visual language
  and responsive conventions only; no screenshot matching, shell redesign, or
  screen-by-screen polish.

## 13. Final Cross-Check / Unresolved Conflicts

The plan satisfies the approved requirements for the exact GET contract,
request rejection, deterministic joined ordering, patient and recommendation
lineage, no N+1, shared Session, safe errors, frontend validation and state
handling, shared navigation, Feature 004 continuity, Dashboard consistency,
no migration, no AI, and Feature 008 separation.

No unresolved architectural conflict or blocker is known from the current
repository inspection. The only compatibility detail is the intentional
separation between the existing booking response/aggregate and the new list
read projection so `patient_name` can be resolved without changing Feature
004. If implementation inspection invalidates a referenced file or test seam,
record the smallest compatible adjustment in the implementation task/PR
notes before changing architecture.

## 14. Definition of Done for Implementation

Feature 007 implementation may be considered complete only after all stages
have evidence: exact API and joined repository path; request-scoped
composition; backend and PostgreSQL booking continuity; unchanged Dashboard
count behavior; dedicated validated frontend service; all screen states and
one-request Retry; responsive presentation; consultation navigation; shared
desktop/mobile Appointments navigation; Features 001–006 regressions; no
migration; no AI/network; Docker/runtime checks; and final vertical-slice
verification. This plan itself stops before implementation and task creation.
