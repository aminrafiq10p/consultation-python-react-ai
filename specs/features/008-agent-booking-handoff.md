# Agent Booking Handoff Feature Specification

**Status:** Proposed — specification only

## 1. Purpose

Define the Agent Booking Handoff feature for the AI Consultation Platform. The
feature connects booking intent expressed in the existing persistent AI
conversation to the already-approved deterministic consultation → summary →
recommendation → appointment workflow.

The authoritative continuity is:

```text
New Consultation
       ↓
PENDING consultation and persisted chat
       ↓
booking intent in a user message
       ↓
application-owned handoff action
       ↓
existing summary/recommendation screen
       ↓
Feature 004 booking API and transaction
       ↓
persisted appointment
       ↓
Feature 007 Appointments and Dashboard reads
```

Feature 008 is a handoff feature, not an autonomous booking feature. The
application recognizes actionable intent, evaluates the persisted consultation
state, and returns a typed next action. The model may provide conversational
wording, but it never chooses or persists appointment data.

## 2. Problem and Product Goal

The existing Features 001–007 support persistent consultation chat, summary
generation, persisted recommendations, deterministic booking, and appointment
listing. The existing chat agent has no connection to that capability and can
therefore answer a booking request with a misleading statement that booking is
not supported.

When a user asks to book or schedule an appointment, the application shall
acknowledge that the internal workflow exists and guide the user to the next
valid lifecycle action. A vague conversational request shall never be treated
as permission to invent a recommendation, appointment time, location, or
booking confirmation.

## 3. Repository Findings and Resolved Architecture Decisions

Repository inspection confirms the following existing boundaries:

| Concern | Existing implementation used by Feature 008 |
| --- | --- |
| Consultation lifecycle | `ConsultationStatus` has exactly `PENDING`, `COMPLETED`, and `BOOKED`. A new consultation is `PENDING`; successful summary persistence changes it to `COMPLETED`; Feature 004 changes it to `BOOKED`. |
| Chat application path | `ConsultationApplicationService.submit_message` validates the consultation, persists the user message, loads bounded persisted context, calls `AIService.generate_response`, validates `AIResult`, persists the assistant message, and returns the confirmed exchange. |
| AI boundary | `AIService` delegates to `ConsultationAgent`, `ConsultationSkill`, and the `AIProvider` protocol. `OpenAIProvider` uses structured provider output; `MockAIProvider` is deterministic and network-free. |
| Existing AI result | `AIResult` contains nonblank assistant `content` and an optional scalar/scalar-array `structured_payload`. That payload is informational and is not a business command. |
| Message persistence | `Message.structured_payload` is nullable PostgreSQL JSONB. User messages must not carry a payload. Assistant payloads are persisted with the assistant message. Messages are retrieved in `(created_at, id)` order. |
| Summary eligibility | A `PENDING` consultation needs at least one user message, at least one assistant message, and an assistant as the latest persisted message. The existing summary POST is the completion operation. |
| Summary route | `POST /api/v1/consultations/{consultation_id}/summary` generates or returns the persisted summary; the existing detail screen exposes `Generate Summary`, and the summary screen exposes recommendation selection and booking navigation. |
| Booking authority | Feature 004's `POST /api/v1/consultations/{consultation_id}/appointments` is the only appointment creation path. It requires `COMPLETED`, a persisted summary, an owned recommendation, future time/location input, and no existing appointment. |
| Appointment read | Feature 007's `GET /api/v1/appointments` and `/appointments` screen read PostgreSQL-backed appointments. There is no consultation-specific appointment route. |
| Frontend chat | `ConsultationConversation` loads and submits through `consultationApi`, renders persisted assistant messages, and is hosted by `ConsultationDetailScreen` inside the existing router and `AppLayout`. |

The smallest compatible design is therefore an extension of the existing
message exchange and AI/application seam. Feature 008 shall not add an AI tool
runtime, an appointment endpoint, a booking service, or a second repository
hierarchy.

### 3.1 Conflict resolved by this specification

The current model makes a consultation read-only after `COMPLETED` and
`BOOKED`, so a new booking-intent message cannot be submitted in those states.
Accordingly, “summary/recommendations available” is represented by a
`COMPLETED` consultation reached after a booking-intent message in its prior
`PENDING` conversation; “already booked” is handled when a persisted handoff
is reloaded or when the authoritative state is rechecked. Feature 008 does not
relax the existing conversation-closed rule.

