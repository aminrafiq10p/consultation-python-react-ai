# ABH-008 — Verify Reload and Current-State Handoff Projection

**Task ID:** ABH-008

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Ensure handoff behavior remains coherent after persisted-message reload and across completed/booked read-only states without reopening chat or calling AI.

## Scope

Implement/verify reload projection only. No new writable workflow.

## Expected files/areas affected

- message history projection/DTO helpers
- consultation message retrieval path
- relevant frontend reload tests
- focused backend tests

## Implementation requirements

- Persisted valid handoff markers restore a typed handoff on reload.
- Reload must not call AI merely to reconstruct CTA metadata.
- `COMPLETED` and `BOOKED` consultations remain read-only.
- Where approved and architecture-compatible, current authoritative state may normalize the actionable projection to `VIEW_SUMMARY` or `VIEW_APPOINTMENTS`.
- Any normalization must be read-only and derived from persisted state.
- Stale historical handoffs must never authorize booking.
- Malformed/legacy metadata renders ordinary assistant text only.

If dynamic normalization would materially complicate the existing read path, retain persisted historical handoffs and rely on downstream authoritative APIs, documenting the decision against the acceptance criteria.

## Dependencies

- ABH-006
- ABH-007

## Acceptance criteria

- Reload restores valid CTA metadata without AI.
- Completed/booked read-only rule remains unchanged.
- No status/message/appointment mutation occurs from reload.
- Stale metadata cannot bypass downstream validation.
- Malformed metadata fails safely.

## Testing requirements

Cover:

- persisted reload
- no-AI-on-reload
- completed state
- booked state
- stale handoff
- malformed marker
- legacy message
- no mutation

## Definition of Done

ABH-008 is complete when persisted handoffs survive reload safely and current-state behavior remains coherent without reopening conversations or adding a new write path.
