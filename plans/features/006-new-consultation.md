# New Consultation Implementation Plan

## 1. Objective

Implement the approved Feature 006 New Consultation vertical slice on top of
completed Features 001–005:

```text
Existing + New Consult action
        ↓
/consultations/new in AppLayout
        ↓ patient_name + primary_concern
dedicated consultation frontend service
        ↓ POST /api/v1/consultations
existing consultation Flask blueprint + strict Pydantic DTO
        ↓
existing ConsultationApplicationService
        ↓
existing ConsultationRepository.create_consultation
        ↓ commit + refresh in request-scoped SQLAlchemy Session
PostgreSQL PENDING Consultation
        ↓ validated 201 response and replacement navigation
/consultations/{authoritative-id}
        ↓
existing persistent AI conversation lifecycle
```

The implementation will add one creation operation to the existing
consultation resource, one focused form screen, one static frontend route, and
functional desktop/mobile New Consult navigation. It will reuse all existing
persistence, application, API, service, router, and layout boundaries.

There will be no migration, new repository hierarchy, new database/session
architecture, creation-time AI call, child-record side effect, dashboard
mutation, Feature 007 appointment navigation/listing, or unrelated refactor.

## 2. Current-System Alignment

Feature 006 will extend these implemented conventions:

- `Consultation` in
  `backend/app/infrastructure/consultation_models.py` has exactly `id`,
  `patient_name`, `primary_concern`, `recommended_procedure`, and `status`.
  The UUID has a SQLAlchemy `uuid4` default; the three text values and status
  are non-null; approved statuses are `PENDING`, `COMPLETED`, and `BOOKED`.
- The existing Alembic chain already creates the required consultation table
  and enum. PostgreSQL accepts the approved fresh-row shape with
  `recommended_procedure=""`; Feature 003's restart workflow persists that
  exact initial projection. No schema change is needed.
- `ConsultationRepository` already accepts the request-scoped `Session` and
  exposes `create_consultation(consultation)`. That method adds, commits,
  refreshes, returns, and rolls back/re-raises on failure. It is the creation
  unit-of-work owner and will be reused without a parallel repository.
- `ConsultationApplicationService` already coordinates consultation list,
  detail, conversation, summary, restart, and appointment workflows. Its
  restart path constructs a new UUID-bearing `PENDING` consultation with an
  empty recommendation and delegates to the existing create method.
- `consultation_routes.py` owns the consultation blueprint registered under
  `/api/v1`, Pydantic boundary validation, explicit response serialization,
  and safe route-level known-outcome translation. The application-wide error
  handler returns `{ "error": "Internal server error" }` for unexpected
  exceptions.
- Existing request DTOs use Pydantic v2, `extra="forbid"`, before validators
  for trimming, strict types where coercion must be prohibited, and the exact
  safe `{ "error": "Invalid request" }` response. Existing response DTOs use
  explicit fields and `from_attributes=True` where mapping persisted objects.
- `create_app` creates one SQLAlchemy session per production request, composes
  consultation/message/summary/appointment/dashboard repositories around that
  session, injects the service through `app.extensions`, and closes the
  session during teardown. Tests can inject a consultation-service double.
- PostgreSQL tests run the existing Alembic chain against temporary PostgreSQL,
  clean child tables before consultations, and verify persistence through real
  SQLAlchemy sessions. Existing API persistence tests exercise the production
  application composition with deterministic AI configuration/doubles.
- `consultationTypes.ts` contains the existing `ConsultationRecord` and status
  types. `consultationApi.ts` uses an injectable fetch transport, safe typed
  errors, explicit URL construction, exact status handling, and runtime
  validation before returning data to screens.
- `App.tsx` owns one nested React Router tree beneath `AppLayout`; existing
  consultation records, detail, summary, and appointment-booking paths must
  remain unchanged.
- `AppLayout.tsx` has one shared `SidebarContent` used by the permanent desktop
  drawer and temporary mobile drawer. Its prominent `+ New Consult` MUI Button
  is currently disabled. Existing navigation treats every
  `/consultations/...` descendant as active Consultations context and closes
  the temporary drawer through the shared `onNavigate` callback.
- Existing screens use feature-local service interfaces, React state,
  React Testing Library, MUI, accessible state feedback, and `useNavigate`.
  Router tests use `MemoryRouter`; AppLayout tests provide deterministic
  `matchMedia` behavior for desktop/mobile coverage.
- Feature 005's dashboard counts all persisted consultation rows through
  `DashboardRepository`. A committed Feature 006 row therefore changes the
  next dashboard read naturally, with no dashboard code change.
- `compose.yaml` already supplies PostgreSQL, Flask, Vite, API URL, CORS, and
  optional real/mock AI configuration. Feature 006 needs no new service,
  environment variable, port, volume, dependency, or health check.

The working tree contains user-owned Feature 005 and other changes. Every
implementation stage must inspect and preserve unrelated edits, especially in
shared composition, router, layout, and test files.

## 3. Specification Traceability

