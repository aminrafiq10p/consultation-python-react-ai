# CR-001 Findings

## Backend Conventions

The repository has no implemented backend files. The following are binding
foundation conventions, rather than code-established module/file conventions:

- Use a Flask application factory as the composition boundary; it configures
  the application, registers the API boundary, initializes infrastructure, and
  supports independently created test applications.
- Organize backend responsibilities beneath the future `backend/app/` area:
  `api`, `application`, `domain`, `ai`, `infrastructure`, and narrowly owned
  `shared` utilities. The foundations reserve `backend/migrations/` for
  Alembic and `backend/tests/` for Pytest.
- Organize HTTP routes with Flask blueprints (or an equivalent Flask-native
  grouping) in the API layer. Route handlers parse/validate HTTP DTOs,
  delegate to application services, and serialize responses; they do not use
  repositories, sessions, domain rules, LangChain, or provider SDKs directly.
- The REST API is versioned in its path namespace. CR-001 confirms the feature
  contract uses the approved `/api/v1` namespace.
- Validate request and response DTOs with Pydantic at the API boundary. DTOs
  are explicit HTTP/application translations, not SQLAlchemy models.
- Application services coordinate use cases and remain independent of Flask
  objects, route mechanics, SQLAlchemy sessions, and provider SDK details.
- Repositories expose focused capabilities to application services; SQLAlchemy
  implementations belong in infrastructure. A generic repository framework is
  not an approved convention.
- API errors must be consistent and client-safe, with known outcomes translated
  at the API boundary and without stack traces, database details, credentials,
  or provider details. No concrete envelope or handler implementation exists.

## Database Conventions

The repository has no Alembic configuration, SQLAlchemy mapping, database
configuration, or test database implementation. Binding foundation rules are:

- PostgreSQL is the system of record; hardcoded business data is not a
  persistence substitute.
- SQLAlchemy mappings, engine/configuration, session lifecycle, and repository
  implementations belong in backend infrastructure. SQLAlchemy types and
  session details must not cross into API DTOs, frontend code, domain behavior,
  or application services.
- Alembic is the only approved schema-evolution mechanism. Reviewable,
  versioned migrations belong under the future `backend/migrations/` location.
