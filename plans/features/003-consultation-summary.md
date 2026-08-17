# Consultation Summary Implementation Plan

## 1. Objective

Implement the approved Consultation Summary vertical slice on top of Features
001 and 002:

```text
React Consultation Detail / Summary
        ↓
consultation feature API/service
        ↓
Flask consultation blueprint + Pydantic DTOs
        ↓
ConsultationApplicationService
        ↓
Consultation + Message + Summary repositories
        ↓
PostgreSQL consultations, messages, summaries, recommendations

ConsultationApplicationService
        ↓
AIService → ConsultationAgent → ConsultationSkill
        ↓
LangChain → configured provider
```

The implementation will generate one immutable summary aggregate from the
complete persisted conversation, atomically persist it with stable ordered
recommendations and the approved consultation completion updates, support
idempotent/concurrent requests, and expose restart and booking-navigation
actions. It will not add appointment persistence, a `BOOKED` transition,
summary regeneration/versioning, dashboard work, or new infrastructure.

## 2. Current-System Alignment

Feature 003 will extend these implemented conventions:

- `create_app` is the only composition boundary. Production requests receive
  one SQLAlchemy session shared by `ConsultationRepository` and
  `MessageRepository`; API tests inject a `ConsultationApplicationService`
  double directly.
- Consultation and message identifiers use native PostgreSQL UUIDs and Python
  `UUID` values, serialized as strings at API/frontend boundaries.
- SQLAlchemy mappings share the infrastructure-owned `Base` in
  `backend/app/infrastructure/consultation_models.py`; migrations form a linear
  chain ending at `20260813_02`.
- Focused repositories accept the request session and own commit/rollback
  mechanics. The application service coordinates business workflows without
  importing Flask or depending on SQLAlchemy session details.
- Conversation history is loaded through `MessageRepository` in ascending
  `(created_at, id)` order. Interactive AI replies use a bounded tail, but all
  rows remain persisted and retrievable.
- `AIService`, one `ConsultationAgent`, one `ConsultationSkill`, and the
  provider protocol expose provider-neutral value objects. Only the AI layer
  imports LangChain/OpenAI.
- Consultation routes live on the existing `/api/v1` blueprint, use Pydantic
  DTOs, and return client-safe JSON errors with `error` and stable `code` where
  a recoverable AI outcome already requires one.
- The frontend remains under
  `frontend/src/app/features/consultation-records/`, uses `consultationApi` as
  its only HTTP boundary, runtime-validates responses, and routes consultation
  detail at `/consultations/:consultationId`.
- Pytest uses deterministic service/provider doubles and temporary PostgreSQL
  16 containers. Vitest/React Testing Library use transport/service doubles.
- The root Compose stack now builds PostgreSQL 16, Flask, and Vite/React. Its
  default mock provider permits network-free feature verification.

No new framework, container, transport layer, blueprint, application service,
AI agent, or frontend feature root is required.

## 3. Specification Traceability

| Approved requirement | Planned responsibility | Verification focus |
| --- | --- | --- |
| Eligibility and explicit completion semantics | Application service using consultation status and complete ordered history | Full status/history matrix; no writes or AI for ineligible cases |
| One persisted summary per consultation | Migration constraints and focused summary repository | Unique consultation linkage and repeat retrieval |
| Stable ordered recommendation IDs | UUID recommendation rows, unique positive position, repository order | Reloaded IDs/order and constraint tests |
| Atomic aggregate plus projection and `COMPLETED` update | One summary-repository transaction | Commit/rollback integration tests; no partial visibility |
| Complete persisted conversation supplied to summary AI | Message repository retrieval and application orchestration | Exact full ordered request, including history beyond Feature 002 limits |
| Provider-neutral structured summary generation | Existing AI service/agent/skill/provider extended with summary contracts | Valid/malformed result and safe-provider-failure tests |
| Idempotent sequential generation | Existing-summary check before eligibility/AI | Same DTO/IDs, `200`, no repeat AI call |
| Concurrent generation | Unique constraint, rollback/reload of winning aggregate | Controlled two-session race produces one aggregate |
| Safe AI/persistence retry behavior | Typed application outcomes and PostgreSQL reconciliation | `503`, safe `500`, unchanged status, retry behavior |
| Completed consultations reject messages | Existing submission workflow status guard | No user row and no AI call; coded `409` |
| Summary GET/POST and restart APIs | Existing blueprint/DTO modules and application service | Exact success/error contracts and DTO shapes |
| Restart preserves source and creates fresh consultation | Application workflow plus consultation/summary repositories | New `PENDING` record with copied/empty fields; source unchanged |
| Frontend completion and summary experience | Existing feature service/types, detail view, new summary screen/route | Eligibility hint, generation, direct retrieval, all states |
| Stable booking navigation boundary | Summary recommendation selection and React Router navigation | IDs in route; no appointment request/status mutation |
| Feature 001/002 and Compose compatibility | Regression suites and runtime verification | Existing record, detail, conversation, migration, build, Compose checks |