| Approved Feature 006 requirement | Planned responsibility | Verification focus |
| --- | --- | --- |
| Only `patient_name` and `primary_concern` are supplied | Strict creation request DTO and frontend request type | Exact payload and forbidden-field tests |
| Trimmed 1–200 and 1–4,000 Unicode-character bounds | DTO validators, application defense, and form validation | Boundary, whitespace, wrong-type, and Unicode tests |
| UUID, empty recommendation, and `PENDING` are server controlled | Consultation application creation workflow | Constructed/persisted value assertions |
| `POST /api/v1/consultations` returns exact `201` record | Existing blueprint and `ConsultationResponse` | Exact status/body and safe error tests |
| No query, malformed body, or extra request field is accepted | Route input checks and Pydantic `extra="forbid"` | Zero-service-call `400` tests |
| Commit is authoritative and rollback is safe | Existing repository create unit of work | Commit/refresh/fresh-session and failure tests |
| Existing request-scoped session is reused | Existing `create_app` service composition | Production-composition persistence test |
| No AI or child aggregate creation | Narrow application workflow and strict doubles | No-call and unchanged-table tests |
| Dedicated frontend creation boundary | Existing consultation types/API module | One-shot request and runtime-validation tests |
| `/consultations/new` is static creation route | Existing nested router | Creation-versus-detail and deep-route tests |
| Accessible initial/validation/submitting/failure/success states | New Consultation screen | RTL state-machine and keyboard tests |
| Duplicate submission and automatic retry are prevented | Pending handler guard and one-shot service | Deferred-promise and request-count tests |
| Ambiguous failure preserves input and advises checking records | Safe creation error mapping and form-level recovery | Transport/malformed-success UI tests |
| Success uses returned ID and replace navigation | Screen navigation after validated `201` | Location/history and no-stale-form tests |
| Existing New Consult works on desktop/mobile | Shared `SidebarContent` action | Link, drawer-close, keyboard, active-state tests |
| Dashboard observes committed row naturally | Existing dashboard repository only | Before/after PostgreSQL metric integration test |
| Features 001–005 remain compatible | Full backend/frontend and route regression | Existing suites plus vertical slice |
| No migration, Feature 007, or redesign | Scope review and unchanged infrastructure/schema | Diff, migration-head, route, and Compose review |

## 4. Stage 1 — Confirm Feature 006 Integration Boundaries

### Purpose

Freeze the exact implementation seams before editing shared files and record
the current test/run commands. This stage prevents a parallel creation design
or accidental overwrite of completed Feature 005 work.

### Likely files and areas inspected

- `specs/features/006-new-consultation.md`
- `backend/app/infrastructure/consultation_models.py`
- `backend/app/repositories/consultation_repository.py`
- `backend/app/application/consultation_service.py`
- `backend/app/api/consultation_dtos.py`
- `backend/app/api/consultation_routes.py`
- `backend/app/__init__.py`
- existing migrations and backend consultation/dashboard tests
- `frontend/src/app/features/consultation-records/consultationTypes.ts`
- `frontend/src/app/features/consultation-records/consultationApi.ts`
- `frontend/src/app/core/App.tsx`
- `frontend/src/app/layout/AppLayout.tsx`
- relevant frontend tests, package scripts, and `compose.yaml`

### Architecture boundary

Read-only investigation across persistence, application, API, frontend
service, routing, layout, testing, and runtime composition. No product code,
migration, task file, or architecture decision is produced by this stage.

### Dependencies

- Approved Feature 006 specification.
- Completed Features 001–005 and their current working-tree state.

### Implementation details

- Confirm exact Python/TypeScript names, imports, fixture cleanup order,
  service injection behavior, and existing error-kind conventions.
- Confirm whether existing tests compare complete response keys or tolerate
  additions only in the new method; Feature 006 must not loosen old validators.
- Confirm the browser test environment's support for semantic forms,
  replacement navigation probes, deferred promises, and responsive drawer
  interaction.
- Record exact backend, frontend, lint, type, build, migration, and Compose
  commands for later verification.
- Inspect `git status --short` before changes and identify overlapping
  user-owned edits in shared files.

### Tests and acceptance evidence

- No new feature test is required during this read-only stage.
- Produce boundary notes in the later task findings/implementation evidence,
  including the current migration head, route tree, session ownership,
  repository commit behavior, and active New Consult control.
- Acceptance evidence is a confirmed file-level change map with no unresolved
  conflict against the approved specification.

### Scope guards

- Do not alter the schema or propose a migration.
- Do not split the application service, repository, session, or frontend HTTP
  client.
- Do not treat inspection findings as permission for unrelated cleanup.
- Stop and document any material conflict with the approved specification
  rather than silently redesigning prior features.

## 5. Stage 2 — Add Backend Creation DTO and Application Workflow

### Purpose

Introduce strict input normalization and the smallest application-facing
creation use case while keeping lifecycle values server controlled.

### Likely files and areas affected

- `backend/app/api/consultation_dtos.py`
- `backend/app/application/consultation_service.py`
- `backend/tests/api/test_consultation_dtos.py`
- `backend/tests/application/test_consultation_service.py` or a focused new
  consultation-creation application test module if that keeps coverage clear

### Architecture boundary

- Pydantic owns HTTP input shape/type/length validation and normalization.
- `ConsultationApplicationService` owns consultation construction and creation
  invariants.
- Neither boundary commits, queries the dashboard, invokes AI, nor creates
  messages/summaries/recommendations/appointments.

### Dependencies

- Stage 1 boundary confirmation.
- Existing `Consultation`, `ConsultationStatus`, and repository create method.

### Implementation details

Add a request DTO, likely `ConsultationCreationRequest`, with:

- `ConfigDict(extra="forbid")`;
- `patient_name` as `StrictStr`, normalized with a `mode="before"` trim
  validator, then constrained to 1–200 characters;
- `primary_concern` as `StrictStr`, normalized the same way, then constrained
  to 1–4,000 characters; and
- no `id`, `recommended_procedure`, `status`, timestamp, or child data field.

Use Pydantic validators in an order that makes whitespace-only values fail
after trimming and prevents number/boolean/container coercion. Measure Python
string length after normalization, matching the approved Unicode code-point
contract.

Extend `ConsultationApplicationService` with one creation method, likely:

```text
create_consultation(patient_name, primary_concern) -> Consultation
```

The method will:

1. defensively require string inputs and normalize/validate the same bounds so
   non-Flask callers cannot bypass core creation invariants;
2. construct one `Consultation` with a fresh UUID (explicit `uuid4` following
   the existing restart style, or the existing model default if boundary
   confirmation establishes one consistent approach);
3. set only normalized user values, `recommended_procedure=""`, and
   `ConsultationStatus.PENDING`;
