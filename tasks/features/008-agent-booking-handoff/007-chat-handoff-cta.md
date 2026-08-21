# ABH-007 — Add Functional Booking Handoff CTA to Consultation Chat

**Task ID:** ABH-007

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Render and execute one safe application CTA for valid assistant handoff metadata in the existing consultation conversation UI.

## Scope

Add functional CTA presentation only within existing chat/detail UI. Broad visual polish is out of scope.

## Expected files/areas affected

- `ConsultationConversation`
- existing summary-generation frontend service usage
- focused component/router tests

## Implementation requirements

Render one CTA per valid handoff:

- `CONTINUE_CONSULTATION` → remain on current consultation; optionally focus existing composer
- `GENERATE_SUMMARY` → call existing summary generation exactly once, then navigate to summary route only on confirmed success
- `VIEW_SUMMARY` → navigate to existing summary route
- `VIEW_APPOINTMENTS` → navigate to `/appointments`

Requirements:

- Use typed handoff metadata only; never parse prose.
- CTA must be keyboard accessible.
- Use existing MUI styling/conventions.
- Prevent duplicate clicks while explicit action is pending.
- Show safe recoverable feedback on summary-generation failure.
- CTA must never call appointment booking directly.
- Do not redesign chat/sidebar/theme/layout.

## Dependencies

- ABH-004
- ABH-006

## Acceptance criteria

- Ordinary messages render no CTA.
- Each valid handoff renders the correct accessible CTA.
- Generate Summary issues exactly one existing summary request and navigates only on success.
- View Summary/Appointments navigate to approved existing routes.
- Continue Consultation has no HTTP side effect.
- No booking POST originates from the CTA.

## Testing requirements

Cover:

- each CTA
- keyboard access
- duplicate-click guard
- summary pending/success/failure
- navigation destinations
- malformed/invalid handoff omission
- no prose parsing
- no booking POST

## Definition of Done

ABH-007 is complete when the consultation chat provides a safe deterministic handoff into existing lifecycle screens with no new booking write behavior.
