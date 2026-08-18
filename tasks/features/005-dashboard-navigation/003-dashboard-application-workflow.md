# DN-003: Add Dashboard Metrics Application Workflow

**Task ID:** DN-003  
**Title:** Add Dashboard Metrics Application Workflow

## Purpose

Implement the provider-neutral dashboard workflow that validates repository
counts and calculates the approved conversion rate with exact decimal rules.

## Traceability

- Feature specification: §§5, §8, §§13–14, §§16–17.
- Implementation plan: §§3 and 5, §12.2, §15 DN-003, and §§16–19.

## Scope

- Add `DashboardMetrics` or an equivalent immutable application value.
- Add a focused `DashboardApplicationService` consuming the dashboard count
  repository through the narrowest useful interface.
- Add strict deterministic unit tests for validation, calculation, call count,
  and dependency isolation.

## Expected files/areas affected

- `backend/app/application/dashboard_service.py`.
- `backend/tests/application/test_dashboard_service.py`.
- Lightweight application exports only if required by existing conventions.

## Implementation requirements

- Call the repository count operation exactly once per `get_metrics()` call.
- Reject either count if it is not an integer or is negative; do not silently
  coerce, clamp, recompute, or repair impossible repository output.
- Return `Decimal("0.00")` when total consultations is zero.
- Otherwise construct `Decimal` values directly from integers, calculate
  `booked / total * 100`, and quantize once to `Decimal("0.01")` using
  `ROUND_HALF_UP`.
- Return the unchanged integer counts and the two-decimal semantic percentage.
- Remain independent of Flask, Pydantic, SQLAlchemy mappings, React, AI,
  LangChain, provider SDKs, and network collaborators.

## Dependencies

- DN-002.

## Acceptance criteria

- `0/0` yields `Decimal("0.00")`; zero bookings with a nonzero total succeeds.
- Exact, repeating, half-up, and full conversion cases produce the approved
  two-decimal results, including `1/4`, `1/3`, `1/32`, and `n/n`.
- Negative or non-integer count output fails defensively.
- Each successful or invalid repository result follows one repository call and
  invokes no unrelated consultation, persistence-write, AI, or network method.

## Testing requirements

- Use a strict count-only repository double and assert exact invocation count.
- Cover `0/0`, `0/n`, `1/4 -> 25.00`, `1/3 -> 33.33`,
  `1/32 -> 3.13`, `n/n -> 100.00`, and invalid count values.
- Assert returned values preserve integer counts and `Decimal` precision, with
  no binary-float input or application-level serialization.

## Architecture and scope guards

- Keep percentage authority in this application service; the repository only
  counts and the frontend only formats the returned value.
- Do not add Flask/DTO behavior, SQLAlchemy model access, mutation, persistence,
  cache, charts, analytics, AI, external service, or infrastructure changes.

## Definition of Done

- Strict unit tests prove one count read, defensive invariants, zero safety,
  integer-origin `Decimal` calculation, `ROUND_HALF_UP` quantization, and full
  dependency isolation.
