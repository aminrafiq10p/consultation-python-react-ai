# Project Development Guidelines

## General

- Follow specification-driven development.
- Do not implement features without an approved specification.
- Do not change architecture without documenting the decision.
- Keep frontend, backend, AI, and infrastructure concerns separated.
- Do not hardcode application data in place of persistence.
- All feature work must include appropriate tests.
- Keep Docker support working throughout development.

## Specification Workflow

Requirement
→ Specification
→ Plan
→ Tasks
→ Implementation
→ Tests
→ Definition of Done

## Feature Development

A feature specification is the source of truth.

Implementation tasks may be divided into:

- backend
- frontend
- AI
- database
- testing
- integration

## Backend

- Flask is the API framework.
- SQLAlchemy is the ORM.
- PostgreSQL is the database.
- Pydantic is used for DTO validation.
- Keep API, application, domain, AI, and infrastructure concerns separated.

## Frontend

- React + TypeScript.
- MUI for UI components.
- Feature-oriented structure.
- API communication through dedicated services.

## AI

- Keep AI logic separate from Flask API routes.
- Use an AI provider abstraction.
- Mock AI must be supported.
- OpenAI is an optional provider.
- LangChain is used inside the AI layer, not throughout the application.
- Business-critical operations such as appointment creation must remain deterministic.

## Docker

- The complete application must run with Docker Compose.
- Do not introduce dependencies that cannot be containerized.

## Before Completing a Task

- Run relevant tests.
- Run lint/type checks where applicable.
- Verify the implementation against the specification.
- Do not mark a task complete if acceptance criteria are not satisfied.
