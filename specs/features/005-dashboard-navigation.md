# Dashboard and Navigation Feature Specification

**Status:** Complete  

## 1. Purpose

Define the Dashboard and Navigation feature for the AI Consultation Platform.
The feature gives users a small backend-driven overview of persisted platform
activity and a reusable application navigation area for reaching Dashboard and
Consultation Records.

This feature completes the approved flow after Appointment Booking:

```text
Persisted consultations and appointments
       ↓
Dashboard metrics
       ↓
Dashboard or Consultation Records navigation
       ↓
Existing consultation detail, summary, and booking routes
```

Dashboard values are read-only projections of PostgreSQL state. React does not
derive, cache as authoritative, or simulate any metric.

## 2. Scope

The feature shall provide:

- one Dashboard screen at `/dashboard`;
- a backend endpoint returning total consultations, booked appointments, and
  conversion rate;
- authoritative aggregate queries over persisted consultations and
  appointments;
- three simple MUI metric cards with loading, zero-data, and recoverable-error
  states;
- a reusable application navigation sidebar containing `Dashboard` and
  `Consultations` entries;
- responsive access to the same navigation destinations on smaller screens;
- active navigation state derived from the current React Router location; and
- a root redirect from `/` to `/dashboard` while preserving every existing
  consultation route and direct link.

No dashboard metric changes application state. No new persistence model or
migration is required by the approved metric definitions.

## 3. Out of Scope

This feature does not implement:

- charts, trends, historical or time-series analytics;
- revenue, recommendation, provider, location, duration, capacity, or
  appointment-status analytics;
- consultation or appointment creation, editing, cancellation, or deletion;
- dashboard filtering, date ranges, pagination, exports, or reporting;
- cached, materialized, denormalized, or asynchronously refreshed metrics;
- user-configurable navigation, breadcrumbs, or a new routing architecture;
- authentication, authorization, user-specific metrics, admin features,
  notifications, email, or external integrations;
- AI-generated insights, OpenAI calls, LangChain execution, RAG, Redis, a
  vector database, LangGraph, WebSockets, or streaming; or
- new infrastructure, database tables, status values, or architecture
  redesign.

## 4. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- Opening `/` redirects with replacement to `/dashboard`.
- Opening `/dashboard` directly loads metrics from the versioned backend API.
- The Dashboard displays `Total consultations`, `Booked appointments`, and
  `Conversion rate` using the exact definitions in §5.
- Zero persisted consultations produces a successful, meaningful zero-data
  display rather than an error or undefined calculation.
- A metric retrieval or response-validation failure is safe and recoverable
  through an explicit user retry.
- The reusable application layout provides Dashboard and Consultations
  navigation on dashboard, records, detail, summary, and appointment-booking
  screens.
- The Consultations entry navigates to the existing `/consultations` records
  route, and the Dashboard entry navigates to `/dashboard`.
- Navigation indicates the active application section without changing or
  duplicating React Router ownership.
- Existing `/consultations`, `/consultations/:consultationId`,
  `/consultations/:consultationId/summary`, and
  `/consultations/:consultationId/appointments/new` direct links remain
  reachable with their current behavior.
- PostgreSQL remains authoritative; React neither loads all consultation rows
  to calculate metrics nor hardcodes metric values.
- Automated tests are deterministic and make no AI or external-service call.

## 5. Metric Definitions

The three metrics describe current persisted state at the time the dashboard
query runs. They are unfiltered and system-wide because authentication,
ownership, date ranges, and dashboard filters are outside scope.

### 5.1 Total consultations

`total_consultations` is the count of all rows in `consultations`, regardless
of whether status is `PENDING`, `COMPLETED`, or `BOOKED`.

The count comes from PostgreSQL. It is not the length of a frontend records
response and is not affected by Consultation Records search or status filters.

### 5.2 Booked appointments

`booked_appointments` is the count of persisted rows in `appointments`.

