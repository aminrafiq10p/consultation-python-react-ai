# ABH-001 Findings — Integration Boundaries

**Status:** Complete (boundary confirmation only; no product code changed)

## Scope and repository state

The authoritative inputs were `specs/features/008-agent-booking-handoff.md`,
`plans/features/008-agent-booking-handoff.md`, and task ABH-001. The existing
working tree was already dirty:

```text
?? plans/features/008-agent-booking-handoff.md
?? specs/features/008-agent-booking-handoff.md
?? tasks/features/008-agent-booking-handoff/
```

`git diff --stat` produced no tracked diff; `git diff --check` passed. The
findings file itself is part of the pre-existing untracked Feature 008 task
directory and is the only file created for this task.

## Backend seams

### Chat application path

`backend/app/application/consultation_service.py` contains
`ConsultationApplicationService.submit_message(consultation_id: UUID,
content: str) -> PersistedExchange`. It normalizes input, loads the
consultation, rejects every status except `PENDING`, persists the user message
with `structured_payload=None`, reloads ordered history, calls
`AIService.generate_response`, reconstructs/validates `AIResult`, persists the
assistant message, and returns `PersistedExchange`.

The exact classifier/integration seam is immediately after
`normalized_content` and consultation validation, before or alongside the
user-message persistence, with authoritative handoff state evaluation after
that user message has been persisted and before the assistant message is
persisted. The classifier must be a pure provider-neutral application helper,
preferably `backend/app/application/booking_intent.py`; it must return only
`BookingIntent.NONE` or `BookingIntent.BOOKING_REQUEST`. It must not be placed
in `AIProvider`, `ConsultationAgent`, or prompt text.

### AI boundary

The chain is:

* `backend/app/ai/service.py`: `AIService.generate_response` and
  `generate_summary`; `create_ai_service` composes the provider.
* `backend/app/ai/consultation_agent.py`: `ConsultationAgent.respond` builds
  `ProviderRequest` and delegates to `AIProvider.generate`.
* `backend/app/ai/consultation_skill.py`: `ConsultationSkill.instructions_for`
  supplies response wording and `summary_instructions_for` supplies summary
  wording.
* `backend/app/ai/providers/base.py`: `AIProvider` protocol,
  `AIResult`, `ProviderRequest`, and payload validation.
* `backend/app/ai/providers/mock.py`: deterministic network-free
  `MockAIProvider`.
* `backend/app/ai/providers/openai.py`: structured OpenAI provider adapter.

The classifier must work without a provider call. Skill wording may be
extended later, but provider output remains informational and cannot select a
handoff action.

### AIResult, JSONB, and marker compatibility

`AIResult` requires nonblank content and validates `structured_payload` using
`validate_structured_payload`: a dict whose values are JSON scalars or arrays
of JSON scalars. `Message.structured_payload` in
`backend/app/infrastructure/consultation_models.py` is nullable PostgreSQL
`JSONB(none_as_null=True)`. A database check constraint
`ck_messages_user_structured_payload_null` rejects payloads on user messages.
`MessageRepository.persist_message` commits one row, and
`list_messages` orders by `(created_at ASC, id ASC)`.

Reserved flat application-owned markers are therefore JSONB-compatible, but
the current `AIResult` contract does not distinguish ownership and the current
API/frontend expose/render every payload key. Later handoff work must use an
explicit encode/decode boundary: keep provider payload in the provider-facing
portion, add reserved flat application markers only on the persisted assistant
payload, validate/strip those markers into a typed top-level `handoff` DTO
projection, and never accept markers from a user message. Malformed markers
must fail closed. This preserves provider payload separation; it is not safe
to rely on the current raw `structured_payload` projection alone.

### Summary, recommendation, and appointment reads

There is no named reusable summary-eligibility helper. The exact existing
backend seam is the inline predicate in
`ConsultationApplicationService.generate_summary`:
`SummaryRepository.get_summary` is checked first; for a summary-less `PENDING`
consultation, `MessageRepository.list_messages` must contain USER and
ASSISTANT roles and the last message must be ASSISTANT. This is the predicate
ABH-005/related workflow work should extract or reuse without changing its
meaning. `get_summary` calls `SummaryRepository.get_summary`, which returns a
`SummaryAggregate` with ordered recommendations. `GET /consultations/<id>/summary`
reads it without AI; `POST` generates/persists it and transitions PENDING to
COMPLETED.

The exact appointment existence seam is
`AppointmentRepository.get_appointment(consultation_id: UUID) -> Appointment |
None`, used inside `ConsultationApplicationService.book_appointment` after
`lock_consultation`. `AppointmentRepository.list_appointments()` is the
authoritative Feature 007 read projection used by
`ConsultationApplicationService.list_appointments` and `GET /api/v1/appointments`.
There is no consultation-specific appointment GET route.

### Lifecycle and read-only behavior

`ConsultationStatus` has exactly `PENDING`, `BOOKED`, and `COMPLETED`.
`submit_message` rejects non-PENDING with `ConsultationConversationClosedError`;
the API maps this to the existing conversation-closed response. The frontend
`ConsultationConversation` computes `readOnly` when status is not PENDING (or
the server reports closure), hides the form, and displays prior messages.
Therefore COMPLETED and BOOKED conversations are read-only. Feature 008 must
not submit a new booking-intent message in those states; persisted handoff
reload/state projection must be read-only and downstream actions must recheck
authoritative state.

