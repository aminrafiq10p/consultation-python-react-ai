# Appointment Booking Implementation Plan

## 1. Objective

Implement the approved Appointment Booking vertical slice on top of completed
Features 001–003:

```text
Consultation Summary recommendation selection
        ↓ stable consultation + recommendation identifiers
Appointment Booking screen
        ↓ consultation feature API/service
POST /api/v1/consultations/{consultation_id}/appointments
        ↓ Flask consultation blueprint + Pydantic DTOs
ConsultationApplicationService booking workflow
        ↓ focused appointment repository / shared SQLAlchemy session
PostgreSQL appointment insert + COMPLETED → BOOKED in one transaction
        ↓ confirmed 201
Consultation Records reloads authoritative BOOKED state
```

The implementation will create exactly one appointment for an eligible
completed consultation, link it to the selected persisted recommendation, and
commit the appointment and `BOOKED` transition atomically. It will not copy
treatment text, invoke AI, add appointment retrieval or lifecycle operations,
or introduce scheduling, dashboard, authentication, or infrastructure scope.

## 2. Current-System Alignment

Feature 004 will extend these implemented conventions:

- `create_app` is the composition boundary. Each production request receives
  one SQLAlchemy session shared by the consultation, message, and summary
  repositories; API tests can inject a `ConsultationApplicationService`
  double.
- Persistence mappings share the infrastructure-owned `Base` in
  `backend/app/infrastructure/consultation_models.py`. Native PostgreSQL UUIDs
  and Python `UUID` values are serialized as strings only at API/frontend
  boundaries.
- The linear Alembic chain currently ends at
  `20260817_03_create_consultation_summaries.py`, which owns the persisted
  summary and stable recommendation tables required by booking.
- Focused repositories own SQLAlchemy queries, commit/rollback, constraint
  classification, and persisted reload. The application service owns business
  eligibility and does not import Flask or provider SDKs.
- The existing consultation blueprint under `/api/v1` validates with Pydantic,
  delegates to the application service, and emits safe `{ "error": "..." }`
  responses with stable codes for business outcomes.
- Feature 003 already exposes summary GET, recommendation UUIDs, and the exact
  `/consultations/:consultationId/appointments/new?recommendation_id=...`
  handoff. `AppointmentUnavailableScreen` currently owns that placeholder.
- The frontend stays in
  `frontend/src/app/features/consultation-records/`; `consultationApi` is its
  only HTTP boundary and runtime-validates server representations.
- Pytest persistence coverage uses temporary PostgreSQL 16 containers,
  Alembic-to-head fixtures, independent sessions, barriers, and deterministic
  doubles. Vitest/React Testing Library use service or transport doubles.
- The Compose stack already supplies PostgreSQL 16, Flask, and Vite/React. The
  default mock AI provider remains available but booking must never call it.

No new framework, blueprint, frontend feature root, AI capability, Compose
service, or architectural decision is required.

## 3. Specification Traceability

| Approved requirement | Planned responsibility | Verification focus |
| --- | --- | --- |
| One consultation has zero or one appointment | Unique `appointments.consultation_id` plus application precheck | Mapping, migration, repeat, and race tests |
| Stable appointment and recommendation lineage | Native UUID PK and two required FKs | Fresh-session reload and FK/ownership tests |
| Persisted recommendation is authoritative treatment | Store only `recommendation_id`; response joins persisted recommendation | No treatment column/copy; unchanged recommendation/projection |
| Explicit-offset strictly future instant | Pydantic request validation plus application clock comparison in UTC | Invalid shape/offset/calendar/current/past/future matrix |
| Trimmed nonblank location up to 200 characters | DTO/application normalization and database checks | Unicode length, trimming, blank, and limit tests |
| Exact booking eligibility and conflict precedence | Application workflow over repository-loaded locked state | Missing, status, summary, recommendation, ownership, duplicate matrix |
| Appointment and `BOOKED` transition are atomic | One repository-owned transaction and one commit | Injected flush/update/commit failures and fresh-session assertions |
| Concurrent create has one winner and stable loser | Consultation row lock plus unique constraint reconciliation | Two-session controlled race: one `201`, one already-exists `409` |
| Exact POST API and safe errors | Existing blueprint and explicit DTOs/outcomes | Exact `201`, `400`, `404`, coded `409`, and safe `500` |
| Booking screen revalidates navigation context | Existing summary GET and stable route/query UUIDs | Direct load and missing/mismatched context states |
| No local status simulation or POST retry | Frontend service and screen behavior | Replacement navigation and subsequent records GET |
| Existing consultation data remains immutable | Focused write set and regression assertions | Messages, summary, recommendations, projection unchanged |
| No AI or external service call | Application composition and deterministic tests | Strict AI doubles and network-free vertical slice |