## 4. Persistence Design

Create one Alembic revision after `20260813_02` and extend the shared mappings
with two tables. Use explicit foreign keys without delete cascades because
deletion is outside this feature.

### 4.1 `consultation_summaries`

| Column | PostgreSQL / SQLAlchemy decision | Constraints and behavior |
| --- | --- | --- |
| `id` | Native UUID / `UUID`, generated with `uuid4` | Primary key and string API representation |
| `consultation_id` | Native UUID / `UUID` | Required FK to `consultations.id`; unique to enforce at most one summary |
| `patient_summary` | `TEXT` | Required; check `btrim(patient_summary) <> ''` |
| `recommendation_rationale` | Nullable `TEXT` | Null when absent; check null or nonblank after trimming |
| `created_at` | Time-zone-aware `TIMESTAMP` | Required, server default `CURRENT_TIMESTAMP`, immutable here |

The unique constraint on `consultation_id` is the durable create-once and race
arbitration mechanism. An index beyond the unique index is unnecessary for the
only consultation-key lookup.

### 4.2 `consultation_recommendations`

| Column | PostgreSQL / SQLAlchemy decision | Constraints and behavior |
| --- | --- | --- |
| `id` | Native UUID / `UUID`, generated with `uuid4` | Primary key and stable later-linkage identifier |
| `summary_id` | Native UUID / `UUID` | Required FK to `consultation_summaries.id` |
| `treatment` | `TEXT` | Required; check `btrim(treatment) <> ''` |
| `position` | `INTEGER` | Required, check `position >= 1`, unique with `summary_id` |

Positions are assigned by the application from validated AI ordering starting
at one. Retrieval always orders ascending `(position, id)`; `id` is a defensive
tie-breaker while the unique `(summary_id, position)` constraint prevents an
actual tie. The database cannot express “at least one child” with a simple row
constraint, so provider-neutral validation plus the single aggregate
transaction enforce that invariant.

The migration will create summaries before recommendations and downgrade in
reverse order. It adds no appointment, version, generation-attempt, audit,
restart-lineage, or deletion columns. Existing consultation/message schemas and
enum values remain unchanged.

## 5. Summary Repository and Transaction Boundaries

Add `SummaryRepository` beside the two existing repositories. It will own
summary aggregate persistence mechanics only:

- `get_summary(consultation_id)` retrieves the summary and its recommendations
  in deterministic order or returns absence;
- `complete_consultation(consultation, validated_summary)` performs the one
  atomic aggregate write; and
- a race-recovery path rolls back a unique-constraint conflict and reloads the
  winner by consultation identifier.

`complete_consultation` will use the shared request session but one explicit
unit of work:

1. add the summary row and flush to establish its UUID/foreign-key identity;
2. add every recommendation row with generated UUID and one-based position;
3. set `consultation.recommended_procedure` to position one's treatment;
4. set `consultation.status` to `COMPLETED`;
5. commit once; and
6. refresh/reload and return the persisted ordered aggregate.

Any failure before commit triggers rollback, including failed recommendation,
projection, or status writes. No transaction is held open during the AI network
call. No partially confirmed SQLAlchemy objects are returned as authoritative.

The repository will distinguish a unique conflict on the one-summary
constraint from other persistence failures. After rollback, it reloads the
summary in the same session; finding it means another request won and produces
an idempotent existing result. If no winner is visible, or a different
constraint failed, the repository re-raises for safe `500` handling. Repository
code will not decide eligibility, invoke AI, or translate HTTP errors.

Extend `ConsultationRepository` only with the focused operation needed to
persist one new restart consultation. That operation commits one insert,
refreshes it, and rolls back on failure, matching `MessageRepository`'s current
simple unit-of-work convention. Source eligibility remains an application rule.

