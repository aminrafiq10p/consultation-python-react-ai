# AP-004: Add List DTOs and GET API Contract

**Task ID:** AP-004  
**Title:** Add List DTOs and GET API Contract

## Objective

Implement the exact safe `GET /api/v1/appointments` response and request
contract in the existing versioned Flask boundary.

## Dependencies

AP-003 and AP-001’s route/error conventions.

## Scope

Dedicated list DTO/envelope, route request guard, serialization, and API tests.

## Implementation requirements

- Return exactly `{ "items": [...] }` with only the approved fields and nested
  recommendation projection; preserve POST booking response unchanged.
- Reject any query parameter or non-empty body before application invocation
  with exactly 400 `{ "error": "Invalid request" }`; empty body/content type is
  valid.
- Serialize UUIDs and aware timestamps with explicit offsets; delegate once.
- Preserve the existing safe 500 handler and never expose internals.

## Likely files/areas

Existing consultation DTO/route modules or a focused module matching current
conventions, plus backend API tests.

## Tests/checks

Exact populated/empty shape, query/body rejection with zero service calls,
timestamp/UUID serialization, safe 500 sanitization, no AI/mutation, and POST
compatibility.

## Acceptance criteria

Valid empty requests return 200 and exact envelope; invalid input never reaches
the application; unexpected failures return safe 500.

## Explicit non-goals/scope guards

No new blueprint unless required, filters, pagination, status/provider fields,
API-wide error changes, or booking semantics changes.

## Completion evidence

Passing Flask test-client contract suite with request-call counts and exact JSON
assertions.
