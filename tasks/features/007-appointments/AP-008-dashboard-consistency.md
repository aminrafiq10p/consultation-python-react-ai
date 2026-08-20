# AP-008: Verify Dashboard Booked-Count Consistency

**Task ID:** AP-008  
**Title:** Verify Dashboard Booked-Count Consistency
**Status:** Complete (2026-08-19)

## Objective

Confirm Dashboard continues to count the same PostgreSQL appointment rows after
Feature 004 booking and Feature 007 listing.

## Dependencies

AP-007.

## Scope

Add or extend one integration assertion; no Dashboard production redesign.

## Implementation requirements

Read Dashboard metrics before booking, after booking, and after list retrieval.
Require the booked count to change only from the persisted appointment row and
remain stable after the read. Check no callback, cache invalidation, local
count mutation, or second count source was added.

## Likely files/areas

Existing Dashboard repository/API integration tests and the AP-007 PostgreSQL
scenario/fixture owner.

## Tests/checks

Dashboard before/after values, persisted appointment count, no list insertion,
and unchanged Feature 005 metric contract.

## Acceptance criteria

Dashboard observes the same authoritative row naturally; Feature 007 adds no
count endpoint, synchronization event, or frontend count mutation.

## Explicit non-goals/scope guards

Do not redesign Dashboard, add metrics, or create a second appointment count.

## Completion evidence

The AP-007 PostgreSQL continuity scenario now reads Dashboard metrics before
booking, after the committed Feature 004 booking, and after the Feature 007
list read. It asserts `0 → 1 → 1` for `booked_appointments`, a matching
persisted `appointments` row count of `0 → 1 → 1`, unchanged appointment row
identity after listing, and the existing Dashboard response contract.

The Dashboard production repository, application service, route, and frontend
logic were unchanged. Focused AP-008 checks passed: 25 tests.
