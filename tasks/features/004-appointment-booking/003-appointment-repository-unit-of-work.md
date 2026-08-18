# AB-003: Add Appointment Repository and Atomic Unit of Work

**Task ID:** AB-003  
**Title:** Add Appointment Repository and Atomic Unit of Work

## Purpose

Provide the focused persistence coordination and atomic unit of work required
to create one appointment and transition its consultation to `BOOKED`.

## Traceability

- Feature specification: §§6–11, §13, §16, and §19.
- Implementation plan: §§3 and 5, §10.1, §13 AB-003, and §§14–17.

## Scope

- Add `AppointmentRepository` using the existing request-scoped SQLAlchemy
  session.
- Add locked consultation loading, existing-appointment lookup, summary and
  recommendation reads, atomic creation/status update, rollback, and committed
  aggregate reload.
- Add repository, failure-injection, constraint-classification, fresh-session,
  and controlled two-session concurrency tests.

## Expected files/areas affected

- `backend/app/repositories/appointment_repository.py`.
- `backend/app/repositories/__init__.py` only if established exports require it.
- Focused repository, persistence rollback, and PostgreSQL concurrency tests.
- Test helpers needed for deterministic independent sessions/barriers.

## Implementation requirements

- Load a consultation by UUID with `SELECT ... FOR UPDATE` as the durable
  coordination point; keep all eligibility reads and writes in that session
  transaction.
- Look up an existing appointment by consultation UUID, including a fresh
  authoritative lookup after rollback.
- Read the consultation's persisted summary and resolve a recommendation
  globally so the application can distinguish absence from cross-owner
  existence without accepting mismatched lineage.
- Accept only application-approved normalized inputs and persisted identities;
  do not decide eligibility or construct HTTP outcomes.
- Add and flush one appointment, update only `consultation.status` to `BOOKED`,
  commit exactly once, and reload the appointment with its persisted
  recommendation projection.
- Expose a focused abort capability that rolls back typed eligibility exits and
  promptly releases the consultation lock while leaving the shared session
  usable.
- Roll back any query, add, flush, update, commit, or reload failure insofar as
  the transaction state permits; never report success before commit.
- Classify only the named appointment-consultation unique violation as a
  duplicate candidate. After rollback, return a typed duplicate repository
  result only if the winning appointment is authoritatively visible; propagate
  unrelated integrity and persistence failures.
- Treat post-commit reload failure as a failure without claiming the committed
  transaction was undone.

## Dependencies

- AB-002.

## Acceptance criteria

- Successful creation produces one linked appointment, one `COMPLETED` to
  `BOOKED` update, one commit, and a persisted recommendation-based projection.
- Forced failures before commit expose neither an appointment nor `BOOKED` in
  a fresh session.
- Two controlled independent requests serialize on the consultation row: one
  wins and one receives the stable duplicate result, with one database row.
- Exact unique-constraint reconciliation works and unrelated constraint or
  persistence errors are never misclassified or leaked.
- Messages, summary, recommendations, treatment text, order, and
  `recommended_procedure` remain unchanged.

## Testing requirements

- Use PostgreSQL 16, independent sessions, barriers/events, and bounded thread
  synchronization for the concurrency test.
- Inject failures at practical query/add/flush/update/commit/reload seams and
  verify rollback and fresh-session authority.
- Test locked SQL behavior, abort/session reuse, exact constraint-name
  classification, duplicate visibility, aggregate reload, and immutable source
  data.

## Architecture and scope guards

- Repositories own SQLAlchemy mechanics and transaction handling only;
  business precedence remains in the application layer.
- Hold the row lock only around database work. Make no AI, provider, calendar,
  network, Flask, or frontend call.
- Do not add idempotency retrieval, automatic retry, advisory/distributed lock,
  serializable-global transactions, appointment GET/lifecycle/status,
  rescheduling, cancellation, or schema/infrastructure redesign.

## Definition of Done

- Focused repository and concurrency tests prove locked coordination, exact
  duplicate reconciliation, one atomic commit, rollback safety, authoritative
  reload, and immutable source data with no business or HTTP leakage.