Feature 004 makes an appointment row the durable appointment identity, gives
it a required foreign key to a consultation, and enforces at most one
appointment per consultation. Counting appointments therefore matches the
original product wording and uses the direct authoritative entity. The
dashboard shall not maintain a second booked metric by separately counting
`consultations.status = BOOKED`.

Under the Feature 004 atomic workflow, the appointment count and `BOOKED`
consultation count agree. If legacy, manually altered, or otherwise
inconsistent state exists, the dashboard reports persisted appointment rows
without repairing data, fabricating an appointment from status, or failing the
read. Consistency enforcement remains owned by Feature 004's write invariant.

### 5.3 Conversion rate

`conversion_rate` is the percentage of all persisted consultations that have a
persisted appointment:

```text
(booked_appointments / total_consultations) × 100
```

- When `total_consultations` is zero, `conversion_rate` is `0.0`.
- Otherwise, the backend computes the percentage and rounds it to two decimal
  places using decimal `ROUND_HALF_UP` behavior.
- The API represents the result as a finite JSON number, not a string and not
  a fraction between zero and one.
- The frontend displays the validated value with exactly two decimal places
  and a percent sign, for example `25.00%`, `33.33%`, or `0.00%`.
- React formats the returned percentage for presentation only; it does not
  recompute it from the two counts.

Because each appointment references one consultation and consultation linkage
is unique, valid Feature 004 state keeps the numerator no greater than the
denominator and the rate between `0.0` and `100.0` inclusive.

## 6. Backend Data Authority and Read Consistency

PostgreSQL is authoritative for both counts. The backend shall execute focused
aggregate counting rather than loading persistence models into application
memory. The dashboard read shall observe both values through one repository
operation using the request-scoped SQLAlchemy session and normal PostgreSQL
transaction semantics.

The Dashboard is a current-state overview, not an audit snapshot. A booking
committed before the dashboard read becomes visible according to PostgreSQL
transaction visibility; a concurrently committing booking may appear on this
request or the next refresh. The endpoint does not acquire write locks, block
Feature 004's booking workflow deliberately, or promise historical
point-in-time reporting.

The read performs no mutation, commit, AI call, or external network call. It
does not change consultation statuses or appointment, summary,
recommendation, and message data.

## 7. Dashboard API Contract

Feature 005 shall add one endpoint to the existing `/api/v1` API:

| Method and path | Purpose |
| --- | --- |
| `GET /api/v1/dashboard` | Retrieve the current persisted dashboard metrics. |

The endpoint accepts no path parameters, query parameters, or request body.
Unknown query parameters or a non-empty request body return the existing safe
`400` response so no undocumented filtering contract is introduced.

### 7.1 Successful response

A successful request returns `200` with this exact shape:

```json
{
  "total_consultations": 4,
  "booked_appointments": 1,
  "conversion_rate": 25.0
}
```

- `total_consultations` is a nonnegative JSON integer.
- `booked_appointments` is a nonnegative JSON integer.
- `conversion_rate` is a finite JSON number rounded as specified in §5.3.
- No consultation, appointment, patient, recommendation, or internal database
  detail is included.

For an empty database, the successful response is:

```json
{
  "total_consultations": 0,
  "booked_appointments": 0,
  "conversion_rate": 0.0
}
```

### 7.2 Validation and errors

The endpoint follows the existing client-safe `{ "error": "..." }`
convention:

| Outcome | HTTP | Response |
| --- | --- | --- |
| Supplied query parameter or non-empty request body | `400` | `{ "error": "Invalid request" }` |
| Persistence or unexpected server failure | `500` | `{ "error": "Internal server error" }` |

No SQL, constraint, connection, stack, environment, patient, AI-provider, or
other sensitive detail may be exposed. Metric retrieval has no business
conflict or not-found outcome: zero rows is a valid `200` result.

## 8. Backend and Architecture Responsibilities

### Flask API layer

A focused dashboard blueprint under the existing `/api/v1` composition shall
own route registration, rejection of undocumented input, explicit response DTO
serialization, and safe HTTP error behavior. It shall delegate one call to the
dashboard application service and shall not access SQLAlchemy, sessions,
repositories, consultation services, or AI components directly.