## 6. Application-Service Workflows

Extend the existing `ConsultationApplicationService`; preserve list, detail,
history, and valid pending-conversation behavior. Inject `SummaryRepository`
through the existing factory seam while keeping optional dependencies
compatible with Feature 001 unit tests.

### 6.1 Summary retrieval

1. Retrieve the consultation through the existing not-found behavior.
2. Load the summary aggregate by consultation identifier.
3. Return it when present; otherwise raise a typed
   `SummaryNotAvailableError` for coded `409` translation.

Retrieval never invokes AI and treats a completed consultation without a
summary as unavailable/inconsistent rather than fabricating data.

### 6.2 Initial generation and eligibility

The generation method returns both the persisted aggregate and a creation flag
so the route can select `201` or `200` without knowing persistence mechanics:

1. Confirm the consultation exists.
2. Check for and immediately return an existing summary before checking status
   or invoking AI. This preserves approved idempotency for completed summaries.
3. Require `PENDING` status.
4. Load the complete message history in repository order.
5. Require at least one `USER`, at least one `ASSISTANT`, and latest role
   `ASSISTANT`; otherwise raise `SummaryNotEligibleError`.
6. Map every persisted row—not Feature 002's bounded tail—to provider-neutral
   `ConversationMessage` values.
7. Invoke `AIService.generate_summary` with consultation context and the full
   ordered tuple. The application performs no truncation or silent omission.
8. Reconstruct/defensively validate a provider-neutral summary value to ensure
   trimmed nonblank patient summary, at least one trimmed nonblank treatment in
   provider order, and null or trimmed nonblank rationale.
9. Ask `SummaryRepository` to atomically complete the consultation.
10. Return `created=True` for its commit or `created=False` when race recovery
    returns the winning aggregate.

If the configured model cannot accept the full persisted input, the provider
failure is translated to `SummaryGenerationError` and the route returns the
approved `503`. This is the plan's deterministic, loss-aware context policy:
never truncate, summarize, or silently discard source messages. PostgreSQL
history and `PENDING` status remain unchanged for explicit retry.

### 6.3 Completed-message prevention

Update `submit_message` to check consultation status immediately after the
existing consultation lookup and before normalizing/persisting a new user
message or calling AI. Only `PENDING` consultations accept new messages.
`COMPLETED` (and existing `BOOKED`) submissions raise a typed
`ConsultationConversationClosedError`, translated to `409` with stable code
`CONSULTATION_CONVERSATION_CLOSED`. Existing `400`, `404`, `503`, user-first
commit, and assistant-failure recovery semantics remain unchanged for pending
consultations.

### 6.4 Restart workflow

1. Retrieve the source consultation or raise the existing not-found outcome.
2. Require source status `COMPLETED` and a persisted summary; otherwise raise
   `ConsultationNotRestartableError` without a write.
3. Construct a new consultation with copied `patient_name` and
   `primary_concern`, empty `recommended_procedure`, and `PENDING` status.
4. Persist and return that new consultation through `ConsultationRepository`.

No source field is changed. No message, summary, or recommendation is copied.
Each successful application call intentionally creates one consultation; no
automatic retry or idempotency key is introduced.

## 7. AI-Layer Extension

Extend the existing AI modules rather than creating a second agent or direct
provider path.

### 7.1 Provider-neutral contracts

Add immutable values in the provider-neutral contract area:

- `SummaryResult(patient_summary, recommended_treatments,
  recommendation_rationale=None)` with defensive normalization/validation;
- `SummaryProviderRequest(system_instruction, consultation_context, messages)`;
  and
- a provider capability for `generate_summary(request)` alongside the existing
  interactive `generate(request)` method.

Validation trims required strings, rejects blank patient/treatment text,
requires at least one treatment, preserves treatment order, and normalizes an
absent rationale to `None`. It does not infer, deduplicate, rank, or medically
reinterpret provider recommendations.

### 7.2 Service, agent, and skill

- `AIService.generate_summary` calls the existing agent and translates any
  agent/provider/validation exception into the existing safe AI-service
  boundary exception.
- `ConsultationAgent.summarize` prepares the focused summary request for its
  already-injected provider. The existing `respond` path remains unchanged.