## 4. Scope

The feature shall provide:

- recognition of appointment-booking intent in the existing message workflow;
- an application-owned, typed handoff outcome attached to an assistant
  message response;
- authoritative evaluation of consultation, summary, recommendation, and
  appointment state before producing that outcome;
- state-specific assistant wording that describes the supported next step;
- a functional CTA in the existing consultation chat/detail screen;
- navigation or invocation of existing summary actions using existing routes
  and services;
- safe reload behavior for persisted conversations;
- runtime validation of handoff metadata on the backend and frontend; and
- deterministic backend, frontend, integration, and regression coverage.

## 5. Non-Goals and Scope Guards

Feature 008 does not implement:

- unrestricted LLM tool calling, agents with write-capable tools, or
  autonomous workflows;
- appointment creation from chat, natural-language date/time extraction, or
  natural-language location extraction;
- appointment availability, provider/doctor search, scheduling conflicts,
  calendar integration, notifications, payments, authentication, or
  authorization;
- a new appointment POST endpoint, appointment repository, booking service,
  booking screen, appointment model, or database engine;
- cancellation, rescheduling, editing, deletion, or a new appointment status;
- a second summary/recommendation architecture or a new consultation-detail
  architecture;
- frontend-created appointment records, browser-storage authority, or
  booking-state synchronization callbacks;
- Dashboard, Consultation Records, Appointments, Summary, Booking, New
  Consultation, shell, typography, theme, or broad responsive redesign;
- Feature 009 screenshot matching; or
- a migration unless implementation inspection proves the existing JSONB
  message payload cannot safely carry the approved reload marker.

## 6. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- A normal non-booking message remains an ordinary chat exchange with no
  booking CTA.
- Booking-intent variations such as “book an appointment,” “can you schedule
  an appointment?”, and “I want to make an appointment” no longer receive an
  application response that falsely says the platform has no booking
  capability.
- A booking-intent exchange produces at most one typed handoff for the
  persisted assistant message, and that handoff is selected from authoritative
  application state.
- A `PENDING` consultation that is not summary-eligible receives a
  `CONTINUE_CONSULTATION` action and guidance to complete the conversation.
- A summary-eligible `PENDING` consultation receives a `GENERATE_SUMMARY`
  action that uses the existing summary operation; it does not create an
  appointment.
- A `COMPLETED` consultation with a persisted summary receives a
  `VIEW_SUMMARY` action leading to the existing recommendation screen.
- A `BOOKED` consultation receives a `VIEW_APPOINTMENTS` action or equivalent
  existing consultation/appointment information action and never a booking
  action that could duplicate the appointment.
- The frontend renders the CTA from typed metadata, never by searching or
  matching assistant prose.
- CTA activation does not bypass existing summary or booking validation.
- A state change between response generation and CTA activation is handled by
  the existing authoritative downstream API/screen; no success is inferred
  from stale metadata.
- Refreshing or reopening a consultation does not require a new AI call merely
  to rediscover a previously persisted handoff.
- Expressing booking intent alone creates no appointment and does not change
  consultation status.
- The Feature 004 booking transaction remains the only path that creates an
  appointment and changes `COMPLETED` to `BOOKED`.
- Feature 007 and Dashboard subsequently read the same persisted appointment;
  no local count or synthetic record is introduced.
- Existing Features 001–007 behavior remains compatible.

## 7. Authoritative State Rules

The application, not the model or browser, is authoritative for:

- consultation ID and current `ConsultationStatus`;
- persisted messages and their deterministic order;
- summary existence and ownership;
- recommendation existence, ownership, ID, and treatment;
- appointment existence and consultation linkage;
- summary eligibility and booking eligibility;
- handoff action type, consultation context, and route target; and
- all persisted appointment values and booking confirmation.

The model must never be allowed to supply or override a consultation ID,
summary ID, recommendation ID, appointment ID, status, date/time, location,
eligibility decision, route, or confirmation. Any provider-produced action-like
fields are ignored for business behavior unless they are treated only as an
untrusted intent signal and validated by the application.

State evaluation occurs after the user message has been persisted and before
the assistant response is persisted. It must use the same request-scoped
repositories/session composition as the existing consultation and booking
flows. A CTA is navigation/context only; the destination and existing API
re-evaluate state at activation time.

## 8. Booking-Intent Recognition Decision

### 8.1 Chosen approach

