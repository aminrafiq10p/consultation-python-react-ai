# Appointments Feature Specification

**Status:** Proposed — specification only

## 1. Purpose

Define the Appointments feature for the AI Consultation Platform. The feature
makes appointments created by Feature 004 visible as a first-class,
application-backed section.

The authoritative flow is:

```text
Feature 004 booking
       ↓
persisted appointments row
       ↓
Appointments navigation
       ↓
/appointments
       ↓
GET /api/v1/appointments
       ↓
Appointments screen
       ↓
related consultation
```

Feature 007 is read-oriented. It reuses Feature 004's appointment persistence,
recommendation lineage, request-scoped session, application service boundary,
and repository boundary. It does not create a second appointment system.

## 2. Repository Findings and Resolved Data Decisions

Repository inspection establishes the following existing persisted model:

| Entity | Existing fields used by this feature | Relationship |
| --- | --- | --- |
| `Appointment` | `id`, `consultation_id`, `recommendation_id`, `scheduled_at`, `location`, `created_at` | One appointment belongs to one consultation and one selected recommendation. `consultation_id` is unique. |
| `Consultation` | `id`, `patient_name`, `primary_concern`, `recommended_procedure`, `status` | `Appointment.consultation_id` references `Consultation.id`. |
| `ConsultationRecommendation` | `id`, `summary_id`, `treatment`, `position` | `Appointment.recommendation_id` references this row; its summary belongs to the same consultation through `ConsultationSummary`. |
| `ConsultationSummary` | `id`, `consultation_id` | Owns the selected recommendation lineage. |

The SQLAlchemy mappings currently use explicit foreign keys and query joins;
they do not define ORM relationship attributes. The read implementation shall
therefore use an appropriately joined repository query or equivalent focused
query, not assume relationship properties that do not exist.

The appointment representation shall contain only persisted or directly
resolved fields supported by this schema:

```json
{
  "id": "appointment UUID",
  "consultation_id": "consultation UUID",
  "patient_name": "Patient name",
  "recommendation": {
    "id": "recommendation UUID",
    "treatment": "Persisted treatment text"
  },
  "scheduled_at": "2026-08-20T14:30:00Z",
  "location": "Downtown Clinic",
  "created_at": "2026-08-17T12:00:00Z"
}
```

`patient_name` is resolved from the related consultation. `treatment` is
resolved from the selected persisted recommendation. Treatment text is not
copied into `appointments`. `recommended_procedure` is an existing
consultation compatibility projection and is not a second appointment
treatment source.

This feature does not expose or invent provider, doctor, clinic, duration,
notes, specialty, availability, or appointment-status fields. The existing
model has no appointment status; a persisted appointment row is the booking
identity. `scheduled_at` is timezone-aware and API timestamps shall include an
explicit UTC offset.

No migration is required. Feature 004's `appointments` table and existing
constraints already contain every value required by this specification.

## 3. Scope

The feature shall provide:

- an `Appointments` destination in the existing shared responsive navigation;
- an `/appointments` route inside the existing `AppLayout`;
- a read API for persisted appointments, reusing the existing Feature 004
  appointment/application boundaries;
- a dedicated frontend appointment-list service with runtime validation;
- an Appointments screen with loading, populated, empty, and recoverable error
  states;
- display of the approved appointment representation above; and
- one clear interaction from an appointment item to its related consultation
  at `/consultations/{consultationId}`.

The same persisted appointment must be visible after it is created through the
existing Feature 004 booking workflow. PostgreSQL remains authoritative at all
times.

## 4. Out of Scope

Feature 007 does not implement:

- appointment creation, booking, or a change to Feature 004 booking
  semantics;
- editing, rescheduling, cancellation, deletion, or status transitions;
- appointment status, calendar, provider scheduling, availability, duration,
  reminders, notifications, payments, recurring appointments, or external
  calendar integration;
- a new appointment model, repository hierarchy, database engine, session
  architecture, table, column, constraint, or migration;
- a denormalized patient or treatment column;
- a complex calendar or date-range UI;
- frontend-only appointment records, localStorage authority, or hardcoded
  appointment data;