- `ConsultationSkill.summary_instructions_for` supplies the approved grounding,
  careful non-diagnostic wording, patient-report distinction, plain-text,
  concise-rationale, and no-booking/status-action constraints. It registers no
  tools and owns no persistence.

### 7.3 OpenAI and mock providers

Extend `OpenAIProvider` with a separate Pydantic structured-output schema and
LangChain chain for the exact summary fields. Reuse the same configured
`ChatOpenAI` model, API key, 30-second timeout, and one SDK retry; do not add new
environment settings or read configuration inside the provider. The provider
maps validated output to `SummaryResult` and converts all SDK, context-limit,
authentication, network, and malformed-output failures to `ProviderError`.

Extend `MockAIProvider` with a deterministic summary based on supplied context
and messages so the Compose default and tests remain network-free. It returns
stable content values but not persisted IDs; PostgreSQL generates the stable
summary/recommendation identities.

## 8. Flask Composition, DTOs, and Routes

Production request composition will construct `SummaryRepository` with the
same session used by the consultation/message repositories and inject it into
the same `ConsultationApplicationService`. Existing direct service injection
remains unchanged for API tests, and the single existing blueprint remains the
route owner.

### 8.1 DTOs

Extend `consultation_dtos.py` with:

- recommendation response fields `id`, `treatment`, and `position`;
- summary response fields exactly matching the approved representation;
- reuse of the existing UUID path DTO for summary and restart paths; and
- explicit coded-error DTOs where helpful for safe serialization tests.

`recommended_treatments` is assembled from ordered persisted recommendation
rows. Response conversion will not expose `summary_id`, SQLAlchemy
relationships, provider types, or internal exceptions. Restart reuses the
existing `ConsultationResponse` DTO.

POST summary and restart accept no request body. A supplied body, including an
empty JSON object, is rejected as invalid `400`, preventing ignored client
input and preserving the approved no-data contract.

### 8.2 Routes and error translation

Add the approved handlers:

- `GET /api/v1/consultations/<consultation_id>/summary`;
- `POST /api/v1/consultations/<consultation_id>/summary`; and
- `POST /api/v1/consultations/<consultation_id>/restart`.

Routes validate, delegate once, serialize persisted data, and translate typed
application outcomes:

| Outcome | HTTP response |
| --- | --- |
| Invalid UUID or non-empty/invalid POST body | `400 {"error": "Invalid request"}` |
| Missing consultation | `404 {"error": "Consultation not found"}` |
| Summary absent on GET | `409` with `code: "SUMMARY_NOT_AVAILABLE"` |
| Initial generation/restart ineligible | `409` with approved `SUMMARY_NOT_ELIGIBLE` or `CONSULTATION_NOT_RESTARTABLE` code |
| Closed Feature 002 conversation submission | `409` with `code: "CONSULTATION_CONVERSATION_CLOSED"` |
| Summary created | `201` with summary DTO |
| Summary already present/race winner reloaded | `200` with summary DTO |
| Summary AI/validation failure | `503` with `code: "SUMMARY_GENERATION_FAILED"` |
| Unexpected persistence/server failure | existing safe `500` envelope |

Display messages will be stable and client-safe, but frontend logic keys on
status/code. No response contains raw AI output, provider/model identity,
prompt text, credential, SQL/constraint detail, exception, or stack trace.

## 9. Frontend Service and Runtime Types

Extend the existing `consultationTypes.ts` and `consultationApi.ts`; do not
introduce a separate HTTP client.

Add feature types for:

- persisted summary and recommendation DTOs;
- summary/restart success values;
- stable summary-not-available, summary-not-eligible,
  summary-generation-failed, not-restartable, and conversation-closed errors;
  and
- the existing consultation DTO returned by restart.

Add service methods:

- `summary(consultationId)` → GET persisted summary;
- `generateSummary(consultationId)` → POST with no body and retain whether the
  response was `200` or `201` only if UI behavior needs it; and
- `restartConsultation(consultationId)` → POST with no body and return the
  validated new consultation.

Runtime guards will validate UUIDs, consultation linkage, nonblank summary and
treatment text, a non-empty recommendation array, positive integer positions,
unique IDs/positions, ascending position order, nullable/nonblank rationale,
and valid timestamps. The service maps only the exact approved status/code
combinations to feature error kinds; malformed successes/errors become safe
retrieval/submission failures. Components receive no raw response, provider
detail, or persistence information.

