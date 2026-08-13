# AI Consultation / Persistent Conversation Feature Specification

## 1. Purpose

Define the AI-assisted conversation experience within an existing consultation.
The feature lets a user reopen a consultation, see its persisted conversation,
submit messages, receive AI-generated responses, and continue the interaction
across multiple messages.

This feature follows Consultation Records in the approved flow:

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

- persisted user and assistant messages associated with an existing
  consultation;
- ordered conversation-history retrieval from PostgreSQL;
- submission of one textual user message at a time;
- AI response generation through the approved AI service, consultation agent,
  consultation skill, LangChain, and provider boundaries;
- real OpenAI integration for the feature's runtime, configured only in the
  backend;
- an assistant response containing text and, when useful, an optional structured
  payload;
- continued multi-message interaction using relevant persisted conversation
  context; and
- explicit, safe behavior when validation, persistence, or AI generation fails.

The existing Consultation Detail experience shall host the conversation UI.
PostgreSQL, accessed through the backend, shall remain the source of truth for
conversation state.

## 3. Out of Scope

This feature does not implement:

- consultation creation, editing, deletion, or status transitions;
- recommendation table or lifecycle changes;
- appointment table changes or appointment creation;
- consultation summary persistence or summary generation;
- RAG, embeddings, vector storage, or external knowledge retrieval;
- LangGraph, multiple agents, autonomous tool execution, or dynamic workflow
  branching;
- unlimited conversation-history transmission to the provider;
- a sophisticated or arbitrary structured-response schema; or
- a user-facing provider selector or mock-AI runtime mode.

The approved mock-provider capability remains available at the AI abstraction
boundary for architecture compatibility and deterministic testing; it is not a
required user-facing mode for this feature.

## 4. User Outcomes and Acceptance Criteria

The feature is complete when all of the following are true:

- A user can open an existing consultation and see its persisted conversation
  in chronological order.
- Refreshing or reopening the consultation restores the same persisted message
  history from PostgreSQL.
- A user can submit a valid textual message from the Consultation Detail view.
- The submitted user message is persisted before AI generation is attempted.
- The AI receives relevant context reconstructed from persisted messages and
  returns an assistant response through the approved AI abstraction.
- A successful assistant response is persisted and returned to the frontend,
  which renders the updated conversation in order.
- The user can repeat this interaction for multiple messages without relying on
  browser state or in-memory LangChain memory as authoritative state.
- Assistant output can contain required text and an optional structured payload
  that the frontend can render safely when present.
- If AI generation fails after the user message is persisted, that user message
  remains retrievable, no fabricated assistant message is stored, and the user
  receives a safe, recoverable failure state.
- OpenAI credentials and provider-specific details remain outside React, API
  routes, response bodies, and client-visible errors.
- Automated tests are deterministic and require neither live OpenAI calls nor
  real OpenAI credentials.

## 5. Conversation Data and Persistence Requirements

Feature 002 introduces only the message persistence needed for the approved
`consultation → messages (1:N)` relationship.

Each persisted message shall conceptually contain:

| Field | Requirement |
| --- | --- |
| `id` | Stable message identifier. Its storage representation is an implementation decision. |
| `consultation_id` | Required linkage to one existing consultation. |
| `role` | Required participant role: `USER` or `ASSISTANT`. |
| `content` | Required textual message content. |
| `structured_payload` | Optional JSON-compatible assistant data for simple insights, tabular data, or extracted information. It shall be absent for user messages. |
| `created_at` | Required creation/order timestamp used with a deterministic tie-breaker to preserve conversation order. |

PostgreSQL shall be authoritative for messages and their ordering. Message
access shall remain behind a focused repository boundary; SQLAlchemy models,
schema types, indexes, constraints, and Alembic operations are implementation
planning decisions.

Persisted assistant data shall always include textual content. The optional
structured payload supplements rather than replaces that text. Its content
shall be treated as AI-generated data, not as authorization to perform
deterministic business operations.

This feature shall not add or change recommendation, appointment, or summary
persistence.

## 6. Required Conversation Flow

For a valid message submission, the system shall perform this conceptual flow:

```text
User submits message
       ↓
validate consultation and input
       ↓
persist user message
       ↓
load relevant persisted conversation context
       ↓
invoke AI service and consultation agent
       ↓
OpenAI generates response
       ↓
persist assistant response
       ↓
return persisted messages to frontend
       ↓
frontend renders updated conversation
```

The application service shall control this workflow. Flask routes shall not
coordinate persistence and AI calls directly.

If the consultation does not exist or input is invalid, no message shall be
persisted and AI shall not be invoked. If persisting the user message fails, AI
shall not be invoked and the request shall fail safely.

If AI generation fails after the user message is persisted:

- the persisted user message shall remain part of the authoritative history;
- no assistant success message or invented fallback response shall be
  persisted;
- the API shall return a client-safe AI-generation failure outcome that makes
  clear the user message was accepted and persisted; and