- dashboard metric redesign or a second booked-appointment count;
- a new consultation-detail architecture;
- AI booking, natural-language appointment creation, OpenAI, LangChain,
  `AIService`, `ConsultationAgent`, `ConsultationSkill`, or any external
  service; or
- unrelated shell redesign or Feature 008 visual-alignment work.

## 5. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- A user can choose `Appointments` from the shared desktop sidebar or mobile
  drawer and reach `/appointments`.
- The navigation entry is active only for `/appointments` and its descendants
  if any are added later; it is not active for consultation routes.
- Opening `/appointments` retrieves the current persisted appointment list from
  the Flask API.
- A booking committed by Feature 004 subsequently appears in the list with
  the same appointment, consultation, recommendation, scheduled time, and
  location identifiers/values.
- The screen displays enough persisted information to understand the booking:
  patient name, selected treatment, date/time, location, and stable
  appointment/consultation identity as specified by the read representation.
- Selecting an appointment item navigates to its existing related consultation
  route using the persisted `consultation_id`.
- Zero persisted appointments produces an intentional empty state, not a
  blank, fabricated, or error state.
- Loading and recoverable API failure states are clear; failure does not become
  an empty list and Retry performs exactly one new request.
- PostgreSQL is the only authoritative source. React does not derive
  appointments from consultation records, Dashboard metrics, booking form
  state, or browser storage.
- The existing Dashboard continues to count the same persisted `appointments`
  rows, with no synchronization callback or local count mutation.
- Existing Feature 004 booking and all existing consultation routes remain
  reachable and behaviorally compatible.
- No AI or external network call is made by the feature's backend or tests.

## 6. Read API Contract

Feature 007 shall add the following endpoint to the existing versioned Flask
API, unless implementation inspection during planning identifies an already
existing endpoint with this exact contract that can be reused:

| Method and path | Purpose |
| --- | --- |
| `GET /api/v1/appointments` | Retrieve all persisted appointments with their approved consultation and recommendation projections. |

No appointment-list endpoint currently exists in the inspected Feature 004
API. The endpoint shall be a natural extension of the existing API, not a
parallel booking resource. The existing
`POST /api/v1/consultations/{consultation_id}/appointments` remains the only
appointment creation endpoint.

### 6.1 Request contract

The list request accepts no query parameters and no request body. This feature
does not define filtering, pagination, date ranges, search, or sorting
controls.

- `GET` with any query parameter is invalid.
- A non-empty request body is invalid.
- A body/content type is not required for a valid empty request.
- Malformed or otherwise supplied input must not reach the repository.

Invalid input returns the existing safe response:

```http
400 Bad Request
```

```json
{ "error": "Invalid request" }
```

### 6.2 Successful response

A valid request returns `200 OK` with this exact top-level shape:

```json
{
  "items": [
    {
      "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      "consultation_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "patient_name": "Amina Khan",
      "recommendation": {
        "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        "treatment": "Physiotherapy"
      },
      "scheduled_at": "2026-08-20T14:30:00Z",
      "location": "Downtown Clinic",
      "created_at": "2026-08-17T12:00:00Z"
    }
  ]
}
```

The response shall contain no SQLAlchemy models, session information, raw
database values, consultation status, recommendation position, or unrelated
summary/message data. UUIDs are serialized as strings. `scheduled_at` and
`created_at` are timezone-aware ISO 8601/RFC 3339-compatible strings with an
explicit `Z` or numeric offset.

An empty database, or a database with no appointment rows, is successful:

```json
{ "items": [] }
```

Items shall be ordered deterministically by `scheduled_at` ascending, then
`Appointment.id` ascending as the unique tie-breaker. The endpoint returns all
persisted appointments, including appointments whose scheduled instant has
passed; it does not invent an appointment-status concept or silently hide
historical rows.

### 6.3 Unexpected failures

An unexpected repository, serialization, database, or server failure returns:

```http
500 Internal Server Error
```

```json
{ "error": "Internal server error" }
```

Raw SQL, constraint, connection, stack, environment, patient, AI-provider,
and exception details must not be exposed. The read performs no commit,
mutation, booking, status change, or AI call.

