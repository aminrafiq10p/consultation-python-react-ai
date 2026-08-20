# AP-001: Confirm Feature 007 Integration Boundaries

**Task ID:** AP-001  
**Title:** Confirm Feature 007 Integration Boundaries

## Objective

Freeze the actual Feature 004–006 persistence, application, API, composition,
frontend, fixture, migration, Docker, and test seams before implementation.

## Dependencies

Approved Feature 007 specification and implementation plan; current repository
state.

## Scope

Read-only inspection and a findings record for the approved architecture.

## Implementation requirements

- Confirm `AppointmentRepository` and `ConsultationApplicationService` are the
  reuse points and that booking response types remain unchanged.
- Confirm the joined model lineage, request-shape/error conventions, one
  request-scoped Session, Dashboard appointment count, AppLayout navigation,
  frontend transport/runtime-validation conventions, fixtures, migration head,
  package scripts, and Compose commands.
- Record dirty-worktree state and preserve unrelated changes.
- If the approved consultation-service boundary is genuinely incompatible,
  document the smallest focused read-service alternative before implementation;
  do not silently redesign architecture.

## Likely files/areas

`specs/`, `plans/`, Features 004–006 code/tasks, appointment models/repository,
consultation service/routes/DTOs, `backend/app/__init__.py`, Dashboard code,
`frontend/src/app/core/App.tsx`, `AppLayout.tsx`, frontend services/tests,
fixtures, migrations, Docker files, and package scripts.

## Tests/checks

No product tests or code changes. Record the focused pytest/Vitest,
typecheck/lint/build, PostgreSQL/migration, Compose, and Git commands for later
tasks.

## Acceptance criteria

- Findings identify exact current names/imports and change ownership.
- No new table, migration, engine, session factory, AI dependency, external
  integration, or navigation system is required.
- Safe parallel branches and shared-file coordination rules are recorded.

## Explicit non-goals/scope guards

Do not implement product code, tests, migrations, task follow-ups, Feature 004
booking changes, or Feature 008 work.

## Completion evidence

An AP-001 findings note with the inspection date, boundary map, commands, and
any blocker/conflict statement; a clean implementation starting point.
