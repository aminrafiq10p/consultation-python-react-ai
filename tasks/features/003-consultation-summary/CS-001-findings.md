# CS-001 Findings

Verified against the approved Feature 003 specification and implementation
plan, the completed Feature 001/002 implementation and tests, and the current
Docker Compose runtime.

Status labels in this document describe the repository before Feature 003
implementation:

- **EXISTING** — an implemented convention Feature 003 shall reuse.
- **ABSENT** — the Feature 003 capability does not exist and belongs to a later
  approved task.
- **DECISION REQUIRED** — no repository precedent exists; this findings review
  fixes the task-local integration choice without changing product behavior.

## Backend Persistence

- **EXISTING:** Infrastructure-owned declarative `Base`, `Consultation`,
  `Message`, `ConsultationStatus`, and `MessageRole` are all in
  `backend/app/infrastructure/consultation_models.py`. Alembic imports
  `Base.metadata` from that module in `backend/migrations/env.py`.
- **EXISTING:** Identifiers use PostgreSQL `UUID(as_uuid=True)`, Python `UUID`,
  and `uuid4`; API JSON and TypeScript expose strings.
- **EXISTING:** Persisted enums use `str, Enum` plus named native PostgreSQL
  enums with `validate_strings=True`. Feature 003 adds no enum.
- **EXISTING:** Required text uses `Text(nullable=False)`. Message constraints
  and indexes are declared in `__table_args__` with explicit names. Time values
  use `DateTime(timezone=True)` and server `CURRENT_TIMESTAMP`.
- **EXISTING:** Foreign keys are explicit and have no delete cascade. Message
  ordering is ascending `(created_at, id)` in `MessageRepository`.
- **EXISTING:** The linear revision chain is
  `20260813_01 (down_revision=None) → 20260813_02
  (down_revision=20260813_01)`. The next revision must directly name
  `20260813_02` as its predecessor and use the existing Alembic environment.
- **ABSENT:** No summary/recommendation table, mapping, relationship, migration,
  constraint, or index exists.

### Feature 003 persistence locations and names

- Add `ConsultationSummary` and `ConsultationRecommendation` to
  `backend/app/infrastructure/consultation_models.py` under the shared `Base`.
- Add exactly one revision under `backend/migrations/versions/`, directly after
  `20260813_02`, creating `consultation_summaries` before
  `consultation_recommendations` and dropping them in reverse.
- Use these fixed constraint names so migration, mapping, race classification,
  and tests agree:

| Constraint | Exact name |
| --- | --- |
| One summary per consultation | `uq_consultation_summaries_consultation_id` |
| Nonblank patient summary | `ck_consultation_summaries_patient_summary_nonblank` |
| Null-or-nonblank rationale | `ck_consultation_summaries_rationale_nonblank` |
| Nonblank treatment | `ck_consultation_recommendations_treatment_nonblank` |
| Positive position | `ck_consultation_recommendations_position_positive` |
| Unique position per summary | `uq_consultation_recommendations_summary_position` |

- Use database `btrim(...) <> ''` checks as planned, native UUID PK/FKs,
  nullable rationale, timezone-aware summary `created_at` with server default,
  and no delete cascade.
- No ORM relationship is required. `SummaryRepository` may query the two
  mappings explicitly, matching the current repository style and avoiding
  implicit loading/ordering behavior.

## Repository, Session, and Transaction Conventions

- **EXISTING:** Repositories live in `backend/app/repositories/`, accept one
  SQLAlchemy `Session` in their constructor, use SQLAlchemy 2 `select` and
  `session.scalar/scalars`, and return mapped objects or `None`/lists.
- **EXISTING:** The production factory opens one session per request in
  `before_request`. All focused repositories for that request receive the same
  session. `teardown_request` closes it and removes request extensions.
- **EXISTING:** `create_session_factory` sets `expire_on_commit=False` and
  documents that failed units must roll back before session reuse.
- **EXISTING:** `MessageRepository.persist_message` owns its focused unit:
  add, commit, refresh; on any exception rollback and re-raise. No transaction
  is held while Feature 002 calls AI because the user-message commit precedes
  the provider call and assistant persistence is a later commit.
- **ABSENT:** `SummaryRepository`, aggregate retrieval/completion, consultation
  creation, and unique-race recovery do not exist.
