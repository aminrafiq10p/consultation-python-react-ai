# AB-008: Verify Appointment Booking Vertical Slice

**Task ID:** AB-008  
**Title:** Verify Appointment Booking Vertical Slice

## Purpose

Verify every approved Feature 004 migration, persistence, concurrency, backend,
frontend, regression, runtime, security, and scope condition end to end.

## Traceability

- Feature specification: §§3–20, especially §§4, 16, and 19.
- Implementation plan: §§3, 10–12, §13 AB-008, and §§14–17.

## Scope

- Verify Summary recommendation → booking route/form → frontend service →
  Flask API → application workflow → `AppointmentRepository` → PostgreSQL →
  persisted appointment/`BOOKED` → API-backed Consultation Records reload.
- Run migration, focused, complete regression, static, build, Compose/runtime,
  immutable-source, secret, architecture, and forbidden-scope checks.
- Record reviewable evidence and add only missing focused tests required by an
  approved acceptance criterion.

## Expected files/areas affected

- Feature-focused test and verification-evidence documentation areas only.
- No new product source, migration, infrastructure, specification, plan, or
  unrelated refactor is expected solely for verification.

## Implementation requirements

- Upgrade to the Feature 004 head, inspect the schema, downgrade/upgrade, and
  prove existing data survives with exact constraints and no forbidden columns.
- Verify valid booking, strict date/location validation, every eligibility and
  ownership outcome, precedence, repeat behavior, controlled concurrency,
  exact unique reconciliation, rollback, fresh-session authority, and safe
  response bodies.
- Inject persistence failures across practical transaction boundaries and show
  that no pre-commit failure leaves either a partial appointment or `BOOKED`.
  Record the defined ambiguity behavior for post-commit reload/response loss.
- Verify messages, summary, recommendation identities/order/treatment, and
  `recommended_procedure` remain value-for-value unchanged.
- Verify the Feature 003 handoff, direct booking reload, selected persisted
  treatment, single-submit form, no retry, replacement navigation, and records
  GET showing authoritative `BOOKED` without frontend mutation.
- Run all Features 001–003 regressions, complete backend and frontend suites,
  frontend typecheck/lint/build, and the established documentation formatting/
  whitespace checks.
- Build/start the existing Compose stack with the mock AI provider, apply
  migrations, verify reachability, exercise the deterministic runtime flow,
  and inspect PostgreSQL for one linked appointment and immutable source rows.
- Review configuration, dependencies, schema, routes, frontend, and diff for
  secrets, live AI execution, architecture drift, and forbidden scope.

## Dependencies

- AB-005 and AB-007; transitively AB-001 through AB-006.

## Acceptance criteria

- Every Feature 004 acceptance criterion has passing automated or explicit
  runtime evidence mapped to the specification and plan.
- Migration round-trip, duplicate/concurrent behavior, rollback, API contracts,
  frontend behavior, authoritative records reload, and immutable source data
  are demonstrated against PostgreSQL.
- Full backend/frontend regression, test, typecheck, lint, build, and Compose
  checks pass deterministically without live credentials or external calls.
- The final diff contains only approved Feature 004 implementation/tests/docs,
  keeps Docker support working, and contains no secret or forbidden scope.

## Testing requirements

- Run migration upgrade/downgrade/upgrade and focused appointment mapping,
  repository, concurrency, application, DTO, route, persisted API, frontend
  service, screen, summary handoff, router, and records-reload tests.
- Run the complete backend Pytest suite and full `npm test`,
  `npm run typecheck`, `npm run lint`, and `npm run build` commands.
- Build/start Compose, migrate, check service health, execute one deterministic
  completed-summary booking, and query PostgreSQL afterward.
- Record exact commands, results, environment assumptions, and any pre-existing
  unrelated failures separately from Feature 004 evidence.

## Architecture and scope guards

- Tests and runtime verification must use deterministic doubles/mock AI and no
  OpenAI, LangChain execution, external calendar, network credential, or other
  external service.
- Confirm there is no appointment GET, multiple appointment, lifecycle status,
  reschedule/cancel, provider availability/conflict/hours, calendar,
  notification, payment, authentication, dashboard, AI booking, RAG, Redis,
  vector database, LangGraph, WebSocket, streaming, or infrastructure redesign.
- Do not broaden product behavior during verification; report independently
  discovered defects for approval unless a missing approved test is sufficient.

## Definition of Done

- All required checks pass and recorded evidence maps the complete booking
  vertical slice, concurrency and rollback safety, immutable source data,
  regressions, Compose runtime, secrets, architecture, and scope to the approved
  Feature 004 definition of done.
