# DN-005: Add Frontend Dashboard Service

**Task ID:** DN-005  
**Title:** Add Frontend Dashboard Service

## Purpose

Add a dedicated typed frontend boundary that retrieves and strictly validates
the dashboard metrics contract without retrying or recalculating it.

## Traceability

- Feature specification: §§5, §7, §9, §§12–14, §§16–17.
- Implementation plan: §§3 and 8, §13.1, §15 DN-005, and §§16–19.

## Scope

- Add dashboard feature-local runtime types and a safe retrieval error.
- Add `dashboardApi.getMetrics()` using the existing injected transport and
  API-base-URL convention.
- Add focused transport, exact-shape validation, invariant, safe-error, and
  no-retry tests.

## Expected files/areas affected

- `frontend/src/app/features/dashboard/dashboardTypes.ts`.
- `frontend/src/app/features/dashboard/dashboardApi.ts`.
- `frontend/src/app/features/dashboard/dashboardApi.test.ts`.

## Implementation requirements

- Make exactly one GET-semantic call to `/api/v1/dashboard` with no query or
  request body and require exact status `200`.
- Parse JSON inside a safe boundary and accept only a non-null, non-array object
  with exactly the three approved own keys.
- Require both counts to be runtime numbers that are finite, safe integers, and
  nonnegative; require conversion to be a finite number in `0..100`.
- Enforce `booked_appointments <= total_consultations` and the zero-total
  all-zero invariant supported by the authoritative schema.
- Do not recalculate or challenge a nonzero conversion rate; the backend owns
  the formula and React may only format the received number.
- Collapse invalid JSON, malformed success, non-`200`, and transport rejection
  to one safe retrieval failure without exposing response or transport detail.
- Perform no automatic retry; only the later screen's explicit Retry may call
  the service again.

## Dependencies

- DN-001 and the approved Feature 005 API contract.
- May proceed in parallel with DN-002 through DN-004.

## Acceptance criteria

- Valid populated and zero payloads return exact typed metrics after one GET.
- Every missing/extra key, wrong shape/type, unsafe or invalid number, incoherent
  zero state, or numerator-above-denominator payload fails safely.
- Invalid JSON, every non-`200`, and network rejection expose no arbitrary
  server or transport detail and trigger no retry.
- The service contains no conversion formula, consultation API extension,
  persistence assumption beyond approved invariants, or mutation.

## Testing requirements

- Assert exact URL, GET semantics, absent query/body, transport call count, and
  no retry after failure.
- Cover null/array/non-object, missing/extra fields, negative/fractional/string/
  non-finite/unsafe counts, invalid conversion types/ranges, impossible count
  combinations, malformed JSON, statuses, and rejected transport.
- Cover valid populated and all-zero responses without relying on a live API.

## Architecture and scope guards

- Keep this boundary in a separate dashboard feature root and do not import or
  extend `consultationApi`.
- Do not add a cache, background refresh, automatic retry, local conversion
  calculation, charts, analytics library, AI, external service, or dependency.

## Definition of Done

- Focused tests prove exact one-shot transport, strict runtime contract and
  structural invariants, safe failure mapping, and backend-only conversion
  authority.
