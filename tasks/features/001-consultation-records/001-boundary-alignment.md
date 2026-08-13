# CR-001: Confirm Consultation Records Integration Boundaries

**Task ID:** CR-001  
**Title:** Confirm Consultation Records Integration Boundaries

## Purpose

Establish the existing project conventions that the approved Consultation Records
implementation must follow, while treating the approved API contract as the
shared backend/frontend boundary.

## Traceability

- Feature specification: §§6, 7, 8, 10–12.
- Implementation plan: §§4, 8, 14.1, 15–17.

## Scope

- Inspect the established application factory, blueprint, error-envelope,
  Pydantic, SQLAlchemy/session, Alembic, PostgreSQL-test, frontend routing,
  frontend-service, and test conventions.
- Record task-local implementation decisions needed by later tasks, including
  identifier storage representation and the detail route path, when those
  conventions are discoverable.
- Confirm the two approved endpoints, DTO shapes, query semantics, error
  outcomes, and no-AI boundary as the cross-team contract.

## Expected files/areas affected

- Task documentation and review notes only; existing backend, frontend,
  database, Docker, configuration, ADR, plan, and specification areas are
  inspected but not changed by this task.

## Implementation requirements

- Do not alter the approved API contract or architecture.
- Identify the locations and conventions later tasks must use rather than
  creating parallel patterns.
- Make no implementation changes in this task.

## Dependencies

- Approved foundations, feature specification, and implementation plan.

## Acceptance criteria

- Later tasks have an unambiguous route-registration, error-format,
  persistence/session, migration, test-data, frontend-service, and routing
  convention to follow.
- The shared contract remains exactly `GET /api/v1/consultations` and
  `GET /api/v1/consultations/{consultation_id}` with the specified fields,
  query parameters, and `400`/`404`/safe-`500` behavior.
- Backend and frontend work are explicitly ready to proceed independently.

## Testing requirements

- Perform a documentation/convention review; no automated feature test is
  created or run solely for this alignment task.

## Definition of Done

- Findings are available to implementers, traceability is intact, and no code,
  configuration, infrastructure, ADR, plan, or specification change was made.
