# New Consultation Feature Specification

**Status:** Complete

## 1. Purpose

Define the missing user-facing entry point into the persisted consultation
lifecycle. The feature lets a user enter the minimum existing consultation
data, create one authoritative PostgreSQL-backed consultation, and continue
immediately in the existing persistent AI conversation experience.

This feature completes the beginning of the approved lifecycle without
reimplementing later stages:

```text
New Consult
       ↓
New Consultation
       ↓
persisted PENDING Consultation
       ↓
AI Consultation and persisted Messages
       ↓
Summary and persisted Recommendations
       ↓
Appointment Booking and persisted Appointment
       ↓
Consultation Records and Dashboard
```

The identifier returned by creation is the authoritative consultation
identifier throughout this flow.

## 2. Scope

The feature shall provide:

- a functional `+ New Consult` action in the existing responsive
  `AppLayout`;
- a focused New Consultation screen at `/consultations/new`;
- collection of the existing model's two user-supplied creation values,
  `patient_name` and `primary_concern`;
- frontend and authoritative backend validation of those values;
- `POST /api/v1/consultations` through the existing consultation API,
  application-service, repository, session, and PostgreSQL boundaries;
- atomic persistence of one consultation with a server-generated UUID,
  server-controlled `PENDING` status, and an initially empty
  `recommended_procedure` projection;
- a `201 Created` response containing the persisted consultation
  representation; and
- navigation to `/consultations/{id}` using the returned authoritative ID so
  the existing Feature 002 conversation can begin immediately.

PostgreSQL shall remain authoritative. Creation shall not be simulated with
hardcoded records, browser storage, component-only state, or a dashboard
mutation.

## 3. Out of Scope

Feature 006 does not implement:

- consultation editing, deletion, duplication, bulk creation, or import;
- a larger patient-intake workflow or new patient/account domain entity;
- authentication, authorization, staff, consultant, or patient management;
- AI generation, an AI-generated intake form, or an initial assistant message
  during consultation creation;
- message, summary, recommendation, or appointment creation as a side effect
  of consultation creation;
- appointment listing/navigation, scheduling management, cancellation,
  rescheduling, or calendar behavior (Feature 007);
- payments, notifications, file uploads, medical-record management, reports,
  or analytics;
- Dashboard redesign or frontend metric synchronization;
- another design system, application shell, Flask application, database
  engine, session architecture, repository hierarchy, or provider
  abstraction;
- a new table, column, constraint, migration, Compose service, or dependency;
  or
- unrelated refactoring of Features 001–005.

## 4. Existing Architecture and Resolved Data Decisions

Repository inspection establishes the current `Consultation` persistence
model as:

| Field | Existing representation | Creation ownership |
| --- | --- | --- |
| `id` | Non-null PostgreSQL UUID primary key with SQLAlchemy `uuid4` default | Server-generated; never accepted from the client. |
| `patient_name` | Non-null `Text` | Required user input, normalized and validated by the backend. |
| `primary_concern` | Non-null `Text` | Required user input, normalized and validated by the backend. |
| `recommended_procedure` | Non-null `Text` | Server initializes it to the empty string. Feature 003 later owns the generated projection. |
| `status` | Non-null PostgreSQL `consultation_status` enum: `PENDING`, `COMPLETED`, or `BOOKED` | Server always initializes it to `PENDING`. Existing completion and booking workflows own later transitions. |

The table has no consultation creation timestamp and this feature shall not
invent one. The smallest sensible user request is therefore exactly
`patient_name` plus `primary_concern`. Asking the user for an ID, status, or
recommendation would expose server-owned lifecycle data and duplicate later
work.

The existing `ConsultationRepository.create_consultation` already adds,
commits, refreshes, and returns a consultation, rolling back and re-raising on
failure. It is currently used by the Feature 003 restart workflow. Feature 006
shall reuse that capability rather than add a `NewConsultationRepository`.

## 5. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- Activating `+ New Consult` on desktop or mobile reaches
  `/consultations/new` and closes the temporary mobile drawer when applicable.
