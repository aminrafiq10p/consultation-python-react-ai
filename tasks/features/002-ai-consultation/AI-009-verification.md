# AI-009 Verification Evidence

Verified 2026-08-13 against the Feature 002 specification, plan, tasks, and
completed implementation.

## Results

- Backend: `106 passed`; PostgreSQL 16 migration, persistence, repository,
  deterministic vertical-slice, application, AI, DTO, and API coverage passed.
- Frontend: `61 passed`; typecheck, ESLint, and production build passed.
- Backend import validation: passed.
- Feature 001 regression: passed as part of the complete backend and frontend
  suites.
- Docker Compose: NOT RUN because no Compose file or Dockerfile exists in the
  repository. Isolated PostgreSQL container tests passed.
- Real OpenAI smoke: PASS. After the provider was corrected to use
  `method="function_calling"`, one authorized follow-up request returned a
  nonblank provider response. The USER and ASSISTANT messages persisted and a
  fresh GET returned both in order.

## Acceptance matrix

| Criterion | Implementation / evidence | Result | Manual |
|---|---|---:|---:|
| Message schema, constraints, FK, payload rules, timestamp, index, migration round trip | message model/migration; persistence tests | PASS | — |
| Repository persistence, isolation, empty history, stable order, rollback | `MessageRepository`; repository tests | PASS | — |
| Provider-neutral AI coordination, context, text/structured results, malformed/failure safety | AI layer; deterministic AI tests | PASS | — |
| USER-before-AI workflow, bounded 20-message/24,000-character context, persistence failure semantics | application service; conversation workflow tests | PASS | — |
| GET/POST validation, populated/empty history, 400/404/503/500 safety | DTO/routes; API tests | PASS | — |
| Repeated PostgreSQL-backed exchange, fresh ordered retrieval, retained USER on AI failure | full API persistence integration tests | PASS | — |
| Conversation UI states, validation, pending/duplicate handling, reconciliation and recovery | frontend detail/API tests | PASS | — |
| Feature 001 backend and frontend behavior | complete backend/frontend suites | PASS | — |
| Backend imports; frontend typecheck, lint and production build | configured repository commands | PASS | — |
| PostgreSQL authoritative; route/application/repository/AI/frontend boundaries preserved | source/import review and integration tests | PASS | — |
| No summary, appointment, dashboard, RAG, embeddings, vectors, Redis, LangGraph, WebSockets, streaming, or multi-agent scope | source/scope review | PASS | — |
| No tracked key; local env ignored; examples placeholders; no frontend OpenAI credential | tracked-file and ignore checks | PASS | — |
| Existing Compose compatibility | no Compose/Dockerfile foundation exists | NOT RUN | — |
| One real OpenAI exchange and fresh persisted retrieval | controlled disposable PostgreSQL runtime smoke | PASS | One authorized post-fix request returned a nonblank response and fresh ordered history |

## Architecture and security review

Routes depend only on the application service and DTOs. The application layer
does not import Flask. Repositories own SQLAlchemy access and do not invoke AI.
The AI layer does not persist messages. React uses the backend service only and
contains no OpenAI dependency or credential. PostgreSQL is the only authoritative
conversation state; neither browser state nor LangChain memory is authoritative.
No production conversation dataset or out-of-scope Feature 003 behavior exists.

Tracked files contain no detected OpenAI key pattern. `backend/.env` and
`frontend/.env` are ignored, examples contain placeholders only, tests use fake
values, and application reporting exposes only a credential-presence boolean.
No credential value was printed or recorded.

## Corrective fixes

1. Feature 001 repository test cleanup now deletes messages before consultations,
   respecting the Feature 002 foreign key.
2. The missing-key configuration test uses an isolated nonexistent dotenv path.
3. The OpenAI provider explicitly uses LangChain's supported structured-output
   `function_calling` method, with a regression assertion.

## Remaining blockers

None. The real-provider correction was verified with one authorized post-fix
runtime request. The disposable PostgreSQL container was removed afterward.
