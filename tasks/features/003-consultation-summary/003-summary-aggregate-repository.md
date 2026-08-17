# CS-003: Add Summary Aggregate Repository

**Task ID:** CS-003  
**Title:** Add Summary Aggregate Repository

## Purpose

Provide ordered summary retrieval and the single atomic persistence unit for
summary completion, plus focused restart consultation persistence support.

## Traceability

- Feature specification: §§6–8, 10, 13–16.
- Implementation plan: §§3–6, 12–14, 16–20.

## Scope

- Add a focused `SummaryRepository` for aggregate retrieval and completion.
- Extend `ConsultationRepository` only with fresh consultation creation needed
  by restart.
- Add repository, rollback, fresh-session, and controlled concurrency tests.

## Expected files/areas affected

- `backend/app/repositories/summary_repository.py` and repository exports.
- `backend/app/repositories/consultation_repository.py`.
- Focused repository/persistence/concurrency tests.

## Implementation requirements

- Retrieve by consultation and order recommendations by `(position, id)`.
- In one commit persist summary, all recommendations, first-treatment
  `recommended_procedure`, and `COMPLETED`; rollback all on any failure.
- Generate stable UUIDs and one-based positions without interpreting AI text.
- Treat only the named one-summary unique violation as a race: rollback,
  reload the winner, and distinguish it from ordinary persistence failure.
- Hold no transaction during AI work and make no AI, eligibility, Flask, or
  frontend decision in repositories.
- Restart persistence inserts one new record and never mutates/copies source
  children or retries automatically.

## Dependencies

- CS-002.

## Acceptance criteria

- Fresh retrieval preserves persisted summary/recommendation IDs and order.
- Aggregate completion is all-or-nothing, including projection and status.
- Two controlled concurrent creators result in one aggregate and both can
  observe the winning values; unrelated integrity errors remain failures.
- Restart creation follows existing commit/rollback conventions.

## Testing requirements

- PostgreSQL tests for ordered retrieval, stable IDs, atomic success, forced
  rollback at aggregate stages, unique-race recovery with independent
  sessions, unrelated integrity failures, and restart insert rollback.

## Definition of Done

- Focused repository tests pass and PostgreSQL remains authoritative without
  leaking transaction/session mechanics or adding out-of-scope persistence.