### HTTP DTO/API

`backend/app/api/consultation_dtos.py` defines `MessageResponse`,
`MessageListResponse`, `MessageSubmissionRequest`, and
`MessageExchangeResponse`. `backend/app/api/consultation_routes.py` provides
GET message history and POST message exchange under
`/api/v1/consultations/<consultation_id>/messages`, plus existing summary and
appointment routes. Request DTOs forbid extra fields; response DTOs currently
have no handoff field. This is the exact later contract extension seam.

## Frontend seams

`frontend/src/app/features/consultation-records/consultationTypes.ts` contains
`ConsultationMessage`, `ConsultationMessageHistory`, and
`ConsultationMessageExchange`; `consultationApi.ts` contains
`messageFromResponse`, `structuredPayloadFromResponse`, and the GET/POST
message methods. Runtime validation currently verifies UUIDs, roles, content,
timestamps, scalar payload shape, and null payload for USER messages. A typed
handoff validator belongs beside these functions and must validate action,
consultation ID, and the approved action/target mapping.

`ConsultationConversation.tsx` is the exact CTA seam: it owns loaded message
state, reconciliation after POST, and per-message rendering. The current
`StructuredPayload` renderer displays all supported provider payload entries;
handoff rendering must be a separate typed projection and must not search
assistant prose. `ConsultationDetailScreen.tsx` owns the existing
`generateSummary` service callback and navigation to
`/consultations/:consultationId/summary`; it already renders `Generate Summary`
for the same eligibility predicate and `View Summary` for COMPLETED.

`frontend/src/app/features/consultation-records/consultationApi.ts` is also the
summary-generation service seam (`generateSummary`) and existing API error
mapping seam. `frontend/src/app/core/App.tsx` registers consultation summary
and `/appointments` routes. `AppLayout.tsx` owns shared navigation. Approved
CTA targets are therefore existing summary/detail routes and `/appointments`;
no new booking endpoint or appointment creation path is needed.

## Tests and runtime

Relevant existing backend tests are under `backend/tests/ai/`,
`backend/tests/application/test_consultation_service.py`,
`backend/tests/application/test_consultation_summary_service.py`,
`backend/tests/application/test_appointment_booking_service.py`,
`backend/tests/api/test_consultation_routes.py`,
`backend/tests/api/test_consultation_dtos.py`, `backend/tests/test_message_*`,
and repository/persistence tests. Relevant frontend tests include
`ConsultationConversation` coverage in the consultation-records tests,
`ConsultationDetailScreen.test.tsx`, `consultationApi.test.ts`, summary screen
tests, `App.test.tsx`, and `AppLayout.test.tsx`.

Supported frontend commands are `npm run test`, `npm run typecheck`,
`npm run lint`, and `npm run build` from `frontend/`. Backend tests use
`pytest` from `backend/` (requirements are in `backend/requirements.txt`).
`compose.yaml` plus `backend/Dockerfile` and `frontend/Dockerfile` are the
container runtime seam; Docker Compose must remain supported.

## Migration decision and head

No migration is required: handoff markers fit the existing nullable JSONB
column and existing user-payload check constraint, provided the application
owns encode/decode and API projection as described above. No schema change is
needed.

Alembic was unavailable on PATH (`alembic: command not found`), so the revision
chain was inspected directly. It is linear:

```text
20260813_01 → 20260813_02 → 20260817_03 → 20260817_04
```

The current migration head is `20260817_04` (`create_appointments`).

## Shared-file and parallel-work risks

Do not concurrently edit `consultation_service.py`,
`consultation_dtos.py`, `consultation_routes.py`,
`infrastructure/consultation_models.py`, `consultationTypes.ts`,
`consultationApi.ts`, `ConsultationConversation.tsx`, or
`ConsultationDetailScreen.tsx` across parallel tasks without explicit
coordination. Backend workflow/AI/message-contract tasks overlap through the
application service and DTO/API files; frontend type/validation and CTA tasks
overlap through the same types/API/conversation files. Isolated classifier
work and focused tests are the safest parallel start.

## Conflicts, deviations, and safe starts

The Feature 008 architecture is compatible with the repository: lifecycle,
deterministic booking authority, provider abstraction, persistence, and routes
all exist as described. Two implementation assumptions are not literal
existing seams and are recorded for later work: summary eligibility is not a
named helper (it is duplicated in frontend detail logic), and typed handoff
metadata/runtime validation does not yet exist. These are implementation gaps,
not reasons to change architecture.

ABH-002 (pure classifier) and isolated classifier tests are safe to start in
parallel. ABH-004 frontend handoff types/validator is also safe if it avoids
simultaneous edits to shared API/conversation files or is sequenced after the
backend contract decision. ABH-003 persistence/model work, ABH-005 workflow,
ABH-006 AI wording/API, ABH-007 CTA, ABH-008 reload projection, and integration
tasks should coordinate around the shared files listed above.