Extend message submission error handling for the coded closed-conversation
`409`, while retaining all Feature 002 recovery behavior.

## 10. Consultation Detail Completion UI

Keep the existing detail route and record/conversation rendering. Refactor the
conversation component minimally so it can report loaded persisted message
roles/history state to its parent, allowing Consultation Detail to compute the
same UI eligibility hint without duplicating persistence or AI rules.

For a `PENDING` record with loaded history containing both roles and ending in
`ASSISTANT`, show `Generate Summary`. Disable it while one request is pending.
On successful generation, navigate to
`/consultations/:consultationId/summary`. Map coded `409`, `503`, missing, and
generic outcomes to distinct safe/retryable alerts; the backend remains
authoritative if state changes between loading and activation.

For a `COMPLETED` consultation, retain read-only history, hide/disable the
message composer, and provide `View Summary` navigation. The backend status
guard protects stale clients. `BOOKED` records do not expose generation or new
message controls. No draft/history deletion occurs.

## 11. Consultation Summary Route and Actions

Add `ConsultationSummaryScreen` in the existing frontend feature and register
`/consultations/:consultationId/summary` in `App.tsx`.

On mount/direct refresh, retrieve through `consultationApi.summary`; do not
regenerate implicitly. Render with MUI:

- patient summary as plain text;
- recommended treatments in backend position order with one accessible
  single-selection control keyed by recommendation UUID;
- optional rationale only when non-null; and
- distinct loading, `SUMMARY_NOT_AVAILABLE`, missing consultation, and generic
  retrieval states.

Generation failures/ineligibility originate on Consultation Detail and are
shown there; the summary screen still recognizes not-available state on direct
load. All text uses normal React rendering with whitespace preservation, never
HTML injection.

### Restart action

Enable `Restart Consultation` only after a persisted summary loads. During its
single request, disable repeat activation. On success navigate to the existing
`/consultations/:newConsultationId` detail route using the validated returned
ID. Show distinct not-restartable, missing, and generic errors without changing
or clearing source UI data. Do not automatically retry the create request.

### Book Appointment boundary

Keep `Book Appointment` disabled until one persisted recommendation is
selected. Activating it performs React Router navigation only to:

```text
/consultations/:consultationId/appointments/new?recommendation_id=:recommendationId
```

Register a small route-level “appointment setup is unavailable” placeholder so
the handoff is explicit until the Appointment feature owns that route. The
placeholder may display the navigation boundary but contains no form, schedule
fields, API request, persistence, or status mutation. Neither treatment text
nor transient objects are navigation identifiers.

## 12. Concurrency and Idempotency Strategy

The implementation deliberately avoids database locks during provider calls:

```text
request A/B: read no summary + eligible history
       ↓
request A/B: independently call AI
       ↓
request A: atomic insert/update commit succeeds
       ↓
request B: unique consultation-summary constraint fails
       ↓
request B: rollback, reload A's persisted aggregate, return existing (`200`)
```

The database unique constraint is authoritative; a preflight existence query
is an optimization and sequential-idempotency guard, not the concurrency
mechanism. Recommendation IDs from the losing result never become visible.
Only the winning transaction updates projection/status. Race recovery returns
the winner's values and IDs rather than comparing or merging AI results.

If a non-race persistence error occurs, rollback and return safe `500`. A later
retry always begins by reading PostgreSQL, so an ambiguously committed result
is returned without a second AI call. No advisory locks, distributed locks,
serializable transaction across AI, idempotency table/token, background job,
outbox, Redis, or provider-call deduplication is introduced.

## 13. Testing Strategy

All automated AI behavior uses deterministic providers/service doubles. No
test reads a real key, calls OpenAI, or requires external network access.

### Persistence and repositories

- Apply the full Alembic chain to temporary PostgreSQL and verify upgrade and
  downgrade of both new tables, UUID/FK behavior, unique consultation linkage,
  nonblank text checks, nullable rationale check, positive/unique positions,
  and no delete cascade.
- Verify aggregate retrieval across a fresh session returns stable summary and
  recommendation UUIDs in `(position, id)` order.
- Verify one commit atomically persists every row plus projection/status.
- Force failures at aggregate stages and prove rollback leaves no summary,
  recommendation, projection change, or completion transition.
- Use two independent sessions and a controlled barrier to prove one winner,
  unique-conflict recovery, one stored aggregate, and common returned IDs.
