# AP-009: Add Frontend Appointment Types and List Service

**Task ID:** AP-009  
**Title:** Add Frontend Appointment Types and List Service with Runtime Validation

## Objective

Provide a dedicated, safe, one-request appointment-list service using existing
frontend transport and API configuration conventions.

## Dependencies

AP-001; the approved API contract in the spec/plan. Live integration depends on
AP-004, but service tests may use transport doubles.

## Scope

Feature-local types, service, safe error mapping, runtime validators, and tests.

## Implementation requirements

- Issue exactly one `GET /api/v1/appointments` per invocation with no query or
  body and configured base URL.
- Accept only 200; safely parse and validate exact `{items: [...]}` structure,
  UUIDs, non-empty strings, nested recommendation fields, explicit-offset
  timestamps, and duplicate/malformed projections.
- Map HTTP, malformed JSON, validation, network, and transport failures to a
  safe typed feature error. Never auto-retry or return `[]` on failure.

## Likely files/areas

Feature-local frontend appointment types/API service/tests, following existing
consultation service and injected `FetchTransport` conventions.

## Tests/checks

Request shape/count, valid populated/empty responses, malformed matrix, non-2xx,
network failure, and one-invocation/no-auto-retry tests.

## Acceptance criteria

The service returns only validated feature-facing data and never exposes raw
response/database/transport details.

## Explicit non-goals/scope guards

No direct screen `fetch`, consultation-derived records, browser storage,
polling, retry loop, AI, external service, or booking-service changes.

## Completion evidence

Passing focused frontend service/type tests and typecheck for feature-local
modules.