Feature 008 shall add a small provider-neutral booking-intent classifier at
the existing application/AI boundary. It shall normalize the current user
message and recognize a bounded set of booking/scheduling expressions using
token-aware phrase patterns, intent verbs, appointment nouns, and explicit
negative/uncertain context rules. It shall return a typed result such as
`BOOKING_REQUEST` or `NONE`, not a free-form action.

This is not a general classification framework and is not a single unsafe
substring check. The classifier is deliberately narrow: it recognizes an
explicit request to create/schedule/book an appointment, while messages about
canceling, rescheduling, appointment information, or hypothetical discussion
remain ordinary chat unless separately supported in a future feature.

The classifier may be implemented as a pure application value/helper and
invoked by `ConsultationApplicationService.submit_message`, or as an equivalent
small method behind `AIService`; the approved implementation shall preserve
the existing application service and provider seams. The implementation plan
shall choose the exact location without introducing a new subsystem.

### 8.2 AI responsibility

The existing `ConsultationSkill.instructions_for` shall be extended with
intent-aware wording guidance: when the user clearly asks to book, explain
that the application can guide them through its consultation and
recommendation workflow, do not claim booking is unavailable, do not claim a
booking occurred, and do not invent missing details. The skill may use the
application-supplied lifecycle context for wording, but the model output is
never the action authority.

The classifier result shall be available to the application workflow without
requiring a live OpenAI call. A provider may also return structured intent
information in the future, but Feature 008 shall not depend on it and shall
ignore any provider action target or booking data.

### 8.3 Safe ambiguity behavior

If intent recognition returns `NONE`, is uncertain, or fails, the request
continues through the existing ordinary chat path. No CTA, booking write, or
status change occurs. A classifier failure must not fail an otherwise valid
conversation exchange unless the existing AI/message operation itself fails.

## 9. Structured Handoff Contract

### 9.1 API-facing message shape

The existing message response DTO shall be extended with an optional,
application-owned field. The conceptual assistant-message shape becomes:

```json
{
  "id": "message UUID",
  "consultation_id": "consultation UUID",
  "role": "ASSISTANT",
  "content": "I can guide you through the appointment process.",
  "structured_payload": {"provider": "mock"},
  "handoff": {
    "type": "BOOKING_HANDOFF",
    "action": "GENERATE_SUMMARY",
    "consultation_id": "consultation UUID",
    "target": "/consultations/{consultationId}"
  },
  "created_at": "2026-08-20T14:30:00Z"
}
```

For ordinary messages and user messages, `handoff` is `null`. The handoff is
allowed only on assistant messages, must contain the persisted consultation ID,
and must contain one approved action/target pair. No appointment ID,
recommendation ID, date/time, location, or booking confirmation is permitted
in this contract.

The approved action values and targets are:

| Action | Target | Meaning |
| --- | --- | --- |
| `CONTINUE_CONSULTATION` | `/consultations/{consultationId}` | Remain in the current conversation and continue the pending lifecycle. The CTA may focus the existing message composer. |
| `GENERATE_SUMMARY` | `/consultations/{consultationId}` | Invoke the existing summary-generation operation, then navigate to the existing summary route on success. |
| `VIEW_SUMMARY` | `/consultations/{consultationId}/summary` | Open the existing persisted summary/recommendations screen. |
| `VIEW_APPOINTMENTS` | `/appointments` | Open the existing Feature 007 appointment list after the consultation is already booked. |

The backend constructs `target` from the validated path UUID. The frontend
must not accept a target for a different consultation or construct a booking
POST from handoff data.

### 9.2 Persistence representation and DTO projection

No new database field is required. Because assistant `structured_payload` is
already PostgreSQL JSONB, the implementation may store a reserved,
application-owned flat marker set within that JSONB, for example:

```json
{
  "_application_handoff_action": "GENERATE_SUMMARY",
  "_application_handoff_consultation_id": "consultation UUID"
}
```

These reserved keys are not provider-owned informational payload. The backend
must validate them, project them into the typed top-level `handoff` field, and
exclude them from the ordinary `structured_payload` presented as assistant
details. Existing scalar/scalar-array payload constraints remain valid, user
messages remain payload-free, and no nested JSON contract or migration is
introduced. Exact internal key names are implementation details subject to
tests; the typed API contract above is authoritative.

If implementation inspection during planning finds a cleaner existing
message-payload projection that preserves the same no-migration and reload
properties, it may be used, but it must not expose unvalidated provider data as
an application action.