### Dashboard application service

A small dashboard application service shall request the aggregate counts from
the focused repository, calculate the zero-safe rounded conversion percentage,
and return a provider-neutral metrics value suitable for DTO mapping. It shall
not depend on Flask, SQLAlchemy models, React, LangChain, or provider SDKs.

The calculation belongs here rather than in React so the API contract has one
authoritative definition. It shall use deterministic decimal arithmetic and
shall defensively reject impossible negative counts as an internal failure.

### Dashboard repository and infrastructure

A focused dashboard repository shall own the SQLAlchemy aggregate query over
the existing `consultations` and `appointments` tables. It shall return only
the two nonnegative counts needed by the application workflow. It shall not
load full entities, reproduce appointment eligibility rules, infer appointments
from status, or commit a transaction.

The repository shall obtain both independent counts without joining the tables
in a way that multiplies rows. No new table, column, index, constraint, Alembic
migration, or generic analytics repository is required.

### Composition boundary

The existing Flask application factory remains the composition boundary. It
shall compose the focused dashboard repository and application service with
the same request-scoped SQLAlchemy session used by the existing focused
repositories, while preserving the existing injectable-service test seams.
This is a small feature boundary, not a replacement for
`ConsultationApplicationService` or the consultation blueprint.

### AI boundary

Dashboard retrieval shall not call `AIService`, the consultation agent/skill,
LangChain, an AI provider, or any external service. The metrics depend only on
persisted consultation and appointment rows.

## 9. Frontend Dashboard Behavior

A focused dashboard frontend feature shall own its screen, types, and dedicated
API/service boundary. The service shall request `GET /api/v1/dashboard`, reject
non-`200` responses safely, parse JSON, and runtime-validate the exact response
shape and value constraints before exposing metrics to the screen.

The screen shall:

- use MUI and the existing application layout;
- request metrics once when the screen is entered;
- show an accessible loading state while the request is pending;
- show three clearly labelled metric cards after successful validation;
- render count values as integers and conversion rate with exactly two decimal
  places plus `%`;
- render `0`, `0`, and `0.00%` as the sensible zero-data state, optionally with
  concise explanatory copy that no consultations exist yet;
- show zero booked appointments normally when consultations exist;
- show a safe retrieval error without raw transport or response detail;
- provide an explicit `Retry` action that starts one new GET request; and
- replace previously displayed metrics with loading/error state as appropriate
  rather than presenting stale values as current after a failed refresh.

The screen shall not load Consultation Records to calculate metrics, compute
conversion rate, mutate consultation state, call HTTP directly, add charts, or
invoke AI. A malformed success response is treated as the same safe,
recoverable retrieval failure as a transport or server error.

## 10. Navigation, Sidebar, and Responsive Behavior

The existing `AppLayout` shall become the reusable navigation shell rather
than introducing a second layout or router. It shall retain the application
title and main content outlet and provide these entries in this order:

| Label | Destination | Active-state rule |
| --- | --- | --- |
| `Dashboard` | `/dashboard` | Active when the canonical pathname is exactly `/dashboard`. |
| `Consultations` | `/consultations` | Active for `/consultations` and every descendant consultation path. |

Active state is presentational and accessible, derived from React Router's
current location. It does not change data loading or route authorization.

At MUI's medium breakpoint and above, the navigation shall be a visible
permanent sidebar beside the main content. Below that breakpoint, the same
entries shall be available through a temporary MUI navigation drawer opened by
an accessible menu button and closed after navigation. There shall be one
logical navigation definition so desktop and mobile destinations and labels do
not drift.

Keyboard operation, visible labels, appropriate navigation landmarks, focusable
links, and selected/current-page semantics are required. Exact colors, icons,
drawer width, spacing, and visual decoration are implementation-planning
decisions.

## 11. Route Conventions and Compatibility

Feature 005 shall extend the current nested React Router layout with:

| Route | Behavior |
| --- | --- |
| `/` | Redirect with replacement to `/dashboard`. |
| `/dashboard` | Render the Dashboard screen inside `AppLayout`. |
| `/consultations` | Preserve the existing Consultation Records screen. |

