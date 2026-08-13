# Consultation Records Implementation Plan

## 1. Objective

Implement the approved Consultation Records vertical slice: persisted
consultation retrieval from PostgreSQL, read-only Flask endpoints, and React
screens that list, search, filter, and display consultation details. The
implementation will use the approved boundaries:

```text
React feature → frontend API/service layer → Flask API
Flask route → Pydantic DTO → application service → repository
PostgreSQL → SQLAlchemy → repository → application service
```

No AI workflow, consultation mutation, pagination, authentication, or
additional infrastructure is part of this plan.

## 2. Feature Scope

The implementation will provide:

- a Consultation Records screen showing patient name, primary concern,
  recommended procedure, and status from backend data;
- optional case-insensitive search across the three approved text fields;
- one optional status filter (`PENDING`, `BOOKED`, or `COMPLETED`) plus an
  all-status UI option;
- combined search and status filtering;
- detail navigation and retrieval for a selected consultation; and
- loading, empty, recoverable error, and unavailable-detail states.

The only feature persistence is a consultation with `id`, `patient_name`,
`primary_concern`, `recommended_procedure`, and `status`. No message,
recommendation, or appointment persistence or workflows will be added.

## 3. Specification Traceability

| Specification requirement | Planned implementation responsibility | Verification focus |
| --- | --- | --- |
| Persisted consultation list and detail data | Alembic, SQLAlchemy infrastructure, repository, application service, Flask API | PostgreSQL-backed retrieval tests |
| `GET /api/v1/consultations` with `search` and `status` | List request/response DTOs, route, service, repository query | API and repository search/filter tests |
| Case-insensitive search across the three text fields | Repository query criteria passed unchanged from validated service input | Search inclusion/exclusion tests |
| Exactly three status values and combined filtering | Domain/status representation, request validation, repository criteria | Per-status, invalid-status, combined-filter tests |
| Detail retrieval and 404 behavior | Detail path DTO, service not-found outcome, route error translation | Detail success and absent-record API tests |
| Backend-driven records UI and navigation | Feature API service, records screen, React Router detail route | Rendering, navigation, and service-boundary tests |
| Loading, empty, error, and unavailable detail | Records and detail UI state handling | React Testing Library state tests |
| No AI or unrelated data/workflows | Layer boundaries and scoped review | No AI provider calls or extra schemas/dependencies |

## 4. Implementation Strategy

Deliver a thin read-only vertical slice. First establish the consultation
persistence and repository query capabilities; expose them through an
application service and the approved versioned API contract; then connect the
feature-oriented React screens through a dedicated frontend service. Keep
translation at each boundary: SQLAlchemy infrastructure data stays behind the
repository, application outcomes stay independent of Flask, API DTOs define
HTTP representations, and frontend feature types stay behind its service
module.

The list endpoint remains unpaginated and uses no implicit sorting contract.
The frontend sends only supplied criteria: a trimmed non-empty search term and
an approved status; its all-status option omits `status`. Invalid supplied
input is left to the API's Pydantic validation and consistent client-safe
error handling.

## 5. Database/Persistence Work

- Add the approved consultation persistence mapping only, using SQLAlchemy in
  the infrastructure/persistence boundary.
- Add one reviewable Alembic migration for the required consultation storage
  and enforce the approved required fields/status value set at the persistence
  layer where consistent with existing foundation conventions.
- Use the project-managed SQLAlchemy engine and session lifecycle; no route or
  application service will access session mechanics directly.
- Preserve PostgreSQL as the system of record. Deterministic development/test
  consultation records, if needed, will be introduced through approved test or
  local-development mechanisms rather than frontend fixtures or hardcoded UI
  data.
- Do not add tables, relationships, columns, or lifecycle rules for messages,
  recommendations, appointments, summaries, or AI output.

## 6. Backend Repository Work

- Define a focused consultation repository interface/contract in the approved
  backend layering, with operations to retrieve one consultation by identifier
  and list consultations using optional validated search and status criteria.
- Implement that contract in the SQLAlchemy infrastructure layer.
- Apply search case-insensitively to `patient_name`, `primary_concern`, and
  `recommended_procedure`; combine text and status predicates with logical
  AND when both are supplied.
- Return only the consultation data needed for the feature and represent an
  absent identifier without exposing database/session details upward.

## 7. Backend Application-Service Work

- Add a consultation read application service that coordinates list and detail
  use cases through the repository contract.
- Accept already validated criteria, pass them to the repository, and return
  application-level data appropriate for response DTO mapping.
