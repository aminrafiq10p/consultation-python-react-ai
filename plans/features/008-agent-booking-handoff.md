# Feature 008 — Agent Booking Handoff Implementation Plan

## 1. Objective

Implement the approved Feature 008 Agent Booking Handoff vertical slice on top of completed Features 001–007.

The intended continuity is:

```text
Feature 006 New Consultation
        ↓
Feature 002 persistent conversation
        ↓
booking intent in a user message
        ↓
provider-neutral booking-intent classification
        ↓
authoritative lifecycle/state evaluation
        ↓
typed application-owned handoff
        ↓
existing Feature 003 summary/recommendations
        ↓
existing Feature 004 booking
        ↓
persisted Appointment
        ↓
Feature 007 Appointments
        ↓
Feature 005 Dashboard booked count
```

Feature 008 is a handoff feature, not an autonomous appointment-booking feature.

The implementation must:

- keep Feature 004 as the only appointment creation path;
- keep PostgreSQL-backed consultation, summary, recommendation, and appointment state authoritative;
- recognize explicit booking intent without relying on free-form assistant prose;
- persist and reload typed handoff metadata without adding a schema migration;
- render a deterministic CTA in the existing consultation conversation;
- preserve completed/booked read-only conversation rules;
- require no live OpenAI call for automated tests; and
- defer broad screenshot matching and visual polish to Feature 009.

No new appointment endpoint, booking repository, booking service, AI tool runtime, or migration is planned.

---

## 2. Current-System Alignment

Feature 008 extends the following existing boundaries confirmed by the approved specification:

- `ConsultationApplicationService.submit_message(...)` remains the authoritative chat workflow.
- `AIService`, `ConsultationAgent`, `ConsultationSkill`, `AIProvider`, `OpenAIProvider`, and `MockAIProvider` remain provider-neutral and unchanged in authority.
- User messages are persisted before assistant generation, and assistant messages are persisted only after a valid AI result.
- Assistant `Message.structured_payload` already uses PostgreSQL JSONB and can carry reserved application-owned flat markers.
- `ConsultationStatus` remains exactly `PENDING`, `COMPLETED`, and `BOOKED`.
- Feature 003 owns summary generation, persisted recommendations, and the `PENDING → COMPLETED` transition.
- Feature 004 owns appointment creation and the `COMPLETED → BOOKED` transition.
- Feature 007 owns appointment listing at `/appointments`.
- The existing consultation chat UI is rendered by `ConsultationConversation` within the existing detail route and `AppLayout`.
- Existing message GET/POST routes remain the transport boundary.
- Existing `400`, `404`, `409`, `503`, and safe `500` behavior remains authoritative.

Feature 008 must extend these seams rather than create parallel architecture.

---

## 3. Architecture Decisions

### 3.1 Booking-intent classifier placement

Use a **small pure provider-neutral application helper** located close to the consultation application layer rather than inside the provider.

Preferred placement:

```text
backend/app/application/booking_intent.py
```

or an equivalent feature-local application module consistent with the repository.

Preferred public shape:

```python
class BookingIntent(str, Enum):
    NONE = "NONE"
    BOOKING_REQUEST = "BOOKING_REQUEST"

def classify_booking_intent(message: str) -> BookingIntent:
    ...
```

Rationale:

- business intent recognition is application behavior, not provider behavior;
- tests can be deterministic and network-free;
- the provider does not become the authority for application actions;
- `ConsultationApplicationService.submit_message(...)` can combine the classifier result with persisted state;
- this avoids introducing a generic intent-classification framework;
- the helper can remain pure and independently testable.

The implementation shall not rely on a single unsafe substring check.

The classifier should use normalized/token-aware rules for booking/scheduling verbs plus appointment-related nouns and must explicitly exclude cancellation, rescheduling, hypothetical discussion, and negated intent.

### 3.2 Handoff state evaluation

The application service remains authoritative for selecting the handoff action.

The classifier returns only intent:

```text
BOOKING_REQUEST
or
NONE
```

It does not return a route, appointment identifier, recommendation identifier, or booking state.

After a booking intent is recognized, the application workflow evaluates authoritative persisted state using existing repositories/helpers:

- consultation status;
- summary eligibility;
- persisted summary existence;
- persisted recommendation state where required;
- persisted appointment existence where required.

The application then chooses exactly one supported action:

- `CONTINUE_CONSULTATION`
- `GENERATE_SUMMARY`
- `VIEW_SUMMARY`
- `VIEW_APPOINTMENTS`