## 4. Appointment Persistence Design

Create one Alembic revision immediately after `20260817_03` and extend the
shared mappings with one `appointments` table. Use explicit foreign keys and no
delete cascade because deletion is outside the approved scope.

| Column | PostgreSQL / SQLAlchemy decision | Constraints and behavior |
| --- | --- | --- |
| `id` | Native UUID / `UUID`, generated with `uuid4` | Primary key and stable API representation |
| `consultation_id` | Native UUID / `UUID` | Required FK to `consultations.id`; named unique constraint elects at most one appointment |
| `recommendation_id` | Native UUID / `UUID` | Required FK to `consultation_recommendations.id` |
| `scheduled_at` | `TIMESTAMP WITH TIME ZONE` / aware `datetime` | Required; application enforces strict future time |
| `location` | `VARCHAR(200)` (or length-bounded equivalent) | Required; named checks enforce `btrim(location) <> ''` and `char_length(location) <= 200` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` / aware `datetime` | Required, server default `CURRENT_TIMESTAMP` |

The mapping will expose the persisted columns needed by repositories and DTO
mapping without introducing a copied treatment field or appointment status.
The unique consultation constraint supplies the lookup index; add only indexes
demonstrably needed by foreign-key/recommendation access. The migration creates
the table after its referenced tables and drops it on downgrade without
changing consultation status enum values or existing rows.

Database checks are defense in depth. Explicit-offset parsing, strict future
comparison, normalization, recommendation ownership, and cross-table lineage
remain application/API responsibilities because ordinary constraints cannot
express all of them.

Expected areas:

- `backend/app/infrastructure/consultation_models.py`
- a new revision under `backend/migrations/versions/`
- focused mapping/migration coverage, primarily
  `backend/tests/test_appointment_persistence.py`
- PostgreSQL fixture cleanup extended to delete appointments before their
  referenced recommendation/consultation rows

## 5. Appointment Repository and Unit of Work

Add `AppointmentRepository` beside the existing focused repositories and
construct it with the same request-scoped session. It will own booking-specific
SQLAlchemy mechanics while leaving business decisions in the application
workflow.

### 5.1 Read and coordination capabilities

The repository will provide narrowly typed capabilities to:

- load a consultation by UUID with `SELECT ... FOR UPDATE`, establishing the
  transaction coordination point for booking;
- look up an appointment by consultation UUID, including a post-rollback fresh
  authoritative reload;
- look up a recommendation globally by UUID so “missing” can be distinguished
  from “exists but belongs elsewhere”;
- load the consultation's persisted summary and its selected recommendation
  lineage without returning an acceptable cross-consultation choice; and
- reload a committed appointment together with its persisted recommendation
  projection for response mapping.

These capabilities may reuse the existing summary mapping/query concepts but
will not make Flask or React query SQLAlchemy. If extending `SummaryRepository`
would split the booking transaction or obscure ownership, the focused
appointment repository will issue the required joined reads directly; this is
repository reuse of persistence mappings, not business-rule duplication.

### 5.2 Atomic create operation

After the application approves the locked state and normalized inputs, the
repository will:

1. add one appointment linked to the loaded consultation and recommendation;
2. flush so FK, check, and unique failures occur before success;
3. set only `consultation.status` to `BOOKED`;
4. commit exactly once;
5. reload the appointment and persisted recommendation; and
6. return a provider-neutral persisted appointment aggregate/value.

The consultation lock and all eligibility reads/writes remain in the same
session transaction. No intermediate repository operation commits. Any query,
insert, flush, status update, commit, or reload failure rolls back the unit of
work; success is never reported before the commit.

Any typed eligibility exit after the lock also explicitly rolls back through a
focused repository abort capability before the outcome leaves the application
boundary. This releases the row lock immediately and keeps the shared session
usable; it does not hide or translate the application outcome.

### 5.3 Duplicate and concurrency reconciliation

The primary coordination strategy is a PostgreSQL row lock on the consultation:

```text
request A: lock COMPLETED consultation → validate → insert + BOOKED → commit
request B: waits for same consultation lock
request B: resumes → sees appointment/BOOKED → APPOINTMENT_ALREADY_EXISTS
```

The named unique constraint on `appointments.consultation_id` remains the
final authority for duplicate prevention, including writes outside the normal
workflow or an unforeseen race. If that exact constraint raises during flush
or commit, the repository rolls back, expires/reloads authoritative state, and
returns a typed duplicate result only when the winning appointment is visible.
Other integrity or persistence errors remain failures and become safe `500`.
No raw constraint detail crosses the repository boundary.

Locking is short-lived and encloses database work only—there is no AI or
network call. No serializable-global transaction, advisory/distributed lock,
idempotency key, automatic retry, or appointment replacement is added.

Expected areas:

- new `backend/app/repositories/appointment_repository.py`
- `backend/app/repositories/__init__.py` only if current export conventions
  require it
- `backend/app/__init__.py` composition using the existing shared session
- focused repository, rollback, constraint-classification, and two-session
  concurrency tests

## 6. Application Booking Workflow

Extend `ConsultationApplicationService` with a focused booking method and an
optional injected `AppointmentRepository`, preserving existing test
construction and Features 001–003 methods. Inject a clock callable returning
an aware current instant (defaulting to UTC server time) so application tests
never depend on wall-clock races.

### 6.1 Boundary normalization

The Pydantic request model first rejects absent/malformed bodies, unknown
fields, invalid UUIDs, non-string/offset-less/invalid datetimes, and invalid
location shape. The application defensively:

- requires an aware `scheduled_at`, converts it to UTC for comparison, and
  requires it to be strictly later than one captured authoritative `now`;
- trims surrounding location whitespace, rejects blank text, and measures the
  normalized Python Unicode string at no more than 200 characters; and
- accepts only validated UUID identities, never treatment text.

Invalid input is resolved before database conflict precedence, as required by
the API contract.

### 6.2 Eligibility and outcome precedence

Within the repository-coordinated transaction, the workflow performs this
ordered decision sequence:

1. lock/load the consultation; absence raises `ConsultationNotFoundError`;
2. check existing appointment first; presence raises
   `AppointmentAlreadyExistsError`;
3. if status is `BOOKED`, raise the same already-exists outcome even if the
   state is inconsistent and no appointment is visible;
4. require status exactly `COMPLETED`; otherwise raise
   `ConsultationNotBookableError`;
5. require the consultation's persisted summary; absence raises
   `RecommendationNotBookableError`;
6. resolve the submitted recommendation identity globally; absence raises
   `RecommendationNotFoundError`;
7. require that recommendation's `summary_id` is the persisted summary for
   the locked consultation; mismatch raises
   `RecommendationNotBookableError`;
8. ask the repository to create the appointment and perform the sole status
   transition/commit; and
9. translate an exact unique-race reconciliation into
   `AppointmentAlreadyExistsError`, otherwise return the persisted aggregate.

This ordering preserves appointment/`BOOKED` precedence, then general status,
then summary and recommendation ownership. It also retains the explicitly
required missing-recommendation `404`: the lookup occurs after consultation
eligibility/summary checks but distinguishes global absence from cross-owner
existence once reached. No matching treatment text can substitute for the UUID
lineage.

Typed application outcomes will include the existing consultation-not-found
type plus focused invalid-booking, recommendation-not-found,
recommendation-not-bookable, consultation-not-bookable, and
appointment-already-exists types. Routes translate them; repositories do not
construct HTTP responses.

Booking has no `AIService`, LangChain, agent, skill, provider, calendar, or
other network dependency. It modifies neither messages, summary rows,
recommendations, `recommended_procedure`, nor any consultation field except
status after appointment insertion is ready to commit.

Expected areas:

- `backend/app/application/consultation_service.py`
- focused `backend/tests/application/test_appointment_booking_service.py`
- existing application regression tests only where constructor fixtures need
  the optional new dependency

## 7. API Composition, DTOs, and Route

Keep the existing consultation blueprint and service composition. Production
composition creates `AppointmentRepository(session)` beside the existing
repositories; the Flask route delegates exactly once and never accesses a
session or repository.

### 7.1 Request and response DTOs

Extend `consultation_dtos.py` with:

- `AppointmentBookingRequest` using `extra="forbid"`, UUID
  `recommendation_id`, strict string input for `scheduled_at` with an explicit
  `Z` or numeric offset before parsing to an aware datetime, and normalized
  location constraints;
- `AppointmentRecommendationResponse` containing only `id` and `treatment`;
  and
- `AppointmentResponse` containing `id`, `consultation_id`, nested persisted
  recommendation, explicit-offset `scheduled_at`, normalized `location`, and
  `created_at`.

Response serialization will use Pydantic JSON mode and tests will require an
explicit offset. UTC may serialize as `Z` or `+00:00` consistently with the
chosen existing/Pydantic convention; consumers accept either approved explicit
form. No response exposes `recommendation_id` as an additional top-level field,
summary internals, SQLAlchemy state, or a copied treatment value.

### 7.2 Route and safe translation

Add only:

```text
POST /api/v1/consultations/<consultation_id>/appointments
```

The route validates the path and required JSON body before invoking the
service, passes only the three approved request values, and returns the
persisted response after commit.

| Outcome | HTTP response |
| --- | --- |
| Invalid path/body/extra field/UUID/datetime/location | `400 {"error":"Invalid request"}` |
| Missing consultation | `404 {"error":"Consultation not found"}` |
| Missing recommendation | `404 {"error":"Recommendation not found"}` |
| Missing/inconsistent summary or cross-consultation recommendation | `409` safe message + `RECOMMENDATION_NOT_BOOKABLE` |
| Non-`COMPLETED` consultation without appointment/`BOOKED` precedence | `409` safe message + `CONSULTATION_NOT_BOOKABLE` |
| Existing appointment, `BOOKED`, or reconciled race loser | `409` safe message + `APPOINTMENT_ALREADY_EXISTS` |
| Committed appointment | `201` exact appointment DTO |
| Unexpected persistence/server failure | `500 {"error":"Internal server error"}` via existing handler |

Tests assert error bodies contain no Pydantic details, SQL/constraint names,
exception text, stack, environment, credential, or sensitive treatment from a
mismatched consultation.

Expected areas:

- `backend/app/api/consultation_dtos.py`
- `backend/app/api/consultation_routes.py`
- `backend/app/__init__.py`
- DTO tests in `backend/tests/api/test_consultation_dtos.py`
- focused route tests, with persistence integration extending the existing API
  vertical-slice conventions

## 8. Frontend Service and Runtime Types

Extend `consultationTypes.ts` and `consultationApi.ts`; do not create another
HTTP client or place transport/business logic in the screen.

Add types for:

- `AppointmentBookingRequest` with stable recommendation ID, explicit-offset
  datetime string, and normalized location;
- persisted appointment and nested recommendation responses; and
- booking-specific safe error kinds for validation, missing consultation,
  missing recommendation, recommendation-not-bookable,
  consultation-not-bookable, appointment-already-exists, and generic
  submission/ambiguous transport failure.

Add `bookAppointment(consultationId, request)` that:

- sends exactly one JSON `POST` to the approved endpoint;
- performs no automatic retry;
- runtime-validates appointment/consultation/recommendation UUIDs and exact
  linkage to the requested identifiers;
- validates nonblank treatment, explicit-offset valid timestamps, normalized
  nonblank location up to 200 characters, and the expected successful `201`;
- maps only exact status/code combinations to stable error kinds; and
- collapses malformed successes/errors, transport failures, and safe `500`
  responses without exposing server text.

The service accepts the browser-converted explicit-offset instant. The screen
will convert a valid browser-local `datetime-local` value to `Date.toISOString()`
immediately before constructing the request; `Z` satisfies the API contract.
No frontend code updates a consultation record or treats URL ownership as
authorization.

Expected areas:

- `frontend/src/app/features/consultation-records/consultationTypes.ts`
- `frontend/src/app/features/consultation-records/consultationApi.ts`
- `frontend/src/app/features/consultation-records/consultationApi.test.ts`

## 9. Appointment Booking Route and Screen

Replace `AppointmentUnavailableScreen` at the already registered route with a
feature-oriented `AppointmentBookingScreen`; remove the placeholder only after
its route tests are replaced. `App.tsx` keeps the exact Feature 003 path.

### 9.1 Navigation context and summary loading

On mount/direct refresh the screen will:

1. require a syntactically valid `consultationId` path value and exactly one
   syntactically valid `recommendation_id` query value;
2. call the existing `consultationApi.summary(consultationId)`—never generate a
   summary or call HTTP directly;
3. rely on service runtime validation that summary `consultation_id` matches
   the path;
4. find the exact persisted recommendation UUID in the returned summary; and
5. display only that recommendation's treatment as read-only text.

Invalid/missing path or query context prevents submission. The UI distinguishes
loading, missing consultation, unavailable summary, missing/mismatched
recommendation, and recoverable retrieval failure. It offers summary navigation
when a valid consultation route permits it, records navigation as a safe
fallback, and an explicit retry only for recoverable retrieval errors.

### 9.2 Form and client guidance

Use accessible MUI controls for:

- one browser-local date/time value; and
- one location value with a 200-character limit/helper feedback.

On confirmation, validate required values, parse the local datetime, require
its instant to be strictly future relative to the browser clock for immediate
guidance, trim location, and enforce nonblank/200 Unicode-character length.
Convert the chosen instant to explicit-offset ISO format and submit only
`recommendation_id`, `scheduled_at`, and `location`. The server remains
authoritative; client and server clock differences can still yield a safe
backend `400`.

One pending flag disables inputs/confirmation and guards the handler so one
activation sends at most one request. No retry library or effect submits the
POST. Validation, conflict, transport, and server failures preserve the user's
date/time and location values.

### 9.3 Error recovery and success

- Backend validation remains displayed beside the form for correction.
- Recommendation/consultation not-bookable outcomes show distinct safe
  guidance without interpreting treatment or status locally.
- Already-booked disables further creation and directs the user to
  Consultation Records.
- Missing consultation/recommendation states prevent submission and provide
  safe navigation.
- Transport or `500` ambiguity re-enables the form but warns against blind
  resubmission and offers Consultation Records to check authoritative state.
- Only a validated `201` calls `navigate("/consultations", { replace: true })`.
  The records screen then performs its existing API-backed load; no cache or
  local object is changed to `BOOKED`.

Expected areas:

- new `frontend/src/app/features/consultation-records/AppointmentBookingScreen.tsx`
- `frontend/src/app/core/App.tsx`
- removal of `AppointmentUnavailableScreen.tsx` after route replacement
- new focused `AppointmentBookingScreen.test.tsx`
- `frontend/src/app/core/App.test.tsx` routing regression updates
- existing summary-screen tests retained to prove the handoff identifiers are
  unchanged

## 10. Deterministic Testing Strategy

No test will invoke OpenAI, LangChain execution, an external calendar, network
access, or a real credential.

### 10.1 Mapping, migration, and repository

- Upgrade the full Alembic chain to head, inspect appointment columns/types,
  named FKs/checks/uniqueness/defaults, and perform downgrade/upgrade round
  trips against temporary PostgreSQL 16.
- Verify UUID identity, aware timestamp round trips, trimmed/length-constrained
  location defense, nonexistent FK rejection, and one appointment per
  consultation.
- Reload through fresh sessions and prove appointment/recommendation linkage,
  treatment projection, normalized values, and explicit aware timestamps.
- Force failures at add/flush/status assignment/commit/reload boundaries and
  prove no appointment and no `BOOKED` status becomes visible. Where direct
  status-assignment injection is impractical, use a repository seam/event that
  fails between flush and commit without changing production semantics.
- Use two independent sessions, a barrier, and bounded thread synchronization
  to prove one committed appointment, one status transition, one winner, and a
  stable duplicate loser rather than raw `IntegrityError`.
- Assert all source messages, summary fields, recommendation identities/order/
  treatment, and `recommended_procedure` are byte-for-byte/value unchanged.

### 10.2 Application and API

- Inject a fixed aware UTC clock and test future, exact-now, past, equivalent
  offsets, and defensive naive datetime rejection.
- Cover missing consultation; existing appointment; inconsistent `BOOKED`
  without appointment; `PENDING`; other non-`COMPLETED`; completed without
  summary; missing recommendation; cross-consultation recommendation; valid
  ownership; blank/trimmed/Unicode/overlong location; and duplicate outcomes.
- Assert precedence when multiple conflict facts coexist and that invalid
  request validation occurs before service/database conflict handling.
- Verify application normalization, exact repository delegation, persisted
  response treatment from the recommendation, and no treatment copy.
- Exercise exact DTO/route `201`, `400`, both `404`s, all three coded `409`s,
  concurrent loser mapping, and safe generic `500`.
- Use strict/mock AI dependencies that fail the test if any booking path calls
  an AI method.
- Exercise API → application → repositories → PostgreSQL, then call the
  existing records GET and summary GET to prove `BOOKED` is authoritative and
  source aggregate data remains retrievable and unchanged.

### 10.3 Frontend

- Transport-test exact path, method, headers/body, no retry, explicit-offset
  transport, `201` runtime invariants, every exact coded error, both `404`
  interpretations, malformed payloads, `500`, and network rejection.
- Screen-test valid Feature 003 path/query handoff, direct summary load, exact
  treatment selection, invalid/missing/mismatched context, and each retrieval
  state.
- Test required/future/length validation, trimming, local-to-ISO conversion,
  one service call per activation, and disabled duplicate activation.
- Test that form values survive recoverable backend validation, conflict,
  transport, and server failures; verify safe distinct guidance and records/
  summary navigation.
- Verify success uses replacement navigation to `/consultations`, performs no
  local status mutation, and causes the existing routed records UI to retrieve
  authoritative state.

## 11. Regression and Vertical-Slice Verification

Run and review in this order:

1. Full migration upgrade to the Feature 004 head and downgrade/upgrade round
   trip against PostgreSQL 16.
2. Focused appointment mapping, repository, concurrency, application, DTO,
   route, and persisted API tests.
3. Complete backend Pytest suite to protect consultation filtering/detail,
   message ordering/submission, summary generation/retrieval/restart, stable
   recommendations, and all prior transaction behavior.
4. Focused frontend service, booking screen, summary handoff, router, and
   records reload tests.
5. Full `npm test`, `npm run typecheck`, `npm run lint`, and `npm run build`.
6. Build/start the existing Compose stack, apply migrations, verify service
   health/reachability, and manually exercise a deterministic completed summary
   through selection, booking, redirect, records `BOOKED`, and summary reload.
7. Query PostgreSQL after the runtime flow to confirm one linked appointment,
   `BOOKED`, and unchanged messages/summary/recommendations/projection.
8. Review routes, schema, frontend, configuration, and diff for forbidden GET/
   lifecycle/provider/availability/calendar/notification/payment/auth/
   dashboard/AI/RAG/Redis/vector/LangGraph/WebSocket/streaming scope.

Any existing fixture cleanup must add appointment deletion in FK-safe order;
prior behavior or assertions change only where the approved new `BOOKED`
transition is intentionally exercised.

## 12. Docker and Runtime Considerations

- No Compose service, port, volume, environment variable, image, or runtime
  dependency is planned.
- The new linear Alembic revision targets the existing PostgreSQL 16 service
  and uses the backend's current migration process.
- Booking is synchronous, deterministic database work. It does not depend on
  `AI_PROVIDER`, `OPENAI_API_KEY`, the mock provider, or external connectivity.
- The existing request-scoped session remains the transaction owner. The row
  lock lasts only through validation, insert, status update, and commit.
- Dockerfiles and `compose.yaml` should remain unchanged. Any independently
  discovered runtime defect must be documented and approved rather than used
  to redesign infrastructure within Feature 004.

## 13. Implementation Sequence

1. **AB-001 — Confirm Feature 004 Integration Boundaries:** record exact
   migration head, mapping names, shared-session composition, repository
   transaction/error conventions, clock seam, DTO/error mapping, summary
   handoff, frontend service/router, PostgreSQL concurrency fixture, and
   Compose commands; change no product code.
2. **AB-002 — Add Appointment Persistence and Migration:** add the linear
   appointment migration, shared mapping, constraints, fixture cleanup, and
   PostgreSQL mapping/migration tests.
3. **AB-003 — Add Appointment Repository and Atomic Unit of Work:** implement
   locked booking-context reads, global/owned recommendation lookup, existing
   appointment lookup, atomic insert/status commit, reload, rollback, exact
   unique-race reconciliation, and repository/concurrency tests.
4. **AB-004 — Add Appointment Booking Application Workflow:** add the
   controllable clock, normalization, exact eligibility/precedence, typed
   outcomes, atomic repository coordination, no-AI assertions, and focused
   application tests.
5. **AB-005 — Expose Appointment Booking API and DTOs:** wire production
   composition, strict request/response DTOs, the one POST route, exact safe
   error translations, and DTO/route/persisted API tests.
6. **AB-006 — Extend Frontend Consultation Booking Service:** add appointment
   types, runtime validation, one-shot POST transport, exact coded error
   mapping, explicit-offset handling, and service tests.
7. **AB-007 — Add Appointment Booking Screen and Route Ownership:** replace the
   placeholder, validate path/query and persisted summary context, add the
   read-only selection/form/states/recovery/single-submit behavior, replacement
   navigation, and RTL/router tests.
8. **AB-008 — Verify Appointment Booking Vertical Slice:** run migration,
   concurrency, backend/frontend regression, static/build, immutable-source,
   scope, and Compose/runtime verification and record acceptance evidence.

These identifiers retain the approved task direction. Detailed task files will
be created only after this plan is approved.

## 14. Task Dependencies and Parallel Work

The critical backend path is:

```text
AB-001
   ↓