- **DECISION REQUIRED (fixed):** Add
  `backend/app/repositories/summary_repository.py`. It accepts the shared
  session, explicitly retrieves summary plus recommendations ordered by
  `(position, id)`, and owns one commit for summary + recommendations +
  projection + `COMPLETED`.
- **DECISION REQUIRED (fixed):** Identify only the expected race by catching
  SQLAlchemy `IntegrityError`, rolling back first, and reading PostgreSQL's
  constraint identity from `error.orig.diag.constraint_name`. Compare it
  exactly with `uq_consultation_summaries_consultation_id`. If the diagnostic
  is absent/different, re-raise. After an expected rollback, reload the winner;
  absence is still failure. Do not parse localized exception strings.
- **DECISION REQUIRED (fixed):** Extend
  `backend/app/repositories/consultation_repository.py` with the focused restart
  insert operation following add/commit/refresh/rollback convention. It decides
  no restart eligibility.

## Application and Composition

- **EXISTING:** `ConsultationApplicationService` is in
  `backend/app/application/consultation_service.py`. Constructor dependencies
  are explicit; optional message/AI dependencies preserve Feature 001 tests.
- **EXISTING:** The service owns orchestration and defensive application
  invariants. It has no Flask imports and does not manipulate request objects.
  It currently returns mapped objects and small frozen dataclasses.
- **EXISTING:** Missing consultation is a typed
  `ConsultationNotFoundError`; invalid internal message input is
  `InvalidMessageError`; recoverable post-user-persistence AI failure is
  `AIGenerationError` carrying the confirmed message. Routes translate these.
- **EXISTING:** `create_app` in `backend/app/__init__.py` is the sole production
  composition seam and supports direct `ConsultationApplicationService`
  injection for route tests. Production constructs the database engine/session
  factory and one shared `AIService` outside request handlers, then constructs
  request repositories/application service inside `before_request`.
- **ABSENT:** Summary retrieval/generation, eligibility, completion result,
  summary errors, closed-conversation status guard, and restart workflow do not
  exist.

### Feature 003 application locations

- Extend the existing `ConsultationApplicationService` constructor with an
  optional `SummaryRepository`, preserving `ConsultationApplicationService(
  repository)` and existing injected-service tests.
- Add Feature 003 typed outcomes and small result values in
  `backend/app/application/consultation_service.py`; do not create a second
  application service or Flask-aware exception.
- Construct `SummaryRepository(session)` beside existing repositories in
  `backend/app/__init__.py` and pass it to the same service. Keep `AIService`
  provider composition once per app and one SQLAlchemy session per request.
- The application service checks existing summary, exact eligibility, complete
  history, calls summary AI outside a database transaction, defensively
  validates, delegates atomic completion, and coordinates restart.

## Flask API, DTOs, and Errors

- **EXISTING:** `consultation_blueprint` and every consultation route are in
  `backend/app/api/consultation_routes.py`; `create_app` registers it once at
  `/api/v1`.
- **EXISTING:** Routes obtain the service from
  `current_app.extensions["consultation_service"]`, validate, delegate, map
  known outcomes, and serialize. They do not access sessions/repositories or
  invoke AI.
- **EXISTING:** DTOs are in `backend/app/api/consultation_dtos.py`, use Pydantic
  v2 explicit fields, `ConfigDict(extra="forbid")` on inputs,
  `ConfigDict(from_attributes=True)` on mapped responses, field validators,
  UUID/datetime types, and `model_dump(mode="json")`.
- **EXISTING:** Validation is `400 {"error": "Invalid request"}`, absence is
  `404 {"error": "Consultation not found"}`, and the app-level catch-all is
  safe `500 {"error": "Internal server error"}` while preserving Werkzeug
  HTTP exceptions. Feature 002's typed recoverable failure is `503` with
  `error`, stable `code`, and safe recovery DTO.
- **EXISTING:** API tests inject `Mock(spec=ConsultationApplicationService)` via
  `create_app(service)` and assert exact bodies plus absence of sensitive text.
- **ABSENT:** Summary/recommendation response DTOs, coded summary/restart/closed
  errors, and all three Feature 003 routes do not exist.