- Verify restart persistence creates only its one fresh consultation and rolls
  back safely on failure.

### Application and AI

- Test the full eligibility matrix: missing, `PENDING` empty, only one role,
  user-last, eligible assistant-last, `BOOKED`, `COMPLETED` with summary, and
  inconsistent `COMPLETED` without summary.
- Assert ineligible paths write nothing and do not invoke AI; existing summary
  returns before status/history checks and AI.
- Assert complete ordered history, including more than 20 messages and more
  than 24,000 characters, reaches summary AI unchanged.
- Verify valid result normalization/order and creation flag, AI/malformed
  output translation, atomic persistence delegation, race-existing result, and
  unexpected failure behavior.
- Verify completed/booked message submission persists no user message and
  invokes no interactive AI, while every Feature 002 pending/failure behavior
  remains green.
- Verify restart source rules, exact copied/initialized values, no child-data
  copying, no source mutation, and no automatic retry.
- Unit-test service → existing agent → skill → provider summary coordination,
  structured OpenAI mapping, deterministic mock summary, full-message
  propagation, and sanitized provider failure.

### API and integration

- Cover GET/POST summary and restart DTOs, invalid UUID/body `400`, missing
  `404`, each exact coded `409`, summary `201`/idempotent `200`, safe coded
  `503`, and generic `500`.
- Cover closed-message `409` without changing Feature 002's existing response
  contracts for pending conversations.
- Assert responses never include provider/model/prompt/raw-output/credential,
  SQL/constraint, exception, or stack details.
- Exercise API → application → message/summary/consultation repositories →
  deterministic AI → PostgreSQL for generation, repeat retrieval, idempotency,
  rollback, completion, and restart independence.

### Frontend

- Extend transport tests for all three methods, exact paths/methods/no-body
  requests, `200`/`201`, runtime summary invariants, restart DTO validation,
  exact coded errors, malformed payloads, and transport failures.
- Extend Consultation Detail tests for eligible/ineligible UI hints, one
  pending generation, navigation, every safe generation error, completed
  read-only history/view action, and stale closed-submission handling.
- Test Summary route direct retrieval, loading, rendering/order/null rationale,
  plain-text safety, unavailable/missing/generic states, stable selection, and
  disabled/enabled actions.
- Test restart single-request protection, exact returned-ID navigation, and
  error states without local source mutation.
- Test booking path/query identifiers and assert no appointment HTTP call,
  status update, form, or scheduling UI exists.

## 14. Regression and Vertical-Slice Verification

Run and review in this order:

1. Full migration upgrade to head and downgrade/upgrade round trip against
   PostgreSQL 16.
2. Focused summary persistence, repository, application, AI, DTO, API, and
   PostgreSQL vertical-slice tests.
3. Complete backend Pytest suite to protect Feature 001 retrieval/filtering and
   Feature 002 history/order/submission/recovery behavior.
4. Frontend service, Consultation Detail, conversation, summary, routing, and
   placeholder tests.
5. Full `npm test`, `npm run typecheck`, `npm run lint`, and `npm run build`.
6. Build/start the Compose stack with its default mock provider, apply
   migrations, verify service health/reachability, and manually exercise one
   deterministic pending conversation through summary, reload, restart, and
   booking navigation.
7. Review tracked frontend/configuration output for OpenAI credentials and
   confirm the browser performs no provider request.
8. Review source/schema/routes for forbidden appointment, `BOOKED`, deletion,
   dashboard, regeneration/versioning, RAG, Redis, vector, LangGraph,
   WebSocket, streaming, or multi-agent scope.

Existing tests that submit messages to fixtures marked `COMPLETED` or `BOOKED`
must be corrected only where they conflict with the newly approved completion
boundary; Feature 001 status display/filter behavior remains unchanged.

## 15. Docker and Runtime Considerations

- No Compose service, image, port, volume, or new runtime dependency is needed.
- The new Alembic revision runs through the backend's existing migration
  process and targets the existing PostgreSQL 16 service.
- Default `AI_PROVIDER=mock` must support summary generation so local Compose
  starts and verifies without a key or network.
- Existing `openai` selection uses the current backend-only key/model settings;
  no `VITE_*` AI setting or frontend SDK is introduced.
- Summary generation holds no database transaction during the provider call.
  The existing request timeout/runtime remains unchanged; provider context
  overflow fails safely as `503` with no partial state.