### 9.3 Runtime validation

Pydantic backend DTOs and the frontend runtime validator shall reject malformed
handoffs, including unknown action values, wrong types, invalid UUIDs,
consultation-ID mismatch, invalid target/action combinations, handoffs on
user messages, extra action fields where exactness is required, and malformed
JSON. Invalid persisted metadata shall fail safely: the message remains
displayable as ordinary assistant text, but no CTA is rendered.

## 10. Lifecycle-State → Handoff Mapping

The application shall determine the mapping from current persisted state, not
from provider assumptions:

| Authoritative state | Assistant guidance | Handoff |
| --- | --- | --- |
| `PENDING`, not summary-eligible | Explain that the conversation needs to be continued so the consultation can be completed before recommendations are available. Do not say booking is impossible. | `CONTINUE_CONSULTATION` to the current consultation route. |
| `PENDING`, summary-eligible | Acknowledge the request and explain that the next step is to generate the consultation summary and recommendations. | `GENERATE_SUMMARY` using the existing summary operation, then the existing summary route. |
| `COMPLETED` with an owned persisted summary | Acknowledge that recommendations are ready and direct the user to select a recommendation in the existing flow. | `VIEW_SUMMARY` to the existing summary route. |
| `BOOKED` with the existing appointment identity | Explain that an appointment is already recorded and direct the user to existing appointment information. Never offer another booking action. | `VIEW_APPOINTMENTS` to `/appointments`. |
| Inconsistent state, missing summary/recommendation/appointment lineage, or state lookup failure | Give a safe recoverable message; do not claim readiness, booking, or absence of capability. | No handoff; CTA is omitted. |

The current service may be unable to receive a new message in the last two
rows because completed/booked consultations are read-only. Their mapping is
still required for reload/reconstruction and for any future compatible message
path. The application shall never fabricate a summary, recommendation, or
appointment to make a handoff possible.

## 11. Backend, Application, and AI Responsibilities

### Flask API

The existing message GET and POST routes remain the transport boundary. The
message DTO serialization shall include the optional typed `handoff`; no new
Feature 008 endpoint is required. Routes continue to validate path/request
input, call the application service, serialize persisted values, and map known
safe errors. They do not inspect the model, query SQLAlchemy, construct route
targets, or call booking code directly.

The existing error behavior remains in force: invalid request `400`, missing
consultation `404`, conversation-closed `409`, AI failure `503` with only the
persisted user message recovery data, and safe `500` for unexpected failures.
The API must not expose prompts, provider output, stack traces, credentials, or
database details.

### Consultation application service

The existing `submit_message` workflow remains authoritative. Its Feature 008
extension shall:

1. validate the consultation and ensure it is still `PENDING`;
2. normalize/classify the current user message for booking intent;
3. persist the user message before AI generation, as Feature 002 requires;
4. generate ordinary assistant text through the existing AI service;
5. if intent is actionable, read current summary and appointment state and
   evaluate summary eligibility using existing repositories;
6. construct the application-owned handoff from the validated state;
7. persist the assistant message and approved handoff marker; and
8. return the existing exchange with the typed handoff projection.

The service shall not call `book_appointment` during chat. It may perform
read-only summary/appointment lookups needed to select a handoff. It shall
reuse the existing request-scoped session and composition; no second engine,
session, transaction architecture, or repository hierarchy is allowed.

### AI service, agent, skill, and providers

`AIService.generate_response`, `ConsultationAgent.respond`, and the provider
protocol remain provider-neutral. The provider returns assistant content and
optional informational payload only. The application validates that result as
it already does and merges only the server-owned handoff marker afterward.

`MockAIProvider` shall remain deterministic and network-free. Tests may inject a
fake AI service/result to cover malformed output and provider failure. The
OpenAI provider may use its existing structured-output mechanism for assistant
content, but no OpenAI credential or live call is required for Feature 008
tests. AI instructions must prohibit claiming a completed booking and must
describe the internal handoff without exposing hidden prompts or reasoning.

## 12. API and DTO Changes

Feature 008 requires no new endpoint and does not modify the Feature 004
appointment creation contract. It extends the existing message response
contract only:

- backend `MessageResponse` gains `handoff: BookingHandoff | None`;
- backend application return values carry the typed handoff alongside the
  persisted exchange, or derive it from the persisted reserved marker;