- `/consultations/new` renders a focused form within the existing application
  shell and is not treated as consultation ID `new`.
- The user can submit a valid patient name and primary concern exactly once
  per deliberate submission.
- Obvious blank input is rejected before a request, and the backend remains
  authoritative for all request validation.
- A successful request commits one consultation with a generated UUID,
  normalized input, empty `recommended_procedure`, and `PENDING` status before
  returning `201`.
- The frontend runtime-validates the response and navigates to
  `/consultations/{returned-id}` only after a valid `201` response.
- The existing detail screen loads the same row and allows the user to begin
  the existing persistent conversation without any creation-time AI call.
- A failed request retains useful entered values, displays safe recoverable
  feedback, and permits an explicit resubmission without automatic retry.
- Newly persisted rows appear naturally in Consultation Records and increase
  the next Dashboard `total_consultations` query without a separate mutation.
- Existing consultation detail, conversation, summary, restart, appointment,
  records, dashboard, and responsive navigation behavior remains compatible.

## 6. Consultation Creation API Contract

Feature 006 shall extend the existing consultation blueprint under `/api/v1`:

| Method and path | Purpose |
| --- | --- |
| `POST /api/v1/consultations` | Validate and atomically persist one new consultation. |

This reuses the same consultation resource already served by
`GET /api/v1/consultations`; no parallel resource hierarchy is introduced.
The endpoint accepts no query parameters. Any supplied query parameter returns
the validation response in §6.4 and performs no persistence.

### 6.1 Request DTO

The request must use `Content-Type: application/json` and have this exact JSON
object shape:

```json
{
  "patient_name": "Amina Khan",
  "primary_concern": "Persistent knee pain"
}
```

| Field | Contract |
| --- | --- |
| `patient_name` | Required strict JSON string. Trim leading and trailing whitespace, then require 1–200 Unicode characters. |
| `primary_concern` | Required strict JSON string. Trim leading and trailing whitespace, then require 1–4,000 Unicode characters. |

Lengths are measured after trimming. The bounds keep the new public write
contract deterministic without changing the existing `Text` columns. The
backend stores the normalized strings returned by these rules.

The request DTO shall forbid unknown fields. In particular, `id`,
`recommended_procedure`, and `status` are unsupported lifecycle fields, not
ignored hints. Supplying any of them makes the entire request invalid and
persists nothing.

An absent body, empty body, JSON `null`, malformed JSON, non-object JSON value,
missing required field, wrong JSON type, empty string, whitespace-only string,
over-length string, unknown field, or query parameter is invalid. Numeric,
boolean, array, and object values shall not be coerced to strings.

### 6.2 Server-controlled values

After request validation, the application workflow constructs one
`Consultation` with:

```text
id                    = newly generated UUID
patient_name          = normalized request value
primary_concern       = normalized request value
recommended_procedure = ""
status                = PENDING
```

The server shall not accept a client-selected status or trigger any later
lifecycle transition. The empty recommendation is the established
pre-summary representation already used by Feature 003's restart workflow;
it is not a generated recommendation or missing required input.

### 6.3 Successful response

Only after persistence commits successfully, the endpoint returns `201
Created` and the existing exact `ConsultationResponse` representation:

```json
{
  "id": "4a7f9139-19d1-4734-8bf5-dcd234d99d31",
  "patient_name": "Amina Khan",
  "primary_concern": "Persistent knee pain",
  "recommended_procedure": "",
  "status": "PENDING"
}
```

- `id` is the database-confirmed generated UUID and is authoritative for
  navigation and every later relationship.
- The two user fields contain the normalized persisted values.
- `recommended_procedure` is exactly the empty string.
- `status` is exactly `PENDING`.
- The response shall not include messages, a summary, recommendations, an
  appointment, internal model/session data, or AI output.

No success response may be returned before the commit and refresh complete.
The endpoint does not promise a `Location` header because existing creation
endpoints do not establish that convention; the response ID provides the
authoritative navigation target.

### 6.4 Validation and errors

The endpoint preserves the existing client-safe error convention:

