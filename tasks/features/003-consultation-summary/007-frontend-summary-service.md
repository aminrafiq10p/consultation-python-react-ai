# CS-007: Extend Frontend Consultation Summary Service

**Task ID:** CS-007  
**Title:** Extend Frontend Consultation Summary Service
**Status:** Complete

## Purpose

Extend the existing consultation frontend types and transport boundary with
strictly validated summary, generation, restart, and coded-error behavior.

## Traceability

- Feature specification: §§4, 9, 12–16.
- Implementation plan: §§3, 8–11, 13–14, 16–20.

## Scope

- Add summary/recommendation feature types and error kinds.
- Add `summary`, `generateSummary`, and `restartConsultation` methods to
  `consultationApi`.
- Extend closed-conversation submission translation and transport tests.

## Expected files/areas affected

- `frontend/src/app/features/consultation-records/consultationTypes.ts`.
- `frontend/src/app/features/consultation-records/consultationApi.ts` and its
  tests.

## Implementation requirements

- Use exact approved routes/methods and no POST request body.
- Runtime-validate UUID/linkage, nonblank text, non-empty treatments, unique
  IDs/positive unique ascending positions, nullable/nonblank rationale, and
  valid timestamp.
- Map only exact status/code combinations to summary-not-available,
  not-eligible, generation-failed, not-restartable, conversation-closed, and
  existing safe errors; malformed bodies fail generically.
- Continue through the single service; expose no raw transport/provider data
  and add no direct component fetch or OpenAI dependency.

## Dependencies

- CS-001 and the approved Feature 003 HTTP contract.
- Live integration depends on CS-006.

## Acceptance criteria

- Consumers receive only validated persisted summary/restart data and can
  distinguish every approved UI state.
- `200` and `201` summary responses work without changing DTO values.
- Existing list/detail/message service behavior remains compatible.

## Testing requirements

- Vitest transport tests for exact URL/method/no-body, `200`/`201`, valid/null
  rationale, every runtime invariant, all coded errors, malformed errors,
  closed submission, and network/generic failures without a backend.

## Definition of Done

- Service tests and typecheck pass; React consumers need no HTTP, persistence,
  AI, or appointment implementation knowledge.
