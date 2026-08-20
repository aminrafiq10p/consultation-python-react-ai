# AP-014: Verify No-AI, No-Migration, Docker, and Scope Isolation

**Task ID:** AP-014  
**Title:** Verify No-AI, No-Migration, Docker, and Scope Isolation

**Status:** Complete (2026-08-19)

## Objective

Prove Feature 007 is deterministic, schema-preserving, container-compatible,
and isolated from Feature 008.

## Dependencies

AP-013 and all implementation/test tasks.

## Scope

Release-quality dependency, migration, Compose, test, and diff review only.

## Implementation requirements

- Confirm no migration/model/table change and current Feature 004 migration
  head remains valid.
- Run strict no-AI/no-network tests and inspect the list dependency path for no
  AIService, LangChain, provider, or external request.
- Run backend/frontend tests, typecheck, lint, build, `docker compose config`,
  and approved Compose build/runtime checks without new services/dependencies.
- Review diff for only Feature 007 work and explicitly reject screenshot
  matching, shell redesign, or Feature 008 visual alignment.

## Likely files/areas

Git diff, migrations/head, AI imports/doubles, Docker/Compose, package and
requirements files, changed tests.

## Tests/checks

No-migration diff/head, no-AI/no-network, pytest/Vitest, type/lint/build,
Compose config/build/runtime, and scope review.

## Acceptance criteria

All checks pass or an environment/pre-existing limitation is clearly recorded;
no migration, AI/external network, or Feature 008 leakage exists.

## Explicit non-goals/scope guards

Do not add indexing migrations, AI fallback, external calendar integration,
Compose topology, visual polish, or unrelated cleanup.

## Completion evidence

All AP-014 checks passed:

- `backend/.venv/bin/pytest -q tests`: 413 passed, 32 pre-existing Alembic
  deprecation warnings.
- Frontend `npm test`: 305 passed; `npm run typecheck`, `npm run lint`, and
  `npm run build` passed.
- `backend/.venv/bin/alembic heads`: `20260817_04 (head)`.
- `docker compose config --quiet` and `docker compose build` passed.
- Compose runtime smoke check passed: PostgreSQL healthy, backend served the
  persisted `GET /api/v1/appointments` response, frontend served its page, and
  `docker compose down` stopped services without removing volumes.
- The appointment list path contains no AI provider, LangChain, OpenAI, or
  external-network call. No migration/model/table/dependency/Compose topology
  change exists. Secrets remain environment-backed and ignored; no secret was
  added to Feature 007 files.
- Diff review found only Feature 007 implementation/tests and its supplied
  specification/plan/task artifacts. No Feature 008 work, screenshot matching,
  shell redesign, or unrelated refactor was introduced.

AP-015 is unblocked.
