# ABH-001 — Confirm Feature 008 Integration Boundaries

**Task ID:** ABH-001

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Confirm the exact existing backend/frontend seams required for Agent Booking Handoff before product changes begin.

## Scope

Read-only inspection of the current chat, AI, message persistence, summary, booking, appointment-list, frontend conversation, routing, tests, migration, and Docker boundaries.

Confirm at minimum:

- `ConsultationApplicationService.submit_message`
- `AIService`, `ConsultationAgent`, `ConsultationSkill`, provider protocol, `MockAIProvider`, `OpenAIProvider`
- `AIResult` and current `structured_payload` rules
- assistant/user `Message` JSONB persistence and ordering
- summary eligibility and summary/recommendation read seams
- appointment existence/read seams
- current message GET/POST DTO/API behavior
- current consultation conversation frontend types/runtime validation
- `ConsultationConversation` CTA/action integration points
- current migration head and Docker/test commands
- dirty working-tree/shared-file risks

## Expected files/areas affected

- Feature 008 spec/plan
- backend application, AI, repositories, models, DTOs, routes, tests
- frontend consultation conversation/types/API/router tests
- migration and Compose configuration

No product code should change.

## Implementation requirements

- Record actual file/module names and callable signatures.
- Confirm whether existing JSONB validation permits reserved flat application markers without migration.
- Confirm exact summary-eligibility reuse point.
- Confirm exact appointment-existence lookup seam.
- Confirm completed/booked read-only conversation behavior.
- Identify shared files that should not be concurrently edited.
- Produce an `ABH-001-findings.md` file in this task directory if that matches established prior-feature convention.

## Dependencies

None beyond approved Feature 008 specification/plan and completed Features 001–007.

## Acceptance criteria

- No unresolved architecture conflict remains.
- No migration is required based on current schema/payload rules, or a concrete blocker is documented.
- Backend and frontend implementation seams are explicit.
- Safe parallel work for ABH-002/ABH-004 is identified.
- No product code is changed.

## Testing requirements

Run documentation/repository checks required by the task, including:

- `git status --short`
- `git diff --stat`
- `git diff --check`

Record exact backend/frontend test/build commands for later tasks.

## Definition of Done

ABH-001 is complete when the actual implementation boundaries are documented, no product code changed, and later backend/frontend work can begin without architectural guesswork.