- **DECISION REQUIRED (fixed):** Reuse `ConsultationDetailPath` for path UUIDs.
  Add summary/recommendation response DTOs to `consultation_dtos.py` and the
  approved handlers to `consultation_routes.py`. A POST summary/restart body is
  invalid whenever `request.get_data(cache=True)` is non-empty, including `{}`
  or whitespace; absent body is valid. This is the exact no-request-data seam.

## AI Architecture and Configuration

- **EXISTING:** `backend/app/ai/service.py` contains `AIService`, safe
  `AIServiceError`, configuration error, and `create_ai_service(environment)`.
  The service converts all agent/provider failures to a provider-neutral safe
  failure and reconstructs validated values.
- **EXISTING:** `backend/app/ai/consultation_agent.py` contains the single
  `ConsultationAgent`. It converts ordered messages/context plus skill
  instructions into a provider request and invokes the injected provider.
- **EXISTING:** `backend/app/ai/consultation_skill.py` contains the single
  consultation prompt boundary, including non-diagnostic and no-business-
  mutation instructions.
- **EXISTING:** `backend/app/ai/providers/base.py` contains frozen validated
  provider-neutral dataclasses, type aliases, `ProviderRequest`, `ProviderError`,
  and the `AIProvider` protocol. Validation occurs in `__post_init__` and
  normalizes strings/roles/payloads.
- **EXISTING:** `OpenAIProvider` is the only LangChain/OpenAI location. It
  converts provider-neutral messages to `SystemMessage`/`HumanMessage`/
  `AIMessage`, uses a private Pydantic schema with `extra="forbid"`, calls
  `with_structured_output(..., method="function_calling")`, accepts an injected
  chat model for tests, and wraps all failures as `ProviderError`.
- **EXISTING:** `MockAIProvider` is deterministic and network-free.
- **EXISTING:** `create_ai_service` centrally reads `AI_PROVIDER`,
  `OPENAI_API_KEY`, and `OPENAI_MODEL`, defaulting model to `gpt-4.1-mini`, and
  injects provider → existing agent → existing skill. Providers read no
  environment themselves. Root/backend examples and Compose contain server-
  side settings; the frontend contains only `VITE_API_BASE_URL` and an explicit
  no-secret warning.
- **EXISTING:** Backend dependencies contain `langchain-core` and
  `langchain-openai`; frontend has no OpenAI SDK.
- **ABSENT:** Provider-neutral summary values/request, service/agent/skill
  summary methods, exact OpenAI summary schema/chain, and mock summary output.

### Feature 003 AI locations

- Extend `providers/base.py` with `SummaryResult`, summary request, and protocol
  capability; export application-facing values through `app/ai/__init__.py`.
- Extend the same `AIService`, `ConsultationAgent`, and `ConsultationSkill` with
  summary methods. Do not add an agent or memory/tool/workflow system.
- Extend both `OpenAIProvider` and `MockAIProvider`; OpenAI uses a separate
  private exact Pydantic output schema/chain but the same configured model.
- Application code supplies every persisted message; the AI layer must not
  silently truncate it. Provider/context failure returns through the safe AI
  boundary.

## Frontend Conventions

- **EXISTING:** The feature root is
  `frontend/src/app/features/consultation-records/`. Types/constants are in
  `consultationTypes.ts`; the only HTTP boundary is `consultationApi.ts`.
- **EXISTING:** `createConsultationApi` accepts an injectable fetch-compatible
  transport. It constructs `VITE_API_BASE_URL` + encoded `/api/v1` paths,
  validates unknown JSON at runtime, and exposes safe `ConsultationApiError`
  kinds rather than raw bodies.
- **EXISTING:** Runtime guards validate response object/array shapes, roles,
  statuses, UUIDs for messages, timestamps with syntax plus `Date.parse`,
  nonblank message text, and supported structured payload values. Malformed
  server/recovery data becomes a safe feature error.
- **EXISTING:** `ConsultationDetailScreen.tsx` reads `consultationId` with
  `useParams`, injects/defaults its service, and has discriminated loading,
  success, not-found, and error state. It renders record details, then the
  colocated `ConsultationConversation`.
- **EXISTING:** `ConsultationConversation.tsx` owns history/draft/submission
  state, reload reconciliation, pending duplicate prevention, plain-text
  rendering, and safe recovery. It currently always renders its composer after
  successful history load.
