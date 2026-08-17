# CS-010 Verification Evidence

Verified 2026-08-17 against the approved Feature 003 specification, plan,
CS-001 through CS-010 task definitions, CS-001 findings, implementation, prior
feature regressions, and Docker Compose runtime.

## Results

- Backend: `206 passed` against a disposable PostgreSQL 16 container. This
  includes migration downgrade/upgrade, schema constraints, repository
  rollback and controlled concurrency, application, AI, DTO, API, and full
  persistence integration coverage. The 17 warnings are the existing Alembic
  `path_separator` deprecation warning, not test failures.
- Frontend: `128 passed`; TypeScript typecheck, ESLint, and production Vite
  build passed.
- Docker: `docker compose config` and both image builds passed. The complete
  stack started with `AI_PROVIDER=mock` on alternate host ports because port
  3000 was already occupied; PostgreSQL was healthy and both HTTP services
  were reachable.
- Runtime API: a persisted USER/ASSISTANT exchange generated a summary with
  `201`; GET and repeated POST returned `200` with the same summary and
  recommendation UUIDs; a new message returned coded closed-conversation
  `409`; restart returned a distinct empty-projection `PENDING` consultation
  with `201`.
- Corrective product changes: none. No acceptance-blocking defect was found.

## Specification acceptance matrix

| Feature 003 acceptance criterion | Implementation location | Proving evidence | Result |
| --- | --- | --- | ---: |
| Eligible persistent conversation can request a summary from Detail | `ConsultationDetailScreen.tsx`; `ConsultationApplicationService.generate_summary` | Detail RTL eligibility/loading/navigation tests; application eligibility tests; runtime flow | PASS |
| Complete persisted ordered history reaches the existing AI abstraction | application service; `AIService` → `ConsultationAgent` → `ConsultationSkill` → provider | application >20-message/>24,000-character forwarding test; AI coordination tests | PASS |
| Validated aggregate persists before completion or success | `SummaryRepository.complete_consultation`; application service | repository atomic success/rollback tests; persistence API integration | PASS |
| Nonblank patient summary, one or more ordered treatments, nullable concise rationale | provider-neutral `SummaryResult`; mappings/migration; DTO/service guards | AI invalid-shape tests; PostgreSQL constraint tests; frontend runtime-validation tests | PASS |
| Recommendation identifiers are stable across reload and repeated generation | summary/recommendation mappings and repository | fresh-session repository/persistence tests; repeated API tests; runtime identical UUID evidence | PASS |
| Refresh, reopen, and direct summary retrieval use persistence without AI | `get_summary` application/API flow; `ConsultationSummaryScreen` | application no-AI retrieval tests; API and Summary-screen direct-load tests; runtime GET | PASS |
| Repeated generation is idempotent and creates no duplicates | pre-AI summary lookup; DB unique constraint; race recovery | application idempotency tests; repository sequential/concurrent tests; runtime repeat POST | PASS |
| Missing, ineligible, BOOKED, and inconsistent COMPLETED records do not generate or write | application eligibility ordering and typed outcomes | application status/history matrix; route error matrix | PASS |
| Validation, AI, and persistence failures remain safe and non-partial | AI/service exception translation; repository rollback; safe Flask errors | AI malformed/provider tests; aggregate rollback tests; application/API leak tests | PASS |
| Restart creates a distinct clean PENDING consultation and preserves source/history | application restart workflow; consultation repository | application and PostgreSQL API integration tests; runtime restart | PASS |
| Booking requires a persisted recommendation and performs navigation only | `ConsultationSummaryScreen.tsx`; `AppointmentUnavailableScreen.tsx`; router | Summary-screen selection/path test and router placeholder test; no appointment transport/schema found | PASS |
| Automated verification is deterministic without live OpenAI or credentials | mock provider and injected doubles | full backend/frontend suites; Compose runtime with `AI_PROVIDER=mock` | PASS |

## Layer verification

