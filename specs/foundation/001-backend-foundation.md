# Backend Foundation Specification

## 1. Purpose

Define the backend foundation required before backend feature development begins
for the AI Consultation Platform. The foundation shall provide a clear,
testable, containerizable Flask REST API boundary and preserve the approved
layered architecture for application workflows, domain rules, persistence, and
AI integration.

This specification defines backend-wide responsibilities, boundaries, and
structure. It does not define individual feature behavior, HTTP endpoints,
database schemas, migrations, AI prompts, or AI skills.

## 2. Scope

This specification governs the future `backend/` project area and its runtime,
configuration, persistence integration, migration, testing, and container
requirements. It applies to the backend support needed for the approved core
flow while remaining intentionally small enough for the two-day delivery.

It authorizes no implementation by itself. Backend implementation begins only
after this specification is approved and a plan and tasks are created.

## 3. Backend Responsibilities

The backend shall:

- expose the Flask REST API used by the frontend;
- validate API request and response DTOs with Pydantic at API boundaries;
- delegate use cases to application services;
- enforce deterministic business workflows through application and domain
  responsibilities;
- persist application data in PostgreSQL through SQLAlchemy repositories;
- manage PostgreSQL schema evolution through Alembic migrations;
- coordinate AI assistance through a separated AI layer and provider
  abstraction;
- run with the mandatory mock AI provider without an external AI API;
- obtain runtime configuration from environment variables; and
- be independently testable and containerizable.

The backend shall not own frontend presentation concerns, implement external
provider details outside the AI layer, or treat LLM output as deterministic
business authority.

## 4. Backend Project Structure

The backend shall use a small, layer-oriented structure that reflects the
approved architecture without introducing generic frameworks or abstractions.
The expected foundation organization is:

```text
backend/
├── app/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── ai/
│   ├── infrastructure/
│   └── shared/
├── migrations/
├── tests/
├── Dockerfile
└── requirements.txt
```

The `app/` area shall contain backend runtime code organized by responsibility:

- `api/` owns Flask application/blueprint registration, HTTP concerns, DTO
  boundary handling, and API error translation.
- `application/` owns use-case coordination and workflows.
- `domain/` owns business rules and domain behavior.
- `ai/` owns AI services, consultation-agent orchestration, LangChain use,
  provider abstractions, and provider implementations.
- `infrastructure/` owns SQLAlchemy, repository implementations, database
  configuration, and other approved technical integrations.
- `shared/` contains only cross-cutting backend utilities or contracts with
  clearly defined ownership; it shall not become an unstructured common-code
  area.

`migrations/` shall be reserved for Alembic-managed schema migration assets;
`tests/` shall contain backend tests; the `Dockerfile` and dependency manifest
shall support the approved Docker Compose runtime. Exact module and file names
may be determined during implementation planning as long as they retain these
responsibilities and dependency boundaries.

No generic repository framework, excessive base-class hierarchy, CQRS, event
sourcing, microservice decomposition, message broker, dependency-injection
framework, background worker, Redis, Kubernetes, Terraform, or unapproved
technology is required or authorized by this foundation.

## 5. Flask Application Factory Requirements

The backend shall use an application factory as the composition boundary for
the Flask application. The factory shall support configuration by environment,
registration of the approved API boundary, initialization of approved backend
infrastructure, and independent test application creation.

The application factory shall not contain feature use-case logic, domain rules,
AI orchestration, or direct feature persistence behavior. It shall assemble
approved concerns without reversing their dependency direction.

## 6. API and Blueprint Organization

The REST API shall be organized through Flask blueprints or an equivalent
Flask-native route grouping mechanism inside the API layer. Route organization
shall keep HTTP handling separate from application workflows and allow feature
routes to be added without a single monolithic route module.

API handlers shall be limited to HTTP concerns: receiving requests, validating
and translating DTOs, delegating to application services, and returning
responses. They shall not directly manipulate SQLAlchemy sessions or
repositories, contain domain business rules, or invoke LangChain or
provider-specific SDKs.

## 7. API Versioning Boundary

The backend shall provide an explicit versioned REST API boundary from its
first externally consumable API. Version identification shall be part of the
API route namespace so the frontend has a stable, discoverable contract and
future changes can be introduced deliberately.

This foundation does not define a version identifier, endpoint inventory, or
resource contract. Those belong in later API and feature specifications.

## 8. DTO Validation Requirements

Pydantic shall validate request and response DTOs at the API boundary.

- API input shall be validated before an application service executes a use
  case.
- API output shall be represented by explicit response DTOs before being sent
  to a client.
- DTOs shall translate between HTTP representations and application-facing
  data without becoming persistence models or domain business-rule containers.
- Validation failures shall be translated into the consistent API error format
  defined by this foundation.