4. call `self._repository.create_consultation(...)` exactly once; and
5. return the repository-confirmed object.

Prefer a small typed invalid-creation application outcome only if needed for
defensive non-DTO callers; translate it to the existing safe `400` contract.
Do not add a new domain framework or generic validator abstraction.

### Tests

DTO tests:

- accept exact minimum and maximum normalized lengths;
- trim both fields;
- reject missing, empty, whitespace-only, over-length, numeric, boolean,
  array, object, `null`, and unknown fields;
- prove `id`, `status`, and `recommended_procedure` are forbidden; and
- verify validation does not mutate or persist anything.

Application tests:

- assert normalized fields, generated UUID, empty recommendation, and exact
  `PENDING` status on the object passed to the repository;
- assert one repository create call and return of the repository-confirmed
  object;
- cover defensive blank/wrong/over-length input if the service exposes those
  guards; and
- use strict dependencies or explicit assertions proving no message, summary,
  appointment, dashboard, or AI method is invoked.

### Acceptance evidence

- Focused DTO and application tests pass.
- A captured repository argument shows the exact five-field initial state.
- No persistence mapping, migration, application composition, or AI file is
  changed.

### Scope guards

- Do not accept client lifecycle values.
- Do not generate a greeting, message, recommendation, summary, or appointment.
- Do not create a new application service or repository for the use case.
- Do not infer clinical meaning from either input.

## 6. Stage 3 — Verify Repository Creation and Expose the POST API

### Purpose

Reuse and harden the existing authoritative persistence operation, then expose
the exact REST creation contract through the current consultation blueprint.

### Likely files and areas affected

- `backend/app/repositories/consultation_repository.py` only if focused tests
  reveal a small specification mismatch; otherwise production code remains
  unchanged
- `backend/app/api/consultation_routes.py`
- `backend/app/__init__.py` only if boundary verification reveals an actual
  composition requirement; none is expected
- `backend/tests/test_consultation_repository.py`
- `backend/tests/api/test_consultation_routes.py`
- `backend/tests/api/test_consultation_persistence_api.py`
- relevant backend fixtures only for additive, FK-safe cleanup or strict
  no-side-effect assertions

### Architecture boundary

- Repository owns add/commit/refresh/rollback against the existing session.
- Flask owns HTTP/content/query/body parsing, DTO invocation, response mapping,
  and safe error translation.
- Application service remains the only route dependency.

### Dependencies

- Stage 2 DTO and application creation method.
- Existing repository unit-of-work behavior and `ConsultationResponse`.

### Implementation details

#### Repository verification

Retain `ConsultationRepository.create_consultation` as the single creation
operation. Do not rename or duplicate it merely for Feature 006. Verify that:

- `add` occurs before `commit`;
- a successful commit is followed by `refresh` and the refreshed persisted row
  is returned;
- any add/commit/refresh exception triggers `rollback` and is re-raised;
- a fresh session can retrieve the returned UUID and normalized values; and
- failure does not leave a visible committed row.

If current behavior already satisfies every point, add tests without changing
the repository. A correction is allowed only if a focused test proves an
approved invariant is missing, and it must preserve Feature 003 restart
behavior.

#### Route

Add exactly:

```text
POST /api/v1/consultations
```

The route will:

1. reject any query parameter before service delegation;
2. require an actual JSON request content type and parse one JSON object
   safely, ensuring absent, empty, malformed, `null`, array, scalar, or
   non-JSON bodies become the exact safe `400`;
3. validate via the creation DTO, including forbidden extra fields;
4. call the existing application service once with the DTO's normalized two
   values;
5. map a defensive application validation outcome, if present, to `400`;
6. serialize the returned persisted object through the existing
   `ConsultationResponse`; and
7. return exact HTTP `201` only after repository commit/refresh succeeded.

All unexpected repository, database, refresh, serialization, or application
errors flow through the existing safe `500` handler. Do not catch and expose
raw exception text. The route does not add a `Location` header because the
approved contract does not promise one.

#### Composition

No production composition change is expected: the request-scoped service
already contains the required `ConsultationRepository`. Confirm injected
service tests still work and production requests use the same session shared
with existing repositories. Change `create_app` only if a concrete missing
wiring seam is discovered; do not add another constructor argument, session,
engine, or service instance for creation.

### Tests

Repository tests:

- commit/refresh/return on success;
- rollback/re-raise for controlled add/commit/refresh failure seams where
  practical without altering production semantics;
- persisted reload by generated UUID; and
- existing restart creation compatibility.

API tests:

- exact valid request, one service call with normalized values, exact `201`,
  and exact five-field response;
- no query parameters;
- required JSON content type;
- absent, empty, malformed, `null`, scalar, array, missing-field, wrong-type,
  empty, whitespace, over-length, and extra-field bodies;
- forbidden `id`, `status`, and `recommended_procedure` fields;
- service not called for every boundary-invalid request; and
- safe generic `500` with no SQL, database URL, credentials, environment,
  stack, or exception detail.

Persistence/API integration tests:

- call production-composed `POST`, retrieve through existing GET detail/list
  using the returned ID, and assert normalized values, empty recommendation,
  and `PENDING` from a fresh database read;
- assert exactly one consultation was added;
- assert messages, summaries, recommendations, and appointments have no new
  row;
- configure a strict failing AI boundary or use a provider double and prove no
  provider/AI call occurs; and
- verify a creation failure yields no success representation or fabricated ID.

### Acceptance evidence

- Focused repository/API/persistence tests pass against PostgreSQL.
- A successful API response ID retrieves the same committed row through
  Feature 001.
- The migration head and `create_app` session architecture remain unchanged.

### Scope guards

- No new route hierarchy, repository, unit-of-work framework, or session.
- No GET changes, status transition, child insert, dashboard write, or AI call.
- No migration or mapping change.
- Do not change the Feature 003 restart endpoint or its response semantics.

