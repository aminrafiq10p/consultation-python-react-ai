# CR-005: Expose Consultation Read API with DTO Validation

**Task ID:** CR-005  
**Title:** Expose Consultation Read API with DTO Validation

## Purpose

Deliver the approved versioned Flask endpoints, explicit Pydantic DTOs, and
safe HTTP outcome translation for consultation list and detail retrieval.

## Traceability

- Feature specification: §6, §7, §10, §12.
- Implementation plan: §§3, 8, 12–16, 18.

## Scope

- Register `GET /api/v1/consultations` and
  `GET /api/v1/consultations/{consultation_id}` in the existing API grouping.
- Define list query/path request DTOs and explicit consultation/list response
  DTOs.
- Delegate through CR-004 and map validation, absent-detail, and unexpected
  failures to the established safe API format.

## Expected files/areas affected

- `backend/app/api/` route, DTO, blueprint registration, and error-translation
  areas.
- Backend API tests and test application fixtures.

## Implementation requirements

- Validate only the statuses `PENDING`, `BOOKED`, and `COMPLETED`; reject an
  invalid status, blank supplied search, and invalid path/query input with
  `400`.
- Return `{ "items": [...] }` for successful lists, including empty lists,
  and the specified five-field record shape.
- Return `404` only for absent detail and a client-safe `500` without internal
  persistence details for unexpected failures.
- Routes must not access repositories or sessions directly.

## Dependencies

- CR-004.

## Acceptance criteria

- Both endpoints exactly honor the approved request and response contract.
- Search/status criteria, empty list success, detail success, `400`, `404`,
  and safe `500` outcomes are observable at the HTTP boundary.

## Testing requirements

- Add Pytest API tests for DTO shapes, valid lists/details, empty results,
  blank/invalid input, missing detail, and safe unexpected error behavior.

## Definition of Done

- API tests pass, API routes delegate through the application service, and no
  contract, architecture, or scope expansion is introduced.
