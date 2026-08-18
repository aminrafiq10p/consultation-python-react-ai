# NC-008: Verify New Consultation Vertical Slice

**Task ID:** NC-008  
**Title:** Verify New Consultation Vertical Slice

## Purpose

Verify the complete Feature 006 browser-to-PostgreSQL flow, regress Features
001–005, validate Docker/runtime compatibility, and record final acceptance
evidence without broadening approved scope.

## Traceability

- Feature specification: §§4–17, especially §§5–14 and §17.
- Implementation plan: §§3 and 11–18.

## Scope

- Run focused/full automated, static, build, migration, PostgreSQL, Compose,
  responsive smoke, security/scope, documentation, and Git checks.
- Manually exercise New Consult through creation, detail/conversation, Records,
  and Dashboard at desktop and mobile widths.
- Record exact commands/results and make only minimal fixes directly required
  by an approved Feature 006 criterion.

## Expected files/areas affected

- Feature-focused test and verification-evidence documentation areas only.
- Minimal Feature 006 implementation/test corrections are allowed when traced
  to a failed approved acceptance criterion.
- No new migration, feature, dependency, service, or unrelated refactor is
  expected.

## Implementation requirements

- Review the final diff first and last, preserving unrelated user work and
  confirming only approved Feature 006 files/lines changed.
- Run focused DTO/application/repository/route/persistence/dashboard/no-AI and
  frontend service/screen/router/layout tests, then complete backend/frontend
  regression suites.
- Run repository TypeScript/typecheck, lint, production frontend build,
  Markdown/whitespace, migration-head, and `git diff --check` commands.
- Verify the current Alembic head supports a clean creation flow and that no
  Feature 006 revision/schema change exists.
- Run `docker compose config`, build/start the unchanged stack, apply current
  migrations as established, and verify backend/frontend/database health.
- At desktop and mobile widths exercise `+ New Consult` → static route →
  validation → submit → returned-ID detail → deliberate first message →
  Records → Dashboard, including mobile drawer closure and active state.
- Exercise recoverable/ambiguous failure where practical: input remains, no
  automatic retry occurs, and guidance directs the user to authoritative
  records before deliberate retry.
- Inspect PostgreSQL and AI call evidence for exact initial state, one identity,
  no creation-time child rows/calls, later message linkage, and natural
  dashboard total increment with booked count unchanged.
- Separate and report any unrelated/pre-existing failure; do not fix it without
  explicit approval.

## Dependencies

- NC-007; transitively NC-002 through NC-006.
- Both backend NC-002 → NC-003 and frontend NC-004 → NC-005 → NC-006 chains
  must be complete before NC-007/this verification.

## Acceptance criteria

- Every Feature 006 acceptance criterion maps to passing automated or explicit
  runtime evidence, including exact POST, accessible state machine, responsive
  navigation, replacement routing, same-ID lifecycle, dashboard, and no-AI/
  no-child creation behavior.
- Focused/full backend and frontend suites, typecheck, lint, build,
  PostgreSQL/migration, and Compose/runtime checks pass or an unrelated
  pre-existing limitation is clearly documented.
- Features 001–005 remain green and their routes/lifecycle semantics are
  unchanged.
- Final scope review finds no migration, Feature 007, patient entity, AI
  intake, auth, analytics, dashboard redesign, localStorage, second session,
  architecture drift, secret, or unrelated refactor.

## Testing requirements

- Use the exact commands confirmed in NC-001; record command, outcome, and any
  intentionally unavailable environment prerequisite.
- Include desktop/mobile route and state evidence, authoritative API/SQL
  evidence, dashboard before/after values, and strict AI/child call/row counts.
- Run `git status --short`, `git diff --stat`, and `git diff --check` last and
  distinguish pre-existing/unrelated changes from Feature 006.

## Architecture and scope guards

- Verification does not authorize new behavior. Fix only a defect directly
  traceable to the approved specification; otherwise stop and request scope.
- Do not introduce a migration, new Compose topology/dependency, live external
  AI, automatic retry, dashboard mutation, Feature 007 route/navigation, or
  any unrelated cleanup.
- Preserve PostgreSQL authority and existing Flask/application/repository/
  frontend-service/AppLayout boundaries.

## Definition of Done

- Recorded deterministic evidence proves the complete approved Feature 006
  vertical slice and Features 001–005 regressions across current migrations and
  Docker Compose, with no creation-time AI/child effects, migration, Feature
  007 leakage, architecture drift, or unresolved in-scope failure.