| Area | Evidence | Result |
| --- | --- | ---: |
| Alembic chain and PostgreSQL schema | `test_migration_upgrade_downgrade_preserves_feature_001_and_002` starts from base, upgrades through `20260813_02` to head, checks both tables/types/FKs/named constraints, downgrades, confirms consultations/messages survive, then upgrades again | PASS |
| Database invariants | focused persistence tests exercise UUID/FK failures, unique consultation summary, patient/treatment nonblank checks, nullable-or-nonblank rationale, positive position, unique per-summary position, timestamp, and no-cascade behavior | PASS |
| Summary repository | absent lookup, atomic completion, ordered fresh-session retrieval, stable UUIDs, full rollback, named-constraint race classification, controlled concurrent winner/reload, unrelated integrity failure, and restart rollback tests | PASS |
| AI architecture and safety | one existing service/agent/skill/provider chain; full history contract distinct from bounded interactive context; normalized structured result; deterministic mock; sanitized provider errors; no chain-of-thought field or prompt | PASS |
| Application workflow | existence/idempotency checks precede eligibility/AI; exact role/latest-message rules; AI precedes repository transaction; completion/projection are atomic; race loser reloads; failures preserve state; COMPLETED/BOOKED close before USER write/AI | PASS |
| API contract | route/DTO tests cover exact GET/POST paths, no-body validation, 200/201/400/404, all approved coded 409/503 outcomes, safe 500, DTO field allowlists, and leak resistance; routes delegate only to the application service | PASS |
| Frontend service | one `consultationApi` transport boundary; exact paths/no-body POSTs; UUID/linkage/text/timestamp/rationale/recommendation order/position validation; coded and malformed-error handling | PASS |
| Detail and Summary UI | RTL covers eligibility, generation loading/single activation/navigation/errors, completed read-only history, booked closure, direct summary load, ordering/null rationale/plain-text rendering, selection, restart, and booking navigation | PASS |
| Regression | complete backend and frontend suites include Feature 001 list/detail/filter behavior and Feature 002 pending conversation/history/failure recovery | PASS |
| Runtime | Compose migration reached head; PostgreSQL healthy; backend list endpoint and frontend returned success; deterministic create/retrieve/repeat/close/restart flow passed | PASS |

## Commands and observed results

```text
docker run --rm --network host ... consultation-python-react-ai-backend pytest -q
206 passed, 17 warnings in 4.55s

npm test -- --run
5 files passed; 128 tests passed

npm run typecheck
npm run lint
npm run build
all passed; Vite production build completed

docker compose config
passed

docker compose build
backend and frontend images built

FRONTEND_PORT=3300 BACKEND_PORT=5500 POSTGRES_PORT=55432 docker compose up -d
PostgreSQL healthy; backend and frontend running
```

The alternate ports were runtime-only environment overrides. The first start
attempt could not bind host port 3000 because another local process already
owned it; this was environmental and required no repository change.

## Architecture, security, and scope review

- Flask summary/restart/message routes validate and serialize, then delegate
  to `ConsultationApplicationService`; they do not import or access sessions,
  repositories, LangChain, or providers directly.
- React uses only `consultationApi`; no frontend OpenAI SDK, provider request,
  credential, or duplicate HTTP client exists.
- OpenAI/LangChain code remains isolated in the existing provider layer. Mock
  AI is the Compose default, and automated verification made no live request.
- Source/config review found placeholder-only `OPENAI_API_KEY` settings and no
  committed key pattern. Error tests explicitly prevent SQL, constraints,
  stack traces, provider details, prompts, credentials, and exception names
  from reaching responses/UI.
- No appointment persistence/form/API, `BOOKED` transition, dashboard,
  regeneration/versioning, history deletion, authentication, RAG, embeddings,
  vectors, Redis, LangGraph, WebSockets, streaming, extra agent, or unrelated
  architecture was introduced. The appointment route is a deliberately
  non-functional navigation placeholder.

## Remaining blockers

None.
