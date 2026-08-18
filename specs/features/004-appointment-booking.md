# Appointment Booking Feature Specification

## 1. Purpose

Define the Appointment Booking feature for the AI Consultation Platform. The
feature lets a user carry one selected persisted recommendation from a completed
Consultation Summary into a booking form, choose an appointment date/time and
location, confirm the booking, and return to Consultation Records.

This feature follows Consultation Summary in the approved flow:

```text
Consultation Summary
       ↓
Appointment Booking
       ↓
Consultation Records showing BOOKED
       ↓
Dashboard metrics (later feature)
```

Appointment creation is deterministic business behavior. It does not use
OpenAI, LangChain, or any AI-produced booking decision.

## 2. Scope

The feature shall provide:

- an Appointment Booking screen reached through Feature 003's existing route
  handoff containing a consultation identifier and recommendation identifier;
- retrieval of the persisted summary so the selected recommendation and its
  treatment text can be displayed and the navigation context can be checked;
- input of one appointment date/time and one location;
- authoritative backend validation of consultation eligibility,
  recommendation existence and ownership, and booking input;
- PostgreSQL persistence of one appointment linked to both the consultation and
  selected persisted recommendation;
- one atomic operation that creates the appointment and transitions the
  consultation from `COMPLETED` to `BOOKED`;
- prevention of duplicate appointments, including concurrent submissions; and
- navigation to Consultation Records after confirmed persistence.

The existing persisted recommendation is the authoritative selected treatment.
The user shall not type or override treatment text.

## 3. Out of Scope

This feature does not implement:

- provider or treatment availability, schedule conflict detection, business
  hours, appointment duration, or capacity management;
- selecting a different recommendation on the booking screen;
- multiple appointments for one consultation;
- appointment retrieval, editing, rescheduling, cancellation, deletion, or
  lifecycle statuses;
- provider/location tables, external calendars, notifications, email, SMS,
  payments, authentication, or authorization;
- dashboard screens, dashboard metrics, or dashboard queries;
- mutation of consultation messages, summaries, or recommendations;
- AI-generated booking decisions, OpenAI calls, LangChain execution, RAG,
  Redis, a vector database, LangGraph, WebSockets, or streaming; or
- infrastructure or architecture redesign.

## 4. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- Selecting one persisted recommendation on Consultation Summary and choosing
  `Book Appointment` opens the booking route with the existing stable
  consultation and recommendation identifiers.
- Directly loading that route retrieves backend data and displays the treatment
  belonging to the selected persisted recommendation.
- The user can enter a valid future date/time and nonblank location and submit
  one booking request.
- The backend independently confirms that the consultation exists, is
  `COMPLETED`, has its persisted summary, and owns the selected recommendation.
- A successful request creates exactly one appointment linked to both records
  and changes the consultation to `BOOKED` in one transaction.
- A successful request returns the persisted appointment and redirects the user
  to Consultation Records, whose existing API-backed UI naturally displays the
  persisted `BOOKED` status.
- Invalid, ineligible, repeated, mismatched, concurrent, and failed requests do
  not leave a partial appointment or an incorrect consultation status.
- Refreshing records after success uses PostgreSQL state; React does not
  simulate the status transition locally.
- Booking leaves the consultation's messages, summary, recommendations, and
  recommended-procedure projection unchanged.
- Automated tests are deterministic and make no AI or external-calendar call.

## 5. User Flow

```text
Completed Consultation Summary
       ↓ select persisted recommendation
Book Appointment navigation
       ↓ consultation_id + recommendation_id
load persisted summary through consultation service
       ↓ validate route context and show treatment
enter future date/time + location
       ↓ client-side UX validation
POST booking request
       ↓ authoritative backend validation
atomically persist appointment + set consultation BOOKED
       ↓ confirmed 201 response
redirect to /consultations
```

The current Feature 003 handoff is:

```text
/consultations/{consultation_id}/appointments/new
    ?recommendation_id={recommendation_id}
```

Feature 004 shall take ownership of that route and replace its unavailable
placeholder. Route and query values provide navigation context only and never
constitute business authorization.

## 6. Booking Eligibility and Status Rules

A booking may succeed only when all of the following are true at the
application boundary:

- the consultation exists;
- the consultation status is exactly `COMPLETED`;
- the consultation has one persisted summary;
- the selected persisted recommendation exists;
- that recommendation belongs to the persisted summary for the same
  consultation;
- no appointment already exists for the consultation; and
- the submitted date/time and location satisfy §9.

Feature 004 owns the only new approved status transition:

```text
COMPLETED → BOOKED
```

