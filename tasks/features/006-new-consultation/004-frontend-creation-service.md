# NC-004: Extend Frontend Consultation Creation Service

**Task ID:** NC-004  
**Title:** Extend Frontend Consultation Creation Service

## Purpose

Add one feature-local, one-shot, runtime-safe frontend operation for creating a
consultation while preserving all existing read/lifecycle validators.

## Traceability

- Feature specification: §§6, 9, §§12 and 14–15, and §17.
- Implementation plan: §§3 and 7, §§12.4, 14–16, and §§17–18.

## Scope

- Extend the existing consultation types and API module with the exact
  two-field request and `createConsultation` operation.
- Add creation-specific safe error kinds and strict success validation.
- Add comprehensive injected-transport tests without changing screens/routes.

## Expected files/areas affected

- `frontend/src/app/features/consultation-records/consultationTypes.ts`.
- `frontend/src/app/features/consultation-records/consultationApi.ts`.
- `frontend/src/app/features/consultation-records/consultationApi.test.ts`.
- No component, router, layout, storage, backend, or infrastructure file.

## Implementation requirements

- Define a request type with exactly `patient_name` and `primary_concern`.
- Trim both fields at the call boundary and issue exactly one POST to
  `/api/v1/consultations` with JSON content type and exactly those snake-case
  body keys; perform no retry or follow-up GET.
- Map only an exact valid safe `400` envelope to a confirmed creation-
  validation error kind. Collapse transport errors, unexpected statuses,
  malformed error/success bodies, safe `500`, and unreadable JSON to one safe
  ambiguous submission/confirmation kind.
- Require exact HTTP `201`, readable JSON, an exact five-key record, valid UUID,
  exact normalized-value equality, empty `recommended_procedure`, and
  `PENDING` status before returning.
- Keep creation-only exactness in a wrapper/refinement so existing list,
  detail, messages, summary, restart, and booking validators still accept all
  their approved states.
- Never surface response text, transport exception detail, credentials, SQL,
  environment data, or backend internals.

## Dependencies

- NC-001 and the approved Feature 006 API contract.
- May run in parallel with NC-002 and NC-003; live integration waits for
  NC-003.

## Acceptance criteria

- Tests prove exact normalized URL/method/header/body, one transport call, and
  no retry/follow-up request.
- Exact valid `201` returns the record; exact safe `400` and every ambiguous
  failure map to distinct stable safe kinds.
- Missing/extra keys, invalid UUID/types, mismatched values, nonempty
  recommendation, and non-`PENDING` status never return success.
- Existing consultation service behavior and validators remain compatible.

## Testing requirements

- Cover `201`, `200`, `202`, `204`, valid/malformed `400`, `404`, `409`, `500`,
  transport rejection, unreadable JSON, and every malformed-success invariant.
- Assert exact request count and absence of raw backend/transport details from
  public errors.
- Run focused API tests and the existing consultation service regression suite
  using NC-001 commands.

## Architecture and scope guards

- Keep HTTP and runtime validation in the existing dedicated service; React
  components must not acquire transport concerns.
- Do not add another client/feature hierarchy, auto-retry, localStorage/global
  cache, dashboard mutation, AI/follow-up creation, or weaken old validators.
- Do not implement the screen, route, navigation, backend, migration, or
  Feature 007.

## Definition of Done

- Transport tests prove one exact safe creation request and creation-specific
  authoritative response validation, with distinct confirmed/ambiguous errors
  and no regression or hidden side effect.