AB-002 persistence
   ↓
AB-003 repository / transaction
   ↓
AB-004 application workflow
   ↓
AB-005 API / integration
   ↓
AB-008 verification
```

The frontend contract path is `AB-001 → AB-006 → AB-007 → AB-008`. AB-006 may
proceed from the approved HTTP contract while AB-002 through AB-005 are under
way. AB-007 may proceed after AB-006 with service doubles; live integration
waits for AB-005. Within AB-002, migration/mapping tests follow the agreed
schema. Within AB-003, repository unit/rollback coverage and the controlled
concurrency fixture can be developed together after mappings exist. AB-008
requires AB-005 and AB-007.

| Task | Depends on | Enables |
| --- | --- | --- |
| AB-001 | Approved Feature 004 spec and completed Features 001–003/Compose | All streams |
| AB-002 | AB-001 | AB-003 and persistence integration |
| AB-003 | AB-002 | AB-004 |
| AB-004 | AB-003 | AB-005 |
| AB-005 | AB-004 | Live frontend integration and AB-008 |
| AB-006 | AB-001 and approved API contract | AB-007 |
| AB-007 | AB-006; coordinate with existing summary/router contracts | AB-008 |
| AB-008 | AB-005 and AB-007 | Feature completion evidence |

## 15. Risks, Controls, and Planning Assumptions

- **Lock placement:** lock the consultation row before inspecting appointment,
  status, summary, and ownership so concurrent requests serialize on the one
  durable cardinality owner. Keep every read/write in the same session unit of
  work and verify generated SQL/behavior in PostgreSQL tests.
- **Unique-race classification:** name and inspect only the consultation unique
  constraint. After rollback, require a visible winning appointment before
  translating it to already-exists; never swallow unrelated integrity errors.
- **`BOOKED` without appointment:** per the approved precedence, return
  `APPOINTMENT_ALREADY_EXISTS` and do not fabricate/repair a row. This follows
  the API table's explicit treatment of `BOOKED` and the stated precedence,
  despite the state being inconsistent.
- **Recommendation disclosure:** a globally missing recommendation produces
  the approved `404`; an existing cross-consultation recommendation produces a
  safe coded `409` without returning its treatment or owner.
- **Datetime strictness:** Pydantic must not silently accept numeric, date-only,
  or naive datetime values. The application compares one captured aware server
  time in UTC; PostgreSQL stores the instant with timezone awareness.
- **Unicode length:** count normalized Unicode code points consistently at the
  Python/TypeScript UX boundaries and use PostgreSQL `char_length` for database
  defense. Grapheme-cluster semantics are not introduced.
- **Ambiguous transport result:** the browser never auto-retries. A safe warning
  directs the user to records because the first request might have committed
  after the response was lost.
- **Post-commit reload:** a reload failure after a successful commit cannot be
  rolled back. Treat it as safe `500`; a subsequent attempt will reconcile as
  already booked, and the UI's ambiguity guidance directs the user to records.
- **Frontend local time:** `datetime-local` has no offset. Conversion through a
  valid JavaScript `Date` to UTC `toISOString()` supplies the required explicit
  designator; named timezone/DST preference is deliberately out of scope.
- **Existing summary handoff:** retain the exact route/query names and stable
  recommendation IDs. The booking screen re-fetches the summary and never
  trusts treatment text or transient navigation state.
- **No architecture decision:** a focused repository, clock injection, and
  row-level lock are extensions of current boundaries. They do not require a
  new ADR, unit-of-work framework, service layer, or infrastructure component.
- **Working tree preservation:** implementation and later verification must
  preserve unrelated user changes and generated artifacts.

No product or architecture conflict blocks task generation. Exact constraint
names, helper names, and file-level test splits remain task-local details so
long as the named-constraint classification and approved behavior are kept.

## 16. Acceptance-Criteria Validation Matrix

| Feature 004 acceptance criterion | Plan coverage |
| --- | --- |
| Summary selection opens stable booking route/query | §§2, 8–9, 10.3 |
| Direct route load displays persisted selected treatment | §§8–9.1, 10.3 |
| Valid future time/location submits one request | §§6.1, 8–9.2, 10 |
| Backend independently checks consultation/summary/ownership | §§5–7, 10.2 |
| One appointment and `COMPLETED → BOOKED` commit atomically | §§4–6, 10.1–10.2 |
| Success returns persisted appointment and records shows `BOOKED` | §§7, 9.3, 10–11 |
| Invalid/ineligible/repeat/race/failure leaves no partial state | §§5–7, 10 |
| Records refresh uses PostgreSQL, not React mutation | §§9.3, 10.3–11 |
| Messages/summary/recommendations/projection stay unchanged | §§4–6, 10–11 |
| Tests are deterministic and make no AI/calendar call | §§6, 10–12 |

The detailed traceability table in §3 covers the remaining persistence, API,
UI, error, concurrency, regression, and scope requirements. Each implementation
task will trace its tests back to these sections after plan approval.

## 17. Definition of Done

Feature 004 is ready only when:

- the linear migration and shared mapping enforce UUID/FK/check/timestamp
  requirements and one appointment per consultation without treatment/status
  duplication;
- the focused repository proves locked coordination, authoritative lookup,
  one atomic appointment/`BOOKED` commit, rollback, reload, and stable
  concurrent loser reconciliation;
- the application workflow enforces strict input, exact eligibility,
  recommendation ownership, conflict precedence, a controllable clock, and no
  AI dependency;
- the existing blueprint exposes only the approved POST with explicit DTOs and
  exact safe `201`/`400`/`404`/coded `409`/`500` behavior;
- the frontend service validates the contract and the booking route replaces
  the placeholder with persisted-treatment context, accessible inputs,
  duplicate-submit protection, safe recovery, and replacement navigation;
- the records screen obtains `BOOKED` from PostgreSQL and all source messages,
  summary, recommendation, and projection data remain unchanged;
- migration, focused, concurrency, full backend/frontend regression, lint,
  type, build, scope, and Docker Compose checks pass deterministically; and
- no appointment GET/lifecycle/multiple booking, rescheduling/cancellation,
  provider/availability/conflict/hours, calendar, notification, payment, auth,
  dashboard, AI booking, RAG, Redis, vector database, LangGraph, WebSocket,
  streaming, or infrastructure redesign is introduced.
