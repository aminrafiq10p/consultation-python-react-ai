# NC-002: Add Backend Creation DTO and Application Workflow

**Task ID:** NC-002  
**Title:** Add Backend Creation DTO and Application Workflow

## Purpose

Add the strict two-field creation input boundary and the smallest existing-
service workflow that constructs a server-controlled pending consultation.

## Traceability

- Feature specification: §§2–3, §§6.1–6.2, §§7–8, §§12–15, and §17.
- Implementation plan: §§3 and 5, §§12.1, 14–16, and §§17–18.

## Scope

- Add a strict creation request DTO for `patient_name` and
  `primary_concern`.
- Extend `ConsultationApplicationService` with consultation creation using the
  existing repository.
- Add focused DTO and application tests, including no-AI/no-child assertions.

## Expected files/areas affected

- `backend/app/api/consultation_dtos.py`.
- `backend/app/application/consultation_service.py`.
- `backend/tests/api/test_consultation_dtos.py`.
- Existing or focused consultation application-service test modules.
- Inspect NC-001 findings before editing; no route, model, migration,
  repository, composition, or frontend change is expected.

## Implementation requirements

- Define a Pydantic v2 request DTO with `extra="forbid"`, `StrictStr` fields,
  before-validation trimming, and post-trim lengths of 1–200 Unicode code
  points for patient name and 1–4,000 for concern.
- Reject missing, null, blank, overlong, numeric, boolean, array, object, and
  unknown values; forbid client `id`, `status`, and
  `recommended_procedure`.
- Add one application method accepting the two values, defensively enforcing
  string/trim/bounds for non-HTTP callers without a generic validation
  framework.
- Construct exactly one consultation with a fresh UUID following the verified
  existing convention, normalized text, `recommended_procedure=""`, and
  `ConsultationStatus.PENDING`.
- Delegate exactly once to
  `ConsultationRepository.create_consultation` and return its confirmed object.
- Keep AI, messages, summaries, recommendations, appointments, dashboard, and
  commit/session behavior outside this method.

## Dependencies

- NC-001.

## Acceptance criteria

- DTO tests prove exact strict types, trimming, bounds, Unicode behavior, and
  forbidden fields.
- A captured repository argument has the exact five-field initial state,
  generated UUID, empty recommendation, and `PENDING`; the repository result
  is returned after one call.
- Defensive invalid application inputs do not call the repository.
- Tests explicitly prove no AI or child-aggregate collaborator is invoked.

## Testing requirements

- Parameterize minimum, maximum, whitespace, wrong-type, missing, unknown,
  server-controlled-field, and supplementary-Unicode cases.
- Test normalized construction, UUID uniqueness/validity, one delegation,
  returned authoritative object, and defensive failure behavior.
- Run focused DTO/application tests and relevant existing restart-service
  regressions using the exact NC-001 commands.

## Architecture and scope guards

- Keep HTTP validation in DTOs and creation invariants in the existing
  application service; do not add another service or repository.
- Do not expose the POST route in this task except an unavoidable tiny import
  seam documented in the report.
- Do not add a migration, model field, AI call, greeting, child record,
  dashboard mutation, or Feature 007 behavior.

## Definition of Done

- Focused tests prove strict normalized input and one existing-repository
  creation of the exact server-controlled pending consultation, without route,
  persistence-architecture, AI, child-side-effect, or migration changes.
