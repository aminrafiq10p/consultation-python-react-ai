# AI-001 Findings

## Backend Composition

- `backend/app/__init__.py:create_app` is the sole composition boundary. It
  accepts an optional `ConsultationApplicationService`; API tests inject a
  service double directly.
- Without injection, the factory creates one engine and a session factory,
  opens one SQLAlchemy `Session` in `before_request`, constructs
  `ConsultationRepository(session)` and `ConsultationApplicationService`, and
  closes/removes the request dependencies in `teardown_request`.
- The service is resolved by routes from
  `current_app.extensions["consultation_service"]`. Feature 002 must evolve
  this composition so the same request session is supplied to both focused
  repositories and the configured provider-neutral AI service is supplied to
  the same application service, while preserving direct service injection.
- `consultation_blueprint` is registered once at `/api/v1`. The application
  error handler preserves Werkzeug HTTP exceptions and converts other
  exceptions to `{"error": "Internal server error"}` with status `500`.

## Persistence

- The infrastructure-owned declarative `Base` and mappings are in
  `backend/app/infrastructure/consultation_models.py`; Alembic imports
  `Base.metadata` from that module.
- `Consultation.id` uses PostgreSQL `UUID(as_uuid=True)` with Python `UUID`
  values and `uuid4`; Pydantic JSON serialization and frontend types expose
  identifiers as strings.
- Persisted enums use a Python `str, Enum` plus SQLAlchemy native named enum
  (`native_enum=True`, `validate_strings=True`). The migration explicitly
  creates/drops the matching PostgreSQL enum.
- The only revision is `backend/migrations/versions/20260813_01_create_consultations.py`,
  with `revision = "20260813_01"` and `down_revision = None`. The message
  revision must follow it directly as the plan specifies.
- No timestamp column convention is implemented by Feature 001. The minimum
  first-use convention is fixed by the approved plan: time-zone-aware
  `TIMESTAMP`, server default `CURRENT_TIMESTAMP`, with history ordered by
  ascending `(created_at, id)`.
- The exact Feature 002 mapping location is
  `backend/app/infrastructure/consultation_models.py`; the exact focused
  repository location is
  `backend/app/repositories/message_repository.py` beside the consultation
  repository. Neither exists yet.

## Application Layer

- `backend/app/application/consultation_service.py` contains
  `ConsultationApplicationService`. Constructor dependencies are explicit and
  methods accept already validated Python values, delegate persistence, and
  return mapped objects without Flask concerns.
- Missing consultation detail is represented by the application-level
  `ConsultationNotFoundError`, raised by the service after the repository
  returns `None`; routes translate it to `404`.
- Feature 002 retrieval/submission methods and its typed recoverable AI failure
  belong in this existing module/class. The service must receive the new
  message repository and provider-neutral AI service and own the two-commit
  workflow and approved bounded-context policy; routes and repositories must
  not coordinate it.
- Existing list/detail constructor use and behavior must remain compatible.

## API

- The existing consultation blueprint and route module is
  `backend/app/api/consultation_routes.py`; Feature 002 adds both message
  handlers there under the existing `/api/v1` prefix.
- DTOs belong in `backend/app/api/consultation_dtos.py`. Pydantic v2 models use
  explicit fields, `extra="forbid"` for inputs, validators where needed, and
  `ConfigDict(from_attributes=True)` for mapped response conversion. Routes
  catch `ValidationError` and serialize with `model_dump(mode="json")`.
- The fixed message endpoints are:
  `GET /api/v1/consultations/{consultation_id}/messages` and
  `POST /api/v1/consultations/{consultation_id}/messages`.
- Existing safe errors are `400 {"error": "Invalid request"}`,
  `404 {"error": "Consultation not found"}`, and
  `500 {"error": "Internal server error"}`. The approved first extension is
  `503` with `error`, `code: "AI_GENERATION_FAILED"`, and a validated persisted
  `user_message`; provider details never enter the response.
- API boundary tests inject a `Mock(spec=ConsultationApplicationService)` via
  `create_app(service)`, so message route tests use the same seam without a
  database or AI provider.

## Frontend

- The feature root is
  `frontend/src/app/features/consultation-records/`. Transport-facing feature
  types and runtime constants are in `consultationTypes.ts`; the dedicated
  same-origin transport and response guards are in `consultationApi.ts`.
