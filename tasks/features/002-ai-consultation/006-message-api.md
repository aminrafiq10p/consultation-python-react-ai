# AI-006: Expose Consultation Message API

**Task ID:** AI-006  
**Title:** Expose Consultation Message API

## Purpose

Expose ordered history and submission through the existing versioned consultation blueprint with explicit DTOs and safe errors.

## Traceability

- Feature specification: §§6–7, 10, 12, 14.
- Implementation plan: §§3, 6, 8, 11, 12.4, 13–14.

## Scope

- Add GET/POST `/api/v1/consultations/<consultation_id>/messages`, Pydantic DTOs, outcome translation, compatible factory composition, API tests, and deterministic persistence integration coverage.

## Expected files/areas affected

- `backend/app/api/consultation_dtos.py`, `consultation_routes.py`, `backend/app/__init__.py`, and backend API/integration tests/fixtures.

## Implementation requirements

- Validate UUID and trimmed non-blank content up to 4,000 characters.
- GET returns `{ "items": [...] }`; POST returns confirmed `user_message` and `assistant_message` DTOs.
- Return `400` invalid input, `404` absent consultation, safe `500` unexpected/persistence failure.
- Translate typed AI failure to `503` with `error`, `code: "AI_GENERATION_FAILED"`, and the persisted `user_message` DTO.
- Never expose prompts, raw output, provider/model names, exceptions, stacks, or credentials.
- Routes parse, delegate once, serialize, and translate; no direct repository/session/LangChain use.
- Preserve Feature 001 routes and injectable tests while production dependencies share the request session.

## Dependencies

- AI-005.

## Acceptance criteria

- GET covers ordered, empty, invalid, and absent histories; POST covers successful persisted exchange and every approved failure contract.
- Production/test composition remains compatible and safe.

## Testing requirements

- Pytest DTO/API coverage for shapes, GET/POST success, blank/oversized/invalid body or UUID, `404`, valid recovery `503`, safe `500`, and absence of sensitive text.
- PostgreSQL-backed repeated-message API→service→repositories test with a deterministic AI double and fresh retrieval; no live AI.

## Definition of Done

- API/integration tests pass and only approved application contracts are exposed.
