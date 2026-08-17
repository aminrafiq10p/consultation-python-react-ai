# CS-006: Expose Consultation Summary and Restart APIs

**Task ID:** CS-006  
**Title:** Expose Consultation Summary and Restart APIs

## Purpose

Expose approved summary retrieval/generation and restart operations through the
existing consultation blueprint with explicit DTOs and safe errors.

## Traceability

- Feature specification: §§4, 8–10, 13–16.
- Implementation plan: §§3, 6, 8, 12–16, 18–20.

## Scope

- Add GET/POST summary and POST restart DTOs/routes.
- Wire `SummaryRepository` through existing request composition.
- Translate closed-message submissions and add API/persistence integration
  coverage.

## Expected files/areas affected

- `backend/app/__init__.py`.
- `backend/app/api/consultation_dtos.py` and `consultation_routes.py`.
- Backend DTO/API/integration tests and fixtures.

## Implementation requirements

- Expose exactly the three approved endpoints and summary/recommendation DTO
  fields/order; restart returns existing consultation DTO with `201`.
- Reject invalid UUID or any supplied POST body with safe `400`; return missing
  `404` and exact coded `409`/`503` outcomes from the plan.
- Return summary `201` only for creation and `200` for sequential/race-existing
  results.
- Translate closed message submission to coded `409
  CONSULTATION_CONVERSATION_CLOSED`.
- Routes validate, delegate once, and serialize; no route may access a
  repository/session or invoke AI/LangChain.
- Preserve injection tests and existing Feature 001/002 contracts; expose no
  raw output, prompt, provider/model, credential, SQL, constraint, or exception.

## Dependencies

- CS-005.

## Acceptance criteria

- HTTP behavior exactly matches approved `200`/`201`, `400`, `404`, coded
  `409`, coded `503`, and safe `500` contracts.
- Production composition shares one request session across all repositories.
- The deterministic full slice persists/reloads one summary and a fresh restart
  without live AI.

## Testing requirements

- Pytest DTO/API coverage for all success/status/code/body/UUID/malformed and
  leakage paths.
- PostgreSQL integration for create, repeat GET/POST, atomic completion,
  closed messages, safe failure, and restart/source independence using an AI
  double.

## Definition of Done

- API/integration tests pass through established boundaries and no appointment
  API, `BOOKED` transition, or unrelated route/composition refactor is added.