No provider-generated action-like field may override this decision.

### 3.3 Persistence-marker design

Persist handoff metadata using existing assistant-message JSONB.

Use reserved flat application-owned keys, for example:

```json
{
  "_application_handoff_action": "GENERATE_SUMMARY",
  "_application_handoff_consultation_id": "..."
}
```

Exact internal key names may differ if existing conventions suggest a better prefix, but they must:

- be reserved to the application;
- be flat scalar values compatible with current payload constraints;
- never be accepted from user messages;
- never be treated as provider-owned informational payload;
- be stripped from the ordinary `structured_payload` exposed to the frontend;
- be decoded/validated into a typed top-level `handoff` projection; and
- fail closed if malformed.

No migration is required.

### 3.4 API-facing typed handoff

Add a typed `BookingHandoff` projection to assistant messages.

Conceptual shape:

```json
{
  "type": "BOOKING_HANDOFF",
  "action": "GENERATE_SUMMARY",
  "consultation_id": "UUID",
  "target": "/consultations/{consultationId}"
}
```

For ordinary messages and user messages:

```json
"handoff": null
```

Only approved action/target pairs are valid:

| Action | Target |
| --- | --- |
| `CONTINUE_CONSULTATION` | `/consultations/{consultationId}` |
| `GENERATE_SUMMARY` | `/consultations/{consultationId}` |
| `VIEW_SUMMARY` | `/consultations/{consultationId}/summary` |
| `VIEW_APPOINTMENTS` | `/appointments` |

The backend constructs targets from validated authoritative IDs.

The handoff carries no recommendation ID, appointment ID, date/time, location, provider data, or booking confirmation.

---

## 4. Implementation Stages

### Stage 1 — Confirm Feature 008 integration boundaries

**Objective**

Freeze the actual implementation seams before editing shared backend and frontend files.

**Likely areas inspected**

- Feature 008 specification
- `ConsultationApplicationService.submit_message`
- AI service/agent/skill/provider files
- message model/repository/DTO/routes
- summary repository/application helpers
- appointment repository/application helpers
- consultation lifecycle/state helpers
- `ConsultationConversation`
- frontend consultation message types/API/runtime validation
- existing summary generation client call
- router/AppLayout
- backend/frontend tests
- current migration head
- Docker/Compose runtime
- dirty working tree

**Acceptance evidence**

- exact file-level change map;
- confirmed summary-eligibility helper/repository seams;
- confirmed appointment-existence lookup seam;
- confirmed message JSONB encode/decode seam;
- confirmed message DTO/runtime-validator behavior;
- confirmed no migration required;
- confirmed no architecture conflict.

**Scope guard**

Read-only. No product changes.

---

### Stage 2 — Add the booking-intent classifier

**Objective**

Add a deterministic pure classifier for explicit booking intent.

**Likely files**

- new application helper module, e.g. `backend/app/application/booking_intent.py`
- focused unit tests

**Implementation**

Normalize message text consistently.

Recognize representative positive patterns such as:

- book an appointment
- schedule an appointment
- make an appointment
- arrange an appointment
- I want an appointment
- can you help me book/schedule an appointment

Explicitly avoid classifying:

- cancel my appointment
- reschedule my appointment
- how does appointment booking work?
- what happens at an appointment?
- I do not want to book an appointment
- hypothetical discussion
- ambiguous unrelated use of “book” or “schedule”

The classifier returns only:

```text
BOOKING_REQUEST
NONE
```

No provider call.

**Tests**

- capitalization/punctuation variants;
- positive phrases;
- negative/negated phrases;
- cancellation;
- rescheduling;
- informational/hypothetical appointment discussion;
- ambiguous inputs;
- blank input;
- no external call.

---

### Stage 3 — Add typed handoff models and JSONB marker helpers

**Objective**

Define the server-owned handoff types and safe persistence projection.

**Likely files**

- application/domain value module
- message DTO module
- message persistence/projection helper
- focused tests

**Implementation**

Define typed values for:

```text
BOOKING_HANDOFF
CONTINUE_CONSULTATION
GENERATE_SUMMARY
VIEW_SUMMARY
VIEW_APPOINTMENTS
```

Add encode/decode helpers for reserved application markers.

Requirements:

- assistant messages only;
- consultation ID must match the message consultation;
- action must be approved;
- target must match action exactly;
- malformed markers are ignored for CTA purposes;
- ordinary provider structured payload remains unchanged after reserved-key removal;
- user messages cannot expose or persist a handoff.