- `consultationApi` uses an injectable fetch-compatible transport, constructs
  `/api/v1` URLs, validates every response field at runtime, and translates
  malformed/network/server outcomes into safe `ConsultationApiError` kinds.
  Feature 002 must extend these two files, not create another transport stack.
- `ConsultationDetailScreen.tsx` is mounted by `App.tsx` at
  `/consultations/:consultationId`. It receives a defaultable service prop,
  reads the ID with `useParams`, and uses explicit loading/success/not-found/
  error state. The conversation UI extends this screen after the existing
  detail fields, optionally through a focused colocated component.
- UI uses MUI layout/feedback components and React Router. Tests use Vitest,
  React Testing Library, `MemoryRouter`, and injected service doubles; API
  tests inject transport stubs. Test setup is `frontend/src/test/setup.ts` and
  Vitest configuration is in `frontend/vite.config.ts`.

## AI and Configuration

- `backend/app/ai/` is absent. AI-004 must add the approved minimal
  `service.py`, `consultation_agent.py`, `consultation_skill.py`, and
  `providers/{base,mock,openai}.py` structure; AI-001 adds none of it.
- Current backend configuration reads environment variables centrally in an
  infrastructure function (`database_url_from_environment` accepts an
  optional mapping for deterministic use). The corresponding AI configuration
  and provider construction must be centralized and supplied by `create_app`;
  providers must not read environment variables themselves.
- Root `.env.example` already contains `AI_PROVIDER=mock` and a blank
  `OPENAI_API_KEY`. `backend/.env.example` contains only PostgreSQL and Flask
  values. `frontend/.env.example` explicitly forbids browser-side OpenAI
  secrets. `OPENAI_MODEL` is absent everywhere.
- Real OpenAI remains the intended Feature 002 runtime provider. Credentials
  remain backend-only. `MockAIProvider` and provider switching exist only for
  architecture/local-test support, never as user-facing behavior. Automated
  tests must use deterministic doubles and never call OpenAI.
- `backend/requirements.txt` is the backend dependency file and currently has
  no LangChain/OpenAI package. AI-004 adds the plan-approved minimal
  `langchain-core` and `langchain-openai` dependencies. Frontend dependencies
  remain in `frontend/package.json`/`package-lock.json`; no browser OpenAI
  dependency is permitted.

## Testing

- Backend unit/boundary locations are `backend/tests/application/` and
  `backend/tests/api/`; persistence/repository tests currently live directly
  in `backend/tests/`, with API persistence integration in
  `backend/tests/api/`.
- `backend/tests/conftest.py` creates a session-scoped temporary
  `postgres:16-alpine` Docker container. Persistence suites run Alembic to
  `head`, create focused sessions, seed deterministic rows, and clean tables
  between tests. Repository tests exercise a real PostgreSQL database;
  application and route tests use mocks.
- Frontend tests are colocated under
  `frontend/src/app/features/consultation-records/` as `*.test.ts`/`*.test.tsx`
  and use transport or feature-service doubles. No implemented test calls an
  external AI service or requires OpenAI credentials.

## Docker / Infrastructure

No Dockerfile or Compose file exists. Only the PostgreSQL test-container
fixture and the approved Docker/Compose documentation exist. The approved
complete-platform `docker compose up --build` requirement remains outstanding;
AI-001 does not implement it.

## Integration Decisions

