# DN-008: Verify Dashboard and Navigation Vertical Slice

**Task ID:** DN-008  
**Title:** Verify Dashboard and Navigation Vertical Slice
**Status:** Complete  

## Purpose

Verify the complete Feature 005 PostgreSQL-to-UI metrics path, shared
navigation, Feature 004 booking update, regressions, Docker runtime, security,
and approved-scope boundaries.

## Traceability

- Feature specification: §§4–18, especially §§5–7, §§10–14, and §17.
- Implementation plan: §§3, 12–14, §15 DN-008, and §§16–19.

## Scope

- Verify PostgreSQL → repository → application service → dashboard API →
  frontend service → Dashboard UI.
- Verify `AppLayout` → Dashboard/Consultations → every existing consultation
  deep route across desktop and mobile behavior.
- Verify a deterministic persisted consultation → initial dashboard → Feature
  004 booking → appointment/`BOOKED` → refreshed dashboard scenario.
- Run focused, regression, static, build, Compose, architecture, secret, AI,
  migration, and diff/scope checks and record reviewable evidence.

## Expected files/areas affected

- Feature-focused test and verification-evidence documentation areas only.
- Minimal implementation/test corrections are allowed only when required to
  satisfy an already approved acceptance criterion.
- No new migration, feature, service, dependency, or unrelated refactor is
  expected during verification.

## Implementation requirements

- Persist mixed consultation statuses and related rows, read initial metrics,
  book one eligible completed consultation through the Feature 004 boundary,
  and read updated metrics in a new request/session.
- Prove the appointment persists, the consultation becomes `BOOKED`, booked
  count increments exactly once, total remains authoritative, and backend
  half-up conversion updates correctly.
- Compare fresh-session snapshots proving dashboard reads mutate nothing and
  only the explicit booking performs its approved appointment/status changes;
  messages, summary, recommendations, treatment, and projections remain intact.
- Verify exact safe API request/response behavior, strict frontend validation,
  loading/cards/zero/error/Retry, root redirect, responsive navigation, active
  state, mobile closure, and existing deep-route/query compatibility.
- Confirm Alembic remains at the Feature 004 head with no new revision or
  schema/dashboard persistence change.
- Run with deterministic doubles/mock AI and no OpenAI, LangChain execution,
  live credential, network account, or external service.
- Review dependencies, routes, schema, configuration, source, generated output,
  and diff for secrets, architecture drift, and forbidden scope.

## Dependencies

- DN-004 and DN-007; transitively DN-001 through DN-006.
- Both the backend DN-002 → DN-003 → DN-004 chain and frontend
  DN-005 → DN-006 → DN-007 chain must be complete.

## Acceptance criteria

- Automated or explicit runtime evidence maps every Feature 005 criterion to
  the approved specification and plan.
- PostgreSQL-backed before/after booking proves exact counts, rounding,
  authoritative appointment/status behavior, and read-only dashboard access.
- Complete backend/frontend regressions, lint, typecheck, build, and Compose
  checks pass deterministically without real AI or external calls.
- Root/dashboard navigation and desktop/mobile shared-shell behavior coexist
  with unchanged records, detail, summary, booking, and query handoff routes.
- The final diff contains only approved Feature 005 code/tests/docs and no
  migration, persistence/cache, secret, architecture drift, or forbidden scope.

## Testing requirements

- Run focused dashboard repository, application, DTO/route/composition,
  persisted API, frontend service, screen, router, and layout tests.
- Run the full backend Pytest suite where practical and full frontend
  `npm test`, `npm run lint`, `npm run typecheck`, and `npm run build`.
- Run `docker compose config`, `docker compose build`, and an existing-stack
  smoke test reaching `/api/v1/dashboard` and the frontend `/dashboard` route.
- Exercise the deterministic Feature 004 booking-to-dashboard scenario against
  migrated PostgreSQL and run Features 001–004 regressions.
- Run scope/file/migration, secret/AI, architecture, Markdown/whitespace, and
  final diff checks; record exact commands/results and separate any pre-existing
  unrelated failure.

## Architecture and scope guards

- Verification must not broaden behavior. Minimal fixes must trace directly to
  an approved criterion; otherwise stop and report the defect for approval.
- Confirm absence of new migration/table/cache, chart/filter/history, analytics
  framework, background job, auth, notification, external integration, AI
  insight/call, RAG, Redis, vector database, LangGraph, WebSocket, streaming,
  Compose service, or infrastructure/routing redesign.
- Preserve PostgreSQL authority, backend-only conversion calculation, one
  dashboard endpoint, and all Features 001–004 behavior.

## Definition of Done

- All required checks pass and recorded evidence proves the full read-only
  metrics and responsive-navigation slices, booking-driven metric update,
  safe recovery, regressions, Compose runtime, no live AI/secrets, unchanged
  migration head, and exact approved scope.
