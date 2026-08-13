# AI-007: Extend Frontend Consultation Conversation Service

**Task ID:** AI-007  
**Title:** Extend Frontend Consultation Conversation Service

## Purpose

Extend the existing consultation types and transport service with a safely validated persistent-conversation contract.

## Traceability

- Feature specification: §§7, 10–12.
- Implementation plan: §§3, 8–10, 12.5, 13–14.

## Scope

- Extend `consultationTypes.ts` with role/message/history/exchange/payload/error types.
- Add `messages(consultationId)` and `submitMessage(consultationId, content)` to `consultationApi.ts` with transport tests.

## Expected files/areas affected

- `frontend/src/app/features/consultation-records/consultationTypes.ts`, `consultationApi.ts`, and frontend service tests.

## Implementation requirements

- Represent roles exactly as `USER | ASSISTANT`, persisted IDs/timestamps, nullable structured objects with scalar/scalar-array values, history, and exchanges.
- Runtime-validate every response and reject unsupported nesting.
- POST JSON `{ "content": ... }` to the approved endpoint.
- Map validation, missing, recoverable AI, retrieval/submission, and generic failures safely. Accept a `503.user_message` only when it is a valid persisted USER DTO; malformed bodies become generic failures.
- Preserve Feature 001 service behavior. Components must have no direct fetch/OpenAI logic, provider detail, or credentials.

## Dependencies

- AI-001 and fixed API contract; live integration depends on AI-006.

## Acceptance criteria

- Both methods construct the correct request and expose only validated feature data.
- Consumers can distinguish missing consultation, persisted-user AI recovery, validation, and general failures.
- Malformed success/recovery responses fail safely.

## Testing requirements

- Vitest coverage for GET/POST construction, ordered/empty results, text/structured payloads, malformed DTOs, all error kinds, valid/invalid recovery data, and transport failure using stubs only.

## Definition of Done

- Service tests/typecheck pass and conversation consumers need no transport/provider knowledge.
