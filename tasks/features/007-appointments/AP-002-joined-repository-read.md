# AP-002: Add Joined AppointmentRepository List Read

**Task ID:** AP-002  
**Title:** Add Joined AppointmentRepository List Read

## Objective

Extend the existing appointment repository with one deterministic joined read
that projects authoritative appointment, patient, and selected treatment data.

## Dependencies

AP-001.

## Scope

Repository method/value projection and focused repository tests only.

## Implementation requirements

- Select appointment fields plus `Consultation.patient_name` and selected
  recommendation `id/treatment`.
- Explicitly join Appointment → Consultation → Recommendation → Summary, with
  Summary constrained to the appointment consultation.
- Use one SQLAlchemy load path, no ORM relationship assumptions, N+1 loads,
  Python matching, fabricated values, or `distinct()` as a join substitute.
- Order by `scheduled_at ASC`, then `Appointment.id ASC`; do not commit or
  mutate. Let inconsistent lineage fail for the safe API boundary.
- Keep Feature 004 booking aggregates, columns, constraints, and transaction
  semantics unchanged.

## Likely files/areas

`backend/app/repositories/appointment_repository.py`, provider-neutral read
value/type area if established, repository tests, model imports, PostgreSQL
fixtures.

## Tests/checks

Empty, one-row, multiple-row, same-time tie-break, patient/treatment lineage,
no-duplicate, one-query/no-N+1, no-commit/mutation, and strict no-AI tests.

## Acceptance criteria

One persisted appointment produces exactly one complete read projection and all
items are deterministically ordered from PostgreSQL values.

## Explicit non-goals/scope guards

No API serialization, Flask access, new repository hierarchy, schema/model
change, booking change, Dashboard change, AI, or external network.

## Completion evidence

Focused repository tests and a diff showing only the existing repository/read
projection boundary and its tests.
