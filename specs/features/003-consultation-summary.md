# Consultation Summary Feature Specification

## 1. Purpose

Define the Consultation Summary feature for the AI Consultation Platform. The
feature lets a user complete an eligible persistent AI consultation, generate
and revisit a PostgreSQL-backed summary, review stable treatment
recommendations, restart the consultation as a new conversation, or navigate
toward booking an appointment for one recommendation.

This feature follows Persistent AI Consultation in the approved flow:

```text
Consultation Records
       ↓
AI Consultation
       ↓
Consultation Summary
       ↓
Appointment
       ↓
Dashboard metrics
```

## 2. Scope

The feature shall provide:

- explicit eligibility rules for completing a persistent conversation;
- AI generation of a patient summary, one or more recommended treatments, and
  an optional concise recommendation rationale;
- PostgreSQL persistence and later retrieval of one authoritative summary per
  consultation;
- stable persisted recommendation identifiers and ordering suitable for later
  appointment linkage;
- idempotent summary generation and safe retry behavior;
- a Consultation Summary experience reached from Consultation Detail;
- a `Restart Consultation` action that creates a new consultation while
  preserving the completed consultation, its messages, and its summary; and
- a `Book Appointment` action that crosses only the frontend navigation
  boundary for a selected persisted recommendation.

Summary data displayed by React shall come through the Flask API and dedicated
frontend consultation service. AI execution shall remain behind the existing
backend AI service, consultation agent/skill, LangChain, and provider
abstraction.

## 3. Out of Scope

This feature does not implement:

- appointment persistence, creation, confirmation, or lifecycle rules;
- appointment date, time, location, provider, or availability selection;
- a `BOOKED` status transition;
- dashboard screens or metrics;
- editing, deleting, regenerating, or versioning a persisted summary;
- editing or deleting recommendations;
- resuming message submission on a completed consultation;
- automatic completion based only on message count, provider wording, or an
  AI-produced structured payload;
- RAG, embeddings, vector storage, Redis, LangGraph, multiple agents,
  autonomous tools, WebSockets, or streaming; or
- diagnosis, emergency triage, or a representation that AI recommendations
  are confirmed medical prescriptions.

The appointment destination and its behavior belong to a later feature. This
feature defines only the navigation handoff described in §12.3.

## 4. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- A user with an eligible persistent conversation can request its summary from
  Consultation Detail.
- Summary generation uses the consultation and its complete persisted message
  history as authoritative input through the existing AI abstraction.
- A successful result is validated and persisted before the consultation is
  considered `COMPLETED` or success is returned to the frontend.
- The summary presents a non-blank patient summary, at least one ordered
  recommended treatment, and an optional concise rationale when one was
  generated.
- Each recommended treatment has a stable persisted identifier that remains
  unchanged across reloads and repeated generation requests.
- Refreshing, reopening, or directly navigating to the summary retrieves the
  same persisted summary without invoking AI again.
- Repeating a generation request for a consultation that already has a summary
  returns that summary and creates neither another summary nor duplicate
  recommendations.
- An ineligible, missing, or already completed consultation cannot start a new
  summary-generation operation with unintended writes or AI execution.
- Validation, AI, and persistence failures produce safe, recoverable states;
  failed attempts do not mark the consultation `COMPLETED` or expose a partial
  summary.
- `Restart Consultation` creates and navigates to a distinct `PENDING`
  consultation with no messages or summary, while the source consultation and
  all of its history remain unchanged and retrievable.
- `Book Appointment` requires a selected persisted recommendation and navigates
  with the consultation and recommendation identifiers without creating an
  appointment or changing consultation status.
- Automated tests are deterministic and require no live OpenAI request or real
  OpenAI credential.

## 5. Summary Eligibility and Completion Semantics

### 5.1 Eligibility

A consultation is eligible for initial summary generation only when all of the
following are true at the application boundary:

- the consultation exists;
- its status is `PENDING`;
- it has at least one persisted `USER` message and at least one persisted
  `ASSISTANT` message; and
- its latest persisted message in Feature 002's deterministic
  `(created_at, id)` order has role `ASSISTANT`.

The latest-assistant rule means every submitted user message has received a
persisted assistant response. A retained user message from a failed AI exchange
therefore makes the conversation ineligible until a later successful exchange
again leaves an assistant message last. Eligibility does not depend on browser
state, message wording, an AI-declared completion flag, or a minimum number of
turns beyond one completed exchange.

