# ABH-005 — Integrate Authoritative Handoff Evaluation into Message Workflow

**Task ID:** ABH-005

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Integrate booking intent and authoritative lifecycle evaluation into the existing `submit_message` workflow without changing booking authority.

## Scope

Extend application-level chat processing only. Do not add frontend CTA behavior yet.

## Expected files/areas affected

- `ConsultationApplicationService`
- existing summary/appointment read helpers/repositories as needed
- focused application tests

## Implementation requirements

Preserve the existing order:

1. validate consultation/conversation state
2. classify current user message
3. persist user message
4. load bounded context
5. call existing AI service
6. validate `AIResult`
7. if booking intent is actionable, evaluate persisted state
8. construct application-owned handoff
9. persist assistant message plus reserved marker
10. return confirmed exchange

Authoritative mapping:

- `PENDING`, not summary-eligible → `CONTINUE_CONSULTATION`
- `PENDING`, summary-eligible → `GENERATE_SUMMARY`
- `COMPLETED` + persisted summary → `VIEW_SUMMARY` projection
- `BOOKED` + persisted appointment → `VIEW_APPOINTMENTS` projection
- inconsistent/missing state → no handoff

Requirements:

- Reuse existing summary-eligibility semantics; do not duplicate lifecycle rules.
- Read persisted state through existing repositories/application seams.
- Provider output cannot override the chosen action.
- Do not call Feature 004 booking from chat.
- Do not create an appointment or change consultation status merely because booking intent was expressed.
- Preserve Feature 002 user-message persistence and AI failure semantics.
- No second session/engine/repository hierarchy.

## Dependencies

- ABH-002
- ABH-003

## Acceptance criteria

- Ordinary message remains ordinary.
- Booking intent produces at most one authoritative handoff.
- All approved lifecycle mappings are correct.
- No appointment write occurs.
- No status transition occurs from handoff generation.
- Provider action-like data cannot override application state.
- Existing AI failure behavior remains intact.

## Testing requirements

Cover:

- ordinary message
- pending not eligible
- pending eligible
- completed projection
- booked projection
- inconsistent state
- state lookup failure
- provider action-like payload
- no booking write
- no status mutation
- AI/provider failure
- malformed AI result
- marker persistence

## Definition of Done

ABH-005 is complete when the existing message workflow emits/persists only application-authorized handoffs while preserving all existing conversation and booking boundaries.