## 7. Backend Architecture and Data Access

The required conceptual path is:

```text
GET /api/v1/appointments
       ↓
Flask API boundary
       ↓
appointment-list application operation
       ↓
AppointmentRepository (extended from Feature 004)
       ↓
request-scoped SQLAlchemy Session
       ↓
PostgreSQL
```

### Flask API layer

The route owns request-shape rejection, response DTO serialization, and
translation to the existing `400`, `200`, and `500` conventions. It delegates
to the application layer and does not access SQLAlchemy sessions, execute
queries, construct models, derive Dashboard data, or call AI.

### Application layer

The smallest compatible extension shall be a list operation on the existing
appointment-capable application boundary, preferably the existing
`ConsultationApplicationService` if that preserves current composition and
test seams. It returns a provider-neutral appointment read aggregate/value.
It must not depend on Flask, React, SQLAlchemy mechanics, or AI components.

If planning demonstrates that placing the operation on the consultation
service would create an inappropriate boundary, the approved implementation
may introduce a focused appointment read service, but it must still reuse the
existing `AppointmentRepository`, request-scoped session, and composition
pattern. That architectural decision must be documented in the implementation
plan before code is changed.

### Repository

Extend `AppointmentRepository` with a focused list query. The query shall:

- select appointments and the related consultation patient name and selected
  recommendation treatment through explicit joins;
- constrain the recommendation lineage so the recommendation's summary belongs
  to the appointment's consultation;
- avoid N+1 queries;
- return one read item per appointment, with no duplicate rows from joins;
- apply `scheduled_at ASC, appointment.id ASC`; and
- perform no commit or mutation.

The query must preserve one authoritative appointment identity. It shall not
join Dashboard aggregates, load all consultations and appointments into
separate Python collections for matching, or create records from consultation
status. Because Feature 004 enforces the recommendation and consultation
foreign keys and application ownership during booking, a valid booked row has
the expected lineage. If legacy inconsistent data is encountered, the read
must fail safely according to the existing server error boundary rather than
fabricate related data.

### Composition and session

`create_app` shall continue to compose the appointment repository and
application dependencies with the same request-scoped SQLAlchemy session used
by consultation, booking, and Dashboard reads. No second engine, session
factory, repository hierarchy, or transaction architecture is permitted.

## 8. Relationship to Feature 004 and Dashboard

Feature 004 remains authoritative for the write flow:

```text
persisted recommendation
       ↓
POST booking
       ↓
one appointments row + consultation BOOKED in one transaction
```

Feature 007 must not create test/demo appointments through its own endpoint or
screen. Integration coverage shall create an appointment through the existing
Feature 004 booking workflow, commit it, then retrieve it through
`GET /api/v1/appointments` and assert that the returned `id`, consultation
link, recommendation link/treatment, date/time, location, and creation time
come from that same persisted row.

The resulting state must remain visible to the existing Dashboard. The
Dashboard's `booked_appointments` remains a PostgreSQL count of `appointments`
rows. Feature 007 adds no count endpoint, count calculation, or synchronization
event.

The full continuity scenario is:

```text
New Consultation
  → AI Conversation
  → Summary/Recommendations
  → Feature 004 Appointment Booking
  → persisted Appointment
  → GET /appointments
  → related Consultation
  → Dashboard booked_appointments
```

The IDs and foreign-key relationships in PostgreSQL remain authoritative at
every step.

## 9. Frontend Service Contract

The frontend shall add an appointment-list service at the established API and
configuration boundary. The Appointments screen must not call `fetch` directly
and must not reuse consultation-list data as an appointment source.

The service shall:

- issue one `GET /api/v1/appointments` request per explicit load invocation;
- send no query parameters and no request body;
- use the configured API base URL convention;
- accept only a `200` response as success;
- parse JSON and runtime-validate the exact `{ items: [...] }` shape;
- validate UUIDs, non-empty strings, nested recommendation fields, and
  explicit-offset timestamps;
- reject malformed JSON, missing/extra structural content where the existing
  service convention requires exactness, invalid values, and duplicate or
  malformed item projections as a safe retrieval failure;