**Tests**

- valid encode/decode;
- action/target mapping;
- invalid action;
- invalid UUID;
- mismatched consultation;
- user-message rejection;
- malformed marker omission;
- provider payload preservation;
- reserved marker stripping from exposed structured payload;
- legacy messages without markers remain compatible.

---

### Stage 4 — Add authoritative handoff evaluation to the application layer

**Objective**

Determine handoff actions from persisted application state.

**Likely files**

- `ConsultationApplicationService`
- existing summary/appointment repository interfaces where read helpers are reused
- focused application tests

**Implementation**

Add a small private/helper operation conceptually equivalent to:

```text
evaluate_booking_handoff(
    consultation,
    messages,
    summary_state,
    appointment_state
) -> BookingHandoff | None
```

Rules:

1. `PENDING` and not summary-eligible:
   - `CONTINUE_CONSULTATION`

2. `PENDING` and summary-eligible:
   - `GENERATE_SUMMARY`

3. `COMPLETED` with authoritative persisted summary:
   - `VIEW_SUMMARY`

4. `BOOKED` with authoritative persisted appointment:
   - `VIEW_APPOINTMENTS`

5. inconsistent/missing state:
   - no handoff

Re-use existing summary-eligibility semantics rather than duplicate them.

Use read-only state checks only.

No booking write.

No status transition.

**Tests**

- each lifecycle mapping;
- state lookup failure;
- inconsistent summary state;
- inconsistent booked/appointment state;
- provider-supplied action-like payload cannot override application result;
- no appointment write;
- no status mutation.

---

### Stage 5 — Integrate booking handoff into `submit_message`

**Objective**

Extend the existing chat workflow while preserving Feature 002 persistence and failure semantics.

**Implementation order**

For a `PENDING` consultation:

1. validate consultation and conversation state;
2. classify current user message;
3. persist the user message exactly as today;
4. load bounded persisted context;
5. call existing `AIService.generate_response`;
6. validate existing `AIResult`;
7. if classifier returned `BOOKING_REQUEST`, evaluate authoritative handoff state;
8. extend assistant wording guidance as needed;
9. merge application-owned marker into the persisted assistant payload;
10. persist the assistant message;
11. return the confirmed exchange including typed handoff projection.

The application must never call:

```text
book_appointment(...)
```

from chat.

If state lookup for handoff fails but ordinary assistant text can safely persist, omit the handoff rather than fabricate one.

Existing AI failure behavior remains:

- user message remains persisted;
- no assistant success message;
- no handoff marker;
- existing safe `503`.

**Tests**

- ordinary message unchanged;
- booking intent produces application-owned handoff;
- user persistence order remains unchanged;
- assistant persistence contains marker only after valid AI success;
- provider failure preserves Feature 002 behavior;
- malformed AI result does not create a handoff;
- no booking call;
- no status mutation.

---

### Stage 6 — Extend AI wording guidance

**Objective**

Prevent misleading “booking is unavailable” responses while keeping the model wording-only.

**Likely files**

- `ConsultationSkill` instructions or equivalent
- focused AI/skill tests

**Implementation**

When booking intent is recognized, wording guidance should tell the model:

- the application can guide the user through its internal consultation/recommendation workflow;
- do not say the application lacks booking capability;
- do not claim an appointment has been booked;
- do not invent date/time/location/recommendation/provider details;
- do not emit authoritative route/action values;
- keep wording consistent with the lifecycle next step.

The action remains application-owned.

**Tests**

Use deterministic MockAIProvider/fake AI results.

No live OpenAI.

---

### Stage 7 — Extend message API/DTO projection

**Objective**

Expose the typed handoff consistently through existing message GET and POST responses.

**Likely files**

- message/consultation DTOs
- consultation message routes
- API tests

**Implementation**

No new endpoint.

Extend message serialization with:

```text
handoff: BookingHandoff | None
```

Requirements:

- ordinary assistant message → `handoff: null`;
- user message → `handoff: null`;
- valid assistant handoff → exact typed shape;
- reserved internal marker keys never leak in `structured_payload`;
- invalid stored markers produce ordinary assistant text with no CTA;
- existing response/error semantics remain unchanged.

**Tests**

- GET history;
- POST exchange;
- null handoff;
- valid handoff;
- malformed marker omission;
- user handoff prevention;
- existing 400/404/409/503/500 compatibility.

