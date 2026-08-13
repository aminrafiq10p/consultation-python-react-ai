# Database Foundation Specification

## 1. Purpose and Scope

Define the persistence foundation required before database and feature
implementation begins for the AI Consultation Platform. The foundation shall
provide a reliable PostgreSQL system of record, with SQLAlchemy persistence
isolated behind the approved repository/infrastructure boundary and Alembic
used for controlled schema evolution.

This specification applies to the persistence foundation for the approved core
data areas: consultations, messages, recommendations, and appointments. It
does not define their business schema, feature behavior, migrations, seed data,
or query-specific optimization.

This specification authorizes no implementation by itself. Database
implementation begins only after this specification is approved and a plan and
tasks are created.

## 2. PostgreSQL Responsibility

PostgreSQL shall be the system of record for persisted application data and
conversation state. Persisted data shall provide the authoritative state used
by backend workflows; hardcoded business data shall not substitute for
persistence.

The approved core relationships remain:

```text
consultation → messages        (1:N)
consultation → recommendation  (1:1)
consultation → appointment     (1:0..1)
```

Their table definitions, columns, constraints, foreign-key implementation,
enums, lifecycle rules, and indexes require later data-model or feature
specifications.

## 3. SQLAlchemy Responsibility

SQLAlchemy shall provide the approved backend ORM and PostgreSQL persistence
integration. SQLAlchemy configuration, mappings, sessions, and persistence
implementations shall reside in the backend infrastructure area.

SQLAlchemy-specific types and session details shall not become API DTOs,
frontend concerns, domain behavior, or application-service dependencies.

## 4. Repository and Persistence Boundary

Repositories shall isolate SQLAlchemy and PostgreSQL access from the rest of
the backend. Flask routes shall never directly access SQLAlchemy, sessions, or
repositories. Application services shall coordinate use cases through focused
repository capabilities, while domain and application code remain independent
of SQLAlchemy session mechanics.

Repository implementation belongs to the infrastructure boundary. Repository
interfaces and feature-specific persistence operations shall be introduced only
through later approved specifications. Generic repository frameworks are not
required.

## 5. Alembic Migration Responsibility

Alembic shall be the only approved mechanism for managed PostgreSQL schema
evolution. Each approved schema change shall be represented by a versioned,
reviewable migration compatible with the Docker Compose runtime.

This foundation does not define migration files, revisions, generation
commands, or schema changes. Those require a later approved data-model
specification and implementation plan.

## 6. Database Configuration and Environment Requirements

Database connectivity shall be centrally configured through environment values
in accordance with `specs/foundation/000-project-foundation.md` and the backend
foundation. PostgreSQL database name, user, password, port, and any later
connection settings shall be documented with their purpose and required or
optional status.

Credentials and connection secrets shall never be committed, hardcoded,
included in logs, or exposed to the frontend. `.env.example` may provide only
safe development values or placeholders. Environment access shall remain at
composition/infrastructure boundaries rather than scattered through business
code.

## 7. Connection and Session Management Expectations

The backend infrastructure shall centrally manage PostgreSQL connections and
SQLAlchemy session lifecycle. Sessions shall be scoped to backend work in a
predictable way and released or rolled back when that work completes or fails.

Routes, domain objects, and AI components shall not own database connections or
session lifecycle. Exact engine, pooling, request-lifecycle, and session-factory
details are implementation decisions for a later plan and shall remain
appropriately small for the two-day scope.

## 8. Transaction Expectations

Operations that require multiple related persistence changes shall have
appropriate atomic transactional behavior: either all required changes are
durably applied or the operation is rolled back on failure. Transaction control
shall remain in the application/infrastructure workflow boundary and shall not
be implemented by API routes or delegated to LLM behavior.

Feature-specific transaction scopes, ordering, retry behavior, and concurrency
rules are not defined by this foundation.

## 9. Data Integrity Principles

The persistence design shall preserve the approved relationship cardinalities
and maintain consistent, valid persisted state. Data integrity shall be upheld
through the later approved data model, repository behavior, deterministic
application workflows, and migrations.

The database foundation shall not rely on the frontend, hardcoded data, or AI
output to guarantee persisted state. Detailed constraints, validation rules,
foreign keys, deletion behavior, and indexes are explicitly deferred.

## 10. Local Development and Docker Requirements

PostgreSQL shall run as part of the mandatory Docker Compose environment with
the frontend and backend. The database setup shall use environment-based
configuration and remain compatible with the approved
`docker compose up --build` complete-platform outcome.

The persistence foundation shall not require external managed databases,
host-specific setup, additional infrastructure, or external AI services to
support the local core runtime.

## 11. Testing and Database Strategy

Database persistence shall be testable independently through the approved
backend Pytest approach. The eventual strategy shall support deterministic
local and CI execution without external services beyond the approved
Docker/PostgreSQL setup.

Later specifications shall define test isolation, database lifecycle,
fixtures, migration verification, and feature-specific persistence tests. The
foundation does not authorize test files or prescribe a test database design.

## 12. Definition of Done

Database foundation implementation work is complete only when all of the
following are satisfied:

- PostgreSQL is configured as the source of truth for approved persisted data
  and conversation state.
- SQLAlchemy access, connection/session lifecycle, and repository
  implementations remain within the infrastructure boundary.
- API routes do not access persistence directly, and domain/application code
  does not rely on SQLAlchemy session details.
- Alembic supports versioned, reviewable schema evolution.
- Database configuration is environment-driven, and no credentials or secrets
  are committed or exposed.
- Related persistence changes receive appropriate transaction handling.
- The database participates in the Docker Compose runtime and is independently
  testable through the approved backend testing approach.
- The implementation remains within approved scope and introduces no
  unapproved persistence technology or architecture.

## 13. Acceptance Criteria

This database foundation specification is accepted when:

- `specs/foundation/003-database-foundation.md` exists.
- It defines PostgreSQL as the source of truth, SQLAlchemy as the approved ORM
  integration, repositories as the persistence boundary, and Alembic as the
  schema-evolution mechanism.
- It defines environment-based credential handling, centralized
  connection/session expectations, appropriate transactions for related
  changes, data-integrity principles, Docker Compose compatibility, and
  independently testable deterministic persistence.
- It preserves the approved core data areas and relationship cardinalities
  without defining their schema implementation.
- It prohibits direct API access to SQLAlchemy and prevents domain/application
  dependencies on SQLAlchemy session details.
- It excludes actual table columns, indexes, enums, foreign-key
  implementation, migrations, seed data, feature persistence behavior, RAG,
  Redis, MongoDB, vector databases, Qdrant, NoSQL, sharding, CQRS, event
  sourcing, database-per-service architecture, and additional infrastructure.
- No database models, migrations, Docker files, tests, or architecture/ADR
  changes are created by this phase.
