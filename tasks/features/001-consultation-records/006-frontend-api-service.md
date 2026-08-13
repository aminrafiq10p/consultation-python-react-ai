# CR-006: Build Consultation Records Frontend Service Boundary

**Task ID:** CR-006  
**Title:** Build Consultation Records Frontend Service Boundary

## Purpose

Provide the dedicated frontend API/service module and feature-facing types
that isolate records/detail screens from HTTP transport.

## Traceability

- Feature specification: §§6, 8, 10, 12.
- Implementation plan: §§3, 9, 12, 14.4–15, 16–18.

## Scope

- Define feature-facing TypeScript types for a consultation record, list
  response, approved statuses, and distinguishable transport/not-found
  outcomes.
- Implement contract-conformant requests for both approved endpoints.
- Construct query parameters only for active trimmed search and selected
  status; omit `status` for all-status.

## Expected files/areas affected

- Frontend consultation-records feature API/service and feature-type areas.
- Frontend service/transport contract tests.

## Implementation requirements

- This service is the sole frontend transport boundary for consultation data.
- Translate response and transport errors for screen use; components must not
  make direct HTTP calls or access persistence.
- Do not add frontend datasets, backend filtering rules, AI integration, or
  unapproved endpoint calls.

## Dependencies

- CR-001 and the approved API contract.
- This task may run in parallel with CR-002 through CR-005; live endpoint
  integration depends on CR-005.

## Acceptance criteria

- The service represents the approved DTO/error contract and builds URLs with
  only applicable query criteria.
- All-status omits `status`, while approved statuses are transmitted exactly.
- Frontend consumers can distinguish a detail `404` from a recoverable
  transport/retrieval error.

## Testing requirements

- Add deterministic frontend tests that stub the transport boundary and verify
  list/detail request construction, response translation, transport failure,
  and not-found translation without a live backend.

## Definition of Done

- Service tests and relevant type checks pass; the work is independently
  reviewable and remains compatible with the shared API contract.
