# AI-005: Add Persistent Conversation Application Workflow

**Task ID:** AI-005  
**Title:** Add Persistent Conversation Application Workflow

## Purpose

Extend the consultation application service to retrieve messages and coordinate user persistence, AI generation, and assistant persistence with exact failure semantics.

## Traceability

- Feature specification: §§4–6, 8–9, 12, 14.
- Implementation plan: §§3, 5–7, 11, 12.3, 13–14.

## Scope

- Add retrieval/submission use cases, application exchange/failure outcomes, exact bounded-context selection, and isolated deterministic service tests.
- Preserve Feature 001 list/detail behavior.

## Expected files/areas affected

- `backend/app/application/consultation_service.py`, related application values/exports if needed, and application tests.

## Implementation requirements

- Compatibly inject message repository and provider-neutral AI service.
- Retrieval confirms consultation existence and returns repository-ordered history.
- Defensively trim/reject blank or over-4,000-character input before writes.
- Submission order is: confirm consultation; persist/commit USER; reload PostgreSQL history; select context; invoke AI; validate; persist/commit ASSISTANT; return both confirmed messages.
- Context is at most the newest 20 whole messages and 24,000 combined characters, always retains the current user, and is restored chronologically. Older rows remain persisted.
- Supply consultation ID, primary concern, existing display fields, ordered messages, and current interaction data.
- Require non-blank assistant text and supported JSON-compatible payload.
- Failures before/at user persistence prevent AI. AI/malformed-result failure carries the persisted user in a typed recovery outcome and persists no assistant. Assistant-persistence failure never returns success.
- No Flask, open transaction over AI, fabricated fallback, or background retry.

## Dependencies

- AI-003 and AI-004.

## Acceptance criteria

- Repeated persisted history and exact bounded context are deterministic.
- Call order proves USER-before-AI and ASSISTANT-after-valid-AI; all failure states preserve authoritative data.
- Feature 001 behavior remains green.

## Testing requirements

- Test retrieval, absence, defensive validation, user-persist failure, call order, repeated context, both limits/current-user retention, text/structured success, malformed/failed AI, and assistant-persist failure with deterministic doubles.
- Assert no premature AI call or fabricated/unconfirmed assistant.

## Definition of Done

- Application tests pass and orchestration remains independent of Flask and SQLAlchemy mechanics.
