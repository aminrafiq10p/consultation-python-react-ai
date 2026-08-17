# CS-010: Verify Consultation Summary Vertical Slice

**Task ID:** CS-010  
**Title:** Verify Consultation Summary Vertical Slice

## Purpose

Verify every approved Feature 003 persistence, AI, backend, frontend, failure,
concurrency, regression, runtime, security, and scope condition.

## Traceability

- Feature specification: §§3–16.
- Implementation plan: §§3–20, especially §§12–15 and 19–20.

## Scope

- Verify migration → PostgreSQL → repositories → application → deterministic
  AI → Flask → frontend service → Detail/Summary/routes/actions.
- Run complete backend/frontend/static/build/Compose checks and scope/secret
  review.
- Record reviewable verification evidence; add only missing focused tests
  needed for approved criteria.

## Expected files/areas affected

- Feature-focused test and verification-evidence documentation areas only.
- No new product source, migration, infrastructure, specification, plan, or
  unrelated refactor is expected solely for verification.

## Implementation requirements

- Verify migration round trip, constraints, PostgreSQL authority, ordered
  stable IDs, atomic rollback, sequential idempotency, and controlled
  concurrency winner recovery.
- Verify exact eligibility, full untruncated history, safe AI failures, closed
  messages, restart independence, all API contracts, runtime frontend guards,
  Detail completion, Summary reload/selection, restart navigation, and booking
  navigation only.
- Run all Feature 001 and Feature 002 regression coverage, allowing only
  deliberate fixture/test updates for approved closed conversations.
- Run complete backend tests, frontend tests, typecheck, lint, build, and
  Docker Compose with mock AI; automated checks never call live OpenAI.
- Review secrets and forbidden scope: no appointment persistence/form,
  `BOOKED` transition, dashboard, regeneration/versioning, history deletion,
  direct React/Flask OpenAI, RAG, Redis, vectors, LangGraph, WebSockets,
  streaming, authentication, multiple agents, or unrelated refactoring.

## Dependencies

- CS-006, CS-008, and CS-009; transitively CS-001 through CS-007.

## Acceptance criteria

- Every specification acceptance criterion has passing automated or explicit
  runtime evidence.
- Backend/frontend/full regression/static/build/Compose checks pass
  deterministically with no leak or architecture violation.
- The complete vertical slice preserves source history and prior features and
  contains no unauthorized scope.

## Testing requirements

- Run migration upgrade/downgrade/upgrade; focused and full Pytest; full
  `npm test`, `npm run typecheck`, `npm run lint`, and `npm run build`.
- Build/start Compose with mock provider, apply migrations, verify services,
  and exercise summary creation/reload/restart/booking navigation.
- Record exact commands/results plus secret, dependency, schema, route, and
  scope-review evidence.

## Definition of Done

- All required checks pass and evidence maps migration, persistence,
  repositories, workflows, AI, APIs, frontend service/screens/actions,
  regressions, Compose, secrets, and scope to the approved definition of done.
