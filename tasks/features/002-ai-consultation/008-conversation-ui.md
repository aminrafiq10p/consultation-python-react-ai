# AI-008: Implement Persistent AI Conversation UI

**Task ID:** AI-008  
**Title:** Implement Persistent AI Conversation UI

## Purpose

Extend Consultation Detail with a safe PostgreSQL-reconciled conversation while preserving existing record behavior.

## Traceability

- Feature specification: §§4, 7, 11–12, 14.
- Implementation plan: §§3, 9–10, 11.5, 12.5, 13–14.

## Scope

- Integrate conversation history/composer after existing detail fields, optionally using a focused feature-local component.
- Load, submit, reconcile, and recover only through AI-007; add React Testing Library coverage.

## Expected files/areas affected

- `frontend/src/app/features/consultation-records/ConsultationDetailScreen.tsx`, optional feature-local conversation component, and related tests.

## Implementation requirements

- Render backend order with stable IDs/timestamps and an explicit empty state.
- Add multiline MUI input, trim-aware blank/4,000-character feedback, pending state, and duplicate prevention; do not present a draft as persisted.
- On success merge/replace from both confirmed messages and preserve backend order.
- On recoverable AI failure incorporate only validated persisted USER data, show a safe retryable alert, and reload history.
- On ambiguous submission failure reload authoritative history before showing a retryable error.
- Preserve distinct conversation loading, retrieval error, and consultation-not-found behavior.
- Render assistant content as plain React text. Render scalar/scalar-array payloads with MUI elements and ignore unsupported nesting while retaining text.
- No direct fetch/OpenAI, unsafe HTML, fabricated assistant, provider details, streaming, WebSockets, summary, recommendation action, or booking.

## Dependencies

- AI-007; connected backend behavior depends on AI-006.

## Acceptance criteria

- Ordered/empty history, repeated confirmed submissions, validation, one pending request, and safe text/structured output work.
- Recovery retains/restores the persisted user without fabrication; ambiguous outcomes reconcile from PostgreSQL.
- Existing Consultation Detail behavior is unchanged.

## Testing requirements

- RTL tests cover ordered/empty/loading/missing/error states, validation, pending/duplicate prevention, successful/repeated reconciliation, safe payload rendering, AI recovery reload, and generic failure reload.
- Assert no unsafe HTML, credentials, provider detail, or fabricated response renders.

## Definition of Done

- UI tests plus typecheck/lint/build pass and established detail/service boundaries remain intact.
