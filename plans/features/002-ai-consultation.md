# AI Consultation Implementation Plan

## 1. Objective

Implement the approved persistent, multi-message AI consultation vertical slice
inside the existing Consultation Detail experience:

```text
React Consultation Detail
        ↓
consultation feature API/service
        ↓
Flask consultation blueprint + Pydantic DTOs
        ↓
ConsultationApplicationService
        ↓
MessageRepository + PostgreSQL history
        ↓
AIService → ConsultationAgent → ConsultationSkill
        ↓
LangChain → configured AI provider
```

PostgreSQL remains authoritative for every message. The implementation will
extend Feature 001's UUID, SQLAlchemy session, repository, application-service,
Pydantic error, blueprint, feature-local frontend service, React Router, and MUI
conventions. It will not modify Feature 001 behavior or introduce summary,
recommendation, appointment, RAG, tool, or multi-agent scope.

## 2. Current-System Alignment

Feature 002 will reuse these implemented conventions rather than establish a
parallel architecture:

- `create_app` is the composition boundary and creates one request-scoped
  SQLAlchemy session when dependencies are not injected.
- Consultation IDs are PostgreSQL UUIDs and are serialized as strings at the
  API/frontend boundaries.
- SQLAlchemy mappings share the infrastructure-owned declarative `Base`;
  PostgreSQL-native enums and Alembic revisions are already established.
- Focused repositories accept a SQLAlchemy session; the consultation
  application service owns orchestration without Flask dependencies.
- Consultation endpoints live on the existing `/api/v1` consultation
  blueprint, validate explicit Pydantic DTOs, and return client-safe JSON
  errors with an `error` field.
- The React feature is rooted at
  `frontend/src/app/features/consultation-records/`; its components call
  `consultationApi`, validate transport data into feature types, and render
  under `/consultations/:consultationId`.
- Pytest uses deterministic dependency doubles for boundary tests and a
  temporary PostgreSQL 16 container for persistence/integration tests. Vitest
  and React Testing Library use feature-service/transport doubles.

The repository currently has no Dockerfiles or Compose file even though the
approved foundation requires them. Feature 002 will keep all new dependencies
containerizable and will verify against Compose if that foundation is restored
during implementation; creating the missing general Docker foundation is not
part of this feature plan.

## 3. Specification Traceability

| Approved requirement | Planned responsibility | Verification focus |
| --- | --- | --- |
| Persisted ordered history per consultation | Message migration/mapping and focused repository | Foreign-key isolation, reload, `created_at`/`id` order |
| `GET` messages, including empty history and missing consultation | DTOs, consultation service, existing blueprint | `200` items, `404`, invalid UUID `400` |
| Persist user before AI and persist successful assistant output | Application workflow plus two repository commit boundaries | Call/commit order and persisted outcomes |
| Relevant persisted multi-message context | Deterministic bounded-tail selection in the application service | Exact ordered context over repeated messages |
| Safe AI and assistant-persistence failures | Typed application/AI outcomes and route translation | User retained, no fabricated assistant, no false success |
| AI service/agent/skill/LangChain/provider boundaries | Small `app/ai/` implementation | Coordination tests with deterministic doubles |
| OpenAI runtime with server-only credentials | Factory/configuration and OpenAI provider | No frontend/provider-detail leakage; no live calls in tests |
| Consultation Detail conversation UX | Existing frontend feature, service/types, MUI components | History, pending, recovery, structured data, all error states |
| PostgreSQL is authoritative | GET/reconciliation after every ambiguous failure | Refresh/reopen and integration coverage |

## 4. Persistence Design

Add only a `messages` table linked to the existing `consultations` table.