`BOOKED` consultations are ineligible for initial generation because this
feature does not redefine or reverse the appointment lifecycle. A `COMPLETED`
consultation with a persisted summary is retrievable but is not regenerated. A
`COMPLETED` consultation without a summary is an inconsistent state and shall
fail safely rather than invoke AI or fabricate summary data.

### 5.2 Completion boundary

The user's summary-generation request is the explicit intent to complete the
conversation. The consultation transitions from `PENDING` to `COMPLETED` only
in the same successful database transaction that persists its validated
summary and recommendations.

No status change occurs when input is ineligible, AI generation fails, AI
output is invalid, or summary persistence fails. Once completed, the
consultation's messages and summary are immutable in this feature, and new
messages shall not be accepted for that consultation. The existing Feature 002
message-submission path shall enforce this completed-conversation boundary when
this specification is implemented.

## 6. Summary and Recommendation Data Requirements

Feature 003 introduces one summary per consultation and one or more ordered
recommendations per summary:

```text
consultation 1 ─── 0..1 consultation summary
consultation summary 1 ─── 1..N recommendations
```

### 6.1 Consultation summary

| Field | Requirement |
| --- | --- |
| `id` | Stable summary identifier. Its storage representation is an implementation decision. |
| `consultation_id` | Required unique linkage to the summarized consultation. |
| `patient_summary` | Required non-blank plain text grounded in the persisted consultation conversation. |
| `recommendation_rationale` | Optional concise plain text explaining the recommendations collectively. Absence is represented as `null`. |
| `created_at` | Required timestamp recording successful persistence. |

### 6.2 Recommendation

| Field | Requirement |
| --- | --- |
| `id` | Stable recommendation identifier intended to support later appointment linkage. |
| `summary_id` | Required linkage to one persisted consultation summary. |
| `treatment` | Required non-blank recommended-treatment text. |
| `position` | Required deterministic display order, unique within the summary. |

PostgreSQL shall be authoritative for summaries, recommendations, identifiers,
ordering, and completion state. Access shall remain behind focused repository
boundaries; SQLAlchemy mappings, constraints, indexes, and Alembic operations
are implementation-planning decisions.

The existing consultation `recommended_procedure` field was defined by Feature
001 as display-only compatibility data. On first successful summary creation,
the application shall deterministically set it to the first ordered persisted
recommendation's treatment in the same transaction. The recommendation row and
its identifier remain the authoritative recommendation for later linkage; the
consultation field remains a list/detail display projection and shall not be
used as an appointment foreign key.

## 7. Required Summary Flow

For an eligible initial generation request, the system shall perform this
conceptual flow:

```text
User requests summary
       ↓
validate consultation and eligibility
       ↓
load complete persisted conversation
       ↓
invoke AI through the existing abstraction
       ↓
validate provider-neutral structured summary result
       ↓
atomically persist summary + ordered recommendations
       ↓
set recommended-procedure projection + COMPLETED status
       ↓
return persisted summary to frontend
```

The consultation application service shall coordinate the workflow. Flask
routes shall not coordinate repositories, transactions, or AI calls directly.
The provider shall receive the complete persisted conversation for this
summary operation; Feature 002's bounded interactive-response context does not
define the summary input. If a practical provider limit is required, the plan
must define a deterministic, explicit failure or loss-aware strategy without
altering or silently discarding PostgreSQL history.

AI output shall be provider-neutral structured data containing patient summary
text, a non-empty ordered collection of treatment texts, and nullable rationale
text. Empty required text, no recommendations, unsupported shapes, or output
that cannot be validated shall be treated as AI-generation failure. AI output
shall not directly mutate persistence or consultation status.

## 8. Idempotency, Concurrency, and Retry Behavior

Summary generation is create-once per consultation:

- Before AI invocation, the application shall retrieve and return an existing
  persisted summary when one exists.
- Repeated sequential requests shall return `200` with the same persisted
  identifiers and values and shall not invoke AI again.
- Persistence shall enforce the one-summary-per-consultation invariant.
- Concurrent initial requests may perform redundant AI calls, but only one
  complete summary can be committed. A request that loses the creation race
  shall discard its unpersisted result, reload the winning persisted summary,
  and return it successfully.
- No partial summary or recommendation collection shall become visible. The
  summary, all recommendations, projection update, and `COMPLETED` transition
  succeed or roll back together.
