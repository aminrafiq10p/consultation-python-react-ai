# ABH-004 — Add Frontend Handoff Types and Runtime Validation

**Task ID:** ABH-004

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Teach the frontend consultation-message boundary to understand and safely validate typed booking handoffs.

## Scope

Extend existing consultation message types/runtime validation only. No CTA UI yet.

## Expected files/areas affected

- existing frontend consultation/message types
- existing consultation API/runtime validators
- focused frontend tests

## Implementation requirements

- Add typed `BookingHandoff` / action union.
- Validate approved action values and exact target mapping.
- Validate UUIDs and consultation ID consistency.
- Only assistant messages may expose a handoff.
- Ordinary messages must remain compatible with `handoff: null` or absent legacy behavior as approved by the backend contract.
- Malformed handoff metadata must not cause prose parsing or create actions.
- Do not parse assistant content to infer booking actions.
- Preserve all existing message/list/summary/booking validators.

## Dependencies

- ABH-001
- Approved Feature 008 API contract

May proceed in parallel with ABH-002/ABH-003.

## Acceptance criteria

- Every approved action validates.
- Invalid action/UUID/target/mismatch is rejected or safely omitted according to the approved compatibility rule.
- Existing ordinary messages remain valid.
- No UI, route, backend, or booking code is changed.

## Testing requirements

Cover:

- all valid actions
- invalid action
- invalid UUID
- mismatched consultation
- invalid target
- handoff on user message
- extra fields
- legacy ordinary messages
- no prose parsing

## Definition of Done

ABH-004 is complete when the frontend service boundary can safely expose typed handoff metadata without changing existing conversation behavior.