| Outcome | HTTP | Exact response | Persistence and side effects |
| --- | --- | --- | --- |
| Any invalid request described in §6.1 | `400` | `{ "error": "Invalid request" }` | No row is added or committed; no AI call occurs. |
| Unexpected repository, commit, refresh, database, serialization, or server failure | `500` | `{ "error": "Internal server error" }` | No success is reported; the failed repository unit of work is rolled back. No automatic retry or AI call occurs. |

Validation errors shall not echo invalid values. Unexpected errors shall not
expose SQL, SQLAlchemy or PostgreSQL details, stack traces, environment
variables, credentials, database URLs, OpenAI keys, provider details, or raw
exception messages.

## 7. Backend Responsibilities and Transaction Semantics

The required path is:

```text
POST /api/v1/consultations
       ↓ existing consultation Flask blueprint and creation DTO
ConsultationApplicationService
       ↓ existing ConsultationRepository.create_consultation
request-scoped SQLAlchemy Session
       ↓
PostgreSQL consultations
```

### Flask API layer

The existing consultation blueprint shall own content/query checks, JSON
parsing, Pydantic request validation, explicit response DTO serialization, and
translation to the safe `400` and `500` contracts. It shall make one creation
call to the consultation application service and shall not construct
SQLAlchemy sessions, access the repository directly, execute SQL, commit, or
invoke AI.

### Consultation application service

Creation belongs in the existing `ConsultationApplicationService` because it
is a consultation aggregate use case and that service already coordinates
consultation reads, conversation lifecycle, summaries, restart creation, and
booking. It shall accept normalized application-facing values, enforce or
defensively preserve the creation invariants, construct the new consultation,
and delegate one persistence operation. It shall not depend on Flask request
objects or call message, summary, appointment, dashboard, or AI services.

### Consultation repository and unit of work

The existing `ConsultationRepository` owns persistence of the consultation
aggregate and shall retain its current creation unit-of-work convention:

1. add the new consultation to the request-scoped session;
2. commit the transaction;
3. refresh the committed consultation;
4. return the refreshed object; and
5. on any add/commit/refresh failure, roll back the session and re-raise for
   safe API translation.

Creation is atomic: a valid `201` means the row committed. A failure never
returns a fabricated identifier or a success representation. The application
factory shall continue composing the service and repository with the existing
request-scoped session and closing it during request teardown. No second
engine, session factory, session scope, repository, or Flask application is
allowed.

## 8. Lifecycle and Cross-Feature Continuity

Creation performs exactly one lifecycle mutation: insertion of a `PENDING`
consultation. It creates no related row.

- Feature 001 continues to retrieve the row through the existing records and
  detail APIs.
- Feature 002 begins only when the user submits a first message from the
  existing detail route; its message persistence and AI flow are unchanged.
- Feature 003 remains solely responsible for summary/recommendation generation,
  the `COMPLETED` transition, and the recommendation projection.
- Feature 004 remains solely responsible for appointment persistence and the
  `BOOKED` transition.
- Feature 005's `DashboardRepository` naturally counts the committed
  consultation on its next aggregate query. Feature 006 shall not mutate,
  invalidate, or optimistically adjust dashboard metrics.

React may hold temporary form and submission state, but it shall not create a
second client-side consultation identity. All screens and persisted child
records continue using the one UUID returned by PostgreSQL-backed creation.

## 9. Frontend Service Contract

The existing consultation feature's dedicated TypeScript service shall be
extended with a creation operation; the screen shall not call `fetch`
directly.

One invocation shall:

1. issue exactly one `POST` to `/api/v1/consultations`;
2. send `Content-Type: application/json`;
3. serialize exactly `patient_name` and `primary_concern` using the normalized
   form values;
4. require HTTP `201`;
5. parse JSON; and
6. runtime-validate the response as an existing `ConsultationRecord`, with a
   valid UUID, normalized values matching the submitted values, empty
   `recommended_procedure`, and `PENDING` status.

The service shall return the validated record. A `400` maps to a safe creation
validation outcome. Transport failure, any other non-`201` status, unreadable
JSON, a missing/extra or wrong-typed required response field, invalid UUID,
non-`PENDING` status, non-empty recommendation, or submitted-value mismatch
maps to one safe creation-submission failure. Raw server/transport response
details shall not reach the UI.