## 7. Stage 4 — Extend the Frontend Creation Service and Runtime Types

### Purpose

Provide one feature-local, runtime-safe frontend operation for consultation
creation before building the screen.

### Likely files and areas affected

- `frontend/src/app/features/consultation-records/consultationTypes.ts`
- `frontend/src/app/features/consultation-records/consultationApi.ts`
- `frontend/src/app/features/consultation-records/consultationApi.test.ts`

### Architecture boundary

The existing consultation API module owns HTTP, safe error translation, and
runtime response validation. React components consume typed outcomes and do
not call `fetch`, parse JSON, or reproduce server lifecycle rules.

### Dependencies

- Stage 1 confirmed frontend conventions.
- Approved API contract; this stage can proceed in parallel with Stages 2–3
  using an injected transport.

### Implementation details

Add a request type containing exactly:

```text
patient_name: string
primary_concern: string
```

Add stable creation error kinds to the existing `ConsultationApiError`
taxonomy, keeping at least:

- a confirmed creation-validation outcome for exact HTTP `400`; and
- a generic creation-submission/confirmation outcome for transport errors,
  unexpected statuses, safe `500`, malformed errors, and malformed apparent
  success.

Add `createConsultation(request)` to the existing service. One invocation will:

1. normalize both values with `trim()` at the call boundary;
2. issue exactly one request to `/api/v1/consultations`;
3. use `POST`, `Content-Type: application/json`, and a body with exactly the
   two snake-case fields;
4. perform no automatic retry;
5. map only a valid exact safe `400` envelope to the confirmed validation kind
   and collapse all other failures safely;
6. require status `201` and readable JSON;
7. validate an exact five-key object using/refining the existing consultation
   record validator;
8. require a valid UUID, submitted normalized values exactly matching the
   response, `recommended_procedure === ""`, and `status === "PENDING"`; and
9. return the validated `ConsultationRecord`.

The existing list/detail/restart validators must remain compatible with
non-empty recommendations and all approved statuses. If exact-key validation
is stricter only for creation, implement a small creation-specific wrapper
around the reusable record parser rather than changing old read behavior
accidentally.

Never expose raw response text, server error content, transport exceptions, or
credentials through the error object. Do not validate by issuing a follow-up
GET; navigation/detail loading provides later authoritative retrieval.

### Tests

- Exact URL, method, JSON content header, exact normalized body, one transport
  call, and no retry.
- Valid exact `201` response returns the record.
- Exact safe `400` maps to the creation-validation error kind.
- `200`, `202`, `204`, `400` with malformed envelope, `404`, `409`, `500`,
  transport rejection, and unreadable JSON map to safe creation-submission.
- Malformed success coverage includes missing/extra keys, invalid UUID, wrong
  field types, wrong/mismatched normalized values, non-empty recommendation,
  and non-`PENDING` status.
- Raw backend/transport details are absent from surfaced error messages.
- Existing list/detail/messages/summary/restart/booking service tests remain
  unchanged and pass.

### Acceptance evidence

- Focused frontend API tests prove one request per invocation and every
  response invariant.
- No screen, router, AppLayout, storage, dashboard, or AI code changes in this
  stage.

### Scope guards

- Do not create another HTTP client or new consultation feature hierarchy.
- Do not store a created record in localStorage, global cache, or dashboard
  state.
- Do not auto-retry or perform an AI call/follow-up creation.
- Do not weaken the runtime validation used by completed features.

## 8. Stage 5 — Add the New Consultation Route and Screen

### Purpose

Implement the accessible, deterministic creation form inside the existing
application shell and navigate only from a validated authoritative response.

### Likely files and areas affected

- new
  `frontend/src/app/features/consultation-records/NewConsultationScreen.tsx`
- new focused
  `frontend/src/app/features/consultation-records/NewConsultationScreen.test.tsx`
- `frontend/src/app/core/App.tsx`
- `frontend/src/app/core/App.test.tsx`

### Architecture boundary

- Screen owns temporary form, validation display, pending state, recoverable
  feedback, and navigation.
- Dedicated consultation service owns transport and runtime response safety.
- Router owns static route selection; AppLayout continues to own the shell.

### Dependencies

- Stage 4 creation service/type contract.
- Existing router and AppLayout.
- Backend Stage 3 is required only for live integration, not screen tests using
  an injected service double.

### Implementation details

#### Route

Register `consultations/new` within the existing `AppLayout` route tree and
make its static ownership explicit relative to
`consultations/:consultationId`. Preserve all existing route strings and the
root Dashboard redirect. Direct navigation/refresh must render the creation
screen rather than passing `"new"` to the UUID detail workflow.

#### Screen structure and visuals

Create a focused feature component using existing MUI components and styling
patterns:

- `New Consultation` `h1`;
- required `Patient name` text field;
- required `Primary concern` field, preferably multiline within the approved
  MUI convention;
- `Start Consultation` primary action;
- `Cancel` secondary action;
- a restrained bordered `Paper`/panel, comfortable spacing, existing
  typography/background, and responsive sizing inherited from `AppLayout`;
- inline helper/error text associated with each field; and
- an accessible form-level status/error region.

Do not add a second shell, header/sidebar design, patient picker/entity,
screenshot-only controls, or another design system.

#### State and validation

Maintain explicit state equivalent to initial, validation error, submitting,
API failure, and success/navigation. On semantic form submission:

1. return immediately if a synchronous ref/pending guard shows a request is
   already in flight; the guard must close the same-event gap before React
   rerender, not rely only on a disabled button;
2. trim both values;
3. validate 1–200 and 1–4,000 JavaScript string/code-point lengths consistently
   with the approved contract;
4. set clear per-field errors, identify/focus the first invalid field, and make
   zero service calls when invalid;
