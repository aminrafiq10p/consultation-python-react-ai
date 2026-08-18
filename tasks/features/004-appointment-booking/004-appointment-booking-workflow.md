# AB-004: Add Appointment Booking Application Workflow

**Task ID:** AB-004  
**Title:** Add Appointment Booking Application Workflow

## Purpose

Implement deterministic booking eligibility, normalization, precedence, and
typed outcomes above the atomic appointment repository.

## Traceability

- Feature specification: §§6, §§8–11, §§13, 15–16, and §19.
- Implementation plan: §§3 and 6, §10.2, §13 AB-004, and §§15–17.

## Scope

- Extend `ConsultationApplicationService` with one focused booking method.
- Inject an optional `AppointmentRepository` and controllable aware clock while
  preserving Features 001–003 construction and behavior.
- Add booking input normalization, exact eligibility/conflict ordering,
  recommendation ownership checks, typed outcomes, and focused application
  tests with strict no-AI doubles.

## Expected files/areas affected

- `backend/app/application/consultation_service.py` and established application
  outcome/value modules if they are separate.
- `backend/tests/application/test_appointment_booking_service.py`.
- Existing application fixtures only where optional dependency construction
  must remain compatible.

## Implementation requirements

- Capture one aware authoritative `now`, reject a naive `scheduled_at`, compare
  in UTC, and require the requested instant to be strictly later than `now`.
- Trim surrounding location whitespace, reject blank normalized text, and
  enforce at most 200 Python Unicode code points.
- Accept only UUID consultation/recommendation identities and never treatment
  text.
- Within the repository-coordinated transaction, apply this exact precedence:
  locked missing consultation; existing appointment; `BOOKED`; any status not
  exactly `COMPLETED`; missing persisted summary; globally missing
  recommendation; recommendation not owned by that persisted summary; atomic
  create; exact duplicate-race reconciliation.
- Raise the existing `ConsultationNotFoundError` plus focused invalid-booking,
  `RecommendationNotFoundError`, `RecommendationNotBookableError`,
  `ConsultationNotBookableError`, and `AppointmentAlreadyExistsError` outcomes.
- Map both an existing appointment and inconsistent `BOOKED` without a visible
  appointment to already-exists; do not fabricate or repair a row.
- Abort/roll back every typed exit after the lock and translate only the exact
  repository duplicate result to already-exists.
- Return the committed persisted aggregate and its authoritative recommendation
  treatment without modifying any source aggregate field.

## Dependencies

- AB-003.

## Acceptance criteria

- Valid future input delegates normalized UTC-equivalent time and trimmed
  location exactly once and returns the persisted aggregate.
- Exact-now, past, naive time, blank location, and over-200-character normalized
  location fail before an approved create.
- Missing, repeat, `BOOKED`, `PENDING`, other non-`COMPLETED`, missing-summary,
  missing-recommendation, and cross-consultation cases produce the approved
  typed outcomes in the required precedence.
- A duplicate race becomes `AppointmentAlreadyExistsError`; unrelated
  persistence failures remain unexpected failures.
- Booking invokes no AI method and changes no message, summary, recommendation,
  treatment projection, or consultation field other than the repository-owned
  successful status transition.

## Testing requirements

- Inject a fixed aware UTC clock and cover future, exact-now, past, equivalent
  offsets, naive datetime, trimming, blank, Unicode, and length boundaries.
- Cover every precedence combination with repository doubles, including
  conflicting facts, abort behavior, exact delegation, and duplicate result.
- Use a strict AI dependency that fails if any booking path invokes it; run
  existing service regressions affected by constructor changes.

## Architecture and scope guards

- The application owns business decisions but imports neither Flask nor AI
  provider SDKs; SQLAlchemy mechanics remain in the repository.
- Do not invoke AI/LangChain, external services, calendar/provider logic, or
  network access, and do not retry automatically.
- Do not add retrieval/lifecycle/status, multiple appointments, repair logic,
  rescheduling, cancellation, availability/conflicts/hours, authentication,
  dashboard, or source-data mutation.

## Definition of Done

- Focused deterministic tests prove normalization, exact eligibility and
  precedence, ownership, typed outcomes, repository coordination, no AI call,
  and compatibility with all prior application workflows.
