# AP-015: Verify the Feature 007 Final Vertical Slice

**Task ID:** AP-015  
**Title:** Verify the Complete Feature 007 Vertical Slice
**Status:** Complete (2026-08-19)

## Objective

Close the Definition of Done by proving the full authoritative booking-to-list-
to-consultation-to-Dashboard flow.

## Dependencies

AP-014 and all AP-001–AP-014 implementation/test tasks. This task cannot begin
early or serve as a substitute for any preceding task.

## Scope

Final verification and evidence collection only; no new feature implementation.

## Implementation requirements

Exercise and cross-check:

```text
Feature 004 booking
  → committed PostgreSQL Appointment
  → GET /api/v1/appointments
  → /appointments populated state
  → one related /consultations/{consultationId} action
  → Dashboard booked_appointments
```

Verify exact IDs, treatment, patient, scheduled/created timestamps, location,
ordering, empty/error/retry behavior, desktop/mobile navigation, active states,
and all regression/scope requirements. Run focused and full backend/frontend
tests, PostgreSQL integration, typecheck/lint/build, migration, no-AI/network,
Docker/Compose, and final Git checks including `git status --short`,
`git diff --stat`, and `git diff --check`.

## Likely files/areas

Full test suites, PostgreSQL fixtures, browser/router tests, Docker runtime,
migration directory, and final diff/evidence documentation.

## Tests/checks

Use deterministic persisted data and fresh authoritative reads; no live AI or
external network. Record every command, result, prerequisite, and any
pre-existing limitation.

## Acceptance criteria

- The same Feature 004 appointment row is returned by the list API and shown by
  the screen.
- The persisted consultation ID reaches the existing consultation route.
- Dashboard booked count reflects the same row before and after list retrieval.
- All approved spec acceptance criteria and plan stages have evidence.
- No migration, AI/external call, second write flow, scope leak, or unreviewed
  shared-file conflict remains.

## Explicit non-goals/scope guards

Stop after Feature 007 evidence. Do not create new task files, modify the
approved spec/plan, commit automatically, or begin Feature 008.

## Completion evidence

A final verification report with the complete flow, command results, spec/plan
traceability, dependency completion, scope review, and final Git status/diff
checks.

## Verification result (2026-08-19)

All AP-015 acceptance criteria passed. The isolated PostgreSQL lifecycle test
exercised the authoritative Feature 004 booking, fresh Feature 007 list API
read, exact persisted appointment/recommendation/consultation values, and
Dashboard booked-appointment count. Frontend tests exercised populated, empty,
loading, recoverable-error/retry, responsive rendering, shared navigation, and
the single related-consultation action.

- `backend/.venv/bin/pytest -q tests`: 413 passed (32 pre-existing Alembic
  configuration deprecation warnings).
- `frontend npm test -- --run`: 305 passed; `npm run typecheck`, `npm run
  lint`, and `npm run build` passed (the existing Vite chunk-size advisory is
  non-failing).
- `backend/.venv/bin/alembic heads`: `20260817_04 (head)`; no migration,
  model, table, dependency, or Compose-topology change was introduced.
- `docker compose config --quiet`, `docker compose build`, and a non-destructive
  `docker compose up -d` runtime smoke test passed. PostgreSQL was healthy;
  `GET /api/v1/appointments` returned a persisted appointment and
  `/appointments` returned HTTP 200. `docker compose down` stopped the stack
  without `--volumes`, preserving local PostgreSQL data.
- The appointment read path is deterministic and contains no AI/provider,
  LangChain, OpenAI, or external-network call. Diff review found only Feature
  007 scope; `git diff --check` passed. No commit was created.
