# Consultation Records Feature Specification

## 1. Purpose

Define the Consultation Records feature for the AI Consultation Platform. The
feature gives users a backend-driven view of persisted consultations, lets them
find records by search or approved status, and lets them open a consultation's
detail view.

This is the first feature in the approved downstream flow:

```text
Consultation Records
       ↓
AI Consultation
       ↓
Summary
       ↓
Appointment
       ↓
Dashboard metrics
```

## 2. Scope

The feature shall provide:

- a Consultation Records screen showing patient name, primary concern,
  recommended procedure, and status for each returned consultation;
- backend retrieval of persisted consultation records;
- case-insensitive search of records;
- filtering by exactly one approved status at a time: `PENDING`, `BOOKED`, or
  `COMPLETED`;
- navigation from a selected record to its consultation detail route; and
- backend retrieval and frontend presentation of the selected record's detail
  data.

Consultation records displayed by the frontend shall come from the Flask API.
Hardcoded or mock frontend data shall not be a source of consultation records.

## 3. Out of Scope

This feature does not implement:

- AI chat or conversation messages;
- AI recommendation generation;
- consultation summary generation;
- appointment creation;
- dashboard metrics;
- status changes or status-transition rules;
- creation, editing, or deletion of consultations;
- messages, recommendations, or appointments persistence schemas; or
- pagination, sorting controls, or advanced search.

`recommended_procedure` is display-only data in this feature. Its generation,
meaning, and lifecycle are owned by the later recommendation workflow.

## 4. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- A user can open Consultation Records and see persisted consultation records
  with the four required fields.
- A user can enter a search term and receive only the matching persisted
  records.
- A user can select `PENDING`, `BOOKED`, or `COMPLETED` and receive only
  records with that status.
- Search and status filter work together when both are supplied.
- A user can select a returned record and is navigated to its detail route.
- The detail screen retrieves and displays the selected persisted consultation
  record, including its patient name, primary concern, recommended procedure,
  and status.
- Loading, empty, recoverable error, and unavailable-detail states are clear
  and safe for users.
- The frontend obtains all persisted consultation data through its dedicated
  API/service layer, and PostgreSQL remains the system of record.
- No AI provider, LangChain workflow, external AI credential, new technology,
  or unapproved business status is required.

## 5. Consultation Data and Persistence Requirements

This feature defines only the persisted consultation data needed to retrieve
and identify a record:

| Field | Requirement |
| --- | --- |
| `id` | Stable consultation identifier used by list results, detail retrieval, and routing. Its storage representation is an implementation decision. |
| `patient_name` | Required patient name displayed in records and detail. |
| `primary_concern` | Required consultation concern displayed in records and detail. |
| `recommended_procedure` | Existing recommended-procedure text displayed in records and detail. This feature does not generate or modify it. |
| `status` | Required status with one of `PENDING`, `BOOKED`, or `COMPLETED`. |

PostgreSQL shall persist these consultation values as the authoritative source.
SQLAlchemy mapping and access shall remain in infrastructure, behind a focused
consultation repository. An Alembic migration shall introduce the required
consultation persistence when this approved specification is implemented.

The implementation shall not define message, recommendation, or appointment
tables, relationships, fields, or lifecycle rules for this feature. The
`recommended_procedure` value may be persisted with the consultation solely to
support this feature's display requirement; it does not establish the later
recommendation data model.

## 6. API Contract

The feature shall expose the following versioned Flask REST endpoints:

| Method and path | Purpose |
| --- | --- |
| `GET /api/v1/consultations` | Retrieve consultation records, optionally narrowed by search and status. |
| `GET /api/v1/consultations/{consultation_id}` | Retrieve one consultation record for the detail view. |

### 6.1 List retrieval, search, and filtering

`GET /api/v1/consultations` accepts these optional query parameters:

| Parameter | Validation and behavior |
| --- | --- |
| `search` | A non-empty, trimmed text term. Search is case-insensitive and matches patient name, primary concern, or recommended procedure. If omitted, no text-search restriction is applied. |
| `status` | One of `PENDING`, `BOOKED`, or `COMPLETED`. If omitted, records of all approved statuses are eligible. |

If both parameters are provided, a returned record shall satisfy both
restrictions. The response returns an `items` array of consultation record
DTOs. This feature intentionally defines no pagination or sorting contract.

Each list item shall contain:

```json
{
  "id": "consultation identifier",
  "patient_name": "Patient name",
  "primary_concern": "Primary concern",
  "recommended_procedure": "Recommended procedure",
  "status": "PENDING"
}
```

An empty matching result is successful and returns an empty `items` array.

### 6.2 Detail retrieval

`GET /api/v1/consultations/{consultation_id}` returns the same consultation
record representation for the identified persisted record. It returns `404`
when the identifier does not correspond to a consultation available to this
feature.

### 6.3 Validation and errors

Request query and path data shall be validated with Pydantic DTOs at the API
boundary. The API shall use the project's consistent, client-safe error format
for these outcomes:

- `400` for invalid query or path input, including an unsupported status or a
  blank supplied `search` value;
