# NC-007: Verify Lifecycle, Dashboard, and No-AI Integration

**Task ID:** NC-007  
**Title:** Verify Lifecycle, Dashboard, and No-AI Integration

## Purpose

Prove one created PostgreSQL consultation remains authoritative across existing
records, dashboard, and later deliberate conversation behavior, with no
creation-time child or AI side effect.

## Traceability

- Feature specification: §§5, 7–8, §§12–14, and §17.
- Implementation plan: §§3 and 10, §§12.6, 14–16, and §§17–18.

## Scope

- Add deterministic PostgreSQL-backed integration scenarios spanning creation,
  Feature 001 retrieval, empty Feature 002 history, dashboard metrics, and a
  later deliberate first message.
- Verify exact row/count/call deltas and same-ID continuity.
- Do not change production Dashboard, AI, persistence mapping, migrations, or
  Compose merely to produce evidence.

## Expected files/areas affected

- Existing consultation/dashboard persisted API integration test modules or a
  focused Feature 006 vertical-slice integration module.
- Existing fixtures only for additive deterministic setup/cleanup.
- Production files only for a narrowly traced Feature 006 defect; report and
  seek approval for unrelated/pre-existing defects.

## Implementation requirements

- From a clean deterministic database snapshot, capture dashboard metrics,
  create through production-composed POST, and retrieve the returned UUID via
  existing list/detail, empty messages, and a fresh SQLAlchemy session.
- Immediately after creation prove exactly one consultation delta with
  normalized values, `PENDING`, and empty recommendation; prove zero message,
  summary, recommendation, and appointment row deltas.
- Use a strict deterministic AI/provider double to prove zero calls during
  creation and all immediate reads.
- Read Dashboard through existing repository/API code and require only
  `total_consultations + 1`; booked appointments remain unchanged and
  conversion follows the unchanged Feature 005 formula.
- Deliberately submit the first Feature 002 message only after the above
  assertions; allow its existing deterministic AI boundary and prove the
  resulting messages retain the same consultation UUID.
- Verify a failed creation changes no consultation/dashboard/child counts and
  returns no fabricated authoritative identity.

## Dependencies

- NC-003, NC-005, and NC-006.

## Acceptance criteria

- POST response, list/detail, fresh-session row, empty messages, later message,
  and dashboard evidence all refer to one returned UUID.
- Creation adds exactly one pending consultation and no child row or AI call.
- Dashboard observes total `+1` naturally; booked count is unchanged and no
  production dashboard mutation/invalidation code is added.
- AI call count changes only upon the deliberate first-message workflow.
- Failed creation leaves every relevant count unchanged.

## Testing requirements

- Run migrated-PostgreSQL before/after row and metric assertions using existing
  FK-safe cleanup and request-scoped production composition.
- Assert strict provider call counts and deterministic first-message behavior;
  never use a live OpenAI request, credential, network call, or retry.
- Run relevant Features 001–005 persistence/regression tests in addition to
  the focused lifecycle integration scenario.

## Architecture and scope guards

- Keep PostgreSQL as sole authority and creation independent of AI/provider
  availability.
- Do not add dashboard writes/cache/invalidation, related creation rows,
  creation-time conversation, schema/migration, new session/service, or local
  authoritative frontend state.
- Do not alter summary, restart, booking, appointment-list, or Feature 007
  behavior.

## Definition of Done

- Deterministic integration evidence proves one authoritative consultation ID,
  exact immediate row/call deltas, natural dashboard visibility, and AI use
  only after an explicit later message, with no production scope expansion.