- map non-2xx responses and network/transport failures to a safe feature error;
  and
- never automatically retry or return an empty list for a failure.

The service may expose a feature-specific error type or extend the existing
consultation API error taxonomy, provided the established frontend service
boundary and safe error behavior remain consistent. It must not expose raw
response text, database errors, or transport details to the screen.

An explicit Retry action invokes the same service method once. No polling,
automatic retry loop, or hidden background refresh is introduced.

## 10. Appointments Screen

The screen is rendered at `/appointments` inside the existing `AppLayout` and
uses React, TypeScript, MUI, and the application's existing light,
professional visual language. It should follow the established Consultation
Records presentation convention rather than introduce a new visual system.

### Loading state

On initial entry and explicit retry, the screen shows an accessible loading
indicator/status while the request is pending. Previously rendered data must
not be presented as current while a retry is in progress.

### Populated state

Each item visibly presents:

- patient name;
- selected recommendation/treatment;
- scheduled appointment date and time, formatted for display from the
  timezone-aware persisted instant;
- location; and
- enough identity/context to distinguish the appointment, including the
  appointment identifier or a stable row identity and the consultation
  relationship.

On desktop, a restrained MUI table is appropriate for the row-oriented data.
On narrow screens, the same items shall remain readable without horizontal
overflow, using a responsive stacked/card/list treatment if needed. This is a
responsive presentation adaptation, not a second data or navigation model.

One clear interaction is defined: selecting the appointment row/card navigates
to `/consultations/{consultationId}` using the persisted consultation ID.
The entire item may be a keyboard-accessible link/button, or one explicit
`View consultation` action may be used; implementation shall choose one and
shall not add redundant row, patient-name, and action navigation behaviors.

### Empty state

For `{ "items": [] }`, show an intentional message such as “No appointments
yet.” The screen may direct the user toward the existing consultation lifecycle
or Consultation Records, but it must not create a new booking flow or imply
that an appointment exists.

### Recoverable error state

On validation, non-2xx, malformed-response, or network failure, show safe
user-facing feedback and an explicit `Retry` action. Do not show raw backend or
database exceptions. One click invokes one new request. The error state must
not be rendered as the empty state.

## 11. Navigation and Route Compatibility

The existing single shared desktop/mobile navigation definition shall become:

| Label | Destination | Active-state rule |
| --- | --- | --- |
| Dashboard | `/dashboard` | Exact `/dashboard` pathname. |
| Consultations | `/consultations` | `/consultations` and all existing consultation descendants. |
| Appointments | `/appointments` | Exact `/appointments` pathname and any future appointment descendants. |

The prominent `+ New Consult` action remains intact and continues to navigate
to `/consultations/new`. Desktop uses the existing permanent sidebar; mobile
uses the existing temporary MUI Drawer. Labels, destinations, active-state
rules, and accessibility semantics are defined once and shared by both.

Adding the entry must not duplicate navigation definitions, replace the
router, flatten existing consultation paths, or redesign the application
shell. Existing routes remain reachable, including:

```text
/
/dashboard
/consultations
/consultations/new
/consultations/{consultationId}
/consultations/{consultationId}/summary
/consultations/{consultationId}/appointments/new
```

The new route is:

```text
/appointments
```

The Appointments destination is active when the current pathname is the
appointments section, while Consultation remains active throughout the
existing booking screen and all other consultation descendants. Mobile drawer
navigation closes after navigating, as established by Features 005 and 006.

## 12. AI and Persistence Boundaries

Listing appointments is deterministic and read-only. It must not invoke an AI
provider, `AIService`, LangChain, consultation agent/skill, or external
network. Automated tests must run without OpenAI credentials or a real AI
request.

PostgreSQL is authoritative. The feature must not use hardcoded datasets,
localStorage, session storage, component-created appointment objects, or
consultation API responses as a substitute for the appointment endpoint.

No migration is created or required by this specification because Feature 004
already supplies the appointment schema and all required foreign keys,
constraints, and indexes.

## 13. Testing Requirements

All tests shall use deterministic persisted values and existing test seams.