- frontend `ConsultationMessage` gains `handoff: BookingHandoff | null`;
- frontend service/runtime validation validates the exact approved handoff;
  and
- existing message GET and POST responses expose the same field consistently.

The existing `structured_payload` informational contract remains compatible for
ordinary provider data. A handoff is not represented as arbitrary nested model
output and is never accepted as an appointment command.

## 13. Frontend Chat and CTA Behavior

`ConsultationConversation` shall render the existing message content exactly
as ordinary chat and, when an assistant message has valid handoff metadata,
render one adjacent MUI CTA using the existing visual language. It shall not
parse prose or display duplicate patient-name/row/action controls.

CTA labels shall communicate the action, for example:

- `Continue consultation` for `CONTINUE_CONSULTATION`;
- `Generate summary` for `GENERATE_SUMMARY`;
- `View recommendations` for `VIEW_SUMMARY`; and
- `View appointments` for `VIEW_APPOINTMENTS`.

The CTA shall be a keyboard-accessible MUI button or link with an accessible
name. It shall be disabled while its explicit operation is pending, show the
existing loading/error conventions, and prevent duplicate clicks. A
`CONTINUE_CONSULTATION` action remains on the existing detail route and may
focus the current composer. A `VIEW_SUMMARY` or `VIEW_APPOINTMENTS` action
navigates only to its existing route.

`GENERATE_SUMMARY` invokes the existing `generateSummary` service operation
once. On success it navigates to
`/consultations/{consultationId}/summary`; on `409` not-eligible, `503`, or
transport/validation failure it shows safe recoverable feedback and does not
claim completion. It does not call the appointment API.

The CTA is rendered only for a valid handoff whose consultation ID matches the
currently displayed consultation. Invalid or stale metadata is ignored and
the ordinary conversation remains usable. The detail screen continues to
respect the existing read-only behavior for non-`PENDING` consultations.

## 14. Persistence and Reload Semantics

Handoff metadata is persisted with the assistant message using the existing
JSONB payload, with the reserved application-owned markers described in §9.2.
This preserves an action after a conversation reload without adding a
duplicate handoff table, column, or event stream.

On initial load, the frontend retrieves the existing message history and
validates each message. It renders a CTA only for a valid assistant handoff.
The backend/application remains authoritative at action time: summary
generation and all downstream routes re-read current PostgreSQL state. A stale
`VIEW_SUMMARY` or `VIEW_APPOINTMENTS` action therefore cannot authorize a
booking or fabricate data.

For a currently `BOOKED` consultation, the detail screen may normalize or
reconstruct the latest valid booking-intent handoff to `VIEW_APPOINTMENTS`
from current consultation/appointment state. This is a read projection only;
it must be validated against the existing appointment relationship. If the
metadata is absent or inconsistent, the screen shows ordinary persisted chat
and existing consultation status; it does not call AI solely to recreate a
CTA.

No localStorage, sessionStorage, component-created appointment, or
consultation-list substitute is permitted.

## 15. Failure and Fallback Behavior

| Failure | Required behavior |
| --- | --- |
| Intent classifier returns `NONE` or cannot classify | Continue ordinary chat; no handoff and no booking write. |
| AI provider failure after user persistence | Preserve the existing Feature 002 `503` recovery behavior with the persisted user message; persist no assistant success or handoff. |
| AI structured output malformed/nonblank validation fails | Treat as the existing safe AI-generation failure; never use malformed output as an action. |
| Handoff state lookup fails | Persist/return safe assistant text without a CTA if possible; do not claim readiness or booking. Unexpected persistence/application failures use existing safe error handling. |
| Persisted handoff metadata malformed | Render assistant text only; omit CTA and do not expose raw metadata. |
| Consultation state changes before CTA activation | Existing summary/detail/booking API validates current state. Show safe “no longer available/not eligible” feedback; no appointment is created by the CTA. |
| Summary generation fails or becomes ineligible | Show the existing summary error/retry behavior; do not navigate as if completed. |
| Recommendation retrieval/ownership fails | Existing summary screen rejects or safely reports unavailable data; handoff does not carry a recommendation ID and cannot bypass that check. |
| Appointment already exists | Never submit a second booking. Direct the user to `/appointments` when state is known as `BOOKED`; existing Feature 004 `409 APPOINTMENT_ALREADY_EXISTS` remains authoritative for any independent booking attempt. |
| Frontend transport/non-2xx failure | Map to the existing safe `ConsultationApiError` taxonomy; no raw response text or backend details are rendered. |

