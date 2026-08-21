# ABH-003 — Add Typed Booking Handoff and Persistence Markers

**Task ID:** ABH-003

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Define the application-owned handoff model and safely persist/reload it through existing assistant-message JSONB without a migration.

## Scope

Add typed handoff values, action/target validation, and reserved JSONB marker encode/decode/projection helpers.

## Expected files/areas affected

- application/domain value module for handoff types
- message payload/projection helpers
- backend DTO/value tests

Use existing file structure confirmed by ABH-001.

## Implementation requirements

Approved action set:

- `CONTINUE_CONSULTATION`
- `GENERATE_SUMMARY`
- `VIEW_SUMMARY`
- `VIEW_APPOINTMENTS`

Approved target mapping:

- current consultation route
- current consultation route for summary generation action
- consultation summary route
- `/appointments`

Requirements:

- Handoff is application-owned, not provider-owned.
- User messages cannot carry handoffs.
- Consultation ID must match the persisted message/consultation.
- Backend constructs targets; arbitrary URLs are forbidden.
- Reserved flat keys must remain compatible with current scalar/scalar-array payload rules.
- Reserved keys must be stripped from ordinary `structured_payload` exposed to clients.
- Malformed/mismatched markers must fail closed: ordinary assistant content remains usable but no CTA is projected.
- Legacy messages without markers remain compatible.
- No migration.

## Dependencies

- ABH-001

Can proceed in parallel with ABH-002.

## Acceptance criteria

- Valid markers round-trip to exact typed handoff.
- Invalid action/UUID/target/mismatch yields no actionable handoff.
- Provider payload remains intact apart from reserved-key separation.
- User messages cannot expose a handoff.
- No schema change or migration is introduced.

## Testing requirements

Cover:

- every valid action
- target/action exactness
- invalid UUID
- consultation mismatch
- malformed marker
- user-message marker rejection
- provider payload preservation
- reserved-key stripping
- legacy-message compatibility

## Definition of Done

ABH-003 is complete when typed handoffs can be safely encoded, persisted, decoded, and projected without leaking provider data or requiring schema changes.