| Column | PostgreSQL / SQLAlchemy decision | Constraints and behavior |
| --- | --- | --- |
| `id` | Native UUID / `UUID`, generated with `uuid4` | Primary key, API string representation |
| `consultation_id` | Native UUID / `UUID` | Required foreign key to `consultations.id`; no delete cascade is introduced |
| `role` | Native enum `message_role` | Required; exactly `USER` or `ASSISTANT` |
| `content` | `TEXT` | Required; application/DTO boundary enforces trimmed, non-blank content |
| `structured_payload` | `JSONB` | Nullable; must be null for `USER`; assistant payload remains optional |
| `created_at` | Time-zone-aware `TIMESTAMP` | Required, server default `CURRENT_TIMESTAMP`, immutable in this feature |

Deterministic history order is ascending `(created_at, id)`. Add a composite
B-tree index on `(consultation_id, created_at, id)` to support the only history
query. Add a check constraint enforcing
`role != 'USER' OR structured_payload IS NULL`; assistant text remains required
through non-null `content` plus application-boundary validation. Do not add
recommendation, appointment, summary, sequence, edit, or deletion columns.

Create one Alembic revision directly after `20260813_01`. It will create the
`message_role` enum, table, foreign key, check constraint, and composite index;
its downgrade will remove them in reverse order. Extend the existing metadata
with a `Message` mapping and `MessageRole` enum. A SQLAlchemy relationship is
not required: repository queries will use the foreign key explicitly, avoiding
changes to Feature 001's consultation read behavior.

## 5. Message Repository and Transaction Boundaries

Add a focused `MessageRepository` beside the existing consultation repository.
It will contain persistence mechanics only:

- `persist_message(...)` adds one message, commits it, refreshes/returns the
  confirmed persisted row, and rolls back before re-raising on failure;
- `list_messages(consultation_id)` returns only that consultation's rows in
  ascending `(created_at, id)` order; and
- a bounded-history query may apply the same deterministic order/limit policy
  needed by the application service, but it will not decide semantic context or
  invoke AI.

The repository will use the same request-scoped session as
`ConsultationRepository`. Committing inside this focused persistence operation
is deliberate because the feature requires the user message to survive an AI
failure. The workflow therefore has two simple database units of work:

1. persist and commit the `USER` message;
2. after successful AI generation, persist and commit the `ASSISTANT` message.

No transaction is held open during the network call. There is no distributed
transaction, background retry, outbox, or fabricated fallback message.

## 6. Application Workflow

Extend `ConsultationApplicationService` with message retrieval and submission
while preserving its existing list/detail behavior. Inject the focused message
repository and provider-neutral AI service; tests may inject deterministic
doubles. Production factory composition supplies both.

### Retrieval

1. Retrieve the consultation by validated UUID and raise the existing
   application-level not-found outcome when absent.
2. Return that consultation's messages from the message repository in
   deterministic chronological order.

### Submission

For an API-validated message of at most **4,000 characters after trimming**:

1. Confirm the consultation exists.
2. Persist and commit the normalized `USER` message.
3. Reload relevant history from PostgreSQL, including that new user message.
4. Select provider context deterministically: take at most the newest 20 whole
   messages whose combined content is at most 24,000 characters, always retain
   the current user message, and restore chronological order before invoking
   AI. Older rows remain unchanged and retrievable from PostgreSQL.
5. Pass consultation context (identifier, primary concern, and existing
   display fields), ordered messages, and current interaction data to the AI
   service.
6. Validate the provider-neutral result: trimmed assistant text must be
   non-blank; its optional payload must be JSON-compatible.
7. Persist and commit the `ASSISTANT` message.
8. Return the two confirmed persisted messages.

DTO validation occurs before the service call. The service retains defensive
invariants so non-HTTP callers cannot persist blank/over-limit user or blank
assistant content.

### Failure boundaries

| Boundary | Required outcome |
| --- | --- |
| Invalid UUID/body or absent consultation | No message write and no AI call; route returns existing safe `400` or `404` form |
| User-message commit failure | Repository rolls back; AI is not called; safe `500` |
| AI failure after user commit | User row remains; no assistant row; typed recoverable application outcome carries the persisted user message |
| Invalid/malformed AI result | Treat as AI generation failure; retain user only and expose no raw output |
| Assistant-message commit failure | Roll back that failed unit only; do not report success; return safe `500` and have the frontend reload authoritative history |

