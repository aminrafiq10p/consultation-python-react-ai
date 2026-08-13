# AI-009: Verify AI Consultation Vertical Slice

**Task ID:** AI-009  
**Title:** Verify AI Consultation Vertical Slice

## Purpose

Verify the complete persistent conversation path and every approved state, failure, security, architecture, and scope condition.

## Traceability

- Feature specification: §§3–14.
- Implementation plan: §§1–14, especially §§11–14.

## Scope

- Verify PostgreSQL → repository → application → deterministic AI double → Flask → frontend service → Consultation Detail.
- Run applicable persistence/repository/application/AI/API/integration/frontend/static/build checks.
- Define a manual real-OpenAI smoke procedure with a developer-supplied backend key; never add it to normal automation.
- Review Feature 001 regression, secrets, Docker availability, and scope.

## Expected files/areas affected

- Feature-focused tests and verification documentation/task evidence only; no new product source, migration, or unrelated infrastructure is expected solely for verification.

## Implementation requirements

- Exercise repeated messages and fresh retrieval to prove PostgreSQL authority, stable `(created_at, id)` order, exact 20-message/24,000-character context, and USER-before-AI/ASSISTANT-after-AI boundaries.
- Verify AI failure retains USER with no assistant and assistant-persistence failure yields no false success.
- Automated checks never call live OpenAI, read a real key, or use network; verify no frontend AI secret/dependency.
- Document a manual smoke that selects `openai`, supplies `OPENAI_API_KEY` and optional `OPENAI_MODEL` only to backend, submits to a disposable existing consultation, verifies persisted retrieval, and removes credentials. State network/cost/key prerequisites.
- If Compose remains absent, record verification unavailable rather than creating unrelated infrastructure.
- Add no summary, treatment workflow, restart, booking/`BOOKED`, dashboard, RAG, embeddings, vectors, Redis, LangGraph, WebSockets, streaming, extra agents, auth, or Azure.

## Dependencies

- AI-006, AI-007, and AI-008; transitively AI-001 through AI-005.

## Acceptance criteria

- Repeated interaction persists/reloads in order with exact bounded context and all failure semantics.
- API/UI errors and payload rendering are safe, Feature 001 stays green, and no secret/provider detail leaks.
- Compose passes when available or its pre-existing absence is reported; manual OpenAI steps remain non-automated.

## Testing requirements

- Run relevant Pytest persistence, repository, application, AI, API, and PostgreSQL integration suites.
- Run `npm test`, `npm run typecheck`, `npm run lint`, and `npm run build` under `frontend/`.
- Verify Alembic upgrade/downgrade and Compose only when its approved foundation exists; record results/unavailable checks.

## Definition of Done

- Applicable deterministic checks pass, manual-smoke instructions are reviewable, all acceptance criteria are evidenced, and no regression, leak, architecture violation, or scope expansion remains.