No fallback may say that a booking was made unless a confirmed Feature 004
booking response has been received. Feature 008 itself never emits a booking
confirmation.

## 16. No-Duplicate-Booking and Authority Guarantees

Expressing intent, receiving an assistant message, rendering a CTA, and
clicking a handoff CTA do not create an appointment. `GENERATE_SUMMARY` calls
only the existing summary endpoint. `VIEW_SUMMARY` and `VIEW_APPOINTMENTS` are
navigation only.

Actual appointment creation remains the existing Feature 004 flow:

```text
summary recommendation selection
       ↓
existing booking screen
       ↓
POST /api/v1/consultations/{consultation_id}/appointments
       ↓
Feature 004 authoritative eligibility and transaction
       ↓
one appointment + COMPLETED → BOOKED
```

Feature 004's consultation uniqueness constraint, row locking/concurrency
handling, recommendation ownership checks, and `APPOINTMENT_ALREADY_EXISTS`
response remain unchanged. Feature 008 must not duplicate any of them.

## 17. Migration Decision

No migration is required. Existing assistant-message JSONB can carry reserved
flat application markers, and the typed `handoff` is an API/application
projection. Consultation status, summary/recommendation rows, appointment
rows, and persisted messages already contain all authoritative state required
to evaluate the handoff.

No new persisted appointment or duplicated lifecycle field is allowed. If
implementation inspection proves the current JSONB constraints cannot support
the reserved marker without weakening existing safety, implementation must
stop and document that conflict before proposing a migration; it must not
silently alter the schema.

## 18. Security, Secrets, and External-Call Constraints

- OpenAI credentials remain backend-only and never appear in React, DTOs,
  handoff metadata, logs, or client-safe errors.
- Handoff metadata is application-owned and must not contain prompts, provider
  raw output, hidden reasoning, credentials, or arbitrary URLs.
- Route targets are generated from validated UUIDs and restricted to the
  approved internal routes.
- The model has no database session, repository, appointment tool, or write
  capability.
- Feature 008 backend and automated tests make no external network call.
- MockAIProvider coverage is mandatory for deterministic tests; live OpenAI is
  not required.

## 19. Testing Requirements

### Backend/application/AI boundary

Tests shall cover:

- ordinary messages produce no handoff and preserve existing exchange behavior;
- representative booking-intent variations are recognized;
- negated, cancellation, rescheduling, and ambiguous messages do not produce
  a booking handoff;
- pending, not-eligible state produces `CONTINUE_CONSULTATION`;
- pending, summary-eligible state produces `GENERATE_SUMMARY`;
- completed state with an authoritative summary produces `VIEW_SUMMARY`;
- booked state with an authoritative appointment produces
  `VIEW_APPOINTMENTS`;
- model/provider action-like output cannot override application state;
- summary/recommendation/appointment lookup failures omit the CTA safely;
- malformed `AIResult` and AI/provider failure preserve existing safe errors;
- no appointment repository write or booking service call occurs on intent;
- no status change occurs merely from intent or handoff generation;
- handoff target and consultation ID are server-derived;
- reserved persistence markers project to the exact typed DTO;
- malformed or mismatched persisted markers are ignored safely;
- `MockAIProvider` remains deterministic and no live OpenAI call is required;
- existing bounded context selection, message ordering, user-message
  persistence, and closed-conversation behavior remain compatible.

### Backend API and DTO

Tests shall cover:

- message GET and POST include `handoff: null` for ordinary messages;
- valid assistant handoffs serialize with the exact approved shape;
- user messages cannot expose a handoff;
- invalid action, target, UUID, role, mismatch, extra fields, and malformed
  marker data are rejected or safely omitted;
- existing `400`, `404`, `409`, `503`, and safe `500` conventions remain
  intact;
- API response never exposes provider details or booking data not persisted by
  Feature 004.

### Frontend service and chat

Tests shall cover:

- ordinary assistant messages render unchanged and no CTA is shown;
- each supported lifecycle action renders the correct accessible CTA;
- CTA behavior uses typed `handoff`, never prose parsing;
- `CONTINUE_CONSULTATION` keeps the user in the existing conversation;
- `GENERATE_SUMMARY` invokes the existing summary operation once and navigates
  only after success;