- the frontend shall reconcile with backend history and present a recoverable
  error without removing the user's persisted message.

If assistant-response persistence fails, the API shall not report a successful
completed exchange. On reload, only messages confirmed by PostgreSQL shall be
shown. Exact transaction and retry mechanics are deferred to implementation
planning.

## 7. API Contract

The feature shall extend the versioned consultation API with:

| Method and path | Purpose |
| --- | --- |
| `GET /api/v1/consultations/{consultation_id}/messages` | Retrieve the consultation's persisted conversation in chronological order. |
| `POST /api/v1/consultations/{consultation_id}/messages` | Persist one user message, generate and persist its assistant response, and return the completed exchange. |

### 7.1 Conversation retrieval

A successful retrieval response shall contain an `items` array of explicit
message DTOs. A consultation with no messages returns an empty array. A missing
consultation returns `404` rather than an empty conversation.

Each item shall have this conceptual shape:

```json
{
  "id": "message identifier",
  "consultation_id": "consultation identifier",
  "role": "ASSISTANT",
  "content": "Assistant response text",
  "structured_payload": null,
  "created_at": "timestamp"
}
```

### 7.2 Message submission

The submission request shall contain one non-blank textual `content` value.
The backend shall trim and validate input and shall define a reasonable bounded
length during implementation planning.

A successful response shall return the persisted `user_message` and
`assistant_message`, using the message representation above. Returning both
messages allows the frontend to reconcile temporary submission state with the
backend's authoritative identifiers and ordering.

When AI generation fails after user-message persistence, the error response
shall use the project's consistent error format and include the persisted
`user_message` representation as safe recovery data. It shall not include raw
provider output, provider error details, credentials, prompts, or stack traces.

### 7.3 Validation and errors

Path and request data shall be validated with Pydantic DTOs at the API
boundary. The API shall provide consistent, client-safe outcomes for:

- `400` when the message input or consultation identifier is invalid;
- `404` when the consultation does not exist;
- an appropriate recoverable upstream-service error when AI generation is
  unavailable or fails after user-message persistence; and
- `500` for unexpected server or persistence failures.

The exact upstream error status within the established API conventions is an
implementation-planning decision. Provider-specific errors shall never pass
through directly. DTOs shall not expose SQLAlchemy models, database sessions,
LangChain objects, or provider SDK types.

## 8. Backend Responsibilities

### Flask API layer

The Flask API shall own route registration, HTTP parsing, Pydantic validation,
response serialization, and translation of known application outcomes into the
specified client-safe responses. Routes shall call the consultation application
service and shall not manipulate persistence or invoke AI components directly.

### Consultation application service

The consultation application service shall validate the consultation's
existence, coordinate message persistence and retrieval, reconstruct ordered
conversation context, call the AI service, persist successful assistant output,
and expose deterministic success and failure outcomes to the API layer. It
shall not depend on Flask, LangChain, provider SDKs, or SQLAlchemy session
details.

### Message repository

A focused message repository shall persist user and assistant messages and
retrieve messages for one consultation in deterministic conversation order.
Its PostgreSQL/SQLAlchemy implementation belongs to infrastructure. The
repository shall not own AI orchestration or frontend/API concerns.

## 9. AI Layer Responsibilities

### AI Service

The AI service shall accept application-facing consultation input and relevant
persisted conversation context, coordinate AI execution, and return a
provider-neutral result containing assistant text plus an optional structured
payload. It shall translate provider/agent failures into safe AI-boundary
outcomes and shall not persist messages or depend on Flask.

### Consultation Agent

One consultation agent shall coordinate the AI-assisted interaction. It shall
use the consultation skill and approved LangChain-contained orchestration to
produce a response from the supplied context. It shall not autonomously create
appointments, change consultation status, or perform out-of-scope business
operations.

### Consultation Skill

The consultation skill shall provide focused consultation-oriented AI behavior
and shape the response expected by the agent. It may produce helpful text and
simple structured data, but shall not introduce RAG, autonomous tools, summary
persistence, or recommendation/appointment workflows.

### Conversation context

Relevant AI context shall be reconstructed from persisted messages for the
consultation. LangChain or process memory may assist within a single execution
but shall never replace PostgreSQL as the authoritative conversation state.

The feature does not require unlimited history. If the provider context window
requires selection, truncation, or another context-management policy, the plan
shall define a deterministic approach that retains PostgreSQL history without
changing what is persisted.

## 10. OpenAI Provider and Configuration

The deployed runtime for this feature shall use the real OpenAI provider behind
the approved provider abstraction. The backend environment shall supply:

```text
OPENAI_API_KEY
```

The key is a server-side secret. It shall not be committed, returned by an API,
placed in frontend environment variables, bundled into React, or logged.
Provider construction and credential access shall remain at backend
configuration/composition boundaries.