- `404` for a consultation detail request whose record is absent; and
- `500` for an unexpected server failure, without exposing internal,
  persistence, or sensitive details.

Response DTOs shall be explicit and shall not expose SQLAlchemy models or
database-session details.

## 7. Backend Responsibilities

### Flask API layer

The API layer shall own route registration, HTTP request parsing, Pydantic DTO
validation, response serialization, and translation of known outcomes to the
specified HTTP responses. Routes shall delegate to the application service and
shall not access SQLAlchemy sessions, repositories, domain rules, or AI
components directly.

### Application service

The consultation application service shall coordinate list and detail
retrieval. It shall pass validated search/filter criteria to the repository,
translate absent detail results into an application-level not-found outcome,
and return data suitable for response DTO mapping. It shall not depend on
Flask objects or SQLAlchemy session mechanics.

### Domain responsibility

The consultation domain shall preserve the approved consultation status value
set. No status transition, appointment, recommendation-generation, or AI
business workflow is introduced by this read-only feature.

### Repository and infrastructure

A focused consultation repository shall retrieve a single consultation by its
identifier and retrieve consultations using the optional search and status
criteria. Its SQLAlchemy/PostgreSQL implementation belongs to infrastructure.
The repository shall not require or retrieve messages, recommendations, or
appointments to fulfil this feature.

## 8. Frontend Responsibilities

The consultation-records frontend feature shall own:

- the Consultation Records screen and a consultation-detail screen or view;
- MUI table or list presentation of the four required record fields;
- temporary search-input and selected-status state;
- invoking its dedicated frontend API/service module to load list and detail
  data;
- an all-status option that removes the status restriction, alongside the
  three approved status filter options;
- an explicit loading state while list or detail data is requested;
- an empty state for a successful list response with no matching records;
- a recoverable, safe error state when list or detail retrieval fails;
- an unavailable-detail state when the API reports that the selected record is
  not found; and
- React Router navigation to a consultation detail route containing the
  selected consultation identifier.

The dedicated frontend API/service module shall own request construction,
response translation into feature-facing types, and transport-error handling
support. Screen and presentation components shall not make direct HTTP calls,
access persistence, or duplicate backend status/business rules.

The exact visual layout, route path naming, and rendering component choices are
implementation-planning decisions, provided they use React Router and MUI and
meet this specification.

## 9. AI Boundary

AI is not part of Consultation Records. This feature shall not invoke
LangChain, an AI provider, `MockAIProvider`, or an external AI service. It may
only display the persisted `recommended_procedure` value supplied by the
backend.

## 10. Testing Requirements

Tests shall use deterministic consultation data and shall not require an
external AI service or credential.

### Backend tests (Pytest)

- List retrieval returns the expected persisted consultation DTOs.
- Search returns matching records and excludes non-matches.
- Each approved status filter returns only its matching records.
- Combined search and status filtering applies both restrictions.
- Detail retrieval returns the requested persisted record.
- Invalid filter input receives the specified client-safe validation response.
- A missing detail record receives the specified not-found response.
- Unexpected failures use the project's safe error behavior.

### Frontend tests (React Testing Library)

- The records screen renders returned record fields.
- Search interaction requests and displays the matching result set through the
  feature API/service boundary.
- Status selection requests and displays the filtered result set.
- Loading, empty, and recoverable error states are visible and understandable.
- Selecting a record navigates to its detail route.
- The detail view renders retrieved data and presents unavailable-detail and
  retrieval-error states appropriately.

### Persistence and integration tests

- Deterministically persisted consultation records can be retrieved through the
  repository/API path.
- Persisted records can be filtered by each approved status and by search
  criteria.
- No test depends on messages, recommendation generation, appointment data, or
  external AI services.

Relevant frontend type checks, backend checks, and feature tests shall pass
before the implementation is considered complete.

## 11. Dependencies and Follow-on Features

This feature depends only on the approved frontend, backend, database,
infrastructure, and testing foundations. It requires no AI workflow.

Later AI Consultation, Summary, Appointment, and Dashboard Metrics features
may use consultation identifiers and persisted consultation records established
by this feature. They must define their own additional data, business rules,
APIs, and persistence requirements rather than expanding this feature
retroactively.

## 12. Definition of Done

Implementation of this approved feature is done when the API, persistence, and
React feature jointly satisfy every acceptance criterion in this specification;
records are sourced from PostgreSQL rather than frontend fixtures; required
tests pass deterministically; and the completed vertical slice remains
compatible with the approved Docker Compose runtime without introducing AI
work, unapproved technologies, or out-of-scope schemas.

## 13. Implementation Tasks

- [x] TASK-001 — Confirm Consultation Records integration boundaries
- [x] TASK-002 — Implement consultation persistence
- [x] TASK-003 — Implement consultation repository
- [x] TASK-004 — Implement consultation application service
- [x] TASK-005 — Implement Consultation Records API and DTOs
- [x] TASK-006 — Implement frontend consultation API/service
- [x] TASK-007 — Implement Consultation Records screen
- [x] TASK-008 — Implement Consultation Detail screen
- [x] TASK-009 — Add feature and integration tests
- [x] TASK-010 — Perform vertical-slice verification