DTO contracts, fields, and endpoint-specific validation rules require later
specifications.

## 9. Application Service Layer

Application services shall coordinate backend use cases and control workflow
across domain behavior, repositories, and AI services where applicable.

Application services shall not depend on Flask request/response objects,
route-specific concerns, or provider SDK details. They shall preserve
deterministic control of business-critical operations, including appointment
creation and consultation status transitions. AI assistance may inform an
application workflow but shall not replace deterministic application decisions.

## 10. Domain and Business Logic Boundaries

The domain layer shall contain business rules and domain behavior. Domain code
shall not depend on Flask or on direct SQLAlchemy session details.

Domain behavior shall remain independent from HTTP transport, database access
mechanics, LangChain APIs, and provider SDKs. Individual consultation,
recommendation, summary, appointment, and status-transition rules are outside
this foundation and shall be specified before implementation.

## 11. Repository Layer

Repositories shall isolate persistence access from application and domain
layers. Application services shall use repository contracts or focused
repository capabilities rather than direct SQLAlchemy session manipulation.

Repository implementations belong to infrastructure and shall use SQLAlchemy
to access PostgreSQL. Repository design shall be explicit and task-focused; a
generic repository framework is not required. Repository APIs and behavior
shall be determined by later domain and feature specifications.

## 12. SQLAlchemy Requirements

SQLAlchemy shall be the backend ORM and persistence integration for
PostgreSQL. SQLAlchemy configuration, sessions, mappings, and repository
implementations shall remain in infrastructure rather than Flask routes,
application services, or the AI layer.

Persistence boundaries shall ensure that PostgreSQL is the source of truth for
persisted application and conversation state. SQLAlchemy-specific details shall
not be exposed as API DTOs or used as substitutes for domain behavior.

## 13. Alembic Migration Requirements

Alembic shall manage PostgreSQL schema evolution. Schema changes shall be
represented by versioned, reviewable migrations and shall be compatible with
the Docker Compose runtime.

Migration generation, review, and application procedures shall be defined by a
later database/persistence specification. Migrations shall not be manually
treated as an alternative to a specified data model, and this foundation does
not define any tables or schema revisions.

## 14. Configuration Management

Backend configuration shall be centralized, environment-driven, and separated
from business logic. Configuration shall distinguish environment-independent
application behavior from deployment-specific values such as runtime mode,
network bindings, database connection settings, and selected AI provider.

Configuration access shall be available to the composition and infrastructure
boundaries without scattering environment reads across API, application,
domain, or AI workflow code. Configuration defaults shall be safe for local
development and shall not embed secrets.

## 15. Environment Variables

The backend shall use the project environment configuration strategy defined
by `specs/foundation/000-project-foundation.md`. It shall honor the documented
project variables that apply to backend runtime, PostgreSQL connectivity, and
AI provider selection, including `APP_ENV`, PostgreSQL settings,
`BACKEND_PORT`, `AI_PROVIDER`, and optional `OPENAI_API_KEY`.

Later backend specifications may define additional environment variables only
when they document the variable purpose, required/optional status, and safe
example value, and only when no new dependency or architecture decision is
needed. Secrets shall be supplied outside version control; environment examples
shall contain no production credentials.

## 16. Error Handling

The API layer shall return consistent, client-safe error responses for request
validation, missing resources, domain/application failures, and unexpected
server failures. Error handling shall preserve an appropriate HTTP status while
avoiding disclosure of secrets, internal stack traces, database details, or
provider-specific implementation information.

The API layer shall translate known application/domain outcomes to HTTP
responses. Application and domain layers shall not depend on Flask response
types or route-level exception handling. Exact error response contracts and
feature-specific failure cases require later specifications.

## 17. Logging Requirements

The backend shall produce structured, operationally useful logs appropriate to
the configured environment. Logs shall support diagnosis of application
startup, HTTP request outcomes, unexpected failures, persistence/integration
availability, and selected AI-provider operation without exposing sensitive
request contents, credentials, API keys, or unnecessary private consultation
content.

Logging configuration shall be centralized. API, application, infrastructure,
and AI code may record events within their responsibility while maintaining the
same secret and privacy safeguards. Log sinks, formats, levels, and retention
details may be refined by later approved specifications without adding
unapproved infrastructure.

## 18. AI Integration Boundary

AI-specific functionality shall remain in `app/ai/` and be reached from
application services through an AI service/provider abstraction. LangChain
shall be contained inside this AI layer. Flask routes shall not invoke
LangChain, agents, skills, tools, or provider SDKs.

Provider-specific SDK details shall not leak into application or domain layers.
The AI layer shall support the mandatory mock provider as the default path for
running the backend without an external AI API. OpenAI is optional; Azure OpenAI
remains future/optional. This foundation does not define prompts, individual AI
skills, or provider implementation details.