OpenAI SDK calls, model identifiers, timeout values, retry mechanisms, and HTTP
implementation details are deferred to implementation planning. Network,
authentication, rate-limit, malformed-output, and other provider failures shall
be converted to the safe failure behavior defined by this specification.

Provider-specific logic shall not leak into Flask routes, application-facing
DTOs, frontend services, or React components.

## 11. Frontend Responsibilities

The Consultation Detail frontend feature shall own:

- loading persisted conversation history through its dedicated consultation
  API/service module;
- rendering user and assistant messages in backend-provided order;
- an empty-conversation state;
- a text-entry control and submission action with clear validation feedback;
- a pending state that prevents unintended duplicate submissions while an
  exchange is in progress;
- reconciliation of successful responses using persisted message data;
- safe rendering of assistant text and supported optional structured data;
- a recoverable error state that retains or reloads a user message persisted
  before AI failure; and
- safe loading, missing-consultation, retrieval-error, and submission-error
  states.

Temporary input and pending UI state may remain in React, but persisted history
shall always be loaded from or reconciled with the backend. Components shall
communicate through the dedicated frontend service rather than making direct
HTTP calls. React shall not access OpenAI, LangChain, provider credentials, or
provider-specific response types.

Exact layout and supported visual presentations of the simple structured
payload are implementation-planning decisions and shall use the approved React,
TypeScript, and MUI stack.

## 12. Testing Requirements

No automated test shall require a live OpenAI request, external network access,
or real `OPENAI_API_KEY`. Tests shall use deterministic provider or AI-service
test doubles at the approved AI boundary, including the architecture-required
mock provider where appropriate.

### Backend and AI tests (Pytest)

- Conversation retrieval returns only the selected consultation's messages in
  deterministic order, including an empty conversation.
- A valid submission persists the user message before invoking the AI boundary.
- Persisted conversation context is supplied to the AI boundary across multiple
  messages.
- A successful AI result persists and returns assistant text and optional
  structured data.
- Invalid input and missing consultations do not persist messages or invoke AI.
- User-message persistence failure does not invoke AI.
- AI failure after user-message persistence retains that message, persists no
  assistant message, and returns the specified safe recovery outcome.
- Assistant-persistence failure is not reported as a successful exchange.
- Provider failures are translated without exposing secrets or implementation
  details.
- AI-layer tests verify provider abstraction, agent/skill coordination, and a
  deterministic structured result without live OpenAI.

### Frontend tests (React Testing Library)

- Consultation Detail renders backend-provided history in order and renders an
  empty-conversation state.
- A valid message can be submitted through the dedicated API/service boundary.
- Pending and successful exchange states are understandable, and persisted
  user/assistant messages are rendered after success.
- Blank input is rejected with clear feedback.
- Retrieval, missing-consultation, and submission failures are presented safely.
- An AI failure that follows user-message persistence keeps or restores the
  persisted user message and allows recovery without displaying a fabricated
  assistant response.
- Supported structured assistant data is rendered safely when present, while
  text-only responses continue to work.

### Persistence and integration tests

- Messages remain linked to the correct consultation and survive a fresh
  repository/API retrieval.
- Multi-message ordering is stable after reopening the consultation.
- The core submission path crosses API, application, persistence, and a
  deterministic AI double while preserving the specified state outcomes.
- Docker Compose compatibility remains intact.

Relevant backend tests, frontend tests, linting, and type checks shall pass
before implementation is considered complete.

## 13. Dependencies and Follow-on Features

This feature depends on the approved project foundations, AI/provider
architecture, and Feature 001's persisted consultation and Consultation Detail
experience. It introduces only conversation-message persistence and the
AI-assisted exchange required here.

Later features shall define recommendation generation, consultation summaries,
appointments, and dashboard metrics independently. They shall not be inferred
from the optional structured payload or implemented as side effects of this
conversation.

## 14. Definition of Done

Implementation of an approved version of this specification is done when the
Consultation Detail UI, Flask API, consultation application service, message
repository, AI service, consultation agent/skill, LangChain-contained OpenAI
provider, and PostgreSQL persistence jointly satisfy all acceptance criteria;
failure outcomes preserve authoritative conversation state; automated tests are
deterministic without live OpenAI; secrets remain backend-only; and the complete
vertical slice runs with the approved Docker Compose stack without adding
out-of-scope technologies or data models.

## 15. Implementation Tasks

- [x] AI-001 — Confirm AI Consultation Integration Boundaries
- [x] AI-002 — Add Persistent Consultation Messages
- [x] AI-003 — Add Consultation Message Repository
- [x] AI-004 — Add AI Service, Consultation Agent, Skill, and Providers
- [x] AI-005 — Add Persistent Conversation Application Workflow
- [x] AI-006 — Expose Consultation Message API
- [x] AI-007 — Extend Frontend Consultation Conversation Service
- [x] AI-008 — Implement Persistent AI Conversation UI
- [x] AI-009 — Verify AI Consultation Vertical Slice