- An AI failure occurs before summary persistence and leaves the consultation
  eligible for an explicit user retry.
- An unexpected persistence failure returns a safe failure; a retry first
  checks PostgreSQL and therefore returns a committed result if the previous
  outcome was ambiguous.

This feature does not persist generation attempts, provider requests, draft
summaries, idempotency tokens, or background jobs.

## 9. API Contract

The feature shall extend the versioned consultation API with:

| Method and path | Purpose |
| --- | --- |
| `GET /api/v1/consultations/{consultation_id}/summary` | Retrieve the consultation's persisted summary. |
| `POST /api/v1/consultations/{consultation_id}/summary` | Idempotently generate and persist the consultation summary. |
| `POST /api/v1/consultations/{consultation_id}/restart` | Create a new consultation derived from the completed source consultation. |

### 9.1 Summary representation

Successful GET and POST summary responses shall use the same explicit shape:

```json
{
  "id": "summary identifier",
  "consultation_id": "consultation identifier",
  "patient_summary": "Concise summary of the patient's conversation",
  "recommended_treatments": [
    {
      "id": "recommendation identifier",
      "treatment": "Recommended treatment",
      "position": 1
    }
  ],
  "recommendation_rationale": "Optional concise rationale",
  "created_at": "timestamp"
}
```

Recommendations shall be returned in ascending persisted `position` order.
`recommendation_rationale` shall be `null` when absent. SQLAlchemy models,
provider output, prompts, and LangChain or SDK types shall not appear in the
contract.

### 9.2 Retrieval and generation outcomes

- GET returns `200` for a persisted summary.
- GET returns `404` when the consultation does not exist.
- GET returns `409` with stable code `SUMMARY_NOT_AVAILABLE` when the
  consultation exists but no summary has been persisted.
- POST returns `201` when this request creates the summary.
- POST returns `200` with the persisted summary when it already exists or when
  a concurrent request committed it first.
- POST returns `409` with stable code `SUMMARY_NOT_ELIGIBLE` when an existing
  consultation fails the initial-generation eligibility rules.
- POST returns `503` with stable code `SUMMARY_GENERATION_FAILED` when AI is
  unavailable or produces invalid output.

### 9.3 Restart request and response

Restart accepts no request data. It is allowed only for a `COMPLETED`
consultation with a persisted summary. A successful request creates a distinct
consultation that:

- has a new stable identifier;
- copies `patient_name` and `primary_concern` from the source;
- has status `PENDING`;
- has an empty `recommended_procedure` display projection until its own summary
  is successfully generated; and
- has no copied messages, summary, or recommendations.

The successful response shall return the standard consultation response DTO
with status `201`. Each successful restart request represents a new explicit
consultation; the API shall not automatically retry it, and the frontend shall
disable duplicate activation while the request is pending. The source record,
messages, summary, recommendations, status, and identifiers remain unchanged.

Restart returns `404` for an absent consultation and `409` with stable code
`CONSULTATION_NOT_RESTARTABLE` when the source does not meet the completed
summary condition.

### 9.4 Validation and errors

Path data shall be validated with Pydantic DTOs at the API boundary. The API
shall use the project's client-safe error envelope and provide:

- `400` for an invalid consultation identifier or invalid request body;
- the specified `404`, `409`, and `503` feature outcomes; and
- `500` for unexpected server or persistence failures.

Stable `code` values shall accompany the specified `409` and `503` outcomes so
the frontend need not infer business state from display text. Errors shall not
expose partial AI output, provider/model details, prompts, credentials,
exceptions, persistence details, or stack traces.

## 10. Backend Responsibilities

### Flask API layer

The Flask API shall own route registration, HTTP parsing, Pydantic validation,
response serialization, and translation of known application outcomes. Routes
shall delegate to the consultation application service and shall not access
repositories, SQLAlchemy sessions, or AI components directly.

### Consultation application service

The application service shall coordinate eligibility, authoritative history
retrieval, existing-summary checks, AI execution, result validation, atomic
summary persistence, completion, idempotency/concurrency recovery, and restart
creation. It shall expose deterministic outcomes to the API and shall not
depend on Flask, provider SDKs, LangChain internals, or React navigation.

### Repositories and infrastructure

Focused repository capabilities shall retrieve and atomically persist the
summary aggregate and its recommendations, enforce create-once behavior, update
the consultation projection/status, and create the new restart consultation.
Message history shall continue through the Feature 002 repository boundary.
Infrastructure shall not invoke AI or decide HTTP/frontend behavior.

