# DN-001: Confirm Feature 005 Integration Boundaries

**Task ID:** DN-001  
**Title:** Confirm Feature 005 Integration Boundaries

## Purpose

Confirm and record the exact repository, application, API, frontend, routing,
responsive-test, persistence, and runtime seams that Feature 005 must extend
before any dashboard product behavior is implemented.

## Traceability

- Feature specification: §§2–3, §§6–8, §§10–16, and §§17–18.
- Implementation plan: §§2–3, §15 DN-001, and §§16–19.

## Scope

- Inspect Flask composition and request-session ownership, repository and
  application-service conventions, DTO/blueprint/error handling, PostgreSQL
  fixtures, and the current Alembic head.
- Inspect the frontend transport/runtime-validation conventions, nested router,
  `AppLayout` ownership, MUI responsive behavior, test media-query support, and
  Docker Compose assumptions.
- Record exact locations, seams, commands, and constraints for DN-002 through
  DN-008 without implementing product behavior.

## Expected files/areas affected

- A findings/review document under this Feature 005 task directory only.
- Product source, tests, migrations, configuration, specification, and plan
  files are inspected but not changed by this task.

## Implementation requirements

- Confirm `create_app` injection behavior, one-session-per-request composition,
  extension keys, teardown cleanup, and safe unexpected-error handling.
- Confirm focused repository construction and application value/service
  patterns, including where strict doubles belong.
- Confirm Pydantic response, blueprint prefix, request rejection, and numeric
  JSON conventions applicable to `GET /api/v1/dashboard`.
- Confirm PostgreSQL 16 container fixtures, Alembic-to-head setup, foreign-key
  cleanup order, and the exact Feature 004 migration head; verify no Feature
  005 migration is needed.
- Confirm injected `fetch`, safe runtime validation, React state, router,
  `AppLayout`, MUI breakpoint, `matchMedia`, and RTL conventions.
- Confirm existing Compose services, API URL/CORS settings, mock-AI default,
  verification commands, and dirty-worktree preservation requirements.

## Dependencies

- Approved Feature 005 specification and implementation plan.
- Completed and verified Features 001–004.

## Acceptance criteria

- Every downstream DN task has an exact boundary, file owner, dependency, test
  seam, and applicable verification command confirmed from repository evidence.
- The existing Alembic head, shared session, API safety, frontend shell/router,
  responsive test approach, and Compose assumptions are recorded.
- DN-002 and DN-005 can proceed independently from the findings.
- No unresolved repository fact is silently converted into a product or
  architecture decision.

## Testing requirements

- Documentation and repository discovery only; do not run a feature test solely
  to complete boundary confirmation.
- Validate findings from actual source, fixtures, configuration, and commands,
  not only from the approved documents.

## Architecture and scope guards

- Do not create product code, tests, migrations, dependencies, endpoints,
  services, persistence, or infrastructure in this task.
- Preserve Features 001–004, the shared Flask/React architecture, PostgreSQL
  authority, and existing Compose topology.
- Do not add AI, charts, analytics, cache, background work, auth, external
  integrations, routing redesign, or unrelated refactoring.

## Definition of Done

- Reviewable findings make DN-002 through DN-008 unambiguous and traceable, and
  no product, test, migration, configuration, specification, plan, or
  infrastructure file has changed.