- Dockerfiles and `compose.yaml` should need no product change. If a migration
  entrypoint adjustment is independently required to apply the new revision,
  it must reuse the existing backend container boundary and be justified in
  the implementation task rather than add infrastructure.

## 16. Implementation Sequence

1. **CS-001 — Confirm Feature 003 integration boundaries:** record exact model,
   migration, session, error, AI structured-output, frontend routing/service,
   PostgreSQL concurrency-test, and Compose conventions; change no product
   code.
2. **CS-002 — Add summary/recommendation persistence:** add the linear
   migration, mappings, constraints, and focused PostgreSQL schema tests.
3. **CS-003 — Add summary aggregate repository:** implement ordered retrieval,
   one atomic completion transaction, unique-race recovery, restart creation
   support, and repository/concurrency tests.
4. **CS-004 — Extend the AI abstraction for summaries:** add provider-neutral
   values, service/agent/skill operations, OpenAI structured output, mock
   behavior, and deterministic AI tests.
5. **CS-005 — Add consultation summary application workflows:** implement
   retrieval, eligibility, full-history generation, result validation,
   completion, idempotency, message closure, restart, and application tests.
6. **CS-006 — Expose summary and restart APIs:** wire composition, DTOs, three
   endpoints, closed-message response, safe error translation, and API/full
   persistence integration tests.
7. **CS-007 — Extend frontend summary service/types:** add runtime-validated
   types, GET/POST/restart methods, coded errors, and transport tests.
8. **CS-008 — Add Consultation Detail completion behavior:** add eligibility
   hint/state sharing, generate/view actions, completed read-only behavior,
   navigation, recovery, and focused RTL tests.
9. **CS-009 — Add Consultation Summary and navigation boundaries:** add summary
   route/screen, treatment selection, restart navigation, booking-only route
   handoff/placeholder, and RTL/router tests.
10. **CS-010 — Verify the Feature 003 vertical slice:** run migration,
    backend/frontend regression, integration, static/build, secret/scope, and
    Compose verification and record acceptance evidence.

These identifiers are proposed decomposition labels only. Detailed task files
will be created after this plan is approved.

## 17. Task Dependencies and Parallel Work

The critical backend path is:

```text
CS-001
   ↓
CS-002 persistence
   ↓
CS-003 repository
   ↓
CS-005 application workflow
   ↓
CS-006 API/integration
   ↓
CS-010 verification
```

The AI path is `CS-001 → CS-004 → CS-005`. The frontend path is
`CS-001 → CS-007 → CS-008 → CS-009 → CS-010`; CS-007 may proceed against the
approved API contract while CS-002 through CS-006 are underway, and CS-008 can
start after CS-007 with service doubles. CS-009 depends on CS-007 and can run
alongside CS-008 once shared routing conventions are fixed. Live frontend
integration waits for CS-006. CS-010 requires CS-006, CS-008, and CS-009.

| Task | Depends on | Enables |
| --- | --- | --- |
| CS-001 | Approved specification and completed Features 001/002/Compose | All implementation streams |
| CS-002 | CS-001 | CS-003 |
| CS-003 | CS-002 | CS-005 and persistence integration |
| CS-004 | CS-001 | CS-005 |
| CS-005 | CS-003 and CS-004 | CS-006 |
| CS-006 | CS-005 | Live frontend integration and CS-010 |
| CS-007 | CS-001 and approved HTTP contract | CS-008 and CS-009 |
| CS-008 | CS-007 | CS-010 |
| CS-009 | CS-007; coordinate routing with CS-008 | CS-010 |
| CS-010 | CS-006, CS-008, and CS-009 | Feature completion evidence |

## 18. Risks, Controls, and Planning Assumptions

- **Concurrent provider calls:** the approved behavior permits redundant AI
  work. A database unique constraint elects one result; the loser reloads it.
  No transaction or lock spans the network call.
- **Integrity-error classification:** name the summary unique constraint and
  inspect PostgreSQL/SQLAlchemy constraint identity so only that expected race
  becomes success; never convert arbitrary integrity failures to idempotency.
- **Large full history:** send every ordered message as approved. Context-limit
  or timeout errors become safe retryable `503`; no silent truncation or
  secondary summarization is added.
- **Atomic aggregate invariant:** the repository is the single owner of the
  summary/recommendation/projection/status commit. Existing message repository
  commits remain separate and occur only before summary generation.