The root currently redirects to `/consultations`; Feature 005 intentionally
changes only this default entry behavior so the new overview becomes the
application landing page. `/consultations` remains canonical and directly
reachable.

All existing nested paths remain unchanged:

```text
/consultations/:consultationId
/consultations/:consultationId/summary
/consultations/:consultationId/appointments/new
    ?recommendation_id=:recommendationId
```

The navigation shell must not intercept, flatten, rename, or replace these
routes. The Consultations entry is active throughout these deep workflows, and
their existing back, restart, summary, booking, and success navigation behavior
continues unchanged.

## 12. Error Handling and Recovery

- Zero consultations or zero appointments is successful data, not an error.
- Backend aggregate-query failure returns only the safe `500` contract.
- Unexpected or malformed frontend responses produce a safe dashboard
  retrieval error and never display `NaN`, `Infinity`, partial metrics, or raw
  response content.
- The explicit Retry action repeats only the read request; no automatic retry
  loop is introduced.
- Navigation remains usable while dashboard metrics are loading or have
  failed, so users can still reach Consultation Records.
- A dashboard failure does not alter persisted or frontend consultation state.
- Existing consultation-screen error behavior is not changed by the shared
  navigation shell.

## 13. Testing Requirements

No test shall require OpenAI, LangChain execution, an external service,
network access, or a real credential.

### Backend tests (Pytest)

- Repository tests verify exact consultation and appointment counts for an
  empty database and mixed persisted records.
- Counts prove that `PENDING`, `COMPLETED`, and `BOOKED` consultations all
  contribute to the denominator.
- Booked metric tests prove that persisted appointment rows, not status alone,
  supply the numerator.
- Application tests verify zero-total behavior and deterministic percentage
  results including exact two-decimal `ROUND_HALF_UP` cases.
- Application tests verify zero appointments with a nonzero consultation count
  and defensively invalid repository results.
- API tests verify the exact `200` DTO field names and JSON number types for
  populated and empty state.
- API tests reject query parameters and non-empty request bodies with the exact
  safe `400` contract.
- API and composition tests verify safe `500` behavior without persistence or
  sensitive detail.
- Strict doubles prove that dashboard retrieval invokes no consultation
  mutation and no AI service method.

### Frontend tests (React Testing Library and Vitest)

- The Dashboard shows an accessible loading state while its service request is
  pending.
- Valid metrics render in three labelled cards with integer counts and a
  two-decimal percentage.
- Zero data renders `0`, `0`, and `0.00%` without an error.
- A malformed response, transport failure, and non-success response each map to
  the same safe recoverable state without leaking internal detail.
- Retry invokes one new metrics request and can recover to a successful view.
- `/` redirects with replacement to `/dashboard`, and `/dashboard` renders the
  Dashboard in the shared layout.
- Dashboard and Consultations navigation links reach their canonical routes.
- Active state selects Dashboard only on `/dashboard` and Consultations on the
  records route and each existing deep consultation route.
- Responsive navigation keeps both destinations available and closes the
  temporary drawer after selection.
- Existing consultation records, detail, summary, and appointment-booking
  routes remain reachable through direct route tests.

### Persistence and vertical-slice tests

- Persist deterministic consultations of mixed statuses and verify the
  dashboard endpoint returns counts from PostgreSQL.
- Book one eligible completed consultation through Feature 004 or an equivalent
  deterministic application setup, then verify a new dashboard request reports
  the incremented appointment count and recalculated conversion rate.
- Verify an appointment-linked `BOOKED` consultation contributes once to each
  appropriate count and cannot multiply aggregate rows.
- Verify dashboard reads leave consultations, appointments, messages,
  summaries, recommendations, and recommended-procedure projections unchanged.
- Feature 001–004 regression tests, frontend lint/type/build checks, backend
  tests, and Docker Compose compatibility remain intact.

## 14. Architecture Constraints

The feature preserves this flow:

