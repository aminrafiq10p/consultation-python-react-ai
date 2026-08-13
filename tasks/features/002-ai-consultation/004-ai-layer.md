# AI-004: Add AI Service, Consultation Agent, Skill, and Providers

**Task ID:** AI-004  
**Title:** Add AI Service, Consultation Agent, Skill, and Providers

## Purpose

Implement the isolated provider-neutral AI path through one consultation agent and skill to LangChain-backed providers.

## Traceability

- Feature specification: §§2–3, 8–10, 12–14.
- Implementation plan: §§3, 7, 11, 12.3–12.4, 13–14.

## Scope

- Add `backend/app/ai/service.py`, `consultation_agent.py`, `consultation_skill.py`, and `providers/{base,mock,openai}.py`.
- Add minimal compatible `langchain-core`/`langchain-openai`, backend-only configuration/docs, and deterministic AI tests.

## Expected files/areas affected

- `backend/app/ai/`, backend composition/configuration, `backend/requirements.txt`, relevant environment examples, `backend/README.md`, and AI tests.

## Implementation requirements

- Expose provider-neutral context values and `AIResult(content, structured_payload=None)`; require non-blank text and allow a JSON object containing only scalars or scalar arrays.
- Coordinate exactly one service → agent → focused skill → provider call. The skill must not claim deterministic business actions.
- Keep LangChain inside the AI layer and give it no authoritative memory.
- `OpenAIProvider` receives configuration from composition, uses a 30-second timeout and one SDK retry, and reads no environment directly.
- Implement the plan-required deterministic `MockAIProvider` and centralized `AI_PROVIDER` selection (`openai`/`mock`). The mock is architecture/test compatibility, not a user-facing selector. Missing OpenAI key or unsupported provider fails safely at startup; centralize the optional `OPENAI_MODEL` default.
- Translate provider/network/auth/rate-limit/parsing failures into one safe AI exception.
- No Flask, repositories, SQLAlchemy, business mutation, RAG, tools, embeddings, vectors, LangGraph, streaming, or extra agents.

## Dependencies

- AI-001. May proceed independently of AI-002/AI-003; AI-005 performs integration.

## Acceptance criteria

- Text-only and structured results cross provider-neutral boundaries; invalid output/provider failures are sanitized.
- OpenAI configuration is server-only, mock behavior is deterministic, and provider types do not escape the AI layer.

## Testing requirements

- Unit-test one-call coordination, ordered context, valid results, malformed output, safe exception translation, mock determinism, and composition validation with stubs.
- Never issue a live OpenAI call, require a real key, or use external network access.

## Definition of Done

- AI tests pass and the layer satisfies approved provider/configuration boundaries without scope expansion.