5. clear stale form-level errors and enter submitting state;
6. disable both inputs, primary action, and Cancel; show accessible progress;
7. call the service once with normalized values;
8. on confirmed validation failure, retain values and show correctable safe
   guidance;
9. on generic/ambiguous failure, retain values and warn that creation could
   not be confirmed, directing the user to Consultation Records before a
   deliberate retry; and
10. on a valid result, call
    `navigate(`/consultations/${record.id}`, { replace: true })` exactly once.

Always clear the in-flight guard in a failure path. On success, allow route
replacement/unmount to end the form state; do not issue another request or
locally fabricate detail data. Cancel navigates to `/consultations` with no
request only while not submitting.

### Tests

Screen tests using an injected service:

- initial empty controls, labels, required semantics, heading, actions, and no
  premature errors/request;
- trim behavior and exact request values;
- empty, whitespace-only, 201st patient-name character, and 4,001st concern
  character errors with zero service calls; boundary values succeed;
- semantic Enter submission and keyboard operation;
- a deferred service promise shows accessible progress and disables inputs,
  Start, and Cancel;
- repeated click/Enter within one event cycle and while pending still causes
  exactly one service call;
- confirmed validation failure and generic/ambiguous failure retain normalized
  values, clear pending state, display safe distinct guidance, and allow one
  explicit retry;
- success uses the returned UUID, replacement navigation, and leaves no stale
  form; and
- malformed success is already rejected by the service and never navigates.

Router tests:

- `/consultations/new` renders New Consultation in `AppLayout` and not
  Consultation Details;
- a UUID `/consultations/:consultationId` still renders detail;
- records, summary, appointment-booking, Dashboard, and root redirect paths
  remain directly reachable; and
- replacement behavior is location/history-aware and does not resubmit on
  browser Back.

### Acceptance evidence

- Focused screen/router tests pass.
- Visual review at desktop and mobile widths shows the screen belongs to the
  Feature 005 shell and introduces no extra navigation or design system.
- A successful screen test navigates only with the service-returned UUID.

### Scope guards

- No direct `fetch`, local authoritative record, optimistic Dashboard update,
  or localStorage.
- No automatic retry, initial AI message, summary, recommendation, appointment,
  or status transition.
- No sidebar redesign, patient workflow, authentication, analytics, or Feature
  007 route/link.

## 9. Stage 6 — Activate Shared Desktop/Mobile New Consult Navigation

### Purpose

Turn the existing prominent disabled shell control into the single shared
entry point without changing navigation structure or responsive behavior.

### Likely files and areas affected

- `frontend/src/app/layout/AppLayout.tsx`
- `frontend/src/app/layout/AppLayout.test.tsx`
- `frontend/src/app/core/App.test.tsx` for route integration only where useful

### Architecture boundary

`AppLayout` owns shared navigation presentation and route links. It does not
own form state, HTTP, creation, lifecycle decisions, or route content.

### Dependencies

- Stage 5 static creation route.
- Existing shared `SidebarContent`, mobile close callback, and active-state
  logic.

### Implementation details

- Convert the existing `+ New Consult` MUI Button into a keyboard-accessible
  React Router link/action to `/consultations/new`.
- Remove the disabled presentation and retain the established prominent black
  contained-button visual direction unless accessibility testing requires a
  small theme-consistent adjustment.
- Invoke the same optional `onNavigate` callback used by navigation links so
  mobile activation closes the temporary Drawer; desktop needs no callback.
- Keep one shared SidebarContent definition so desktop and mobile destinations,
  label, and behavior cannot drift.
- Preserve Dashboard and Consultations labels, destinations, order, active
  styles, landmarks, and sidebar branding.
- Retain the existing Consultations active rule based on exact
  `/consultations` or `/consultations/` prefix; this naturally includes
  `/consultations/new` without adding special component state.

### Tests

- Desktop renders `+ New Consult` as an enabled link/action with exact target
  and keyboard navigation.
- On mobile, opening the drawer and activating New Consult reaches the static
  route and closes the drawer.
- Consultations has `aria-current="page"` on `/consultations/new`; Dashboard
  does not.
- Existing active states for records/detail/summary/booking remain unchanged.
- Navigation landmark, focusability, visible label, permanent drawer, and
  temporary drawer tests continue to pass.
- No New Consult activation invokes the creation service before the form is
  deliberately submitted.

### Acceptance evidence

- Desktop/mobile layout tests show one shared destination and correct drawer
  close behavior.
- Route integration renders the creation screen inside the unchanged shell.

### Scope guards

- Do not add Appointments navigation or any Feature 007 destination.
- Do not add a second unrelated global New Consultation action.
- Do not redesign the sidebar, brand, breakpoints, navigation order, or active
  rule.
- The navigation click performs no POST request.

## 10. Stage 7 — PostgreSQL, Dashboard, No-AI, and Lifecycle Integration

### Purpose

Prove that creation participates in the existing stateful lifecycle through
one authoritative persisted ID and has no unintended side effects.

### Likely files and areas affected

- `backend/tests/api/test_consultation_persistence_api.py`
- `backend/tests/api/test_dashboard_persistence_api.py` or a focused Feature
  006 vertical-slice integration module
- existing backend test fixtures only where additive setup is required
- no production Dashboard, AI, migration, mapping, or Compose file is expected
  to change

### Architecture boundary

Cross-boundary verification only: API → application → repository → PostgreSQL,
then existing read, dashboard, and deterministic conversation boundaries.

### Dependencies

- Backend Stages 2–3.
- Existing Features 001–005 persistence and deterministic AI test seams.

### Implementation details

Build deterministic integration scenarios around a fresh database state:

1. capture Dashboard metrics;
2. create a consultation through `POST /api/v1/consultations`;
3. retrieve the same row through Feature 001 list/detail and a fresh session;
4. retrieve empty Feature 002 message history;
5. verify no summary, recommendation, or appointment row exists;
6. query Dashboard again and require only `total_consultations` to increase by
   one while `booked_appointments` remains unchanged and conversion follows
   the existing Feature 005 formula;
