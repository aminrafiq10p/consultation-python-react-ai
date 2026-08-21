# ABH-009 — Verify Cross-Feature Booking Handoff Integration and Regressions

**Task ID:** ABH-009

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Prove the full Feature 008 lifecycle across existing Features 002–007 and verify no regressions.

## Scope

Integration/regression verification with only minimal task-scoped fixes for genuine Feature 008 failures.

## Expected files/areas affected

Primarily test/integration files across backend/frontend. Production changes only if a concrete Feature 008 acceptance failure is found.

## Implementation requirements

Verify this continuity:

1. Feature 006 creates consultation
2. Feature 002 ordinary chat persists
3. user expresses booking intent
4. typed handoff is returned/persisted
5. `GENERATE_SUMMARY` uses existing Feature 003 summary flow
6. recommendations are retrieved
7. Feature 004 booking creates exactly one appointment
8. Feature 007 returns that same appointment
9. Feature 005 Dashboard counts that same row

Assertions:

- booking-intent message creates no appointment
- CTA creates no appointment
- only Feature 004 booking writes appointment
- one authoritative consultation/recommendation/appointment identity chain
- repeated/already-booked flow cannot duplicate
- ordinary non-booking chat remains ordinary
- completed/booked closed-conversation behavior remains intact
- no live OpenAI required

## Dependencies

- ABH-005
- ABH-007
- ABH-008

## Acceptance criteria

- Full deterministic lifecycle passes.
- Exactly one appointment is created through Feature 004.
- Feature 007 and Dashboard observe the same persisted row.
- Features 001–007 regression tests remain green.
- No architecture or scope expansion is introduced.

## Testing requirements

Run:

- focused backend Feature 008 tests
- focused frontend Feature 008 tests
- PostgreSQL integration
- existing Features 001–007 backend/frontend regressions
- relevant route/navigation checks

## Definition of Done

ABH-009 is complete when the full booking-handoff lifecycle and all existing feature regressions are verified with PostgreSQL remaining authoritative.