The AI-failure route response will use **HTTP 503** and the existing error style
extended only with stable recovery data:

```json
{
  "error": "Assistant response is temporarily unavailable",
  "code": "AI_GENERATION_FAILED",
  "user_message": { "...": "persisted message DTO" }
}
```

It will contain no prompt, provider name, provider response, exception detail,
credential, or stack trace. Unexpected/assistant-persistence failures remain a
safe `500`; the frontend reconciles those ambiguous outcomes by reloading GET
history rather than assuming either message exists.

## 7. AI Layer

Add the smallest approved `backend/app/ai/` structure, using concrete modules
rather than a general skill framework:

```text
app/ai/
├── service.py
├── consultation_agent.py
├── consultation_skill.py
└── providers/
    ├── base.py
    ├── mock.py
    └── openai.py
```

### AI service

Expose application-facing dataclasses or Pydantic-independent value objects for
ordered context and an `AIResult(content, structured_payload=None)`. The
service coordinates one consultation agent and translates provider/agent
exceptions into one safe AI-boundary exception. It has no Flask, SQLAlchemy,
repository, or provider SDK dependencies in its public contract.

### Consultation agent and skill

Use one `ConsultationAgent`. It combines the ordered persisted context with the
focused `ConsultationSkill` prompt/instructions and invokes the provider. The
skill will instruct the model to provide helpful consultation-oriented text,
avoid claiming deterministic business actions, and optionally return simple
structured data. It will not register tools or implement recommendation,
summary, appointment, RAG, or general skill discovery.

Define the optional payload as a JSON object. The prompt/output contract will
allow only simple scalar values and arrays of scalar values; assistant text is
always mandatory. Unsupported or malformed structured data is discarded or
treated as a safe generation failure according to whether valid text can be
recovered through the declared output parser; it is never used to authorize a
business operation.

### LangChain and providers

Add the minimal compatible `langchain-core` and `langchain-openai`
dependencies. LangChain will be used only here to construct chat messages and
the prompt/output chain; it will not own memory or persistence. The provider
contract accepts the prepared interaction and returns the provider-neutral
result.

- `OpenAIProvider` wraps LangChain's chat-model integration and reads no
  environment directly. Factory configuration supplies the API key, model,
  30-second timeout, and one SDK-level retry. Use an optional backend-only
  `OPENAI_MODEL` setting with a documented default selected during dependency
  implementation, so model choice is centralized rather than exposed to the
  frontend.
- `MockAIProvider` returns deterministic text and optional structured data for
  local architecture compatibility and tests; it never calls the network.
- Existing `AI_PROVIDER` configuration selects `openai` for the Feature 002
  real runtime or `mock` for deterministic local/test use. Unsupported values
  or missing `OPENAI_API_KEY` when `openai` is selected fail safely at
  composition/startup and never expose the key.

Update backend/root environment examples and backend documentation only for
server-side `AI_PROVIDER`, `OPENAI_API_KEY`, and optional `OPENAI_MODEL` usage.
No `VITE_*` AI variable or browser-side OpenAI dependency will be added.

## 8. Flask Composition, DTOs, and Routes

Extend the existing factory instead of adding a second application or
blueprint. Production request composition will create the message repository
from the existing request session and inject the configured AI service into
the same `ConsultationApplicationService`. Factory injection will remain
available so API tests need neither PostgreSQL nor OpenAI.

Extend the existing consultation DTO/route modules with:

- a validated messages path UUID;
- `MessageSubmissionRequest(content)` that trims input, rejects blank text,
  and enforces the 4,000-character maximum;
- explicit message, history-list, successful-exchange, and recoverable
  AI-error response DTOs; and
- the approved `GET` and `POST`
  `/consultations/<consultation_id>/messages` handlers.