A `PENDING` consultation is not bookable. It remains `PENDING`, and no
appointment is created. A `BOOKED` consultation is not bookable again. It
remains `BOOKED`, and the existing appointment is not replaced. No new
consultation or appointment status is introduced.

A `COMPLETED` consultation without a persisted summary is an inconsistent and
non-bookable state. A `BOOKED` consultation without an appointment is also an
inconsistent and non-bookable state; this feature shall fail safely rather than
repairing or fabricating data during a booking request.

## 7. Appointment Persistence Model

Feature 004 introduces this relationship:

```text
consultation 1 ─── 0..1 appointment
consultation summary 1 ─── 1..N recommendations
recommendation 1 ─── 0..1 appointment
```

The recommendation-side upper bound follows from one appointment per
consultation and immutable recommendation ownership; the essential durable
cardinality is `consultation 1 ─── 0..1 appointment`.

The minimum appointment data is:

| Field | Requirement |
| --- | --- |
| `id` | Stable appointment identifier, represented as a UUID consistently with existing persisted identifiers. |
| `consultation_id` | Required foreign-key linkage to the booked consultation and unique to enforce at most one appointment per consultation. |
| `recommendation_id` | Required foreign-key linkage to the selected persisted `consultation_recommendations` row. |
| `scheduled_at` | Required timezone-aware appointment instant. |
| `location` | Required normalized, nonblank text of at most 200 characters. |
| `created_at` | Required timezone-aware timestamp recording successful persistence. |

Treatment text shall not be copied into the appointment. It is resolved through
the immutable persisted recommendation relation for display and response
mapping. This avoids a second treatment source while keeping
`consultation.recommended_procedure` as Feature 003's compatibility projection.

PostgreSQL shall be authoritative for appointment identity, linkage, values,
cardinality, and the consultation status. SQLAlchemy mappings, constraints,
indexes, and an Alembic migration are implementation-planning concerns after
this specification is approved.

## 8. Consultation and Recommendation Linkage

The durable lineage is:

```text
appointment.consultation_id
       → consultation.id

appointment.recommendation_id
       → consultation_recommendation.id
       → consultation_summary.id
       → consultation_summary.consultation_id
       = appointment.consultation_id
```

Before any write, the application workflow shall resolve the recommendation
through the persisted summary for the path consultation. A recommendation is
bookable only if its summary's `consultation_id` equals the requested
consultation identifier. A valid recommendation belonging to another
consultation shall be rejected without revealing it as an acceptable choice
and without any write.

Foreign keys shall prevent nonexistent consultation and recommendation
references. Because ordinary foreign keys alone do not prove cross-table
ownership, the application workflow shall enforce the equality above inside
the booking transaction. Implementation planning shall select appropriate row
locking or equivalent PostgreSQL transaction coordination so eligibility
cannot change between validation and commit.

Booking shall not alter recommendation identity, treatment, position, summary,
messages, or the consultation's recommended-procedure projection.

## 9. Date/Time and Location Validation

### 9.1 Date and time

The API request shall use an ISO 8601/RFC 3339-compatible datetime string with
an explicit UTC designator or numeric offset, for example
`2026-08-20T14:30:00Z` or `2026-08-20T19:30:00+05:00`.

- A date-only value, a local datetime without an offset, an invalid calendar
  value, or a non-string value is invalid.
- The parsed instant must be strictly later than the authoritative server time
  when the application validates the request. Past or exactly-current instants
  are invalid.
- The backend shall compare instants in UTC and persist a timezone-aware value;
  responses shall include an explicit offset. Equivalent offsets represent the
  same instant.
- No maximum booking horizon, named-timezone preference, daylight-saving rule,
  business-hours rule, or availability subsystem is introduced.

The frontend may use a browser-local date/time control for usability, but its
service shall convert the chosen instant to the explicit-offset API format.
Client validation is guidance only; server validation remains authoritative.
Tests shall inject or otherwise control the application clock rather than
depending on wall-clock timing.

### 9.2 Location

Location is required text. The API/application boundary shall trim surrounding
whitespace, reject a value that becomes blank, and reject a normalized value
longer than 200 Unicode characters. The normalized value is persisted and
returned. Location is not resolved against a provider, address, or location
table.

## 10. Atomic Booking Workflow

The focused appointment application workflow shall perform this conceptual
unit of work:

```text
validate request shape
       ↓
begin coordinated database unit of work
       ↓
load consultation and existing appointment state
       ↓
require COMPLETED + no appointment
       ↓
load consultation summary and selected recommendation
       ↓
require recommendation ownership
       ↓
validate normalized location and future instant
       ↓
insert appointment
       ↓
set consultation status BOOKED
       ↓
commit once
       ↓
reload and return persisted appointment
```