7. submit a first message using the existing deterministic AI double only
   after creation and confirm every message uses the returned consultation ID;
8. optionally continue through existing deterministic summary/booking helpers
   only as regression evidence, never as creation side effects; and
9. query persisted state to prove one identity remains authoritative.

Use a strict AI double or call-count assertions to establish zero AI calls
between the creation request and deliberate message submission. The first
message may invoke the existing Feature 002 AI boundary exactly as already
specified; that proves handoff rather than creation-time coupling.

### Tests

- Before/after dashboard counts from PostgreSQL.
- Exact one-row consultation delta and zero child-row deltas immediately after
  creation.
- Same returned UUID across POST response, detail/list, database reload, empty
  messages endpoint, and later deliberate message persistence.
- Empty recommendation, `PENDING`, normalized text, and no hidden local state.
- Failed creation leaves all counts and child tables unchanged.
- Existing summary/restart/booking invariants remain unchanged when exercised
  later in their normal lifecycle.

### Acceptance evidence

- PostgreSQL integration tests pass with the current migration head and no new
  revision.
- Dashboard count change is observed through existing repository/API code with
  no production Dashboard edit.
- AI call count is zero for creation and changes only on deliberate Feature
  002 message submission.

### Scope guards

- Do not add a dashboard invalidation/mutation endpoint or frontend metric
  update.
- Do not make AI available/required to create a row.
- Do not create related rows during the POST.
- Do not change summary, booking, or appointment-list behavior.

## 11. Stage 8 — Final Vertical-Slice and Runtime Verification

### Purpose

Validate the complete Feature 006 experience, regress completed features, and
confirm Docker/local-development compatibility before declaring implementation
complete.

### Likely files and areas affected

- Test/evidence updates only where gaps are found in Stages 2–7.
- No new product scope, migration, runtime service, or task is introduced.

### Architecture boundary

End-to-end verification across the existing browser, Flask, application,
repository, PostgreSQL, and optional deterministic AI handoff boundaries.

### Dependencies

- Completed Stages 2–7.
- Existing Docker Compose development stack and project commands confirmed in
  Stage 1.

### Implementation details and verification order

1. Run documentation/diff checks and confirm only approved Feature 006 files
   and necessary shared-file lines changed.
2. Run focused backend DTO, application, repository, route, persistence,
   dashboard-integration, and no-AI tests.
3. Run the complete backend Pytest suite to protect Features 001–005.
4. Run focused frontend service, New Consultation screen, AppLayout, and router
   tests.
5. Run the complete frontend test suite, TypeScript check, lint, and production
   build using the repository's exact scripts.
6. Confirm Alembic remains at the existing Feature 004 head and that a clean
   upgrade supports creation; no downgrade/new-revision work is expected.
7. Build/start the existing Compose stack without changing service topology,
   apply current migrations, and verify backend/frontend/database health.
8. Manually exercise desktop and mobile widths:
   `+ New Consult → /consultations/new → validation → submit →
   /consultations/{id} → first message`, then verify Records and Dashboard.
9. Exercise a recoverable API failure where feasible and confirm input
   retention, no automatic retry, and authoritative-record guidance.
10. Inspect PostgreSQL after the runtime flow for exact initial row state and
    later message linkage; confirm no creation-time summary, recommendation,
    or appointment.
11. Review the final diff for forbidden Feature 007, migration, patient,
    auth, AI-intake, appointment-navigation, analytics, dashboard-redesign,
    localStorage, new-session, or unrelated-refactor scope.

### Tests

- All focused and full backend/frontend suites.
- Type/lint/build checks.
- PostgreSQL integration and current migration-head verification.
- Docker Compose build/start/reachability and manual smoke flow.
- Git/documentation whitespace and scope review.

### Acceptance evidence

- Command outputs for all automated checks.
- Browser route/state evidence for desktop/mobile navigation and creation.
- API response plus PostgreSQL query/retrieval evidence for the authoritative
  UUID and initial state.
- Dashboard before/after evidence and zero creation-time AI-call evidence.
- Final `git status --short`, `git diff --stat`, and `git diff --check` with
  unrelated user changes preserved.

### Scope guards

- Verification defects are fixed only within the approved feature boundaries.
- Do not broaden the feature because a screenshot or runtime environment shows
  an unrelated opportunity.
- Do not create Feature 007 routes, links, tasks, or plan content.
- Do not add a migration merely for test convenience.

## 12. Deterministic Testing Strategy

No automated Feature 006 test will require a live OpenAI request, external
network, real credential, browser storage, or nondeterministic retry.

### 12.1 Backend DTO and application

- Parameterize exact type, trimming, blank, Unicode length, unknown-field, and
  server-controlled-field cases at the Pydantic boundary.
- Capture the application service's repository argument and assert every
  initial field, one call, and no adjacent dependency call.
- Keep API-invalid input tests separate from defensive application-input tests
  so ownership remains clear.

### 12.2 Repository and PostgreSQL

- Prefer real PostgreSQL for commit/refresh/reload and visibility guarantees.
- Use controlled session/mock seams only to force rollback paths that cannot be
  induced reliably through valid PostgreSQL data.
- Inspect data from a fresh session after success and failure, cleaning child
  tables in existing FK-safe order.
- Reuse the current migration chain; do not manufacture a Feature 006 revision.

### 12.3 API and composition

- Test the route with an injected strict service for parsing/delegation/error
  mapping, then test the production composition for real persistence.
- Assert exact response keys/statuses and zero service calls for boundary
  rejection.
- Keep raw internal detail in test exceptions and assert it never appears in
  the response.

### 12.4 Frontend service

