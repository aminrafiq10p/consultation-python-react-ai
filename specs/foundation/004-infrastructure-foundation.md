# Infrastructure Foundation Specification

## 1. Purpose and Scope

Define the minimal, reproducible infrastructure foundation required before
implementation begins for the AI Consultation Platform. The foundation shall
provide a Docker Compose runtime for the approved React frontend, Flask
backend, and PostgreSQL database, enabling the complete platform to run
locally without an external AI service.

This specification defines infrastructure responsibilities and constraints. It
does not define Dockerfiles, Compose YAML, image versions, commands beyond the
approved startup outcome, scripts, deployment automation, or cloud resources.

This specification authorizes no implementation by itself. Infrastructure
implementation begins only after this specification is approved and a plan and
tasks are created.

## 2. Docker Compose Responsibility

Docker Compose shall provide the mandatory local and complete-platform runtime.
It shall compose the three approved containers and support the established
startup outcome:

```bash
docker compose up --build
```

The runtime shall be reproducible from the repository's documented
configuration and must remain working as approved platform capabilities are
implemented. Docker Compose is not a basis for additional services or
deployment targets without a separate approved specification.

## 3. Container Boundaries

The complete runtime shall contain exactly these approved service boundaries:

- a React frontend container;
- a Flask backend container; and
- a PostgreSQL container.

Each service shall own its corresponding runtime responsibility. Services
shall interact only through their approved network and application boundaries;
containerization shall not collapse frontend, backend, persistence, or AI
responsibilities into one concern.

## 4. Frontend Container Requirements

The frontend shall run in its own container with the approved React,
TypeScript, Vite, React Router, and MUI foundation. It shall communicate with
the backend only through the approved REST API boundary and dedicated frontend
API/service layer.

The frontend container shall not connect to PostgreSQL, use backend/database
credentials, or contain AI-provider secrets. Any frontend configuration shall
remain browser-safe and environment-driven.

## 5. Backend Container Requirements

The backend shall run in its own container with the approved Flask, Pydantic,
SQLAlchemy, Alembic, and separated AI-layer foundation. It shall access
PostgreSQL only through the approved SQLAlchemy/repository infrastructure
boundary.

The backend container shall operate with `MockAIProvider` without external AI
credentials. It may communicate with an external AI provider only when the
optional provider is explicitly configured using server-side environment
configuration. Provider secrets shall never be embedded in container artifacts
or exposed to the frontend.

## 6. PostgreSQL Container Requirements

PostgreSQL shall run in its own container as the system of record for platform
and conversation state. It shall receive database connections only from the
backend through the Docker Compose service network and the approved
SQLAlchemy/repository boundary.

The database shall not be exposed beyond what the local development/runtime
requires. Its data shall persist through an appropriate Docker-managed volume;
database container replacement or restart must not implicitly discard persisted
state.

## 7. Docker Network and Service Communication

Docker Compose shall provide service-to-service communication through its
managed network. The frontend shall communicate with the backend over the REST
API boundary, and the backend shall communicate with PostgreSQL through its
persistence configuration.

Network configuration shall avoid hardcoded implementation-specific hostnames,
ports, and connection values outside environment/configuration boundaries.
Services shall not bypass the approved frontend-to-backend or
backend-to-database boundaries.

## 8. Environment and Configuration Handling

Runtime configuration shall be supplied through environment variables in line
with the project, backend, frontend, and database foundation specifications.
Configuration shall distinguish browser-safe frontend values from server-side
backend and database values.

Secrets, including database credentials and optional external AI-provider keys,
shall not be committed, hardcoded, logged, or placed in frontend-exposed
configuration. The infrastructure configuration shall support a complete mock
AI runtime with no external AI credentials.

## 9. PostgreSQL Persistence and Volume Expectations

The PostgreSQL container shall use an appropriate persistent Docker volume for
database state. Volume ownership and lifecycle shall support repeatable local
development without treating ephemeral container filesystems as durable
application storage.

This foundation does not define volume names, host mounts, backup procedures,
or database initialization/migration commands. Schema evolution remains under
Alembic as defined by the database foundation.

## 10. Startup and Dependency Expectations

The composed runtime shall support the approved complete-platform startup
outcome and account for required service availability: the frontend depends on
the backend API being reachable, and the backend depends on PostgreSQL being
available for persistence work.

Implementation shall use an appropriately simple readiness/dependency approach
for the two-day scope. It shall not assume container start order alone proves a
dependency is ready, nor introduce complex orchestration systems.

## 11. Local Development Requirements

Docker Compose shall provide the supported local runtime for the full platform,
with frontend, backend, and PostgreSQL configured from documented environment
values. The platform shall be runnable without external managed services and
without external AI credentials when the mock provider is selected.

Local development documentation added during implementation shall state the
required safe configuration steps and approved startup outcome without
disclosing secrets. Azure deployment remains optional and outside the two-day
core scope.

## 12. Containerization Constraints

- All application dependencies shall be containerizable.
- Infrastructure shall remain limited to the three approved containers unless a
  later ADR and specification approve a change.
- Kubernetes, Terraform, Azure or AWS infrastructure, CI/CD platforms, Nginx,
  Redis, RabbitMQ, Kafka, service mesh technology, monitoring platforms,
  external managed PostgreSQL, and additional containers are outside this
  foundation.
- The infrastructure shall not introduce host-specific assumptions that prevent
  the approved Docker Compose runtime.
- RAG and supporting vector or NoSQL infrastructure are outside the two-day
  core scope.

## 13. Definition of Done

Infrastructure foundation implementation work is complete only when all of the
following are satisfied:

- Docker Compose provides a reproducible frontend, backend, and PostgreSQL
  runtime compatible with `docker compose up --build`.
- Each application concern runs in its designated container and preserves the
  approved communication boundaries.
- Service-to-service communication uses the Docker Compose network and does not
  bypass frontend-to-backend or backend-to-database boundaries.
- Runtime configuration is environment-driven, browser-safe frontend values are
  separated from server-side values, and secrets are not exposed.
- PostgreSQL uses persistent Docker volume storage and is not unnecessarily
  exposed.
- The backend works with the mock AI provider without external credentials; an
  optional external provider is used only when explicitly configured.
- Startup accounts for required service readiness without unapproved complex
  orchestration.
- No unapproved container, technology, cloud infrastructure, deployment
  system, or scope expansion is introduced.

## 14. Acceptance Criteria

This infrastructure foundation specification is accepted when:

- `specs/foundation/004-infrastructure-foundation.md` exists.
- It defines Docker Compose as the required complete-platform runtime for a
  React frontend, Flask backend, and PostgreSQL container.
- It defines isolated container responsibilities; Docker Compose network
  communication; environment-based, secret-safe configuration; PostgreSQL
  persistent-volume expectations; and simple startup/readiness expectations.
- It preserves the frontend REST API boundary, backend
  SQLAlchemy/repository-to-PostgreSQL boundary, mandatory mock AI runtime, and
  optional external provider configuration.
- It requires the approved `docker compose up --build` startup outcome and
  keeps Azure deployment outside the two-day core scope.
- It excludes Dockerfile and Compose implementation details, deployment
  scripts, Kubernetes, Terraform, Azure/AWS infrastructure, CI/CD, Nginx,
  Redis, RabbitMQ, Kafka, service mesh, monitoring platforms, external managed
  PostgreSQL, additional containers, and unapproved infrastructure.
- No Dockerfiles, Compose files, scripts, infrastructure files, or
  architecture/ADR changes are created by this phase.
