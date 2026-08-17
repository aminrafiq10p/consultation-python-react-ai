# CS-004: Extend AI Abstraction for Consultation Summaries

**Task ID:** CS-004  
**Title:** Extend AI Abstraction for Consultation Summaries
**Status:** Complete  

## Purpose

Extend the existing AI service, single agent/skill, and provider abstraction
with deterministic, provider-neutral structured summary generation.

## Traceability

- Feature specification: §§7, 11, 13–16.
- Implementation plan: §§2–3, 6.2, 7, 13–16, 18–20.

## Scope

- Add validated provider-neutral summary result/request values.
- Add summary operations to the existing AI service, consultation agent/skill,
  OpenAI provider, and mock provider.
- Add deterministic AI-layer tests without network calls.

## Expected files/areas affected

- `backend/app/ai/service.py`, `consultation_agent.py`, and
  `consultation_skill.py`.
- `backend/app/ai/providers/base.py`, `openai.py`, and `mock.py`.
- AI-layer tests and exports where required.

## Implementation requirements

- Require trimmed nonblank patient summary, one or more ordered nonblank
  treatment strings, and null or trimmed nonblank rationale.
- Preserve order without deduplication, ranking, or clinical reinterpretation.
- Add `generate_summary` through the existing service/agent/provider path; do
  not create another agent or call OpenAI from application/API code.
- Use a separate exact Pydantic structured-output schema with the already
  configured ChatOpenAI instance/settings.
- Translate provider, malformed-output, and context-limit failures through the
  existing safe AI boundary.
- Make mock output deterministic and network-free; add no tools, RAG, memory,
  Redis, LangGraph, streaming, or appointment behavior.

## Dependencies

- CS-001.

## Acceptance criteria

- The existing interactive response path remains compatible.
- Summary generation crosses AIService → existing agent → skill → configured
  provider and returns only validated provider-neutral data.
- OpenAI details stay inside the provider; mock summaries are deterministic.

## Testing requirements

- Unit-test normalization and every invalid shape, full ordered message
  forwarding, service/agent/skill coordination, structured OpenAI mapping,
  deterministic mock output, and sanitized failures with provider doubles.
- No automated test may call live OpenAI, read a real key, or use the network.

## Definition of Done

- AI tests pass, Feature 002 AI behavior remains green, and no persistence,
  Flask, frontend, extra-agent, or unauthorized technology enters the layer.