---

### Stage 8 — Add frontend handoff types and runtime validation

**Objective**

Teach the frontend message boundary to validate the exact typed handoff.

**Likely files**

- consultation message types
- consultation API/runtime validators
- frontend service tests

**Implementation**

Add:

```text
BookingHandoff
BookingHandoffAction
```

Validate:

- exact type;
- approved action;
- valid UUID;
- consultation ID matches message/current consultation where applicable;
- exact action/target pair;
- no extra action data;
- only assistant messages may carry a handoff.

Malformed handoff metadata must not break ordinary message rendering.

Preferred behavior:

- validate the message itself;
- if handoff projection is malformed but message content is otherwise valid, omit CTA safely according to the approved backend/frontend compatibility rule.

Do not parse assistant prose.

**Tests**

- every valid action;
- invalid action;
- invalid UUID;
- mismatched ID;
- invalid target;
- handoff on user message;
- extra fields;
- legacy messages;
- ordinary messages unchanged.

---

### Stage 9 — Render functional CTA in `ConsultationConversation`

**Objective**

Render one accessible application action adjacent to an assistant message with a valid handoff.

**Likely files**

- `ConsultationConversation`
- component tests

**CTA labels**

- `Continue consultation`
- `Generate summary`
- `View recommendations`
- `View appointments`

**Behavior**

#### CONTINUE_CONSULTATION

Remain on the current detail route.

Optionally focus the existing composer if the current UI architecture exposes a clean ref.

No HTTP side effect.

#### GENERATE_SUMMARY

Call the existing summary-generation frontend service exactly once.

While pending:

- disable CTA;
- show progress;
- prevent duplicate clicks.

On success:

```text
/consultations/{consultationId}/summary
```

On `409`, `503`, malformed response, or network error:

- show safe recoverable feedback;
- do not claim completion;
- do not navigate as if successful.

No appointment POST.

#### VIEW_SUMMARY

Navigate to:

```text
/consultations/{consultationId}/summary
```

#### VIEW_APPOINTMENTS

Navigate to:

```text
/appointments
```

**Tests**

- normal message no CTA;
- each CTA label;
- keyboard accessibility;
- duplicate-click guard;
- Generate Summary one request;
- success navigation;
- failure remains recoverable;
- View Summary navigation;
- View Appointments navigation;
- no booking POST;
- no prose parsing.

---

### Stage 10 — Add reload/current-state projection behavior

**Objective**

Ensure persisted handoff metadata survives reload and completed/booked state remains coherent without reopening chat.

**Implementation**

On message-history retrieval:

- decode persisted marker;
- validate it;
- expose typed handoff;
- no AI call is made solely to reconstruct the CTA.

Preserve the existing rule:

```text
COMPLETED and BOOKED consultations remain read-only.
```

Do not allow new chat messages merely to get a new handoff.

For state evolution:

- a persisted `GENERATE_SUMMARY` handoff may remain historical after summary creation;
- a reload/current-state projection may normalize the actionable latest handoff when existing application state clearly supports `VIEW_SUMMARY` or `VIEW_APPOINTMENTS`;
- this must be a read-only projection;
- no appointment or summary state is mutated.

If implementing dynamic projection would materially complicate the existing message read path, the implementation may retain persisted historical handoffs and rely on downstream authoritative APIs, provided the approved UX remains coherent and the specification acceptance criteria are satisfied.

This exact choice must be documented in the implementation evidence.

**Tests**

- reload restores CTA from persisted marker;
- no AI call on reload;
- completed state remains read-only;
- booked state remains read-only;
- stale handoff cannot authorize booking;
- malformed marker renders ordinary text only.

---

### Stage 11 — Cross-feature integration verification

**Objective**

Prove the full lifecycle.

**Scenario**

1. create consultation through Feature 006;
2. send ordinary messages through Feature 002;
3. express booking intent;
4. receive typed handoff;
5. follow `GENERATE_SUMMARY`;
6. retrieve persisted summary/recommendations through Feature 003;
7. select recommendation and use Feature 004 booking;
8. verify one persisted appointment and `BOOKED` consultation;
9. retrieve the same appointment through Feature 007;
10. verify Dashboard booked count includes the same row.

**Assertions**

- booking-intent message itself creates no appointment;
- handoff CTA creates no appointment;
- only Feature 004 booking creates the appointment;
- exactly one appointment exists;
- repeated/already-booked path cannot create a duplicate;
- IDs remain authoritative throughout;
- no local browser state is authoritative.

