# ABH-002 — Add Provider-Neutral Booking Intent Classifier

**Task ID:** ABH-002

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Implement a small deterministic application-level classifier for explicit appointment-booking intent.

## Scope

Add only the provider-neutral intent classifier and focused tests.

## Expected files/areas affected

Prefer a small application-layer module such as:

- `backend/app/application/booking_intent.py`
- focused unit tests

Use actual repository naming from ABH-001 findings.

## Implementation requirements

- Classifier returns only typed intent, e.g. `BOOKING_REQUEST` or `NONE`.
- Normalize case, spacing, and punctuation safely.
- Recognize explicit booking/scheduling/make-appointment intent.
- Reject/ignore cancellation, rescheduling, negated, hypothetical, informational, and ambiguous appointment discussion.
- Do not use a single raw substring check.
- Do not call OpenAI or any provider.
- Do not return routes, IDs, lifecycle state, dates, locations, or booking confirmation.
- Keep the helper pure and independently testable.
- Do not add a general-purpose NLP/intent framework.

## Dependencies

- ABH-001

## Acceptance criteria

- Representative positive booking phrases classify correctly.
- Non-booking/cancel/reschedule/negated/hypothetical examples return `NONE`.
- Classifier is provider-neutral and network-free.
- No existing chat/provider behavior is changed in this task.

## Testing requirements

Add deterministic unit tests covering:

- capitalization/punctuation variants
- positive booking phrases
- cancel/reschedule phrases
- negation
- informational/hypothetical discussion
- ambiguous input
- blank input
- no external calls

## Definition of Done

ABH-002 is complete when the classifier is deterministic, narrowly scoped, fully tested, and ready for application-service integration.
