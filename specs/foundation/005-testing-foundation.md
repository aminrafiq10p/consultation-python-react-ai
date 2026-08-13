# Testing Foundation Specification

## 1. Purpose and Scope

Define the project-wide testing foundation required for approved feature work.
The foundation shall provide proportionate, deterministic verification of
behavior and acceptance criteria across the React frontend, Flask backend,
PostgreSQL persistence, and isolated AI layer.

This specification establishes testing responsibilities and boundaries. It
does not define test files, test configuration, fixtures, CI/CD, feature test
cases, coverage thresholds, or application implementation.

## 2. Backend Testing with Pytest

Backend behavior shall be testable independently of the frontend using Pytest.
Backend tests shall cover the appropriate changed responsibilities, including
domain behavior, application workflows, API boundary behavior,
repository/persistence behavior, and AI-service integration as a feature
requires.

Backend tests shall not require production credentials, a live optional AI
provider, or frontend runtime availability.

## 3. Frontend Testing with React Testing Library

Frontend behavior shall be testable with React Testing Library. Tests shall
verify user-observable behavior where practical, including rendered states,
navigation outcomes, form feedback, loading states, recoverable errors, and
user interactions relevant to an approved feature.

Frontend tests shall not depend on implementation details, live backend
availability, PostgreSQL access, or external AI-provider credentials.

## 4. Unit Testing Expectations

Unit tests shall verify isolated, deterministic behavior in the relevant layer,
especially domain rules, application decisions, frontend presentation logic,
and AI-layer result handling where applicable. They shall be focused on
observable inputs, outputs, and acceptance criteria rather than internal
implementation structure where practical.

Tests shall remain proportionate to the two-day scope. This foundation does
not require an exhaustive test taxonomy or unnecessary abstraction around test
utilities.

## 5. API and Application Testing Expectations

Backend tests shall verify that the API boundary validates and translates HTTP
requests and responses, delegates workflows to application services, and
returns safe, consistent outcomes for successful and failure behavior as later
contracts specify.

Application tests shall verify use-case coordination and deterministic
business-control boundaries. They shall confirm that Flask routes do not own
business workflows, persistence access, LangChain orchestration, or
provider-specific behavior.

## 6. Persistence and Integration Testing Expectations

When an approved feature changes persisted state, tests shall verify the
relevant repository/persistence behavior, data state outcomes, and required
transactional behavior. Integration tests may exercise approved boundaries
across API, application, repositories, and PostgreSQL where that provides
meaningful confidence.

Integration coverage shall be focused on the core flow and remain proportional
to the two-day delivery. It shall not replace targeted backend, frontend, or
AI-layer tests.

## 7. AI Testing Using MockAIProvider

`MockAIProvider` shall be the default mechanism for core AI tests. Tests must
not require live OpenAI or Azure OpenAI APIs, their credentials, or network
access to external AI services.

Tests shall be able to verify the approved deterministic path:

```text
User Input
    ↓
Application Service
    ↓
AI Service
    ↓
MockAIProvider
    ↓
Structured AI Result
```

AI tests shall verify that provider integration remains isolated, results are
handled through the approved application/AI boundaries, and LLM assistance does
not autonomously create appointments or enact consultation status transitions.
Prompts, individual skills, and optional-provider behavior require later
specifications.

## 8. Frontend Behavior Testing

Frontend tests shall verify that feature UI communicates through the dedicated
API/service layer and presents backend-driven persisted state appropriately.
Temporary UI interaction state may be tested in the feature that owns it, but
tests shall preserve the backend as the authority for persisted consultation
and conversation state.

Tests shall confirm appropriate user-visible loading, success, validation, and
error feedback for the approved behavior without duplicating backend business
rules in the frontend test suite.

## 9. Feature and Vertical-Slice Testing

An approved feature is not complete without tests appropriate to its acceptance
criteria. Where a feature spans frontend, backend, AI, persistence, or
integration responsibilities, its test coverage shall verify the required
vertical slice at the appropriate boundaries.

Tests shall trace to the feature specification and focus on the most important
core-flow behavior. Optional integrations shall not block completion of the
mock-provider core runtime.

## 10. Test Isolation and Determinism

Core tests shall be deterministic, isolated from external services, and safe
to run repeatedly. Tests shall avoid reliance on production credentials,
production data, uncommitted local state, time-sensitive behavior, or prior
test execution.

Test data, mocks, database state, and configuration shall be controlled to
prevent cross-test interference. Exact fixtures, setup/teardown, time control,
and test-database lifecycle are deferred to later approved specifications and
plans.

## 11. Docker and Database Testing Expectations

Persistence and integration tests that require PostgreSQL shall use the
approved Docker Compose/PostgreSQL environment or an equivalent approved local
PostgreSQL test arrangement. They shall not require managed databases or
additional infrastructure.

Tests shall not depend on the complete frontend runtime when verifying backend
or persistence behavior independently. Docker Compose compatibility shall be
verified for implemented vertical slices where applicable, while avoiding a
complex end-to-end testing platform outside the two-day scope.

## 12. Definition of Done

Testing work for an approved implementation is complete only when:

- Tests cover the changed behavior and applicable acceptance criteria in
  proportion to the feature scope.
- Backend tests run independently with Pytest, and frontend behavior tests use
  React Testing Library.
- Persisted-state changes have appropriate persistence or integration coverage.
- Core AI behavior uses `MockAIProvider` and does not require external AI APIs
  or credentials.
- Tests are deterministic, isolated, and do not expose or depend on production
  secrets or data.
- Relevant vertical-slice boundaries are verified where the feature spans
  frontend, backend, AI, persistence, or integration.
- Applicable linting and type checks pass, as required by the project
  foundation and feature specification.
- No unapproved test technology, infrastructure, CI/CD system, or scope
  expansion is introduced.

## 13. Acceptance Criteria

This testing foundation specification is accepted when:

- `specs/foundation/005-testing-foundation.md` exists.
- It defines Pytest for independently executable backend testing and React
  Testing Library for user-observable frontend behavior testing.
- It defines focused unit, API/application, persistence/integration, AI,
  frontend behavior, and vertical-slice testing expectations.
- It requires `MockAIProvider` for deterministic core AI tests and prohibits
  dependence on live OpenAI/Azure OpenAI APIs or production credentials.
- It requires persistence testing when feature behavior changes database state
  and supports PostgreSQL through the approved Docker Compose environment when
  integration testing requires it.
- It requires test isolation, repeatability, deterministic core behavior, and
  proportional coverage for the two-day scope.
- It excludes test files, test configuration, CI/CD files, feature test cases,
  coverage thresholds, application implementation, external managed services,
  and unapproved testing technologies.
- No test files, test configuration, CI/CD files, application files, or
  architecture/ADR changes are created by this phase.