- Database configuration is centralized and environment-driven. The existing
  `.env.example` documents `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, and `POSTGRES_PORT` as safe local-development inputs.
- Infrastructure centrally owns a predictable connection/session lifecycle:
  release sessions on completion and roll back on failure. The exact
  request/session factory/transaction implementation is not established.
- Persistence tests use Pytest and must support deterministic execution; test
  isolation, database lifecycle, fixtures, migration verification, and seed
  data conventions are explicitly deferred by the foundation.

## Frontend Conventions

The repository has no implemented frontend files. The following foundation
conventions govern later work:

- Use React, TypeScript, Vite, React Router, and MUI. The future structure is
  feature-oriented under `frontend/src/app/`, with `core`, `shared`, `layout`,
  and `features` responsibilities.
- Routing is centrally composed with React Router. Routes coordinate navigation
  and layout selection only; feature screens remain feature-owned and do not
  make HTTP requests.
- A dedicated API/service module is the sole frontend-to-backend boundary. It
  owns request construction, response translation into feature-facing types,
  and transport-error support. UI components do not access persistence or make
  direct network requests.
- Use simple React state/context only for temporary UI state. Backend API data
  remains authoritative for persisted consultations.
- Use MUI for layout, navigation, form controls, feedback states, and
  feature-appropriate presentation. No component-level convention exists yet.
- Each data-loading feature must make loading, successful/empty,
  recoverable-error, and unavailable-data states clear and safe. No existing
  UI error component, data-fetching hook, API client, or test utility exists.
- Feature tests may be colocated with the feature code; no top-level frontend
  test directory is required by the foundation.

## Testing Conventions

- Pytest is the approved backend test framework. The future
  `backend/tests/` location is reserved, but no test package, fixtures,
  conftest, API client, repository fixture, or PostgreSQL lifecycle strategy
  exists.
- React Testing Library is the approved frontend testing approach. Tests should
  assert user-observable behavior and must not require a live backend,
  PostgreSQL, or external AI credentials. No frontend test runner, setup,
  mocks, or file-placement convention exists.
- Tests must be deterministic and isolated. PostgreSQL persistence/integration
  coverage may use the approved Docker Compose/PostgreSQL environment (or an
  equivalent approved local PostgreSQL arrangement); exact setup remains
  absent.
- Consultation Records tests must use controlled persisted consultation data
  and no AI provider, LangChain workflow, external AI credential, messages,
  recommendation generation, or appointment data.

## Task-Local Decisions

| Area | Finding | Status | Evidence |
| --- | --- | --- | --- |
| Flask application factory | Required as the future backend composition boundary, but no factory/module exists to extend. | EXISTING | `specs/foundation/001-backend-foundation.md` §§4–5; empty `backend/` directory inspection |
| Blueprint and route registration | API-layer blueprints (or equivalent Flask-native grouping) are required; no registered blueprint or exact registration module exists. | ABSENT | `specs/foundation/001-backend-foundation.md` §6; empty `backend/` directory inspection |
| API versioning | Versioned route namespace is required; this feature contract establishes `/api/v1`. | EXISTING | `specs/foundation/001-backend-foundation.md` §7; `specs/features/001-consultation-records.md` §6 |
| Pydantic DTOs | Explicit Pydantic request and response DTOs at the API boundary are required; no existing DTO file/style exists. | EXISTING | `specs/foundation/001-backend-foundation.md` §8; empty `backend/` directory inspection |
| Error response envelope | Errors must be consistent and client-safe, but no JSON envelope, exception mapping, or handler convention is implemented or specified. | ABSENT | `specs/foundation/001-backend-foundation.md` §16; `specs/features/001-consultation-records.md` §6.3; empty `backend/` directory inspection |
| Application services | Services coordinate use cases without Flask or session mechanics; no class/function/module naming convention exists. | EXISTING | `specs/foundation/001-backend-foundation.md` §9 |
| Repository conventions | Focused repository capabilities with SQLAlchemy implementation in infrastructure are required; no interface or implementation naming convention exists. | EXISTING | `specs/foundation/001-backend-foundation.md` §§11–12; `specs/foundation/003-database-foundation.md` §§3–4 |
| SQLAlchemy models | Mappings belong in infrastructure; no declarative base, metadata, table naming, column typing, or model convention exists. | ABSENT | `specs/foundation/003-database-foundation.md` §3; empty `backend/` directory inspection |
| Session/transaction lifecycle | Infrastructure centrally owns sessions, release, rollback, and appropriate atomic transactions; exact lifecycle/scope convention is absent. | ABSENT | `specs/foundation/003-database-foundation.md` §§7–8 |
| Alembic | Alembic-only, versioned migrations belong in future `backend/migrations/`; no Alembic config, env, revision naming, or execution convention exists. | ABSENT | `specs/foundation/001-backend-foundation.md` §§4, 13; empty `backend/` directory inspection |
| PostgreSQL configuration/init | Environment-based PostgreSQL configuration is required and `.env.example` supplies local variable names; no compose/init implementation exists. | ABSENT | `specs/foundation/003-database-foundation.md` §§6, 10; `.env.example`; empty `infrastructure/docker/` directory inspection |
| Database test data | Deterministic Pytest persistence testing is required; fixtures, seed data, migration verification, isolation, and lifecycle conventions are absent. | ABSENT | `specs/foundation/003-database-foundation.md` §11; `specs/foundation/005-testing-foundation.md` §§6, 10–11 |
| Frontend feature/service structure | Feature ownership plus a dedicated API/service boundary are required; no source/module/type naming convention exists. | EXISTING | `specs/foundation/002-frontend-foundation.md` §§4, 7; empty `frontend/` directory inspection |
| React Router | Central React Router composition is required; no router or existing path convention exists. | ABSENT | `specs/foundation/002-frontend-foundation.md` §5; empty `frontend/` directory inspection |
| TypeScript/MUI/loading errors | React + TypeScript, MUI, simple UI state, and clear loading/empty/error/unavailable states are required; no component/style/error utility convention exists. | EXISTING | `specs/foundation/002-frontend-foundation.md` §§2, 9, 11–12 |
| Frontend tests | React Testing Library and user-observable assertions are required; runner, setup, service mock, and colocated naming convention are absent. | ABSENT | `specs/foundation/002-frontend-foundation.md` §13; `specs/foundation/005-testing-foundation.md` §3 |
| Consultation identifier representation | The API representation is a stable string `id`; no prior storage representation or route-parameter convention exists. Do not choose one in CR-001. | ABSENT | `specs/features/001-consultation-records.md` §§5–6; `plans/features/001-consultation-records.md` §17; no implementation files |
| Consultation detail route path | A React Router detail route containing the stable identifier is required; no existing frontend route naming exists. Do not choose a path in CR-001. | ABSENT | `specs/features/001-consultation-records.md` §8; `plans/features/001-consultation-records.md` §§11, 17; no implementation files |
| Conflicting conventions | No conflicting implemented conventions were found. | EXISTING | Repository inspection: no backend/frontend implementation files |

## Approved API Contract Confirmation

The approved contract is unchanged:

| Method | Path | Success representation/outcome |
| --- | --- | --- |
| `GET` | `/api/v1/consultations` | `{ "items": [consultation DTO, ...] }`; an empty match is `{ "items": [] }` |
| `GET` | `/api/v1/consultations/{consultation_id}` | One consultation DTO or `404` when absent |

Each consultation DTO contains only `id`, `patient_name`,
`primary_concern`, `recommended_procedure`, and `status`. `id` is the stable
consultation identifier represented as a string in the API. The only allowed
statuses are `PENDING`, `BOOKED`, and `COMPLETED`.

- `search` is optional. When supplied it must be non-empty after trimming; it
  is case-insensitive and matches `patient_name`, `primary_concern`, or
  `recommended_procedure`. Omission applies no text restriction.
- `status` is optional and must be exactly one approved status. Omission makes
  all approved statuses eligible.
- When both are supplied, both restrictions apply (logical AND).
- Invalid query or path input, including blank supplied `search` and an
  unsupported `status`, returns client-safe `400`.
- An absent detail record returns client-safe `404`.
- Unexpected failures return client-safe `500` without internals, persistence
  details, sensitive data, stack traces, or provider details. The exact error
  envelope is currently absent and is not defined here.
- Consultation Records has a strict no-AI boundary: no LangChain,
  `MockAIProvider`, AI provider, external AI credential, or AI workflow may be
  invoked. It only displays persisted `recommended_procedure` text.

## Parallel Development Readiness

The API paths, DTO fields, query behavior, status set, and HTTP outcome rules
are a stable backend/frontend boundary. Subject to the absent implementation
conventions recorded above:

- Backend can independently perform the approved CR-002 through CR-005 work:
  establish the first concrete infrastructure/factory/blueprint/error/session
  conventions, then implement the consultation migration, mapping, repository,
  read service, DTOs, routes, and Pytest coverage.
- Frontend can independently perform CR-006 through CR-008 against
  deterministic contract-shaped service stubs: feature-facing types, service,
  list/detail states, and React Testing Library tests do not need a running
  backend or PostgreSQL instance.
- Before wiring the detail screen route, the frontend implementation must make
  and record the exact detail path decision because no existing router naming
  convention exists. Before persistence work, the backend implementation must
  make and record the identifier storage representation and initial concrete
  factory/blueprint/error/session/Alembic conventions. These are first-use
  implementation decisions, not conflicts resolved by CR-001.
- Integration begins after both streams expose the approved contract-facing
  behavior; it validates the API/service connection and PostgreSQL-backed
  retrieval without changing the contract.

## Open Decisions

No conflicting conventions require resolution. The following conventions are
absent and must be selected by the applicable later implementation task without
changing the approved contract or architecture:

1. Consultation identifier storage representation, while preserving the API
   string `id` and route parameter contract.
2. Exact React Router consultation detail path and parameter spelling, while
   containing the stable identifier.
3. First concrete API error envelope/handlers that satisfy the client-safe
   `400`, `404`, and `500` requirements.
4. First concrete backend module/file names for factory, blueprints, DTOs,
   services, repository, SQLAlchemy base/session, and Alembic environment;
   database test lifecycle/fixtures; and frontend router/service/test setup.

These are absent rather than conflicting conventions. CR-001 intentionally
does not select or implement any of them.
