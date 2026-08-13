# ADR-002: Flask over FastAPI

## Status

Accepted

## Context

The project is intended to reinforce Flask training while delivering a REST API within a two-day constraint.

## Decision

Use Flask for the backend REST API rather than FastAPI.

## Alternatives Considered

FastAPI was considered but not selected.

## Rationale

Flask aligns with the project's training goal and supports the approved layered backend design.

## Consequences

The API layer uses Flask and Pydantic DTO validation, delegating business use cases to application and domain services. Routes must not directly manipulate database persistence.