Runtime rejection of a malformed apparent success is intentionally
conservative: the client shall not navigate with an untrusted identifier. The
UI shall explain that creation could not be confirmed and direct the user to
check Consultation Records before retrying, because an ambiguous network or
response failure may occur after the server committed. The client shall not
automatically retry a creation request.

## 10. Frontend Route, Navigation, and Screen

### 10.1 Routing

The existing nested router shall add:

| Route | Behavior |
| --- | --- |
| `/consultations/new` | Render the New Consultation screen inside `AppLayout`. |

The static `consultations/new` route shall resolve to the creation screen and
must not render `ConsultationDetailScreen` with `consultationId = "new"`.
Route registration/matching shall make this intent explicit while preserving:

```text
/consultations
/consultations/:consultationId
/consultations/:consultationId/summary
/consultations/:consultationId/appointments/new
```

Direct links and browser refresh at all existing paths shall remain intact.
The Consultations navigation section remains active on
`/consultations/new`, consistent with Feature 005's descendant-path rule.

### 10.2 New Consult action

The existing disabled `+ New Consult` control in the shared sidebar shall
become a keyboard-accessible navigation action to `/consultations/new`. The
same logical control shall be available in the permanent desktop sidebar and
temporary mobile drawer through the existing shared sidebar content. On mobile,
activation shall also close the drawer using its established navigation
behavior.

The action is the prominent entry point; the feature shall not add a second
unrelated global creation control. Dashboard and Consultations links and their
order remain unchanged.

### 10.3 New Consultation screen

The screen shall contain:

- a `New Consultation` level-one heading;
- required MUI controls labelled `Patient name` and `Primary concern`;
- a primary `Start Consultation` action;
- a secondary `Cancel` action that navigates to `/consultations` without a
  request; and
- inline field validation plus a form-level recoverable API error area.

The primary concern may use a multiline input; exact dimensions and responsive
layout are implementation-planning decisions. The screen shall use semantic
form submission so keyboard submission follows the same duplicate guard as a
button activation.

### 10.4 Deterministic screen states

| State | Observable behavior |
| --- | --- |
| Initial | Both controls are editable and empty; no validation or API error is shown; `Start Consultation` and `Cancel` are available. |
| Validation error | Submission trims both values, marks each empty/whitespace-only or over-length field with clear inline feedback, focuses or otherwise identifies invalid input, and sends no request. Entered values remain editable. |
| Submitting | Exactly one service call is in flight. The primary action shows clear progress and is disabled; inputs and Cancel are disabled so navigation or repeated click/Enter cannot submit or abandon an in-flight request accidentally. |
| API failure | The form leaves submitting state, retains normalized useful values, shows safe recoverable feedback, and enables explicit correction or resubmission. It performs no automatic retry. Ambiguous failures advise checking Consultation Records before retrying. |
| Success | After a valid `201` response, navigate with replacement to `/consultations/{authoritative-id}`. The stale form is no longer rendered, and browser Back does not resubmit or return to a completed creation form. |

The client-side checks use the same post-trim 1–200 and 1–4,000 character
bounds as the API for immediate feedback, but they do not replace backend
validation.

## 11. Visual, Responsive, and Accessibility Constraints

The screen shall fit the established Feature 005 shell and restrained MUI
visual language:

- persistent left sidebar on desktop and temporary Drawer on mobile;
- existing Auvia brand area, navigation, active treatment, and prominent New
  Consult action;
- light professional background, bordered card or panel, consistent
  typography, comfortable spacing, and clinical/admin tone;
- existing MUI theme, components, breakpoints, and responsive content width;
  and
- no AppLayout redesign or new design system.

Labels, required state, validation associations, progress, error feedback, and
button disabled states shall be accessible to keyboard and assistive
technology users. Focus shall not be trapped or lost during validation or
failure. Screenshot-only destinations or controls such as Patients, AI
Insights, Archive, Invite Patient, Generate Report, revenue analytics, recent
activity, pending reviews, and authentication shall not be introduced.

