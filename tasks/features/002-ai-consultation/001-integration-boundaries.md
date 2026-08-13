# AI-001: Confirm AI Consultation Integration Boundaries

**Task ID:** AI-001  
**Title:** Confirm AI Consultation Integration Boundaries

## Purpose

Record the Feature 001 conventions and integration seams that Feature 002 must extend without changing product behavior.

## Traceability

- Feature specification: §§2–3, 6–12.
- Implementation plan: §§1–3, 6, 8–10, 12–14.

## Scope

- Inspect application-factory/session composition, the consultation service, blueprint/DTO/errors, repositories, PostgreSQL tests, frontend service/types, Consultation Detail, environment examples, dependencies, and Docker availability.
- Record compatible factory injection, route registration, test-double seams, fixed DTO/error contracts, context policy, and transaction boundaries.
- Do not implement product behavior.

## Expected files/areas affected

- `tasks/features/002-ai-consultation/AI-001-findings.md` or equivalent task-local findings only.
- Existing backend, frontend, test, configuration, and infrastructure files are inspected but unchanged.

## Implementation requirements

- Make no source, schema, migration, dependency, configuration, or test-code change.
- Identify how composition can evolve without breaking Feature 001 tests or contracts.
- Treat the approved specification and plan as authoritative and document mismatches instead of silently changing architecture.
- Confirm all Feature 002 scope exclusions.

## Dependencies

- Approved Feature 002 specification/plan and completed Feature 001.

## Acceptance criteria

- Later tasks have exact repository paths and conventions for composition, persistence, DTO errors, frontend transport/routing, tests, environment, and dependencies.
- Both message endpoints and their `400`, `404`, recoverable `503`, and safe `500` contracts are recorded unchanged.
- Missing Docker Compose, if still absent, is recorded without implementation.

## Testing requirements

- Documentation/convention review only; no automated feature test is created or run solely for this task.

## Definition of Done

- Reviewable findings are sufficient for AI-002 through AI-009 and no application behavior or approved requirement changed.