The appointment insert and status update shall commit exactly once as one
transaction. Any validation, constraint, flush, status-update, or commit
failure shall roll back the entire unit: no appointment remains and the
consultation does not become `BOOKED`.

No database transaction shall include an AI or external network call. Flask
routes shall not coordinate this transaction or access repositories directly.

## 11. Cardinality, Repeated Requests, and Concurrency

One consultation may have zero or one appointment. The database shall enforce
this invariant with a unique consultation linkage in addition to application
checks.

Booking POST is an intentional create, not an idempotent retrieval operation:

- the first valid request returns `201` with the created appointment;
- any later request for the same consultation returns the coded already-booked
  conflict, even if every submitted value is identical;
- it never creates, replaces, or updates another appointment; and
- the client shall not automatically retry an ambiguous booking failure.

Concurrent valid submissions shall produce at most one committed appointment
and one `BOOKED` transition. The winning request returns `201`. A losing request
shall roll back, reload authoritative state, and return the same client-safe
already-booked conflict. It shall not expose a raw unique-constraint error.

This feature intentionally adds no idempotency key and no appointment GET
endpoint. Consultation Summary GET already provides the minimum context needed
before booking, and successful booking immediately returns its persisted
representation before redirecting to records.

## 12. API Contract

Feature 004 shall add one endpoint to the existing versioned consultation API:

| Method and path | Purpose |
| --- | --- |
| `POST /api/v1/consultations/{consultation_id}/appointments` | Create the consultation's one appointment and atomically mark the consultation `BOOKED`. |

The existing `GET /api/v1/consultations/{consultation_id}/summary` remains the
read boundary used by the booking screen to display and locally validate the
selected recommendation. Feature 004 adds no appointment retrieval endpoint.

### 12.1 Request

```json
{
  "recommendation_id": "22222222-2222-4222-8222-222222222222",
  "scheduled_at": "2026-08-20T14:30:00Z",
  "location": "Downtown Clinic"
}
```

The body is required, shall reject unknown fields, and shall be validated by an
explicit Pydantic DTO. The path and both identifiers use the existing UUID
convention.

### 12.2 Successful response

A successful creation returns `201`:

```json
{
  "id": "appointment identifier",
  "consultation_id": "consultation identifier",
  "recommendation": {
    "id": "recommendation identifier",
    "treatment": "Persisted selected treatment"
  },
  "scheduled_at": "2026-08-20T14:30:00Z",
  "location": "Downtown Clinic",
  "created_at": "2026-08-17T12:00:00Z"
}
```

The nested recommendation is a response projection resolved from persistence;
only its identifier is stored on the appointment. Position is unnecessary to
the booking result. A success is returned only after both appointment and
`BOOKED` status are committed.

### 12.3 Validation and error outcomes

The API shall follow the existing client-safe `{ "error": "..." }` convention
and add stable `code` values for business conflicts:

| Outcome | HTTP | Response requirement |
| --- | --- | --- |
| Invalid consultation UUID, invalid recommendation UUID, absent/malformed body, unknown field, invalid or non-future datetime, blank/overlong location | `400` | `{ "error": "Invalid request" }` with no internal validation detail. |
| Consultation does not exist | `404` | `{ "error": "Consultation not found" }`. |
| Recommendation identifier does not exist | `404` | `{ "error": "Recommendation not found" }`. |
| Recommendation exists but does not belong to this consultation's persisted summary, or the consultation has no usable persisted summary | `409` | Safe message and `code: "RECOMMENDATION_NOT_BOOKABLE"`. |
| Consultation is `PENDING`, or is otherwise not exactly `COMPLETED` while no appointment can be reconciled | `409` | Safe message and `code: "CONSULTATION_NOT_BOOKABLE"`. |
| Consultation is `BOOKED`, an appointment already exists, or a concurrent request has just created it | `409` | Safe message and `code: "APPOINTMENT_ALREADY_EXISTS"`. |
| Persistence or unexpected server failure | `500` | `{ "error": "Internal server error" }`; no SQL, constraint, stack, environment, or sensitive detail. |

When multiple conflict facts coexist, an existing appointment takes precedence,
then a `BOOKED` status, then general consultation eligibility, then summary and
recommendation ownership. This gives repeated/concurrent requests a stable
already-booked result while keeping invalid input validation at the API
boundary first. A recommendation belonging to another consultation is never
accepted merely because the treatment text matches.

## 13. Backend and Architecture Responsibilities

### Flask API layer

