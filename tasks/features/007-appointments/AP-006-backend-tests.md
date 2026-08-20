# AP-006: Complete Backend Appointment Read Tests

**Task ID:** AP-006  
**Title:** Complete Backend Appointment Read Tests

## Objective

Close deterministic backend repository, application, DTO, API, and failure
coverage for the read feature before live frontend integration.

## Dependencies

AP-005.

## Scope

Backend tests and additive fixture setup only; no new production abstraction.

## Implementation requirements

Cover the approved exact projections, ordering, lineage, one-load path,
request rejection, empty success, safe 500, UUID/timestamp output, no commit,
no mutation, and no AI/external network.

## Likely files/areas

Backend appointment repository/application/API modules, existing booking tests,
PostgreSQL fixtures, and focused integration test modules.

## Tests/checks

Run focused backend pytest tests with deterministic UUIDs/timestamps and child-
first cleanup (`appointments` before related rows). Do not seed through a new
Feature 007 write endpoint.

## Acceptance criteria

The focused backend suite passes and demonstrates safe behavior without OpenAI
credentials or external calls.

## Explicit non-goals/scope guards

No migration, alternate data authority, product refactor, or weakening of
existing Feature 004 assertions.

## Completion evidence

Test report naming commands, pass results, fixture ownership, and any isolated
pre-existing failure.