Routes will parse/validate, delegate once to the application service, serialize
explicit DTOs, and translate known outcomes only. They will not access a
session/repository or invoke AI/LangChain directly. Existing list/detail routes
and their response contracts remain unchanged.

## 9. Frontend Service and Types

Extend the existing consultation feature's `consultationTypes.ts` and
`consultationApi.ts`; do not create a separate transport stack. Add types for
`USER | ASSISTANT`, message DTOs, history responses, successful exchanges,
simple supported structured payloads, and distinguishable validation,
not-found, AI-recoverable, and general submission/retrieval failures.

Add service methods to:

- `messages(consultationId)` using the approved GET endpoint; and
- `submitMessage(consultationId, content)` using JSON POST.

As with Feature 001, runtime response guards will validate all backend data.
The 503 recovery parser will accept `user_message` only when it is a valid
persisted message DTO; malformed error bodies become generic failures. The
service will never expose raw backend/provider error detail to components.

## 10. Consultation Detail Conversation UI

Extend the existing `ConsultationDetailScreen` route/view after its current
record details. Keep record loading/not-found behavior intact and add a
feature-local conversation component where useful for readable tests.

The MUI UI will provide:

- ordered persisted user/assistant message presentation with stable message
  IDs as React keys and timestamps as secondary display data;
- an explicit empty-conversation state;
- a multiline text field and submit action with blank/4,000-character
  validation feedback;
- a pending state that disables repeat submission while one exchange is in
  flight without pretending the draft is persisted;
- success reconciliation by merging/replacing with the two persisted response
  messages, then retaining backend ordering;
- a safe AI-recovery alert that incorporates the returned persisted user
  message and reloads GET history so PostgreSQL resolves ordering/state;
- generic ambiguous submission recovery that reloads history before showing a
  retryable error; and
- distinct conversation loading, retrieval error, and consultation-not-found
  behavior.

Assistant text will be rendered as plain React text, never injected HTML.
Supported structured payload values will render with MUI list/key-value
elements for scalar fields and scalar arrays; unsupported nesting is ignored
while the required assistant text remains visible. The UI will not interpret
payloads as recommendations, summaries, or appointment actions.

## 11. Testing Strategy

All automated AI behavior uses deterministic doubles. No test reads a real
key, calls OpenAI, or requires external network access.

### Persistence and repository

- Upgrade the full Alembic chain against temporary PostgreSQL and verify UUID,
  foreign-key, enum, JSONB, assistant/user payload constraint, timestamp, and
  index behavior.
- Verify consultation isolation, empty history, persistence across a fresh
  session, and stable `(created_at, id)` chronological ordering including tied
  timestamps.
- Verify successful commits and rollback behavior for failed user/assistant
  persistence units.

### Application and AI

- Verify missing consultation, invalid input, and user-persistence failure do
  not call AI.
- Verify user persistence occurs before AI; multi-message persisted history is
  supplied in order; the 20-message/24,000-character policy is deterministic.
- Verify successful text-only and structured AI results persist and return both
  messages.
- Verify AI/malformed-output failure keeps the user only, and assistant commit
  failure never becomes a successful exchange.
- Unit-test AI service → one agent → one skill → provider coordination,
  provider-neutral results, deterministic mock behavior, and safe translation
  of network/authentication/rate-limit/malformed provider failures without
  testing provider SDK internals or making live calls.

### API and integration

- Cover GET/POST DTO shapes, empty history, invalid UUID/body (`400`), missing
  consultation (`404`), success, recoverable `503` including the persisted
  user DTO, and safe `500` responses.
- Assert secrets, prompt text, raw output, and provider exception details never
  appear in responses.
- Exercise the full API → service → repositories → PostgreSQL path with a
  deterministic AI double across repeated messages and fresh retrieval.

### Frontend

- Extend transport tests for both endpoints, runtime DTO validation, POST body,
  all error kinds, and valid/invalid 503 recovery data.