### Backend repository/application tests

- An empty appointments table returns an empty result.
- One persisted appointment returns one correctly projected item.
- Multiple appointments return all items in `scheduled_at ASC, id ASC`
  order, including deterministic same-time tie-breaking.
- Patient name is resolved from the related consultation.
- Treatment and recommendation ID are resolved from the selected persisted
  recommendation.
- Joined retrieval produces no duplicate item for one appointment.
- The repository uses one focused query/load path and does not perform N+1
  related lookups.
- The read performs no commit or mutation and uses the request-scoped session.
- No AI service or external service is called.

### Backend API tests

- `GET /api/v1/appointments` returns `200` and the exact response shape.
- An empty result is `{ "items": [] }` with `200`.
- Query parameters are rejected with the established `400` response.
- A non-empty request body is rejected with the established `400` response.
- Malformed request input does not call the application operation.
- Unexpected application/repository failure returns the safe `500` response
  without internal details.
- Timestamps and UUIDs are serialized according to the contract.

### PostgreSQL integration tests

- A consultation is completed and booked through Feature 004's existing
  booking path.
- The same committed appointment is retrieved through Feature 007's list
  path.
- Consultation and recommendation lineage is correct.
- The returned treatment and patient name match authoritative related rows.
- The appointment remains counted by the existing Dashboard booked metric.
- No appointment is inserted by the list request.

### Frontend service tests

- The service makes the correct single GET request with no body/query.
- A valid populated response is returned in feature-facing types.
- An empty array is returned successfully.
- Malformed JSON, malformed shape, invalid UUID/timestamp/string, and invalid
  nested recommendation data are rejected safely.
- Non-2xx and network failures become safe retrieval errors.
- One service invocation makes one request and does not automatically retry.

### Appointments screen tests

- Loading state is visible while the request is pending.
- Populated appointment information renders correctly.
- Empty state is intentional and distinct from error.
- Recoverable error is visible and includes Retry.
- One Retry click causes exactly one new request.
- Failed retrieval does not fabricate or render an empty list.
- Selecting an appointment navigates to the related consultation route.
- Narrow-screen presentation remains usable without requiring a separate
  navigation or data implementation.

### Navigation and regression tests

- Desktop and mobile expose the same three destinations in the specified
  order.
- `/appointments` marks only Appointments active.
- Existing consultation descendants continue to mark Consultations active.
- `+ New Consult` remains available and functional.
- Direct `/appointments` navigation renders the screen inside `AppLayout`.
- Existing booking, consultation, Dashboard, and root-redirect tests remain
  passing.

## 14. Definition of Done

Feature 007 is ready for implementation planning only when this specification
is approved and its repository findings remain true. After implementation,
the feature is complete only when the API, repository/application path,
frontend service, screen states, shared navigation, integration flow, and
regression tests satisfy this document, with no migration or unrelated shell
redesign introduced.

## 15. Implementation Tasks

- [x] AP-001 — Confirm Feature 007 Integration Boundaries
- [x] AP-002 — Add Joined AppointmentRepository List Read
- [x] AP-003 — Add Application Appointment-List Operation
- [x] AP-004 — Add List DTOs and GET API Contract
- [x] AP-005 — Verify Request-Scoped Appointment Composition
- [x] AP-006 — Complete Backend Appointment Read Tests
- [x] AP-007 — Verify Feature 004 Booking to Feature 007 PostgreSQL Retrieval
- [x] AP-008 — Verify Dashboard Booked-Count Consistency
- [x] AP-009 — Add Frontend Appointment Types and List Service with Runtime Validation
- [x] AP-010 — Build the `/appointments` Screen and Route State Machine
- [x] AP-011 — Add Responsive Appointment Presentation and Consultation Navigation
- [x] AP-012 — Add Shared Desktop/Mobile Appointments Navigation and Active State
- [x] AP-013 — Run Features 001–006 Regression and Lifecycle Verification
- [x] AP-014 — Verify No-AI, No-Migration, Docker, and Scope Isolation
- [x] AP-015 — Verify the Feature 007 Final Vertical Slice