Use deterministic AI doubles.

---

### Stage 12 — Features 001–007 regression verification

Run the existing regression suites for:

- Consultation Records and Detail;
- persistent AI chat;
- summary/recommendations;
- appointment booking;
- Dashboard/navigation;
- New Consultation;
- Appointments list/navigation.

Specifically verify:

- ordinary non-booking chat remains ordinary;
- summary generation/idempotence unchanged;
- booking validation/concurrency unchanged;
- appointment list unchanged;
- Dashboard remains PostgreSQL-backed;
- completed/booked read-only rule remains unchanged.

No weakening of existing assertions.

---

### Stage 13 — No-migration, no-tool-calling, security, and runtime verification

Verify:

- no Alembic migration;
- no appointment write tool exposed to the LLM;
- no new AI tool runtime;
- no new booking endpoint;
- no new appointment repository/service;
- no OpenAI requirement for tests;
- no frontend OpenAI secret;
- reserved handoff markers contain no provider output, prompts, hidden reasoning, arbitrary URLs, or secrets;
- route targets are internal and server-generated;
- Docker/Compose still builds and starts;
- no new service, port, or environment variable.

Feature 009 visual alignment must not appear in the diff.

---

### Stage 14 — Final Feature 008 vertical-slice verification

Run:

- focused classifier tests;
- focused backend application/message persistence tests;
- message DTO/API tests;
- frontend service/runtime-validation tests;
- conversation CTA tests;
- cross-feature PostgreSQL integration;
- full backend tests;
- full frontend tests;
- typecheck;
- lint;
- frontend build;
- migration-head checks;
- Docker Compose config/build/start/smoke checks;
- git diff/status/diff-check.

Manual smoke flow:

```text
+ New Consult
→ create consultation
→ chat normally
→ ask to book an appointment
→ see supported booking handoff CTA
→ generate/view summary
→ choose recommendation
→ existing booking form
→ create appointment
→ /appointments
→ Dashboard
```

Verify that the assistant no longer falsely claims the platform cannot support booking and also never falsely claims that booking already happened.

Stop after Feature 008.

---

## 5. Dependency Order

Recommended implementation dependency graph:

```text
ABH-001 Boundary confirmation
        ↓
        ├── ABH-002 Booking-intent classifier
        │       ↓
        ├── ABH-003 Typed handoff + persistence markers
        │       ↓
        └── ABH-004 Frontend handoff types/runtime validation
                │
ABH-002 + ABH-003
        ↓
ABH-005 Application handoff evaluation + submit_message integration
        ↓
ABH-006 AI wording guidance + message API/DTO projection
        │
        ├───────────────┐
        ↓               ↓
ABH-007 Chat CTA UI     ABH-008 Reload/current-state projection
        └───────┬───────┘
                ↓
ABH-009 Integration + regression verification
                ↓
ABH-010 Final vertical-slice verification
```

Exact task IDs are illustrative only; task generation occurs after plan approval.

---

## 6. Safe Parallelization

After boundary confirmation:

### Backend-safe parallel work

The following can proceed independently if their files do not overlap:

- booking-intent classifier;
- typed handoff value/marker helper;
- focused frontend handoff types/runtime validator.

### Backend critical path

```text
classifier
+ typed handoff/marker helper
        ↓
application state evaluation
        ↓
submit_message integration
        ↓
message API/DTO projection
```

### Frontend critical path

```text
handoff types/runtime validation
        ↓
chat CTA implementation
```

### Convergence

Backend and frontend branches converge for:

- reload behavior;
- integration continuity;
- regression;
- final verification.

Do not parallel-edit these shared files without one owner:

- `ConsultationApplicationService`;
- message DTO module;
- consultation message routes;
- frontend consultation API/runtime validator;
- `ConsultationConversation`;
- shared summary-generation frontend service.

Parallelization is by boundary, not merely by test file.

---

## 7. Testing Strategy

### 7.1 Classifier

Pure deterministic unit tests.

No AI provider.

### 7.2 Application and persistence

Use strict repository/AI doubles for unit tests and PostgreSQL for persistence/reload integration.

Verify no booking write.

### 7.3 API/DTO

Use Flask test client and injected service seams where appropriate.

Verify exact handoff serialization and internal-marker stripping.

### 7.4 Frontend service/runtime validation

Use deterministic transport fixtures.

No live backend.

### 7.5 Conversation UI

