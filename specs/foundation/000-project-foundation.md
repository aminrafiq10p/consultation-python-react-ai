# Project Foundation Specification

## 1. Purpose

Define the project-wide requirements and standards that govern all subsequent
specifications, plans, tasks, implementation, testing, and documentation for
the AI Consultation Platform. This specification establishes shared delivery
constraints and boundaries; it does not define implementation details for an
individual frontend, backend, AI, database, or infrastructure component.

## 2. Scope

This specification applies to the complete platform and its core user flow:

```text
Dashboard
→ Consultation Records
→ Consultation Detail / AI Chat
→ Consultation Summary
→ Appointment Booking
→ Consultation Records
```

It governs work that will later deliver the approved React + TypeScript
frontend, Flask REST API, PostgreSQL persistence, LangChain-contained AI
layer, AI provider abstraction, and Docker Compose runtime.

This specification does not authorize implementation work, create a feature
contract, or prescribe individual files, classes, functions, endpoints,
schemas, or user-interface designs. Those requirements belong in approved
subsequent specifications.

## 3. Project Repository Structure

The repository shall keep project concerns and governance material clearly
separated. At this phase, the repository includes the approved architecture and
decision records, project guidance, environment example, and this
specification structure:

```text
AGENTS.md
README.md
.env.example
.gitignore
docs/
  architecture/
  decisions/
specs/
  foundation/
  features/
```

Future implementation directories and files shall be introduced only when an
approved specification requires them. Their structure shall preserve separation
between frontend, backend, AI, database/persistence, and infrastructure
concerns.

## 4. Development Workflow

All work shall follow this ordered workflow:

```text
Requirement
→ Architecture
→ Specification
→ Plan
→ Tasks
→ Implementation
→ Tests
→ Definition of Done
```

Plans and tasks shall trace to an approved specification. Work may be divided
into backend, frontend, AI, database, testing, and integration tasks where
applicable, while retaining a complete vertical-slice outcome for each approved
feature.

## 5. Specification-Driven Development Rules

- An approved specification is the source of truth for implementation scope and
  acceptance criteria.
- No feature, implementation work, dependency, or material design decision may
  be introduced without an approved specification.
- Specifications shall state required outcomes, constraints, scope, and
  acceptance criteria. They shall not prematurely prescribe low-level
  implementation details unless that detail is necessary to uphold an approved
  architectural decision.
- Conflicts between a proposed specification and an accepted architecture
  document or ADR shall be identified and resolved before implementation.
- Completion requires verification against the applicable specification, not
  only the presence of code.

## 6. Architecture and ADR Compliance

The approved architecture documents in `docs/architecture/` and accepted ADRs
in `docs/decisions/` are binding for subsequent project work.

- Architecture changes require a documented decision before implementation.
- The approved stack is React, TypeScript, React Router, MUI, Python, Flask,
  PostgreSQL, SQLAlchemy, Alembic, Pydantic, LangChain, and Docker Compose.
- The AI provider abstraction includes mandatory mock support and optional
  OpenAI support; Azure OpenAI is future/optional.
- No technology or dependency may be added outside approved scope without an
  ADR and an applicable specification.

## 7. Environment Configuration Strategy

Runtime configuration shall be externalized through environment variables, with
`.env.example` documenting required variable names and safe development
defaults. Environment-specific values shall not be embedded as application
business data or committed secrets.

Configuration requirements introduced by later specifications shall document
their purpose, whether they are required or optional, and the environments to
which they apply. The platform must retain a local configuration path using the
mock AI provider that does not require an external AI API.

## 8. Secrets Management

- Secrets, credentials, tokens, and external provider keys shall never be
  committed to the repository, documentation examples, logs, or client-side
  bundles.
- Local secret values shall be supplied through ignored environment files or
  deployment-managed secret configuration.
- `.env.example` shall contain placeholders or non-sensitive development
  defaults only.
- Optional AI-provider credentials shall be required only when that provider is
  selected.

## 9. Naming Conventions

Names shall be clear, consistent, domain-oriented, and appropriate to their
layer and language ecosystem. The platform shall use the established domain
terms `consultation`, `message`, `recommendation`, and `appointment`
consistently across specifications, API contracts, persistence vocabulary, and
user-facing feature descriptions unless a later approved specification defines
a necessary distinction.

Abbreviations, ambiguous names, and names that expose an implementation-layer
concept through an unrelated boundary shall be avoided. Naming details for
individual APIs, persistence entities, modules, and UI components shall be
defined by their relevant specifications.

## 10. Code Organization Principles

- Ownership and dependencies shall follow concern boundaries, not convenience.
- Frontend, backend, AI, persistence, and infrastructure responsibilities shall
  remain separately organized.
- Backend responsibilities shall distinguish API, application, domain,
  repository, and infrastructure concerns.
- Frontend organization shall be feature-oriented; API communication shall be
  owned by dedicated frontend API/service modules.
- Shared code shall be introduced only when an approved specification defines a
  justified shared responsibility and ownership.

## 11. API, Frontend, and Backend Separation

The Flask REST API is the boundary between the React frontend and backend
application services.

- The frontend shall interact with backend capabilities only through dedicated
  API/service modules.
- The frontend shall not own persistence logic or backend business decisions.
- Flask routes shall validate boundary DTOs with Pydantic, handle HTTP
  representations, and delegate use cases to application services.
- API routes shall not directly manipulate persistence, contain domain business
  rules, or implement AI/provider-specific logic.
