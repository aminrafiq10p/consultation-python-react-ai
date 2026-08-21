# ABH-006 — Update AI Wording Guidance and Message API Projection

**Task ID:** ABH-006

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Prevent misleading booking-unavailable wording and expose typed handoffs through existing message GET/POST responses.

## Scope

Update AI skill/instructions narrowly and extend existing message DTO/API projection. No new endpoint.

## Expected files/areas affected

- `ConsultationSkill` or equivalent instruction builder
- message response DTOs
- existing message GET/POST routes
- focused AI/DTO/API tests

## Implementation requirements

AI wording guidance must:

- acknowledge that the application can guide the user through its internal booking workflow;
- never claim a booking was completed unless Feature 004 actually confirmed it;
- never invent date/time/location/recommendation/provider data;
- never become the authority for action/route selection.

API/DTO requirements:

- existing GET/POST message responses expose `handoff`;
- ordinary/user messages expose null/no handoff according to the approved exact contract;
- valid assistant handoffs serialize exactly;
- reserved internal keys never leak in `structured_payload`;
- malformed markers safely omit CTA metadata;
- existing `400/404/409/503/500` behavior remains unchanged;
- no new endpoint.

## Dependencies

- ABH-005
- ABH-003

## Acceptance criteria

- Booking-intent wording no longer falsely says the platform lacks booking capability.
- AI wording never claims booking occurred.
- GET history and POST response expose consistent typed handoffs.
- No provider/internal marker leakage.
- Existing message API errors remain compatible.

## Testing requirements

Cover:

- wording instruction behavior
- MockAIProvider/fake AI determinism
- ordinary message handoff null
- valid handoff serialization
- user message cannot expose handoff
- malformed marker omission
- reserved marker stripping
- existing API error regressions

## Definition of Done

ABH-006 is complete when conversational wording is aligned with platform capability and typed handoffs are available through the existing message API without changing booking authority.
