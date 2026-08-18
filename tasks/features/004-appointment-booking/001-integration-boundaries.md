# AB-001: Confirm Feature 004 Integration Boundaries

**Task ID:** AB-001  
**Title:** Confirm Feature 004 Integration Boundaries

## Purpose

Confirm and record the exact seams and conventions that Feature 004 must extend
before any appointment product code or migration is created.

## Traceability

- Feature specification: §§5–16 and §§18–20.
- Implementation plan: §§2–3 and §§12–17, especially §13 AB-001.

## Scope

- Inspect the Alembic head, shared SQLAlchemy metadata, request-scoped session,
  repository transaction/error conventions, application-service construction,
  Pydantic/blueprint contracts, summary handoff, frontend service/router,
  PostgreSQL test fixtures, and Compose verification commands.
- Record exact module locations, names, injection seams, cleanup order,
  constraint-classification approach, and verification commands for AB-002
  through AB-008.
- Confirm the approved POST request, success representation, and safe error
  contract as the shared backend/frontend boundary.

## Expected files/areas affected

- A task findings/review document under this feature task directory only.
- Product source, migrations, tests, configuration, Compose, specification, and
  plan files are inspected but not changed by this task.

## Implementation requirements

- Confirm that `20260817_03_create_consultation_summaries.py` is the migration
  head and identify the exact revision ID/down-revision values.
- Confirm how one SQLAlchemy session is shared by production repositories and
  how API tests inject a `ConsultationApplicationService` double.
- Confirm existing repository commit, rollback, reload, and PostgreSQL named-
  constraint inspection conventions, including a safe post-rollback reload.
- Confirm the service constructor can gain optional appointment and clock
  dependencies without breaking Features 001–003 test construction.
- Confirm the exact Feature 003 route
  `/consultations/:consultationId/appointments/new?recommendation_id=...`, its
  placeholder owner, and the existing summary and records service contracts.
- Confirm the dirty worktree before later work and record how unrelated changes
  and generated artifacts will be preserved.

## Dependencies

- Approved Feature 004 specification and implementation plan.
- Completed Features 001–003 and Docker Compose foundation.

## Acceptance criteria

- Every later AB task has an unambiguous file location, boundary, contract,
  dependency, test seam, cleanup rule, and applicable verification command.
- The approved migration chain, shared session, transaction ownership, lock
  point, error contract, route/query handoff, and frontend HTTP boundary are
  confirmed against the repository.
- AB-002 and AB-006 can proceed independently from the recorded findings.
- No unresolved integration fact is silently converted into an architecture or
  product decision.

## Testing requirements

- Documentation and convention review only; run no feature test solely for
  boundary confirmation.
- Validate findings against repository paths and current configuration rather
  than assumptions from the plan alone.

## Architecture and scope guards

- Preserve the existing Flask blueprint, application service, request-scoped
  session, focused repositories, consultation-records frontend feature, and
  Compose topology.
- Do not create product code, migrations, tests, dependencies, endpoints, or
  infrastructure in this task.
- Do not introduce appointment retrieval/lifecycle, scheduling-provider,
  calendar, authentication, dashboard, AI, RAG, Redis, vector, LangGraph,
  WebSocket, streaming, or unrelated refactoring scope.

## Definition of Done

- Findings are reviewable and traceable, all downstream boundaries are exact,
  and no product, migration, test, configuration, specification, plan, or
  infrastructure file changed.