| Area | Finding | Status | Evidence |
| ---- | ------- | ------ | -------- |
| Application factory/composition | Extend `backend/app/__init__.py:create_app`; preserve optional service injection and one request session. | EXISTING | `backend/app/__init__.py` |
| Request session lifecycle | Open in `before_request`, close/remove in `teardown_request`; both repositories share it. | EXISTING | `backend/app/__init__.py`; `backend/app/infrastructure/database.py` |
| Message model | Add `Message`/`MessageRole` to `backend/app/infrastructure/consultation_models.py` and shared `Base`. | ABSENT | Existing mapping module; approved plan §4 |
| Message repository | Add `backend/app/repositories/message_repository.py`, accepting a `Session`. | ABSENT | Existing repository location; approved plan §5 |
| Application integration | Extend `ConsultationApplicationService` in `backend/app/application/consultation_service.py`. | EXISTING | Existing service; approved plan §6 |
| API DTO/routes | Extend `consultation_dtos.py` and `consultation_routes.py` on the existing blueprint. | EXISTING | `backend/app/api/` |
| API prefix/endpoints | Use `/api/v1` and the approved nested GET/POST message paths. | EXISTING | Factory registration; Feature 002 spec §7 |
| Error envelope | Keep `error`; use established 400/404/500 bodies and approved 503 recovery extension. | EXISTING | Factory/routes; approved plan §§6, 8 |
| Application not-found | Repository `None` becomes `ConsultationNotFoundError`; route returns safe 404. | EXISTING | Service/routes |
| Identifier representation | Native PostgreSQL/Python UUID; JSON/TypeScript string. | EXISTING | Model, DTO, API/frontend tests |
| Enum pattern | Python string enum plus named native PostgreSQL enum. | EXISTING | Model and `20260813_01` |
| Timestamp convention | No existing column; first use is timezone-aware server-default timestamp and `(created_at, id)` ordering. | ABSENT | Repository inspection; approved plan §4 |
| Frontend service/types | Extend feature-local `consultationApi.ts` and `consultationTypes.ts` with runtime guards. | EXISTING | Frontend feature files |
| Detail extension | Extend `ConsultationDetailScreen.tsx` after current fields at `/consultations/:consultationId`. | EXISTING | Screen and `App.tsx` |
| Backend tests | Use `backend/tests/{application,api}/` plus PostgreSQL repository/persistence tests in `backend/tests/`. | EXISTING | Current test tree/conftest |
| Frontend tests | Colocate Vitest/RTL tests in the consultation-records feature. | EXISTING | Current frontend test tree |
| AI modules | Add approved minimal `backend/app/ai/` tree in AI-004. | ABSENT | Repository inspection; approved plan §7 |
| Provider/config seam | Central environment mapping + `create_app` composition; inject provider-neutral AI service. | ABSENT | Database precedent; approved plan §§7–8 |
| AI environment values | Root has `AI_PROVIDER`/`OPENAI_API_KEY`; backend example and `OPENAI_MODEL` are absent; frontend correctly has none. | ABSENT | `.env.example` files |
| Dependencies | Backend: `backend/requirements.txt`; frontend: `frontend/package.json` and lockfile; no LangChain/OpenAI package yet. | EXISTING | Dependency files |
| Alembic chain | Next revision follows `20260813_01`; config/env/metadata are established. | EXISTING | `backend/alembic.ini`; migrations |
| Docker/Compose | Complete application Dockerfiles and Compose are missing. | ABSENT | Repository inspection; ADR-006 |

## Feature 002 Integration Map

```text
React Consultation Detail
→ consultationApi
→ Flask consultation blueprint
→ Pydantic DTOs
→ ConsultationApplicationService
→ MessageRepository
→ PostgreSQL

ConsultationApplicationService
→ AIService
→ ConsultationAgent
→ ConsultationSkill
→ provider
```

The application service owns the sequence: validate consultation, commit the
user message, reload/select persisted context, invoke AI, and commit the
assistant message. No transaction remains open across the provider call.

## Open Decisions

No genuine blocker remains for later tasks. The exact default value for the
optional `OPENAI_MODEL` is intentionally a bounded AI-004 first-use decision;
it does not alter the approved composition seam or contract.

## Parallel Development Readiness

- AI-002/AI-003 may independently add the single message mapping/migration and
  focused repository using the established `Base`, UUID/native-enum patterns,
  Alembic chain, request session, and PostgreSQL test strategy.
- AI-004 may independently add the approved AI-layer modules, backend-only
  configuration, dependencies, OpenAI provider, deterministic mock, and unit
  tests. It must not add persistence, routes, or user-facing provider choice.
- AI-005 is the later join point that injects both paths into the existing
  consultation application service and factory.

All Feature 002 exclusions remain in force: no consultation CRUD/status
changes, recommendations, appointments, summaries, RAG, embeddings, vectors,
LangGraph, tools, multiple agents, unlimited provider history, or user-facing
provider selection are introduced by these integration decisions.