- summary and appointment navigation uses the authoritative consultation
  context and approved paths;
- loading/disabled behavior prevents duplicate CTA activation;
- malformed action metadata is ignored safely;
- stale/ineligible/downstream failures show safe recoverable feedback;
- keyboard users can reach and activate the CTA;
- reloading persisted messages restores valid handoff metadata without an AI
  call;
- a handoff never issues a booking POST directly.

### Integration continuity

An integration scenario shall:

1. create a consultation through Feature 006;
2. send ordinary conversation messages through Feature 002;
3. express booking intent and verify the typed handoff;
4. follow the pending-state action to existing summary generation;
5. retrieve the persisted summary/recommendations through Feature 003;
6. use the existing Feature 004 recommendation and booking screen/API;
7. verify one persisted appointment and `BOOKED` consultation state;
8. retrieve the same appointment through Feature 007; and
9. verify the Dashboard booked count reflects the same persisted row.

The integration must also assert that the intent message itself creates no
appointment and that a repeated/already-booked path cannot create a duplicate.

### Regression

Features 001–007 regression coverage must remain green, including ordinary AI
conversation behavior, summary generation/idempotence, recommendation
selection, booking validation and concurrency protections, appointment listing,
Dashboard persistence reads, navigation, and root routing.

## 20. Assignment Alignment

Feature 008 improves the assignment's expected behavior without expanding the
product surface:

- stateful consultation flow is demonstrated by using persisted messages and
  authoritative lifecycle state;
- Chat → Summary → Booking → Records continuity becomes reachable from a
  natural conversational request;
- context-aware AI interaction is retained through the existing consultation
  context and bounded message history;
- the structured application outcome is explicit and runtime-validatable,
  rather than inferred from prose;
- real backend persistence remains authoritative for summary,
  recommendation, appointment, and Dashboard state;
- graceful errors preserve existing message recovery and downstream API
  behavior; and
- clear transitions are expressed as small, accessible CTAs into existing
  screens.

## 21. Visual Scope

Only the functional handoff presentation inside the existing consultation chat
is included. The CTA shall use existing MUI components, spacing, typography,
colors, focus behavior, and error conventions. No screenshot matching,
shell redesign, or screen-by-screen visual alignment is part of Feature 008.
Those deliberate visual changes belong exclusively to Feature 009.

## 22. Unresolved Assumptions and Conflicts

- The exact application classifier placement (`ConsultationApplicationService`
  helper versus a small provider-neutral AI boundary method) is intentionally
  left to implementation planning; both preserve the existing composition.
- The exact reserved JSONB marker names and the internal DTO projection helper
  are implementation details. The top-level typed `handoff` contract and
  no-migration requirement are not optional.
- A completed consultation cannot accept a new chat message under Feature 003;
  therefore completed/booked mapping is primarily a reload/current-state
  projection, while a pending booking request is the normal trigger.
- There is no existing per-consultation appointment route. The approved
  already-booked target is the existing `/appointments` list; adding a detail
  route is out of scope.
- If later implementation inspection finds a persisted-message contract
  incompatibility with reserved markers, work must stop for an architecture
  decision rather than weakening validation or adding an unapproved schema
  change.

## 23. Definition of Done

Feature 008 is ready for implementation planning only when this specification
is approved and the repository findings above remain true. After
implementation, it is complete only when the typed handoff, lifecycle mapping,
chat CTA, reload semantics, safe fallbacks, integration continuity, and
Features 001–007 regression suite satisfy this document.

No plan, task files, migrations, Feature 009 work, or product-code changes are
authorized by this specification-only stage.

## Implementation Tasks

- [x] ABH-001 — Confirm Feature 008 Integration Boundaries
- [x] ABH-002 — Add Provider-Neutral Booking Intent Classifier
- [x] ABH-003 — Add Typed Booking Handoff and Persistence Markers
- [x] ABH-004 — Add Frontend Handoff Types and Runtime Validation
- [x] ABH-005 — Integrate Authoritative Handoff Evaluation into Message Workflow
- [x] ABH-006 — Update AI Wording Guidance and Message API Projection
- [x] ABH-007 — Add Functional Booking Handoff CTA to Consultation Chat
- [x] ABH-008 — Verify Reload and Current-State Handoff Projection
- [x] ABH-009 — Verify Cross-Feature Booking Handoff Integration and Regressions
- [x] ABH-010 — Verify Feature 008 Final Vertical Slice