- **Inconsistent legacy state:** `COMPLETED` without a summary remains
  ineligible/unavailable. No repair, backfill, or AI invocation is inferred.
- **Restart duplicate risk:** restart is an intentional non-idempotent create.
  The UI disables repeat activation and the transport does not auto-retry; a
  network-ambiguous result may require the user to inspect records before
  retrying, as no lineage/idempotency schema is approved.
- **Empty restart projection:** PostgreSQL already permits a non-null empty
  `recommended_procedure`; return it through existing DTO/runtime guards and
  replace it only when that new consultation completes.
- **Closed conversation error:** the approved spec requires rejection but does
  not assign the modified Feature 002 endpoint a code. Use coded `409
  CONSULTATION_CONVERSATION_CLOSED` to preserve safe machine-readable frontend
  behavior without changing the approved summary/restart contracts.
- **Summary route:** use the conventional nested
  `/consultations/:consultationId/summary` path.
- **Booking boundary:** use
  `/consultations/:consultationId/appointments/new?recommendation_id=...` and a
  non-functional placeholder. This is navigation evidence only, not an
  appointment feature.
- **No clinical sufficiency inference:** application eligibility is exactly the
  approved role/status rule. The AI prompt shapes output but does not authorize
  completion; only validated persistence does.
- **Existing dirty worktree:** implementation must preserve unrelated
  documentation/Compose changes and avoid overwriting user work.

No product conflict blocks task generation. The closed-conversation error code,
exact constraint names, module-level helper shapes, and placeholder component
name are implementation details fixed here or left to task-local alignment;
none alters the approved Feature 003 behavior.

## 19. Acceptance-Criteria Validation Matrix

| Feature 003 acceptance criterion | Plan coverage |
| --- | --- |
| Eligible user can request summary from Detail | §§6.2, 8, 10, 13 |
| Complete persisted history through AI abstraction | §§6.2, 7, 13 |
| Persist before `COMPLETED`/success | §§5–6, 12–13 |
| Required summary, treatments, optional rationale | §§4, 7–9, 11 |
| Stable recommendation IDs across reload/repeat | §§4–5, 9, 13 |
| Reopen/direct navigation does not invoke AI | §§6.1, 9, 11, 13 |
| Repeated generation creates no duplicates | §§5–6, 12–13 |
| Ineligible/missing/completed cannot cause unintended generation | §§6, 8, 13 |
| Validation/AI/persistence failures are safe and non-partial | §§5–8, 12–13 |
| Restart creates distinct empty `PENDING` consultation and preserves source | §§5–6.4, 8–9, 11, 13 |
| Booking carries stable IDs without appointment/status mutation | §§9, 11, 13–14 |
| Deterministic tests without live OpenAI | §§7, 13–15 |

Every persistence, API, UI, error, retry, history-preservation, regression, and
scope condition elsewhere in the specification is covered by §§3–18 and will
be traced again in detailed tasks after plan approval.

## 20. Definition of Done

Feature 003 is ready only when:

- the linear migration and shared mappings enforce one summary per
  consultation and stable ordered recommendation persistence;
- the focused summary repository proves ordered retrieval, one atomic
  aggregate/projection/status transaction, rollback, and concurrent winner
  recovery;
- the consultation application service enforces exact eligibility, full
  history, idempotency, completion, closed-message, and restart semantics;
- the existing AI abstraction produces defensively validated structured
  summaries through its one agent/skill and configured mock/OpenAI provider;
- all three approved endpoints and the closed-message extension use explicit
  DTOs and safe exact `400`/`404`/coded `409`/coded `503`/`500` behavior;
- the frontend service runtime-validates every summary/restart response and the
  Detail/Summary routes provide completion, reload, selection, restart, and
  booking-only navigation behavior through that boundary;
- Feature 001 and Feature 002 suites remain green except for deliberate tests
  updated to enforce the approved completed-conversation restriction;
- migration, backend, frontend, integration, lint, type, build, secret/scope,
  and Docker Compose checks pass deterministically without live OpenAI; and
- no appointment persistence/form/scheduling, `BOOKED` transition, dashboard,
  regeneration/versioning, history deletion, direct Flask/React OpenAI call,
  RAG, Redis, vector database, LangGraph, WebSocket, streaming, multiple-agent,
  or other unauthorized scope is introduced.