## 19. Dependency Direction

Backend dependencies shall flow toward stable business responsibilities:

```text
API
  ↓
Application
  ↓
Domain and repository/AI contracts
  ↓
Infrastructure implementations and AI provider integrations
```

The API layer may depend on application services and DTOs. Application
services may coordinate domain behavior, repository capabilities, and AI
services. Infrastructure provides persistence implementations; the AI layer
provides AI implementations and provider integrations. Domain behavior shall
not depend on Flask, SQLAlchemy session details, LangChain, or provider SDKs.

No lower-level technical layer may require dependencies on Flask route modules
or frontend code. Dependency wiring shall occur at a backend composition
boundary and shall remain lightweight and explicit.

## 20. Testing Requirements

The backend shall be testable independently of the frontend using Pytest.
Tests shall be organized to verify relevant API boundary behavior, application
workflows, domain rules, repository/persistence behavior, AI-provider
abstraction behavior, and cross-layer integration as later specifications
require.

Tests shall not require a live external AI API for core behavior; the mock
provider shall support deterministic local and test execution. Test isolation,
database strategy, fixtures, and feature-specific test cases shall be defined
by later approved specifications.

## 21. Docker and Containerization Requirements

The backend shall be containerizable and participate in the mandatory Docker
Compose runtime with frontend and PostgreSQL services. Its container setup
shall obtain configuration through environment variables and shall not embed
secrets or rely on host-specific runtime dependencies.

The backend must remain compatible with the approved
`docker compose up --build` complete-platform outcome and with the mock AI
provider operating without external AI credentials. This foundation does not
define a Dockerfile, Compose service configuration, build commands, or runtime
orchestration details.

## 22. Backend Development Standards

- Backend work shall follow the approved specification-driven workflow and
  trace to an approved plan and tasks.
- Code shall remain focused on the approved two-day core scope and preserve the
  defined layer boundaries.
- Dependencies shall be limited to the approved stack unless an ADR and
  applicable specification approve a change.
- Configuration and secrets shall not be hardcoded.
- Application business data and conversation state shall use approved
  persistence rather than hardcoded data substitutes.
- Feature changes shall be complete vertical slices where applicable, including
  required backend, persistence, AI, testing, and integration responsibilities.
- Relevant tests, linting, and type checks shall pass before work is complete.
- Backend code and documentation shall remain readable, maintainable, and
  appropriately scoped; avoid abstractions that do not serve an approved need.

## 23. Definition of Done

Backend foundation implementation work is complete only when all of the
following are satisfied:

- The implemented structure and composition follow this specification and the
  approved project foundation, architecture documents, and ADRs.
- A Flask application factory, versioned API boundary, and API grouping exist
  according to the approved implementation plan.
- API boundary DTO validation, centralized configuration, consistent error
  handling, and safe logging are present.
- Application, domain, repository/infrastructure, and AI boundaries are
  preserved, with no route-level persistence, business-rule, LangChain, or
  provider-specific behavior.
- SQLAlchemy PostgreSQL persistence and Alembic migration support are prepared
  without defining unspecified feature schema behavior.
- The mock AI provider supports backend operation without external AI
  credentials.
- Relevant backend tests pass independently, along with applicable lint/type
  checks.
- The backend is containerized and remains compatible with the complete Docker
  Compose runtime.
- No unapproved technology, feature contract, schema, business rule, or scope
  expansion has been introduced.

## 24. Acceptance Criteria

This backend foundation specification is accepted when:

- `specs/foundation/001-backend-foundation.md` exists.
- It defines the backend foundation purpose, scope, responsibilities, and a
  justified lean backend project structure.
- It covers Flask application factory requirements; API/blueprint organization;
  API versioning boundary; DTO validation; application services; domain
  boundaries; repositories; SQLAlchemy; Alembic; configuration; environment
  variables; error handling; logging; AI integration; dependency direction;
  testing; Docker/containerization; development standards; and Definition of
  Done.
- It preserves the approved Flask, Pydantic, SQLAlchemy, Alembic, PostgreSQL,
  LangChain-contained AI, provider abstraction, mock provider, and Docker
  Compose decisions.
- It establishes that routes contain HTTP concerns only and do not directly
  manipulate persistence, implement business logic, or contain LangChain or
  provider-specific behavior.
- It establishes deterministic application control over appointment creation
  and consultation status transitions.
- It requires environment-based configuration, safe secret handling,
  independent backend testing, and containerization.
- It excludes individual endpoints, feature business rules, database schemas,
  migrations, prompts, individual AI skills, frontend implementation, and
  unapproved technologies.
- No backend source files, Dockerfiles, requirements files, migrations, models,
  tests, or architecture/ADR changes are created by this phase.