## 11. AI Layer Responsibilities

The existing AI service, consultation agent/skill, LangChain-contained
orchestration, and provider abstraction shall be extended with a focused
summary-generation operation. Its application-facing result shall contain only
validated provider-neutral summary data.

The summary instructions shall use the supplied consultation context and
ordered messages, produce plain text suitable for safe rendering, distinguish
patient-reported information from recommendations, avoid unsupported certainty
or claims that an appointment was booked, and keep the optional rationale
concise. They shall not perform persistence, status transitions, appointment
creation, RAG, tool calls, or autonomous workflow branching.

`MockAIProvider` or deterministic AI-service doubles shall support repeatable
summary tests. Real OpenAI configuration remains server-only under the existing
composition boundary.

## 12. Frontend Responsibilities

The existing consultation frontend feature and dedicated API/service module
shall own summary request/response translation, runtime DTO validation, and
safe feature-facing error types. React components shall not call HTTP, OpenAI,
or LangChain directly.

### 12.1 Consultation Detail completion action

Consultation Detail shall expose a clear summary action only when the loaded
consultation and conversation state can be eligible. The backend remains
authoritative: frontend visibility or disabling is guidance, not enforcement.
While generation is pending, duplicate activation shall be disabled. A success
shall navigate to or render the persisted Consultation Summary experience.

### 12.2 Consultation Summary experience

The summary experience shall:

- retrieve persisted summary data on direct load or refresh;
- render patient summary, ordered recommended treatments, and optional
  rationale using React, TypeScript, and MUI;
- render all AI text as plain text rather than injected HTML;
- provide distinct loading, not-available/ineligible, recoverable-generation,
  missing-consultation, and unexpected-error states; and
- provide the two required actions after a persisted summary is loaded.

Exact visual layout and summary route naming are implementation-planning
decisions.

### 12.3 Action boundaries

`Restart Consultation` shall call the restart endpoint once, prevent duplicate
activation while pending, and navigate to the returned new consultation's
existing detail route. It shall not clear local history as a substitute for
backend creation and shall not alter the source consultation.

The user shall select one persisted recommended treatment before activating
`Book Appointment`. The action shall navigate to the later appointment-entry
boundary carrying both `consultation_id` and the selected recommendation `id`.
The exact route syntax is deferred to implementation planning, but the handoff
shall use stable identifiers rather than treatment text or transient React
state. This feature shall not call an appointment API, persist appointment
data, or change status to `BOOKED`. Until the appointment feature owns the
destination, navigation may reach a route-level unavailable placeholder; that
placeholder is not an appointment implementation.

## 13. Testing Requirements

No automated test shall require a live OpenAI request, external network access,
or real `OPENAI_API_KEY`.

### Backend and AI tests (Pytest)

- Eligibility accepts a `PENDING` consultation ending in an assistant message
  after at least one completed exchange and rejects every other specified
  status/history combination without AI invocation.
- Summary AI receives the consultation context and complete persisted ordered
  conversation through the approved abstraction.
- Valid structured AI output is normalized, atomically persisted, returned in
  recommendation order, updates the display projection, and transitions the
  consultation to `COMPLETED`.
- Empty or malformed required AI output and provider failure persist no
  summary/recommendations and do not change status or projection.
- Retrieval returns the same persisted summary and stable recommendation IDs.
- Sequential repeated POST requests do not reinvoke AI or duplicate data.
- Concurrent creation resolves to one persisted summary aggregate and both
  callers observe its stable values.
- Persistence failure exposes no partial aggregate or false completion, and a
  retry reconciles with PostgreSQL.
- Completed consultations reject new Feature 002 message submissions.
- Restart creates only the specified fresh `PENDING` consultation data and
  preserves all source data; absent and ineligible sources fail safely.
- API tests verify DTOs, `200`/`201`, `400`, `404`, coded `409`, coded `503`,
  safe `500`, and absence of sensitive provider/persistence details.

### Frontend tests (React Testing Library)

- Consultation Detail presents the eligible summary action, prevents duplicate
  generation, and handles success and each safe failure outcome through the
  dedicated service.
- Direct summary loading renders persisted patient summary, ordered treatments,
  nullable rationale, and stable selection values.
- Loading, summary-not-available, ineligible, missing-consultation,
  generation-failure, and unexpected-error states are clear and recoverable.