The existing consultation blueprint shall own route registration, HTTP parsing,
Pydantic request/path validation, response serialization, and translation of
known application outcomes. It shall delegate one call to the application
service and shall not access SQLAlchemy, sessions, repositories, or transaction
mechanics directly.

### Application layer

`ConsultationApplicationService` or a focused appointment application workflow
composed beside it shall coordinate booking eligibility, normalization,
recommendation ownership, appointment creation, status transition, and typed
outcomes. The implementation plan shall choose the smallest arrangement that
preserves the existing composition boundary and separation of concerns. It
shall not depend on Flask, React, LangChain, or provider SDKs.

### Repository and infrastructure layers

A focused appointment repository/unit-of-work capability shall own appointment
lookup, durable constraint handling, the atomic insert/status update, rollback,
and persisted result reload using the existing request-scoped SQLAlchemy
session. Summary/recommendation retrieval shall extend or reuse focused
repository boundaries rather than placing SQLAlchemy queries in the route or
application service.

PostgreSQL remains authoritative. The implementation shall extend the linear
Alembic chain after Feature 003 and preserve Docker Compose support. Exact
mapping, constraint names, locking statement, module placement, and dependency
injection changes belong to the implementation plan.

### AI boundary

Booking shall not call `AIService`, the consultation agent/skill, LangChain, a
provider, or an external service. Existing AI-generated recommendations are
read only after they have been validated and persisted by Feature 003.

## 14. Frontend Responsibilities

The existing consultation frontend feature shall replace
`AppointmentUnavailableScreen` with an Appointment Booking screen at the
current route. The dedicated consultation API/service and types shall own
request construction, response validation, and safe error translation.

The screen shall:

- require both route `consultationId` and query `recommendation_id` context;
- load the persisted summary through the existing service, verify that its
  `consultation_id` matches the route, and find the selected recommendation by
  stable identifier;
- display the selected persisted treatment as read-only text, with no free-text
  treatment input and no recommendation-switching workflow;
- show distinct loading, missing-consultation, unavailable-summary,
  missing/mismatched-recommendation, and recoverable retrieval-error states;
- capture date/time and location with accessible MUI controls;
- provide immediate client-side required/future/length feedback for usability
  while treating the backend as authoritative;
- submit only `recommendation_id`, explicit-offset `scheduled_at`, and normalized
  `location` through the service;
- disable the form/confirmation action while a request is pending and send at
  most one request per user activation;
- preserve entered values after a recoverable validation, conflict, transport,
  or server error so the user can correct or deliberately retry when safe; and
- on confirmed success, navigate with replacement to `/consultations` so the
  records screen reloads authoritative state and displays `BOOKED`.

The frontend shall not mutate cached consultation status, infer ownership from
the URL, call HTTP directly from the screen, automatically retry booking POST,
or display internal backend details. A backend conflict after the screen has
loaded shall be presented safely; already-booked state shall direct the user
back to Consultation Records rather than offering another create attempt.

## 15. Error Handling and Recovery

- Invalid route or query context prevents form submission and offers navigation
  back to the summary or records where possible.
- Summary retrieval failure does not trigger appointment creation. Recoverable
  retrieval failures offer an explicit retry.
- Client validation does not send an invalid request, but equivalent backend
  `400` responses remain displayable next to the form.
- Known `409` codes map to distinct, safe frontend outcomes. They never expose
  database constraints or model internals.
- A transport or safe `500` failure leaves the form available after the pending
  state ends. Because a response may be lost after commit, the UI shall warn
  against blind automatic resubmission and may guide the user to Consultation
  Records to check authoritative status.
- No frontend failure changes consultation, summary, recommendation, or
  appointment state locally.

## 16. Testing Requirements

No test shall require OpenAI, LangChain execution, an external calendar,
network access, or a real credential.

### Backend tests (Pytest)

- Appointment mapping and migration tests verify UUID identity, foreign keys,
  timezone-aware timestamps, nonblank/length-constrained location, and one
  appointment per consultation.
- Application tests cover valid booking, missing consultation, `PENDING`,
  `COMPLETED`, `BOOKED`, missing/inconsistent summary, missing recommendation,
  cross-consultation recommendation, invalid/past datetime, and invalid
  location outcomes.
- A successful workflow uses the persisted recommendation identity and returns
  its treatment without persisting a treatment copy.
- The appointment insert and `COMPLETED → BOOKED` transition commit together;
  injected insert, flush, status-update, and commit failures roll back both.
- Repeated and controlled concurrent submissions create one appointment and
  return the specified stable conflict to all losing requests.
- Persisted reload preserves appointment identifiers, links, normalized values,
  and timezone-aware timestamps.