## 12. Error Handling, Idempotency, and Security

- Invalid frontend input sends zero POST requests.
- While a request is pending, repeated click, Enter, or form submission sends
  no additional request.
- This feature introduces no idempotency-key protocol. Because a connection or
  malformed-response failure can be ambiguous after commit, automatic retry is
  prohibited and recovery copy directs the user to check records before an
  explicit retry.
- A confirmed `400` retains the form and permits correction. A confirmed or
  ambiguous submission failure retains useful values and permits deliberate
  recovery.
- Client-visible errors contain no submitted data beyond what remains in the
  user's own form and no backend internals.
- OpenAI configuration remains backend-only and unused during creation.
- Database credentials and URLs remain server-side. No secret is added to
  React, API output, logs, the specification examples, or persisted
  consultation fields.
- User strings are rendered as text through React/MUI; they are not interpreted
  as markup.

## 13. Migration Decision

No migration is required.

The existing `consultations` table already supports a server-generated UUID,
non-null patient name and primary concern, an empty non-null recommendation
projection, and the `PENDING` enum value. Existing restart creation proves the
same persisted initial shape. API/application validation supplies the bounded
write contract without requiring column changes. Feature 006 shall not add a
table, column, patient entity, timestamp, relationship, index, or constraint.

## 14. Testing Requirements

Tests shall be deterministic, use the existing test seams and migrated test
database where appropriate, and require no live OpenAI call, external network,
or credential.

### Backend DTO and API tests

- A valid exact JSON request returns `201` with the exact five-field
  consultation response.
- The service receives trimmed patient name and concern values.
- The returned ID is a valid authoritative generated UUID; response status is
  `PENDING` and recommendation is empty.
- Missing, empty, whitespace-only, wrong-type, over-length, non-object,
  `null`, malformed, and absent bodies return the exact safe `400` response
  and never call the service.
- Unknown fields, including `id`, `status`, and `recommended_procedure`, and
  any query parameter return `400` and never call the service.
- Unexpected service or serialization failure returns the exact safe `500`
  response without internal or sensitive detail.

### Backend application and repository tests

- The application service constructs one consultation from normalized input,
  with a new UUID, empty recommendation, and `PENDING` status, and delegates
  exactly one create operation.
- Creation invokes no AI service, message repository, summary repository,
  appointment repository, or dashboard mutation.
- Repository creation commits, refreshes, and returns the persisted row.
- A repository failure rolls back and does not yield a successful result; the
  session remains safe for teardown or subsequent controlled use.
- A fresh session can retrieve the created row by the returned ID and sees the
  exact normalized values and initial state.
- A post-creation Dashboard repository query naturally reports one additional
  `total_consultations`, with no appointment-count change.
- Existing consultation list, detail, and restart creation remain compatible.

### Frontend service tests

- One invocation sends exactly one `POST` to `/api/v1/consultations` with the
  JSON content type and exactly the two normalized request fields.
- A valid exact `201` record is returned to the caller.
- `400`, other non-`201` responses, transport failures, and unreadable JSON map
  to their safe creation outcomes without leaking response detail.
- Malformed response tests cover invalid/missing ID, wrong field types,
  unexpected status, non-empty recommendation, submitted-value mismatch, and
  unexpected response fields.
- The service performs no automatic retry and makes one transport request per
  invocation.

### Frontend screen, navigation, and routing tests

- `/consultations/new` renders the required two-field form in `AppLayout`, not
  the detail screen; `/consultations/:consultationId` still renders detail.
- Initial state, labels, required semantics, length feedback, Cancel behavior,
  and keyboard submission are verified.
- Empty and whitespace-only values show inline validation and invoke the
  service zero times.
- A pending promise produces accessible progress and prevents duplicate click
  and Enter submissions; disabled Cancel cannot abandon the in-flight form.
- A failure preserves useful form values, shows safe retry guidance, and a
  deliberate retry causes exactly one new request.
- A valid success navigates with replacement using the returned ID and leaves
  no stale form.