- **EXISTING:** Routes are declared centrally in
  `frontend/src/app/core/App.tsx` as nested `<Route>` elements under
  `AppLayout`; detail is `consultations/:consultationId`. Components navigate
  with React Router and use MUI controls/alerts/progress.
- **EXISTING:** Tests are colocated `*.test.ts`/`*.test.tsx`, use Vitest, React
  Testing Library, `userEvent`, `MemoryRouter`, explicit test routes, injected
  services, and transport doubles. Setup is `frontend/src/test/setup.ts` and
  Vitest config is `frontend/vite.config.ts`.
- **ABSENT:** Summary types/guards/service methods/error kinds, history-to-
  detail eligibility reporting, status-aware read-only conversation,
  generation actions, summary screen, summary route, recommendation selection,
  restart UI, and booking placeholder/path.

### Feature 003 frontend locations

- Extend `consultationTypes.ts` and `consultationApi.ts` plus
  `consultationApi.test.ts`; create no second transport.
- Extend `ConsultationDetailScreen.tsx`, `ConsultationConversation.tsx`, and
  `ConsultationDetailScreen.test.tsx` for completion/read-only behavior.
- Add `ConsultationSummaryScreen.tsx` and
  `ConsultationSummaryScreen.test.tsx` in the same feature root.
- Add a small feature-local appointment-unavailable placeholder component/test
  if separation improves clarity; it must remain navigation-only.
- Register `consultations/:consultationId/summary` and
  `consultations/:consultationId/appointments/new` in `App.tsx`. Booking passes
  `recommendation_id` as the approved query parameter.

## Infrastructure and Testing

- **EXISTING:** `backend/tests/conftest.py` starts one session-scoped disposable
  `postgres:16-alpine` container on a random loopback port, waits for
  `pg_isready` and a real SQLAlchemy connection, yields a URL, and force-removes
  the container.
- **EXISTING:** PostgreSQL suites configure Alembic programmatically, upgrade to
  `head`, create engines/sessionmakers with `expire_on_commit=False`, clean
  child tables before parent tables, seed deterministic mappings, and verify
  data through fresh sessions. Application/API/AI tests use mocks or injected
  doubles.
- **EXISTING:** Repository rollback tests intentionally trigger
  `IntegrityError`, call/rely on repository rollback, then prove the session
  remains usable. Ordering tests use fixed timestamps and sorted UUIDs.
- **ABSENT:** No concurrent test, thread/barrier helper, or constraint-name
  inspection convention currently exists.
- **DECISION REQUIRED (fixed):** CS-003 concurrency coverage will use the
  existing PostgreSQL fixture, one engine/sessionmaker, two independent
  sessions, and `threading.Barrier` (or equivalent deterministic coordination)
  to place both attempts after preflight/AI-equivalent preparation and before
  completion. Each worker owns/closes its session; test results/exceptions are
  collected and asserted after joining. Do not share a SQLAlchemy session
  across threads or use sleeps as synchronization.
- **EXISTING:** Backend checks are `cd backend && pytest -q tests`; migration
  commands run from `backend/` with `alembic upgrade head` and explicit
  downgrade/upgrade for round trips.
- **EXISTING:** Frontend checks are `npm test`, `npm run typecheck`,
  `npm run lint`, and `npm run build` from `frontend/`.
- **EXISTING:** Root `compose.yaml` defines PostgreSQL 16 with healthcheck and
  persistent volume, backend depending on healthy PostgreSQL and running
  `alembic upgrade head` before Flask, and Vite frontend depending on backend.
  Default `AI_PROVIDER=mock` is network-free. Standard runtime command is
  `docker compose up --build` from the repository root.

## Integration Decision Matrix

