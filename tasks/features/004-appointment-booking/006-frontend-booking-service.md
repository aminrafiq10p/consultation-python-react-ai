# AB-006: Extend Frontend Consultation Booking Service

**Task ID:** AB-006  
**Title:** Extend Frontend Consultation Booking Service

## Purpose

Add the typed, runtime-validated, one-shot frontend transport contract for
appointment booking through the existing consultation API service.

## Traceability

- Feature specification: §§9, §12, §§14–16, and §19.
- Implementation plan: §§3 and 8, §10.3, §13 AB-006, and §§14–17.

## Scope

- Add booking request, persisted appointment, nested recommendation, and safe
  error types to the consultation-records frontend feature.
- Add `bookAppointment(consultationId, request)` to `consultationApi`.
- Add focused transport, runtime-validation, linkage, error-mapping, and no-
  retry tests.

## Expected files/areas affected

- `frontend/src/app/features/consultation-records/consultationTypes.ts`.
- `frontend/src/app/features/consultation-records/consultationApi.ts`.
- `frontend/src/app/features/consultation-records/consultationApi.test.ts` or
  the established focused service test file.

## Implementation requirements

- Model a request containing only stable `recommendation_id`, explicit-offset
  `scheduled_at`, and normalized `location`.
- Model the appointment response with UUID `id`, matching `consultation_id`,
  nested recommendation `id`/nonblank `treatment`, valid explicit-offset
  `scheduled_at`, normalized nonblank location of at most 200 Unicode code
  points, and valid explicit-offset `created_at`.
- Send exactly one JSON `POST` to
  `/api/v1/consultations/{consultationId}/appointments` with the approved
  headers/body and no automatic retry.
- Require exact HTTP `201` for success and runtime-validate UUIDs, timestamps,
  representation shape, requested consultation linkage, and requested
  recommendation linkage.
- Map only exact status/code combinations to stable validation, consultation-
  missing, recommendation-missing, recommendation-not-bookable, consultation-
  not-bookable, and appointment-already-exists kinds.
- Collapse malformed success/error payloads, unexpected combinations, safe
  `500`, and transport rejection into safe submission/ambiguous failure kinds
  without displaying arbitrary server text.
- Accept the browser-converted ISO instant; do not parse `datetime-local` or
  mutate consultation records in the service.

## Dependencies

- AB-001 and the approved Feature 004 API contract.

## Acceptance criteria

- A valid call emits exactly one approved request and returns a fully validated
  appointment linked to both requested identifiers.
- Malformed UUIDs, linkage, treatment, timestamps, location, success status, or
  payload structure are rejected safely.
- Every exact approved error maps to its stable frontend kind; malformed,
  transport, and server failures expose no unsafe server text.
- No service behavior retries, changes a local consultation to `BOOKED`, or
  treats URL data as ownership authority.

## Testing requirements

- Transport-test exact path, method, headers, body, explicit-offset input, and
  one invocation with no retry after rejection.
- Runtime-test every success field and requested-identifier invariant,
  including `Z` and numeric offsets, invalid/naive dates, blank treatment,
  untrimmed/blank/overlong location, and malformed payloads.
- Test all exact `400`, both `404`, coded `409`, `500`, unexpected status/code,
  malformed error, and network-rejection mappings.

## Architecture and scope guards

- Keep `consultationApi` as the only HTTP boundary and remain within the
  existing consultation-records feature root.
- Do not create another client, retry mechanism, cache mutation, booking screen,
  appointment GET/lifecycle, provider/calendar logic, auth, dashboard, AI, or
  infrastructure dependency.

## Definition of Done

- Focused frontend service tests prove exact one-shot transport, strict runtime
  invariants, safe error mapping, explicit-offset handling, and no local status
  mutation or unauthorized frontend scope.