- A malformed apparent success does not navigate and presents ambiguous-failure
  recovery guidance.
- The desktop and mobile `+ New Consult` actions reach the creation route; the
  mobile drawer closes; Consultations is active on the route.
- Existing Dashboard, Consultations, detail, summary, and appointment-booking
  routes remain directly reachable.

### Regression and vertical-slice tests

- Create through the API, retrieve through Feature 001, submit a message
  through a deterministic Feature 002 AI double, and confirm the same
  consultation ID throughout.
- Existing Feature 003 summary/recommendation and Feature 004 booking workflows
  remain eligible only through their existing rules and are not triggered by
  creation.
- Feature 005 metrics observe the committed row through PostgreSQL without
  frontend synchronization.
- Backend tests, frontend tests, lint/type/build checks, documentation checks,
  and Docker Compose compatibility remain intact.

## 15. Architecture and Assignment Constraints

The feature preserves separation of concerns:

- React screen → dedicated consultation frontend service;
- Flask route → Pydantic DTO → consultation application service;
- application service → existing consultation repository;
- repository → request-scoped SQLAlchemy session → PostgreSQL; and
- AI/provider, summary, booking, dashboard, and presentation concerns remain
  outside creation.

This supplies a well-defined REST creation API, real persistence, deterministic
lifecycle initialization, appropriate continuity with existing related data,
stateful navigation across screens, and explicit invalid-input/failure behavior.
It introduces no hardcoded application data, UI-only creation, direct route SQL,
or tightly coupled parallel backend design.

## 16. Dependencies, Assumptions, and Resolved Conflicts

Feature 006 depends on Features 001–005, the existing consultation model and
response DTO, `ConsultationApplicationService`,
`ConsultationRepository.create_consultation`, request-scoped session
composition, frontend consultation API/type conventions, React Router,
`AppLayout`, MUI, PostgreSQL, and Docker Compose.

Resolved decisions from repository inspection:

- The model's non-null `recommended_procedure` might appear to require user
  input, but Feature 003's approved restart path already persists `""` for a
  fresh consultation and later summary completion owns the projection.
  Feature 006 therefore uses the same initial value rather than expanding the
  intake form.
- The model has no timestamp, so no creation timestamp is added to the contract
  or schema.
- Repository commit/rollback ownership is already established for consultation
  creation and is preserved rather than moved to the route or application
  factory.
- React Router's current route set has a dynamic consultation detail segment;
  the static `/consultations/new` route is added explicitly and tested so the
  reserved word cannot enter UUID detail handling.
- The existing `+ New Consult` button is intentionally disabled pending this
  feature; it becomes the shared desktop/mobile route action rather than being
  duplicated.

No unresolved product or architectural conflict blocks implementation
planning after this specification is approved. Exact component/module names,
field layout, icon choice, and styling values remain implementation-planning
decisions within the boundaries above.

## 17. Definition of Done

Implementation of an approved version of this specification is done when a
user can activate the existing New Consult action, submit the two validated
creation fields, receive a database-confirmed `201` representation for one new
`PENDING` consultation, and arrive at its existing detail/conversation route;
PostgreSQL remains authoritative across messages, summary, recommendations,
appointment, records, and dashboard; transaction and safe failure behavior
match the existing architecture; no creation-time AI or later-lifecycle side
effect occurs; no migration or Feature 007 scope is introduced; and all
specified deterministic and regression checks pass.

Implementation planning and implementation tasks shall be created only after
this specification is reviewed and approved.

## 18. Implementation Tasks

- [x] NC-001 — Confirm Feature 006 Integration Boundaries
- [x] NC-002 — Add Backend Creation DTO and Application Workflow
- [x] NC-003 — Expose Consultation Creation API and Verify Persistence
- [x] NC-004 — Extend Frontend Consultation Creation Service
- [x] NC-005 — Add New Consultation Screen and Static Route
- [x] NC-006 — Activate Shared New Consult Navigation
- [x] NC-007 — Verify Lifecycle, Dashboard, and No-AI Integration
- [x] NC-008 — Verify New Consultation Vertical Slice