| Area | Status | Exact Feature 003 integration seam |
| --- | --- | --- |
| Summary/recommendation models | ABSENT | Add both to `backend/app/infrastructure/consultation_models.py` under `Base` |
| Migration | ABSENT | One revision in `backend/migrations/versions/` after `20260813_02` |
| Constraint naming | DECISION REQUIRED | Use the six fixed names listed in Backend Persistence |
| Summary repository | ABSENT | Add `backend/app/repositories/summary_repository.py`; shared request session |
| Race classification | DECISION REQUIRED | Named constraint via `IntegrityError.orig.diag.constraint_name`; rollback/reload |
| Restart repository operation | ABSENT | Extend `consultation_repository.py` with focused create commit/rollback |
| Application workflows/outcomes | ABSENT | Extend `backend/app/application/consultation_service.py` and constructor compatibly |
| Application composition | EXISTING | Extend `backend/app/__init__.py:create_app`; one request session, injectable service |
| AI summary contract | ABSENT | Extend `app/ai/providers/base.py` and `app/ai/__init__.py` |
| AI service/agent/skill | EXISTING | Add methods to existing files/classes only |
| OpenAI/mock summary | ABSENT | Extend existing provider modules; separate OpenAI schema/chain, deterministic mock |
| DTOs/routes | EXISTING seam, capability ABSENT | Extend `consultation_dtos.py`/`consultation_routes.py` on existing blueprint |
| POST no-body check | DECISION REQUIRED | Reject any non-empty raw request body; absent body only |
| Frontend types/service | EXISTING seam, capability ABSENT | Extend `consultationTypes.ts`, `consultationApi.ts`, and transport tests |
| Detail completion | EXISTING seam, capability ABSENT | Extend Detail/Conversation components and existing detail test |
| Summary screen | ABSENT | Add feature-local `ConsultationSummaryScreen.tsx` and test |
| Frontend routes | EXISTING seam, routes ABSENT | Add approved nested summary and appointment-boundary routes in `App.tsx` |
| Persistence tests | EXISTING seam | Add focused files directly under `backend/tests/` using PostgreSQL fixture |
| Repository tests | EXISTING seam | Add `backend/tests/test_summary_repository.py` |
| Application tests | EXISTING seam | Add `backend/tests/application/test_consultation_summary_service.py` |
| AI tests | EXISTING seam | Extend `backend/tests/ai/test_ai_layer.py` or add focused summary AI test |
| API/integration tests | EXISTING seam | Extend route/DTO tests and add summary persistence API integration under `backend/tests/api/` |
| Frontend tests | EXISTING seam | Colocate service/detail/summary `*.test.ts(x)` files |
| Compose runtime | EXISTING | Existing three services; no new service/dependency/port/volume |

## Approved HTTP Boundary Confirmation

The cross-stream contract remains exactly:

- `GET /api/v1/consultations/{consultation_id}/summary`;
- `POST /api/v1/consultations/{consultation_id}/summary`, absent body;
- `POST /api/v1/consultations/{consultation_id}/restart`, absent body;
- summary DTO fields `id`, `consultation_id`, `patient_summary`, ordered
  `recommended_treatments[{id,treatment,position}]`, nullable
  `recommendation_rationale`, and `created_at`;
- summary creation `201`, existing/race `200`, invalid `400`, missing `404`,
  exact coded `409`, summary generation coded `503`, and safe `500`; and
- closed message submission coded `409
  CONSULTATION_CONVERSATION_CLOSED`.

The frontend route decisions remain:

- summary: `/consultations/:consultationId/summary`;
- booking boundary:
  `/consultations/:consultationId/appointments/new?recommendation_id=:id`.

## Absent Capabilities and Remaining Decisions

All Feature 003 product capabilities are intentionally absent before CS-002.
The only repository-precedent gaps—constraint-race classification,
concurrency-test coordination, and strict no-body detection—are resolved above
as task-local implementation choices.

No unresolved product or architecture decision blocks CS-002, CS-004, or
CS-007. Exact migration revision identifier, private helper names, summary test
file splitting, and placeholder component filename may follow the established
conventions during their owning tasks without changing contracts.

## Parallel Development Readiness

- **CS-002** can add the two mappings, named constraints, linear migration, and
  PostgreSQL tests independently.
- **CS-004** can extend the provider-neutral values and existing AI
  service/agent/skill/providers independently, using deterministic tests.
- **CS-007** can extend the approved frontend DTO/error contract and transport
  tests independently with no running backend.
- CS-003 follows CS-002. CS-005 is the join point for repository and AI work.
  CS-006 then supplies live HTTP integration. CS-008/CS-009 follow CS-007 and
  can use service doubles until CS-006 is ready.

All scope guards remain active: no appointment persistence/form/scheduling,
`BOOKED` transition, dashboard, regeneration/versioning, history deletion,
direct React/Flask OpenAI call, RAG, Redis, vectors, LangGraph, WebSockets,
streaming, authentication, multiple agents, or unrelated refactoring.