Use React Testing Library with injected services/deferred promises.

Assert semantic behavior rather than brittle snapshots.

### 7.6 Cross-feature integration

Use deterministic Feature 002 AI doubles and the real Feature 003/004/007 persistence/application paths.

### 7.7 Full regression

Run complete existing backend/frontend suites.

---

## 8. Migration Decision

**No migration.**

Existing assistant-message JSONB is sufficient for reserved flat handoff markers.

Feature 008 introduces no:

- table;
- column;
- relationship;
- appointment field;
- consultation field;
- summary field;
- recommendation field;
- new status;
- index.

If implementation inspection proves the current JSONB validation cannot safely support application-owned markers, stop and document the conflict before proposing any schema change.

---

## 9. AI / Provider Decision

The provider remains wording-only.

The provider may:

- generate conversational assistant text;
- return existing informational structured payload.

The provider may not:

- choose handoff action;
- choose route;
- choose consultation state;
- choose recommendation;
- choose appointment;
- choose date/time/location;
- create or confirm booking.

No unrestricted tool calling is introduced.

`MockAIProvider` remains deterministic.

Automated tests require no OpenAI credential or network.

---

## 10. Frontend Visual Boundary

Feature 008 adds only functional CTA presentation within the existing chat.

Use the current MUI/application language:

- current button styling;
- current spacing;
- current loading/error patterns;
- current typography;
- current focus/accessibility behavior.

Do not:

- redesign sidebar;
- redesign consultation chat layout;
- restyle Dashboard;
- restyle Records;
- restyle Summary;
- restyle Booking;
- restyle Appointments;
- perform screenshot matching.

Feature 009 owns deliberate screen-by-screen visual alignment.

---

## 11. Risks and Controls

### False-positive intent recognition

Control with narrow explicit patterns and negation/cancel/reschedule exclusions.

### Provider attempts to supply action-like structured data

Ignore as untrusted for business behavior.

### Handoff marker leakage

Strip reserved keys from exposed provider structured payload.

### Stale CTA

Downstream existing APIs/screens revalidate authoritative state.

### Duplicate booking

Feature 008 never creates an appointment; Feature 004 uniqueness/eligibility remains authoritative.

### Read-only completed/booked consultation

Do not reopen chat. Use persisted/reconstructed read projection only.

### Ambiguous reload projection

Prefer safe omission of CTA over fabricated action.

### AI provider failure

Preserve Feature 002 user-message recovery behavior.

### Broad visual scope creep

Reject as Feature 009 work.

---

## 12. Final Acceptance Matrix

Feature 008 is implementation-complete only when all are true:

- ordinary chat remains unchanged;
- explicit booking intent is recognized deterministically;
- booking intent no longer causes misleading “booking unsupported” wording;
- action is application-owned, typed, and runtime-validatable;
- `PENDING` not eligible → `CONTINUE_CONSULTATION`;
- `PENDING` eligible → `GENERATE_SUMMARY`;
- `COMPLETED` + summary → `VIEW_SUMMARY` projection;
- `BOOKED` + appointment → `VIEW_APPOINTMENTS` projection;
- handoff metadata persists/reloads without a migration;
- frontend never parses prose for actions;
- chat renders one accessible CTA;
- Generate Summary reuses the existing summary call exactly once;
- View Summary and View Appointments navigate to existing routes;
- no CTA issues a booking POST;
- no booking write occurs from chat;
- Feature 004 remains the only appointment creation path;
- exactly one appointment is persisted in the integration flow;
- Feature 007 reads the same appointment;
- Dashboard reads the same appointment count;
- no live OpenAI requirement for tests;
- no tool-calling runtime;
- no Feature 009 visual redesign;
- Features 001–007 regressions remain green;
- full backend/frontend/build/Docker checks pass.

---

## 13. Definition of Done

Feature 008 is done when a user can express booking intent during a normal `PENDING` consultation and receive a persisted, typed, application-owned handoff that guides them through the existing summary/recommendation/booking lifecycle; the assistant no longer falsely claims that the platform lacks booking capability; actual appointment creation still occurs only through Feature 004; persisted handoffs reload without new AI calls or schema changes; the chat UI renders safe accessible CTAs from typed metadata; no duplicate appointment or booking confirmation can be produced by the handoff itself; and all Features 001–007 regression, PostgreSQL, no-AI, no-migration, type, lint, build, Docker, and vertical-slice checks pass.

Feature 009 visual alignment remains out of scope.