- API DTO/route tests verify the exact `201`, `400`, `404`, coded `409`, and safe
  `500` contracts, reject extra fields, and expose no sensitive details.
- Booking tests prove that no AI service method is called.

### Frontend tests (React Testing Library and Vitest)

- The existing booking handoff route and query identifier load the expected
  persisted summary through the service.
- The screen displays only the selected persisted treatment and handles absent
  or mismatched route/recommendation context safely.
- Date/time and location controls provide required, future, and length
  validation and convert the chosen instant to the API format.
- Confirmation invokes the booking service once with the stable recommendation
  identifier and normalized inputs.
- Pending state disables duplicate submission.
- Validation, missing, not-bookable, already-booked, transport, and unexpected
  errors remain safe and recoverable as specified.
- Success replaces navigation with Consultation Records and does not mutate
  consultation status in React.

### Persistence and vertical-slice tests

- A completed consultation with a persisted summary/recommendation crosses the
  booking API, application workflow, repositories, and PostgreSQL to create one
  reloadable linked appointment and persist `BOOKED`.
- The existing records GET then returns that consultation as `BOOKED` without
  frontend hardcoding.
- Transaction rollback and concurrent requests prove no partial or duplicate
  appointment can become visible.
- The source messages, summary, recommendations, and recommended-procedure
  projection remain unchanged and retrievable after booking.
- Feature 001–003 regression behavior and Docker Compose compatibility remain
  intact.

Relevant backend tests, frontend tests, linting, type checks, build checks, and
vertical-slice verification shall pass before implementation is complete.

## 17. Dependencies and Follow-on Features

This feature depends on Feature 001's consultations and approved statuses,
Feature 003's completed summary aggregate, stable persisted recommendation IDs,
booking navigation boundary, existing frontend service/router conventions, and
the PostgreSQL/Docker Compose foundation.

It does not depend on Feature 002 AI execution during booking. A later Dashboard
feature may count or display persisted `BOOKED` consultations or appointments,
but Feature 004 defines no dashboard contract or metric.

## 18. Assumptions and Resolved Ambiguities

- One consultation has at most one appointment; multiple bookings are outside
  the short project scope.
- The selected recommendation is authoritative. Appointment persistence stores
  its ID and does not duplicate treatment text.
- The booking screen reuses Feature 003 summary GET for selected-treatment
  context; no appointment GET is needed for the required create-and-redirect
  flow.
- Booking POST is create-once but not retry-idempotent. Repeats receive a stable
  already-booked conflict rather than the existing appointment representation.
- `scheduled_at` represents an instant and therefore requires an explicit
  offset. Named timezone preferences are unnecessary for this scope.
- Any strictly future instant is allowed. Availability, hours, lead time, and
  maximum horizon require later product requirements.
- Location is normalized free text limited to 200 characters; no location or
  provider entity is introduced.
- The server clock is authoritative for future validation, with a controllable
  clock seam required for deterministic tests.
- Successful navigation returns to the existing `/consultations` records route
  with replacement. No success page or client-side record mutation is needed.
- Authentication, authorization, ownership by signed-in user, audit history,
  retention, and clinical scheduling policies remain future concerns.

No unresolved product or architecture conflict blocks implementation planning.
Locking details, SQLAlchemy mapping details, exact constraint names, transaction
repository placement, and UI component layout are deliberately deferred until
this specification is approved.

## 19. Definition of Done

Implementation of an approved version of this specification is done when the
Feature 003 booking handoff opens a functional Appointment Booking screen; the
selected persisted recommendation is displayed without treatment re-entry; one
valid request atomically persists a linked appointment and the
`COMPLETED → BOOKED` transition; invalid, repeated, concurrent, and failed
requests cannot create partial or duplicate state; successful booking returns
to API-backed Consultation Records showing `BOOKED`; prior messages, summaries,
recommendations, and projection data remain unchanged; deterministic automated
tests and regression checks pass; and the complete vertical slice continues to
run with Docker Compose without AI calls, dashboard work, or other out-of-scope
systems.

## 20. Implementation Tasks

- [x] AB-001 — Confirm Feature 004 Integration Boundaries
- [x] AB-002 — Add Appointment Persistence and Migration
- [x] AB-003 — Add Appointment Repository and Atomic Unit of Work
- [x] AB-004 — Add Appointment Booking Application Workflow
- [x] AB-005 — Expose Appointment Booking API and DTOs
- [x] AB-006 — Extend Frontend Consultation Booking Service
- [x] AB-007 — Add Appointment Booking Screen and Route Ownership
- [x] AB-008 — Verify Appointment Booking Vertical Slice
