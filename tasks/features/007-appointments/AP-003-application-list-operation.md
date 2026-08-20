# AP-003: Add Application Appointment-List Operation

**Task ID:** AP-003  
**Title:** Add Application Appointment-List Operation

## Objective

Expose the repository read through the existing `ConsultationApplicationService`
without coupling the use case to Flask or SQLAlchemy.

## Dependencies

AP-002.

## Scope

One application operation and its unit tests.

## Implementation requirements

- Add `list_appointments()` (or the established equivalent) delegating exactly
  once to the configured `AppointmentRepository`.
- Preserve constructor parameters, booking methods, dependency guards, and
  test seams.
- Return provider-neutral read values; perform no filtering, enrichment,
  counting, caching, commit, mutation, or AI work.

## Likely files/areas

`backend/app/application/consultation_service.py` and application tests.

## Tests/checks

Delegation/identity, missing dependency, repository failure propagation, and
strict no-commit/no-AI tests.

## Acceptance criteria

The operation invokes one repository read and remains independent of Flask,
Pydantic, SQLAlchemy mechanics, React, and AI.

## Explicit non-goals/scope guards

Do not add a parallel appointment service unless AP-001 documents a real
conflict. Do not alter booking eligibility, creation, status, or clocks.

## Completion evidence

Passing application tests and unchanged Feature 004 booking tests.