```text
Dashboard React screen
       ↓ dedicated frontend dashboard service
GET /api/v1/dashboard
       ↓ focused Flask dashboard route
Dashboard application service
       ↓ focused dashboard repository
PostgreSQL consultations + appointments
```

- Flask remains the API framework, SQLAlchemy the ORM, PostgreSQL the database,
  and Pydantic the DTO boundary.
- React, TypeScript, MUI, and React Router remain the frontend stack.
- Flask routes do not query SQLAlchemy directly.
- React does not calculate authoritative metrics from records or statuses.
- Aggregate SQL and persistence mechanics stay in a repository.
- Conversion semantics stay in the application/backend boundary.
- Frontend dashboard concerns remain separate from the existing consultation
  feature, while `AppLayout` owns shared navigation.
- No new dependency, Compose service, migration, analytics abstraction, or ADR
  is required.

## 15. Dependencies and Follow-on Features

This feature depends on Feature 001's persisted consultations and routes,
Feature 004's persisted appointment identity and one-per-consultation invariant,
the existing Flask application composition, frontend service conventions,
nested React Router layout, MUI dependency, PostgreSQL, and Docker Compose.

Later features may define authenticated or filtered dashboards, time-series
analytics, reports, or additional navigation destinations. They must introduce
their own approved definitions and shall not retroactively change Feature 005's
unfiltered current-state metrics without a new specification.

## 16. Assumptions and Resolved Ambiguities

- `Booked appointments` counts `appointments` rows, not consultations whose
  status text is `BOOKED`, because the appointment row is the authoritative
  persisted entity requested by the product and Feature 004 keeps the two in
  sync atomically.
- Conversion uses the appointment count divided by all consultations, matching
  the preferred product definition and the chosen authoritative numerator.
- The conversion value is a percentage JSON number rounded half-up to two
  decimals; the UI formats it with two decimals and `%` without recomputing it.
- Empty persisted state returns `200` with all zero values and no division by
  zero.
- Metrics are global current-state values; there is no user, date, search, or
  status filter.
- `/dashboard` is the canonical Dashboard route, and `/` becomes a replacement
  redirect to it. Existing `/consultations` and deep links are preserved.
- `AppLayout` is the established shared shell and is extended into a responsive
  sidebar/drawer rather than replaced.
- Consultations remains active on all `/consultations` descendants so detail,
  summary, and booking screens retain section context.
- A focused dashboard repository/service/blueprint is smaller and clearer than
  expanding the already multi-workflow consultation service or introducing a
  generic analytics framework.
- Existing tables and constraints already support the required counts; no
  migration or persistence change is required.
- The original requirement creates no need for charts; metric cards are the
  complete approved visualization.

No unresolved product or architecture conflict blocks implementation planning.
Exact module names, SQL expression arrangement, card styling, icons, and drawer
dimensions are deliberately deferred until the specification is approved.

## 17. Definition of Done

Implementation of an approved version of this specification is done when the
root route lands on a functional API-backed Dashboard; PostgreSQL-derived total
consultation and appointment counts and the backend-defined conversion rate
render safely in simple metric cards; empty and failed reads behave as
specified; reusable responsive navigation reaches Dashboard and Consultation
Records with correct active state; every existing consultation route and
workflow remains compatible; no dashboard read mutates data or calls AI; no
unnecessary analytics, persistence, migration, or infrastructure scope is
introduced; and deterministic backend, frontend, persistence, regression, and
Docker Compose verification passes.

## 18. Implementation Tasks

- [x] DN-001 — Confirm Feature 005 Integration Boundaries
- [x] DN-002 — Add Dashboard Metrics Repository
- [x] DN-003 — Add Dashboard Metrics Application Workflow
- [x] DN-004 — Expose Dashboard API and DTO
- [x] DN-005 — Add Frontend Dashboard Service
- [x] DN-006 — Add Dashboard Screen and Route
- [x] DN-007 — Add Reusable Responsive Application Navigation
- [x] DN-008 — Verify Dashboard and Navigation Vertical Slice