- Translate an absent detail result into an application-level not-found
  outcome for the API layer to map to `404`.
- Keep the service deterministic and independent of Flask, SQLAlchemy session
  mechanics, LangChain, and all AI providers.

## 8. Backend API/DTO Work

- Register the versioned consultation routes within the existing Flask
  application/blueprint organization:
  `GET /api/v1/consultations` and
  `GET /api/v1/consultations/{consultation_id}`.
- Define explicit Pydantic request DTOs for optional list query parameters and
  the detail path identifier, and response DTOs for the specified record and
  `{ "items": [...] }` list shape.
- Validate status against only `PENDING`, `BOOKED`, and `COMPLETED`; reject a
  supplied blank or whitespace-only search and invalid path/query input with
  the project-standard client-safe `400` representation.
- Delegate from routes to the application service, serialize explicit DTOs,
  map missing details to `404`, and use the existing safe unexpected-error
  behavior for `500` without revealing persistence internals.

## 9. Frontend API/Service Work

- Create/extend the consultation-records feature API/service module using the
  approved two-endpoint contract as its sole transport boundary.
- Define feature-facing TypeScript types for a consultation record, list
  response, approved statuses, and distinguishable transport/not-found
  outcomes needed by the UI.
- Construct URL query parameters only for active search and status criteria;
  preserve the all-status behavior by omitting `status`.
- Translate HTTP responses and transport failures for screen consumption.
  Components will not make direct HTTP calls or contain persistence/business
  rules.

## 10. Consultation Records UI Work

- Add the feature-oriented Consultation Records route/screen using React,
  TypeScript, React Router, and MUI.
- Present the four required fields in an accessible MUI table or list and make
  each returned record selectable for detail navigation.
- Maintain local temporary search-input and selected-status state. Provide the
  all-status choice plus only the three approved statuses.
- Request backend data through the feature service when the active criteria
  are applied, and render the returned data without frontend fixtures.
- Make list loading, successful empty results, and recoverable request errors
  visually clear and safe. Do not add sorting, pagination, mutations, or
  client-side reimplementation of backend filtering rules.

## 11. Consultation Detail UI Work

- Add a React Router detail route whose route parameter carries the stable
  consultation identifier; select its exact path naming within the existing
  router conventions.
- Retrieve the selected record through the feature API/service module and
  display patient name, primary concern, recommended procedure, and status
  using MUI components.
- Provide clear loading, recoverable retrieval-error, and unavailable-detail
  (`404`) states. The unavailable state must be distinct from a generic
  recoverable error.
- Keep this view read-only and out of the future AI chat, summary, or booking
  scope.

## 12. Testing Strategy

All tests will use controlled consultation data, run deterministically, and
require neither external AI providers nor credentials.

### Backend

- Repository/persistence tests will exercise PostgreSQL-backed single-record
  retrieval, case-insensitive search across each approved field, every
  approved status, and combined search-plus-status criteria.
- Application-service tests, where useful to protect coordination, will cover
  criteria forwarding and the application-level missing-detail outcome without
  coupling to Flask or SQLAlchemy sessions.
- Pytest API tests will cover list and detail DTO shapes; valid criteria;
  empty successful lists; invalid/blank query and path input (`400`); missing
  details (`404`); and the project's safe unexpected-failure behavior (`500`).

### Frontend

- React Testing Library tests will cover rendering all returned record fields,
  search and status interactions through the feature service boundary, and
  combined criteria presentation.
- Tests will cover list loading, empty, and recoverable-error states;
  selection/navigation to the detail route; detail rendering; unavailable
  detail; and detail retrieval errors.
- Frontend tests will stub the feature service/transport boundary and will not
  require a live backend or PostgreSQL instance.

### Integration and quality checks

- Focused PostgreSQL integration coverage will confirm deterministically
  persisted consultations flow through repository, service, and API retrieval,
  including search/filter behavior.
- Verify the frontend service against the approved response/error contract and
  run the applicable backend checks, frontend type checks, and feature tests.
- Confirm the delivered vertical slice remains compatible with the approved
  Docker Compose runtime, without adding Docker files or infrastructure.

## 13. Integration/Verification

Verify acceptance criteria at the vertical-slice boundaries:

1. Persist known consultations containing each status and search term.
2. Retrieve all records and confirm the four-field response representation.
3. Verify search, each status, and combined criteria against persisted data.
4. Retrieve an existing detail record and verify a missing identifier yields
   the specified unavailable-detail path.
