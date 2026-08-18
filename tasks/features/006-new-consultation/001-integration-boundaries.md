# NC-001: Confirm Feature 006 Integration Boundaries

**Task ID:** NC-001  
**Title:** Confirm Feature 006 Integration Boundaries

## Purpose

Confirm and record the exact persistence, application, API, frontend service,
routing, layout, testing, and runtime seams Feature 006 must extend before any
product behavior is implemented.

## Traceability

- Feature specification: §§1–4, §§6–16, and §17.
- Implementation plan: §§2–4, §§12–16, and §§17–18.

## Scope

- Perform read-only repository investigation across the existing consultation
  model, repository, application service, DTOs/routes/composition, migrations,
  PostgreSQL tests, frontend service/types, router, and shared layout.
- Record findings and exact commands for NC-002 through NC-008 in a focused
  findings document under this task directory.
- Inspect and preserve the dirty working tree, especially user-owned Feature
  005 and other edits in shared files.

## Expected files/areas affected

- Add only `tasks/features/006-new-consultation/NC-001-findings.md`.
- Inspect the files listed in plan §4, relevant package/test configuration,
  migrations, `compose.yaml`, and current Git state without changing them.

## Implementation requirements

- Confirm the exact five `Consultation` fields, UUID behavior, and
  `ConsultationStatus` values.
- Confirm `ConsultationRepository.create_consultation` add/commit/refresh/
  return order, rollback/re-raise behavior, and unit-of-work ownership.
- Confirm `ConsultationApplicationService` construction/injection seams and
  existing restart creation convention.
- Confirm Pydantic v2 strict/trim/forbid conventions, response serialization,
  blueprint prefix, safe `400`/`500` contracts, and injected-service tests.
- Confirm one request-scoped SQLAlchemy session, teardown, production service
  composition, current Alembic head, PostgreSQL fixtures, and FK cleanup order.
- Confirm frontend consultation request/error/runtime-validation conventions,
  router precedence, `AppLayout`/shared `SidebarContent`, disabled New Consult
  control, mobile drawer close callback, and consultation active-route rule.
- Record exact focused/full backend and frontend, typecheck, lint, build,
  migration, Compose, and diff-validation commands supported by the repository.
- Identify shared-file conflicts or specification mismatches; stop and report a
  material conflict instead of inventing a parallel architecture.

## Dependencies

- Approved Feature 006 specification and implementation plan.
- Completed Features 001–005 in their current working-tree state.

## Acceptance criteria

- Findings give every downstream NC task verified file owners, symbols,
  conventions, test seams, commands, migration head, and dirty-tree risks.
- The findings confirm whether the approved design can proceed unchanged and
  preserve PostgreSQL authority, one request session, and existing routing.
- NC-002 and NC-004 can begin independently from the recorded evidence.
- No product, test, migration, configuration, specification, or plan file is
  modified.

## Testing requirements

- Repository discovery and documentation checks only; do not implement or run
  a feature test merely to complete this task.
- Base every finding on current source/configuration rather than assumptions
  copied only from the specification or plan.

## Architecture and scope guards

- Do not implement Feature 006, create tests, alter schema, add dependencies,
  or refactor existing code.
- Do not split services/repositories/sessions or begin Feature 007.
- Preserve all unrelated user changes and document any overlap risk.

## Definition of Done

- A reviewable NC-001 findings document makes NC-002 through NC-008
  independently executable and records all requested boundaries and commands,
  with no product or architecture change.
