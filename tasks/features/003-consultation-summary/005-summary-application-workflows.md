# CS-005: Add Consultation Summary Application Workflows

**Task ID:** CS-005  
**Title:** Add Consultation Summary Application Workflows

## Purpose

Coordinate summary retrieval/generation, exact eligibility, idempotency,
completion, closed-conversation enforcement, and restart independently of HTTP
and persistence mechanics.

## Traceability

- Feature specification: §§4–11, 13–16.
- Implementation plan: §§3, 5–7, 12–14, 16–20.

## Scope

- Extend `ConsultationApplicationService` and add typed application outcomes.
- Inject/use summary, consultation, message, and AI boundaries.
- Add isolated deterministic application-workflow tests.

## Expected files/areas affected

- `backend/app/application/consultation_service.py` and application exports if
  present.
- Backend application tests and deterministic repository/AI doubles.

## Implementation requirements

- Retrieval verifies consultation existence, returns persisted aggregate, or
  raises typed summary-not-available.
- Generation checks existing summary before eligibility/AI; otherwise require
  `PENDING`, both message roles, and assistant-last in repository order.
- Send every persisted message unchanged and ordered to summary AI; never use
  Feature 002's bounded tail or silently truncate history.
- Defensively validate the AI result, then delegate the one atomic completion
  unit; return a creation flag and accept repository race-winner recovery.
- Translate AI/malformed result to typed safe generation failure without
  changing status/projection or persisting partial summary data.
- Reject new messages for `COMPLETED` and `BOOKED` before persistence/AI while
  preserving all pending Feature 002 semantics.
- Restart requires `COMPLETED` plus persisted summary and creates exact copied
  patient/concern, empty projection, `PENDING` data without source mutation or
  child copying.

## Dependencies

- CS-003 and CS-004.

## Acceptance criteria

- Every approved status/history eligibility case has deterministic behavior.
- Sequential generation is idempotent and existing summaries bypass AI.
- Complete history reaches AI; valid completion delegates atomically; all
  failure paths avoid unintended writes.
- Closed submissions and restart outcomes are explicit application errors.

## Testing requirements

- Test missing, empty, one-role, user-last, eligible, `BOOKED`, completed with
  summary, and inconsistent completed-without-summary cases.
- Test >20-message/>24,000-character full forwarding, call order, validation,
  AI/persistence/race outcomes, no premature calls, closed-message rejection,
  and exact restart values/source preservation.

## Definition of Done

- Application tests pass; orchestration remains Flask/SQLAlchemy/provider-SDK
  independent and adds no appointment, regeneration, deletion, or other scope.