- Inject transport functions for exact request inspection and every malformed
  response/error case.
- Assert one transport call per invocation and no hidden follow-up GET/retry.
- Preserve existing read/restart/booking validator coverage while applying
  creation-only exact invariants.

### 12.5 Screen, router, and AppLayout

- Inject a focused creation service interface and deferred promises for state
  control.
- Use `user-event` click and keyboard interactions, accessible roles/labels,
  location probes, and history entries to verify replace navigation.
- Use existing deterministic `matchMedia` setup for permanent/temporary drawer
  behavior.
- Avoid brittle CSS snapshots; assert semantic structure, state, route, and
  visible safe copy, with a limited manual responsive visual review.

### 12.6 Regression and vertical slice

- Run existing Feature 001 record/detail retrieval after creation.
- Prove Feature 002 receives the same ID only after a deliberate first message.
- Prove Features 003–004 do nothing at creation and retain eligibility/state
  rules later.
- Prove Feature 005 observes the row through its unchanged PostgreSQL query.
- Run full suites and Compose smoke verification.

## 13. Docker and Runtime Considerations

- No `compose.yaml`, Dockerfile, service, network, port, volume, environment
  variable, secret, package, or Python dependency change is planned.
- The existing PostgreSQL service and current Alembic head already support the
  row shape. Runtime startup/migration commands remain unchanged.
- The existing backend request-scoped session performs creation and is closed
  by current teardown behavior.
- The frontend continues using the existing browser-safe API base URL and CORS
  configuration.
- Consultation creation is synchronous database work and is independent of
  `AI_PROVIDER`, `OPENAI_API_KEY`, LangChain, and external connectivity. A
  runtime configured for either real or mock AI can create a consultation;
  provider availability matters only when the user later submits a message.
- If Compose verification reveals an unrelated pre-existing defect, document
  it and seek approval rather than changing infrastructure within Feature 006.

## 14. Implementation Sequence

The planned units are deliberately small enough to become individual task
definitions only after this plan is approved:

1. **Confirm Feature 006 integration boundaries:** freeze model, repository,
   service, DTO/error, session, frontend service/router/layout, tests, Compose,
   migration-head, and dirty-worktree seams without product changes.
2. **Add strict creation DTO and application workflow:** implement normalized
   two-field input, server-controlled UUID/empty recommendation/`PENDING`, one
   existing-repository delegation, and focused DTO/application/no-AI tests.
3. **Verify repository unit of work and expose creation API:** preserve/add
   commit-refresh-rollback coverage, add exact POST/`201` route, confirm no
   composition change, and add API/PostgreSQL persistence tests.
4. **Extend frontend consultation creation service:** add request/error types,
   exact one-shot POST, creation-specific runtime validation, safe errors, and
   transport tests.
5. **Add New Consultation screen and static route:** implement MUI form,
   validation, submitting guard, recovery, replace navigation, and screen/
   router tests.
6. **Activate shared New Consult navigation:** convert the existing shell
   action to the desktop/mobile route link, preserve active state/drawer close,
   and extend AppLayout tests.
7. **Verify PostgreSQL lifecycle, Dashboard, and no-AI integration:** prove
   authoritative ID continuity, exact row/child deltas, natural metric change,
   and AI invocation only after deliberate message submission.
8. **Verify the final vertical slice:** run focused/full/static/build,
   migration-head, Compose/runtime, responsive UX, regression, scope, and diff
   checks and collect acceptance evidence.

These are planned stages, not implementation task files. Detailed tasks must
not be created until this plan is reviewed and approved.

## 15. Dependencies and Safe Parallel Work

The backend critical path is:

```text
Stage 1
   ↓
Stage 2 DTO + application
   ↓
Stage 3 repository verification + API + PostgreSQL
   ↓
Stage 7 integration
   ↓
Stage 8 final verification
```

The frontend critical path is:

```text
Stage 1
   ↓
Stage 4 frontend service
   ↓
Stage 5 screen + route
   ↓
Stage 6 shared navigation
   ↓
Stage 7 integration
   ↓
Stage 8 final verification
```

| Stage | Depends on | Enables | Safe parallelization |
| --- | --- | --- | --- |
| 1. Boundary confirmation | Approved spec and completed Features 001–005 | All work | None; complete first to avoid shared-file conflicts. |
| 2. DTO/application | Stage 1 | Stage 3 | Can run in parallel with Stage 4 because files and test seams are separate. |
| 3. Repository/API | Stage 2 | Backend live integration and Stage 7 | Repository tests and route tests can be developed together after the service contract stabilizes; coordinate shared backend fixtures. |
| 4. Frontend service | Stage 1 and approved API contract | Stage 5 | Can run in parallel with Stages 2–3 using injected transport; live confirmation waits for Stage 3. |
| 5. Screen/route | Stage 4 | Stage 6 and frontend integration | Screen component/tests and router tests can proceed together with careful coordination on `App.tsx`. |
| 6. AppLayout action | Stage 5 route contract | Stage 7 | Layout implementation/tests can overlap late Stage 5 work only if one owner coordinates shared router integration tests. |
| 7. Lifecycle integration | Stages 3, 5, and 6 | Stage 8 | Backend dashboard/no-AI integration and frontend routed integration can run in parallel, then converge. |
| 8. Final verification | All prior stages | Completion evidence | Focused backend and frontend suites can run in parallel; Compose/manual flow follows successful builds and integration tests. |

Avoid parallel edits to `consultationApi.ts`, `App.tsx`, `AppLayout.tsx`,
`consultation_routes.py`, or shared fixture files without explicit ownership.
Parallel work is safe by boundary, not merely because tests are separate.

## 16. Risks, Controls, and Planning Assumptions

- **Pydantic coercion:** use `StrictStr` plus before-normalization so numbers,
  booleans, and containers cannot silently become text. Parameterized DTO/API
  tests lock this contract.