- Restart sends one request, disables duplicate activation, and navigates using
  the returned consultation identifier without removing source data locally.
- Booking requires a recommendation selection and navigates with both stable
  identifiers without calling an appointment API or changing status.
- Summary text is rendered safely and no provider details or credentials are
  displayed.

### Persistence and integration tests

- A deterministic conversation crosses API, application, message repository,
  AI double, summary repository, and PostgreSQL to produce one reloadable
  completed summary aggregate.
- Transaction rollback, repeated requests, and a controlled concurrent request
  prove atomic create-once behavior.
- Restarted and source consultations remain independent and retrievable.
- Feature 001 record/detail behavior and Feature 002 persistent history remain
  intact, with completed-message submission restricted as specified.
- Docker Compose compatibility remains intact.

Relevant backend tests, frontend tests, linting, type checks, build checks, and
vertical-slice verification shall pass before implementation is considered
complete.

## 14. Dependencies and Follow-on Features

This feature depends on Feature 001's persisted consultations and approved
status values, Feature 002's ordered persistent messages and AI abstraction,
and the completed Docker Compose foundation. It adds only summary,
recommendation, completion, restart, and navigation-boundary behavior defined
here.

The later Appointment feature may link an appointment to the stable persisted
recommendation identifier and may define its own `BOOKED` transition. It shall
own appointment validation, persistence, scheduling fields, routes, screens,
and lifecycle rules. Dashboard work shall independently define its metrics and
queries.

## 15. Assumptions and Resolved Ambiguities

- `COMPLETED` means that a validated summary aggregate has been successfully
  persisted; no separate conversation-completion status is introduced.
- Requesting generation is the explicit completion action. No additional
  “finish conversation” endpoint or AI-detected completion flag is required.
- One completed user/assistant exchange is the minimum sufficient history;
  the backend does not attempt to judge clinical sufficiency.
- One immutable summary per consultation is the smallest lifecycle compatible
  with stable recommendation linkage and idempotent retries.
- Recommendation rationale is one optional summary-level explanation rather
  than separate rationale text for every treatment.
- Restart means creating a new consultation, not deleting messages, clearing
  the source, reverting `COMPLETED`, or appending to the old conversation.
- The restarted consultation intentionally has an empty compatibility
  `recommended_procedure` value until its own successful summary. Changing that
  legacy field's nullability is not required by this specification.
- Restart requests are intentional creates rather than idempotent retries; the
  client must not automatically retry and must prevent duplicate activation.
- Booking handoff requires one selected stable recommendation but implements no
  appointment behavior. Exact frontend route syntax remains for the plan after
  this specification is approved.
- Authentication, authorization, patient identity reconciliation, audit logs,
  retention rules, and clinical review workflows remain governed by future
  requirements and are not introduced here.

No unresolved product or architecture decision blocks planning. Provider input
limits, exact database types/constraints, transaction implementation, module
placement, and frontend route syntax are deliberately deferred to the Feature
003 implementation plan.

## 16. Definition of Done

Implementation of an approved version of this specification is done when the
Consultation Detail completion action, Consultation Summary experience, Flask
API, application workflow, focused repositories, existing AI abstraction,
PostgreSQL summary/recommendation persistence, restart action, and booking
navigation boundary jointly satisfy every acceptance criterion; summaries are
atomic, create-once, reloadable, and linked to stable recommendations;
conversation history and prior-feature behavior are preserved; automated tests
remain deterministic without live OpenAI; and the complete vertical slice runs
with Docker Compose without introducing appointment persistence, `BOOKED`
transition, dashboard work, or other out-of-scope technologies.

## 17. Implementation Tasks

- [x] CS-001 — Confirm Feature 003 Integration Boundaries
- [x] CS-002 — Add Summary and Recommendation Persistence
- [x] CS-003 — Add Summary Aggregate Repository
- [x] CS-004 — Extend AI Abstraction for Consultation Summaries
- [x] CS-005 — Add Consultation Summary Application Workflows
- [x] CS-006 — Expose Consultation Summary and Restart APIs
- [x] CS-007 — Extend Frontend Consultation Summary Service
- [x] CS-008 — Add Consultation Detail Completion Behavior
- [x] CS-009 — Add Consultation Summary Screen and Navigation Boundaries
- [x] CS-010 — Verify Consultation Summary Vertical Slice
