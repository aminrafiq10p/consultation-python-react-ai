# Backend Architecture

## Scope

The backend is a Python Flask application that exposes the REST API and coordinates application services without owning frontend, AI-provider, or infrastructure concerns.

## Layers

- **API layer:** Flask routes accept requests and return responses.
- **DTO validation:** Pydantic validates request and response data at boundaries.
- **Application services:** coordinate consultation, recommendation, summary, and appointment use cases.
- **Domain/business logic:** contains business rules.
- **Repositories:** isolate SQLAlchemy persistence access.
- **Infrastructure:** SQLAlchemy and Alembic support PostgreSQL persistence and schema evolution.

## Rules

- API routes must not directly manipulate database persistence.
- Business logic belongs in application and domain services.
- AI logic remains in the AI layer and is invoked through services, not implemented in routes.
- Appointment creation remains deterministic.

The layered design keeps the small, two-day delivery focused while preserving clear boundaries for later work.