5. Use the records UI to exercise loading, list data, empty result, recoverable
   error, filtering/search interaction, and record navigation.
6. Use the detail UI to exercise loading, success, unavailable, and error
   states.
7. Run targeted automated tests plus relevant type/lint checks, then review
   scope and architecture compliance before declaring completion.

## 14. Implementation Order

For the two-day timeline, use these high-level phases rather than independent
implementation tasks:

1. **Boundary alignment:** confirm existing project conventions for module
   placement, error format, route registration, ID representation, migrations,
   test database setup, and route naming; keep the approved API contract as
   the cross-team boundary.
2. **Backend persistence core (critical path):** implement the consultation
   migration/mapping and repository behavior, with deterministic persistence
   tests.
3. **Backend read API (critical path):** add the application service, Pydantic
   DTOs, routes, and API tests for successful and error paths.
4. **Frontend feature:** implement the frontend service, records screen,
   detail screen, routing, and frontend behavior tests against the contract.
5. **Vertical-slice verification:** run integration tests and relevant quality
   checks; validate every acceptance criterion and Docker Compose
   compatibility.

## 15. Parallel Development Opportunities

After the approved API contract is adopted as the shared boundary, frontend
and backend streams can proceed in parallel:

| Stream | Parallel work | Dependency |
| --- | --- | --- |
| Backend | Consultation persistence, repository, application service, DTOs, routes, and Pytest coverage | Existing foundations and agreed API/error conventions |
| Frontend | Feature API service, feature-facing types, records UI, detail UI, routing, and React Testing Library coverage | Approved endpoint/DTO/error contract; no running backend needed for component tests |
| Integration | Contract verification, PostgreSQL retrieval/filter tests, and end-to-end feature checks | Completed backend API and frontend service/screens |

Frontend work need not wait for the migration or live endpoint: it can use
contract-shaped deterministic service stubs. Backend persistence/API work need
not wait for UI layout decisions. Integration begins once both streams expose
their contract-facing behavior.

## 16. Dependencies

The feature depends only on the approved project, backend, frontend, database,
infrastructure, and testing foundations. Its dependency order is:

```text
Existing application/configuration foundations
        ↓
Alembic migration + SQLAlchemy consultation mapping
        ↓
Consultation repository
        ↓
Consultation application service
        ↓
Pydantic DTOs + Flask routes
        ↓
Frontend API/service layer
        ↓
Records/detail routes and UI
        ↓
Integration and acceptance verification
```

The frontend service and UI can start after the API contract is treated as
stable, in parallel with the backend chain; its live integration depends on
the API route implementation.

## 17. Risks/Constraints

- The specification intentionally leaves the identifier storage representation
  and exact frontend route path naming as implementation-planning decisions.
  These must follow established repository conventions and remain compatible
  with the string identifier API representation; they must not change the
  contract or require an architecture decision.
- Existing project conventions for client-safe error envelopes, application
  factory/blueprint registration, session lifecycle, migration execution, and
  test PostgreSQL setup must be inspected before implementation so this
  feature integrates rather than duplicates foundation behavior.
- Case-insensitive search must be implemented in PostgreSQL/SQLAlchemy rather
  than simulated by client-side filtering, and it must not expand into
  advanced search, sorting, or pagination.
- Empty list results are successful responses, while missing detail is `404`;
  frontend state handling must preserve that distinction from recoverable
  failures.
- The two-day scope requires focused tests and a simple vertical slice. No AI,
  external provider, credentials, new dependency, new container, or
  out-of-scope data model may be introduced.

## 18. Definition of Done

The implementation is complete only when:

- PostgreSQL is the authoritative source for the five approved consultation
  fields, introduced through an Alembic migration and isolated SQLAlchemy
  infrastructure/repository implementation.
- The two approved Flask endpoints validate with explicit Pydantic DTOs,
  delegate through an application service, return the specified DTO shapes,
  combine search and status correctly, and return client-safe `400`, `404`,
  and `500` outcomes as specified.
- The React feature uses only its dedicated API/service module, renders
  backend-supplied list/detail data and all required user states, and supports
  navigation from a record to its detail route.
- Backend, frontend, and focused integration tests pass deterministically,
  along with relevant type/lint checks, without external AI services or
  credentials.
- The complete slice satisfies every approved feature acceptance criterion,
  preserves Docker Compose compatibility, and contains no unauthorized scope,
  technology, persistence schema, architecture, or ADR change.