- Use React Testing Library to cover ordered and empty history; loading,
  not-found, and retrieval failures; blank validation; one pending request;
  successful reconciliation; text-only and supported structured rendering;
  persisted-user recovery after AI failure; authoritative reload after generic
  failure; and repeated submission.
- Assert no fabricated assistant content, unsafe HTML, provider details, or
  frontend AI credentials are rendered.

Run relevant Pytest suites, `npm test`, `npm run typecheck`, `npm run lint`, and
`npm run build`. Verify migration upgrade/downgrade and, when the approved
Compose foundation is available, `docker compose up --build` compatibility.

## 12. Implementation Sequence for the Two-Day Timeline

1. **Contract and composition alignment:** preserve Feature 001 APIs; finalize
   message DTOs, typed outcomes, injected service/provider interfaces, and
   configuration at the existing seams.
2. **Persistence critical path:** add the message mapping/migration/repository
   and PostgreSQL tests, including the two commit boundaries.
3. **Deterministic AI/application path:** implement context selection,
   application orchestration, AI service/agent/skill, mock provider, and unit
   tests before wiring the real provider.
4. **API and OpenAI wiring:** add GET/POST handlers, error translation,
   application-factory composition, dependencies/configuration, and boundary
   tests.
5. **Frontend vertical slice:** extend types/service and Consultation Detail
   conversation behavior with focused component/transport tests.
6. **Integration and definition-of-done review:** run the PostgreSQL-backed
   repeated-message flow, quality checks, secret/scope review, and available
   Docker verification.

Frontend contract tests may proceed once DTO shapes are fixed while backend
persistence/AI work continues, but implementation must converge through the
single existing service and route boundaries.

## 13. Risks and Controls

- **AI latency/failure after persistence:** commit the user first, avoid a
  database transaction during the network call, return typed `503` recovery,
  and reload PostgreSQL history.
- **Assistant persistence ambiguity:** never append an unconfirmed assistant as
  authoritative; return failure and reconcile via GET.
- **Context growth:** send only the deterministic bounded tail while preserving
  complete database history.
- **Ordering collisions:** always use UUID `id` as the timestamp tie-breaker and
  apply the same order in repository, API, and UI reconciliation.
- **Provider leakage:** confine LangChain/OpenAI imports and exceptions to
  `app/ai`, centralize environment reads in composition, and test sanitized
  errors.
- **Structured output variability:** require text, constrain the supported JSON
  subset, validate at the AI/service and frontend boundaries, and render only
  safe React nodes.
- **Existing factory injection shape:** evolve it compatibly so Feature 001
  route and application tests continue to inject their service unchanged.
- **Missing Compose foundation:** do not invent Feature 002-specific containers;
  record verification as unavailable if the repository still lacks the
  approved general Compose assets at implementation time.

## 14. Definition of Done

Feature 002 is ready only when:

- the single message migration/mapping/repository persists UUID-linked user and
  assistant messages with JSONB payloads and stable PostgreSQL ordering;
- GET history and POST exchange routes use explicit DTOs and the existing
  blueprint/application service without changing Feature 001 contracts;
- the workflow proves user-before-AI persistence, bounded persisted context,
  assistant-after-AI persistence, and every specified failure boundary;
- the isolated AI service, single agent, consultation skill, minimal LangChain
  chain, mock provider, and OpenAI provider are composed with server-only
  configuration;
- Consultation Detail loads, submits, reconciles, safely renders, and recovers
  exclusively through its dedicated frontend service;
- backend, AI, PostgreSQL integration, frontend, type, lint, and build checks
  pass deterministically without live OpenAI or credentials;
- available Docker Compose verification passes, or the pre-existing missing
  foundation is explicitly reported without expanding this feature's scope;
  and
- no Feature 001 behavior/specification, summary, recommendation, appointment,
  RAG, vector, tool, LangGraph, multi-agent, or new product scope is added.
