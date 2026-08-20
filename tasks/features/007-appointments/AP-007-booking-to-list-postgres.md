# AP-007: Verify Feature 004 Booking to Feature 007 PostgreSQL Retrieval

**Task ID:** AP-007  
**Title:** Verify Feature 004 Booking to Feature 007 PostgreSQL Retrieval
**Status:** Complete (2026-08-19)

## Objective

Prove the existing Feature 004 booking creates the exact row later returned by
the Feature 007 list API.

## Dependencies

AP-006.

## Scope

One deterministic real-PostgreSQL continuity scenario and supporting fixtures.

## Implementation requirements

- Create completed consultation, summary, and selected recommendation through
  existing deterministic seams.
- Book only through `POST /api/v1/consultations/{id}/appointments`, commit,
  then list from a fresh request/session.
- Assert same appointment/consultation/recommendation IDs, patient, treatment,
  scheduled instant, location, created timestamp, one row, and no list writes.
- Include passed appointments and verify no hidden historical rows.

## Likely files/areas

PostgreSQL API/persistence integration tests and shared fixtures.

## Tests/checks

Fresh-session continuity, lineage, duplicate prevention, row/count deltas,
no-AI/network, and no status mutation.

## Acceptance criteria

Returned data is demonstrably the persisted Feature 004 appointment, not a
consultation-derived or frontend-created record.

## Explicit non-goals/scope guards

No Feature 007 write endpoint, booking change, calendar/status behavior, or
new persistence model.

## Completion evidence

Passing PostgreSQL integration test with before/after row evidence.
