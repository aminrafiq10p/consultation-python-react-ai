# ADR-006: Docker Compose

## Status

Accepted

## Context

The full platform needs a reproducible local runtime for frontend, backend, and database services.

## Decision

Use Docker Compose as part of the project foundation.

## Alternatives Considered

Running each service only through host-specific setup was considered and not selected.

## Rationale

Docker Compose provides one containerized environment for the approved application components.

## Consequences

The complete application must run with `docker compose up --build` using frontend, backend, and PostgreSQL containers. Dependencies must remain containerizable. Azure deployment is optional and not required.