- **Unicode length mismatch:** Python and JavaScript string representations can
  differ for supplementary characters. Implement an explicit frontend
  code-point count such as `Array.from(value).length` so it matches Python's
  approved character semantics, and test boundary Unicode values.
- **Malformed JSON versus absent/non-JSON body:** Flask's silent JSON parsing
  can collapse several cases to `None`. That is acceptable only if all map to
  the same safe `400` and the service is not called; explicitly check content
  type/query/body requirements first.
- **Post-commit refresh failure:** the existing repository catches refresh
  failure and rolls back, but a database commit may already be durable. The API
  must return safe `500`, never fabricate success; the frontend's ambiguous
  failure guidance directs the user to records before retrying. Do not claim a
  rollback can undo an already completed commit.
- **Duplicate browser events:** React state alone may not close the same-tick
  double-submit window. Use a synchronous in-flight guard plus disabled UI and
  deferred-promise tests.
- **Creation is non-idempotent:** no idempotency key is approved. Never
  auto-retry; distinguish confirmed input rejection from ambiguous transport/
  malformed-success failure and retain values for deliberate recovery.
- **Creation-specific exact response validation:** existing read responses can
  contain any approved status/recommendation. Keep the stricter empty/
  `PENDING`/submitted-value/exact-key checks local to the create operation so
  Features 001–004 are not broken.
- **Static `new` route collision:** React Router ranks static routes, but retain
  an explicit static route and regression test rather than relying on an
  undocumented assumption in the feature code.
- **Shared shell control:** `SidebarContent` renders in desktop or mobile modes.
  Reuse its current callback/link mechanism so the action does not drift or
  leave the mobile drawer open.
- **Dashboard visibility:** PostgreSQL commit visibility controls when the next
  dashboard request sees the row. Do not add cache invalidation, local metric
  updates, or a dashboard write endpoint.
- **AI dependency leakage:** the composed consultation service contains an AI
  service for later workflows, but creation must never call it. Strict mock
  call assertions are required even though the dependency is present.
- **No migration:** text columns, UUID default, enum, and empty recommendation
  already support the approved shape. Do not add constraints/timestamps merely
  to mirror API validation in the database.
- **Shared-file working tree:** current Feature 005 changes are user-owned.
  Inspect diffs before every shared edit and preserve unrelated lines.

No product or architectural conflict blocks later task generation. One
transaction nuance is explicitly controlled: a post-commit refresh failure can
be ambiguous because rollback cannot reverse a durable commit. This does not
change the approved safe `500` or frontend recovery contract.

## 17. Acceptance-Criteria Validation Matrix

| Feature 006 acceptance criterion | Plan coverage |
| --- | --- |
| New Consult reaches focused screen on desktop/mobile | §§8–9, 12.5, 14–15 |
| Static `/consultations/new` does not resolve as ID `new` | §§8, 12.5, 16 |
| Only patient name and concern are submitted | §§5, 7–8, 12.1, 12.4 |
| Frontend/backend enforce normalization and bounds | §§5, 8, 12.1, 12.5 |
| Backend persists generated UUID, empty recommendation, `PENDING` | §§5–6, 10, 12.2–12.3 |
| Exact POST returns database-confirmed `201` record | §6 |
| Invalid and unexpected requests fail safely | §§5–8, 12, 16 |
| Duplicate/automatic submissions are prevented | §§7–8, 12.4–12.5, 16 |
| Ambiguous failure retains values and guides recovery | §§7–8, 16 |
| Success replace-navigates using returned ID | §8 |
| Existing Feature 002 begins only on first message | §§6, 10, 12.6 |
| No summary/recommendation/appointment side effect | §§5–6, 10, 12.6 |
| Records and Dashboard observe PostgreSQL state | §§6, 10, 12.6 |
| Features 001–005 and deep routes remain compatible | §§8–12, 14 |
| Existing shell/MUI visual direction is preserved | §§8–9, 11 |
| No migration, Feature 007, or architecture redesign | §§2, 6, 11, 13, 16 |

Every approved specification section maps to a detailed stage, test strategy,
or explicit scope guard above. Later task definitions must trace their
acceptance evidence back to this matrix without expanding scope.

## 18. Definition of Done

Feature 006 implementation will be ready only when:

- the existing consultation blueprint accepts only the approved strict
  two-field JSON creation request at `POST /api/v1/consultations` and returns
  the exact persisted five-field response with `201`;
- the existing application service constructs the generated UUID, normalized
  inputs, empty recommendation, and `PENDING` status and delegates once to the
  existing repository;
- the existing repository/session proves authoritative commit, refresh,
  retrieval, rollback/error safety, and Feature 003 restart compatibility;
- no migration, model/table, repository hierarchy, engine, session, or
  production composition redesign is introduced;
- the existing consultation frontend service performs one runtime-validated
  POST with safe validation/ambiguous-failure outcomes and no automatic retry;
- `/consultations/new` renders an accessible MUI form inside the existing
  AppLayout with deterministic validation, submitting, duplicate-guard,
  recovery, Cancel, and replacement-navigation behavior;
- the existing `+ New Consult` control is functional through the shared
  desktop/mobile sidebar content, closes the mobile drawer, and preserves
  Consultations active state and all existing navigation;
- PostgreSQL remains the sole authority, the Dashboard observes the committed
  row naturally, and the same ID continues through records, detail, and the
  later conversation lifecycle;
- creation makes no AI call and creates no message, summary, recommendation,
  or appointment;
- focused, full regression, PostgreSQL, no-AI, dashboard, type, lint, build,
  documentation, diff, and Docker Compose verification passes; and
- no patient entity, AI intake, authentication, analytics, dashboard redesign,
  appointment list/navigation, Feature 007 work, screenshot-only feature, or
  unrelated refactor is included.

Implementation task files shall be created only after this plan is reviewed
and approved.