- Application and domain services shall own deterministic business operations.

## 12. AI Architecture Boundaries

- AI-assisted consultation responses, recommendations, and summaries shall be
  isolated in the AI layer and invoked through application services.
- LangChain shall be used only within the AI layer for agent, tool, and LLM
  orchestration.
- The provider abstraction shall keep provider-specific integration separate
  from core application behavior.
- `MockAIProvider` support is mandatory so the complete platform can run
  without an external AI API.
- OpenAI integration is optional; Azure OpenAI remains future/optional.
- LLM output may assist consultation workflows but shall not autonomously create
  appointments or enact consultation status transitions.

## 13. Database and Persistence Principles

- PostgreSQL is the system of record for persisted platform data, including
  conversation state.
- The persisted core domain includes consultations, messages, recommendations,
  and appointments, with their approved relationships to be refined in later
  specifications.
- SQLAlchemy access shall be isolated through repositories, and Alembic shall
  manage schema evolution.
- Flask API routes shall not access persistence directly.
- No hardcoded application business data may substitute for real persistence.
- Data model, migration, integrity, and lifecycle details require later
  approved specifications.

## 14. Docker and Infrastructure Principles

- Docker Compose is mandatory for the complete application runtime.
- The complete runtime shall include frontend, backend, and PostgreSQL
  containers and support the approved `docker compose up --build` startup
  outcome.
- All implementation dependencies shall be containerizable.
- Docker Compose support shall remain working throughout development.
- External AI services are optional; the mock provider must support a complete
  local runtime without them.
- Azure deployment is outside the two-day core scope.

## 15. Testing Expectations

- Each approved feature shall include tests appropriate to its changed
  responsibilities and acceptance criteria.
- Backend testing shall use Pytest; frontend testing shall use React Testing
  Library.
- Relevant integration behavior shall be tested for complete vertical slices
  where applicable.
- Relevant linting and type checks shall run where applicable.
- Test coverage, test-data strategy, and exact quality gates shall be defined by
  subsequent approved specifications without weakening these baseline
  expectations.

## 16. Documentation Expectations

- Specifications, plans, tasks, and implementation outcomes shall remain
  traceable to their source requirements.
- Architecture documents and ADRs shall be updated only when a genuine,
  documented architecture decision is approved.
- Configuration, setup, runtime, and user-facing behavior shall be documented
  as later approved work introduces them.
- Documentation examples shall not disclose secrets or present optional
  integrations as mandatory core requirements.

## 17. Git and Change Management Expectations

- Changes shall be focused, reviewable, and traceable to an approved
  specification and plan/task.
- Unrelated repository changes shall not be modified as part of scoped work.
- Changes that alter architecture, dependencies, configuration contracts, or
  delivery scope shall be documented and approved before implementation.
- Generated artifacts, local environment files, credentials, logs, and other
  ignored local state shall not be committed.

## 18. Definition of Done

Work governed by a later approved specification is complete only when all of
the following are satisfied:

- Its requirements and acceptance criteria are met and verified.
- Its implementation respects the approved architecture, ADRs, and this
  foundation specification.
- Appropriate tests pass, and relevant lint/type checks pass where applicable.
- Required documentation and configuration guidance are updated.
- The affected vertical slice is complete across required frontend, backend,
  AI, database, testing, and integration responsibilities.
- Docker Compose support remains valid for implemented platform capabilities.
- No unapproved scope, dependency, architecture change, or secret exposure is
  introduced.

## 19. Two-Day Delivery Constraints

The project is constrained to a two-day core delivery. Subsequent work shall
prioritize the approved core flow and a working, containerized vertical slice.
Optional integrations and enhancements must not delay, replace, or compromise
the core delivery.

OpenAI integration, Azure OpenAI integration, Azure deployment, and dynamic
conversation branching are optional and shall not be required to complete the
core scope. The mandatory mock provider is the baseline for a complete local
runtime.

## 20. Scope Control and Prohibited Scope Creep

The following are prohibited unless supported by an approved ADR and
specification:

- Implementing features before their specifications are approved.
- Adding technologies, dependencies, external services, deployment targets, or
  integrations outside the approved stack.
- Changing accepted architectural boundaries or replacing approved technologies.
- Allowing frontend code, API routes, or LLM behavior to bypass deterministic
  application and persistence boundaries.
- Allowing LLMs to autonomously create appointments or enact consultation status
  transitions.
- Treating optional provider or Azure capabilities as core two-day requirements.
- Using hardcoded business data in place of persisted application data.

Any proposal outside approved scope shall be documented, evaluated, and
approved before work proceeds.

## 21. Acceptance Criteria

This foundation specification is accepted when:

- `specs/foundation/` and `specs/features/` exist.
- `specs/foundation/000-project-foundation.md` exists and defines the
  project-wide requirements and standards before implementation begins.
- The specification covers all 20 required foundation topics: purpose; scope;
  repository structure; workflow; specification-driven rules; architecture/ADR
  compliance; environment configuration; secrets; naming; organization; API,
  frontend, and backend separation; AI boundaries; persistence; Docker and
  infrastructure; testing; documentation; Git/change management; Definition of
  Done; two-day constraints; and scope control.
- The specification preserves the approved architecture and ADRs without
  changing them.
- The specification does not define implementation files, classes, functions,
  database models, migrations, Docker configuration, or individual feature
  contracts.
- No application, infrastructure, database, or dependency implementation files
  are created by this phase.
