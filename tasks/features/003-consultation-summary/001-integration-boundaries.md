# CS-001: Confirm Feature 003 Integration Boundaries

**Task ID:** CS-001  
**Title:** Confirm Feature 003 Integration Boundaries

## Purpose

Confirm the exact existing seams and conventions the approved Consultation
Summary implementation must extend before product code changes begin.

## Traceability

- Feature specification: §§5–16.
- Implementation plan: §§2–3, 8–11, 15–18.

## Scope

- Inspect model/metadata, Alembic chain, request-session, repository,
  transaction/error, AI structured-output, DTO/blueprint, frontend
  service/router, PostgreSQL concurrency-test, and Compose conventions.
- Record exact module locations, constraint names, error representations, route
  paths, injection seams, and verification commands for later CS tasks.
- Confirm the approved HTTP DTO/error contract as the shared backend/frontend
  boundary.

## Expected files/areas affected

- Task findings/review documentation only. Product source, migrations,
  configuration, Compose, specification, and plan files are inspected but not
  changed by this task.

## Implementation requirements

- Preserve the single application service, blueprint, request session,
  consultation frontend feature, and one-agent AI architecture.
- Confirm how a named PostgreSQL unique constraint is identified safely after
  `IntegrityError`; do not treat unrelated integrity failures as races.
- Confirm the existing dirty worktree and avoid overwriting unrelated changes.
- Make no product implementation changes.

## Dependencies

- Approved Feature 003 specification and plan.
- Completed Features 001 and 002 and Docker Compose foundation.

## Acceptance criteria

- Every later task has an unambiguous location, boundary, contract, test seam,
  and applicable command to follow.
- The approved routes, DTOs, transaction semantics, concurrency strategy,
  frontend paths, and scope guards remain unchanged.
- CS-002, CS-004, and CS-007 can proceed independently from recorded findings.

## Testing requirements

- Documentation/convention review only; run no feature test solely for this
  alignment task.

## Definition of Done

- Findings are reviewable, traceability is intact, and no implementation,
  migration, configuration, infrastructure, specification, or plan changed.
