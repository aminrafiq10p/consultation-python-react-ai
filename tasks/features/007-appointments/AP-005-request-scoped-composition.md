# AP-005: Verify Request-Scoped Appointment Composition

**Task ID:** AP-005  
**Title:** Verify Request-Scoped Appointment Composition

## Objective

Prove production list requests use the same request-scoped Session and
repository/application composition as booking and Dashboard reads.

## Dependencies

AP-002, AP-003, AP-004.

## Scope

Composition inspection or minimal compatible composition adjustment, with tests.

## Implementation requirements

- Reuse the existing `AppointmentRepository(session)` and service registration.
- Preserve injected-service API tests and teardown behavior.
- Prove no second engine/session factory, repository hierarchy, transaction, or
  list-request commit/mutation exists.

## Likely files/areas

`backend/app/__init__.py`, composition tests, production PostgreSQL fixtures.

## Tests/checks

Production list request, injected service route, Session identity/teardown,
fresh-session visibility, and no-write assertions.

## Acceptance criteria

The list path reaches the existing service/repository through one request
Session and leaves persisted rows unchanged.

## Explicit non-goals/scope guards

Do not move composition, alter teardown or booking atomicity, or add a session,
engine, repository hierarchy, cache, or dashboard synchronization.

## Completion evidence

Passing composition tests and a documented decision that no production change
was needed or the smallest traced change made.
