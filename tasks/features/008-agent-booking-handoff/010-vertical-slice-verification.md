# ABH-010 — Verify Feature 008 Final Vertical Slice

**Task ID:** ABH-010

## Traceability

Authoritative sources:

- `specs/features/008-agent-booking-handoff.md`
- `plans/features/008-agent-booking-handoff.md`

Preserve approved Features 001–007 behavior and architecture. Feature 009 visual alignment is out of scope.

## Purpose

Perform final Feature 008 acceptance, runtime, security, migration, Docker, and scope verification.

## Scope

Verification only, with minimal corrections limited to genuine Feature 008 acceptance failures.

## Expected files/areas affected

- tests/evidence
- minimal production fixes only if required
- Feature 008 tracker status

## Implementation requirements

Verify:

- classifier behavior
- application-owned handoff selection
- message marker persistence/reload
- message API/DTO projection
- AI wording guardrails
- frontend runtime validation
- chat CTA behavior
- no direct booking from chat
- Feature 004 remains sole appointment write path
- Feature 007 appointment visibility
- Dashboard consistency
- no migration
- no unrestricted tool calling
- no real OpenAI requirement for automated tests
- no secret leakage
- Docker/Compose compatibility
- Feature 009 visual scope exclusion

Manual smoke flow:

```text
+ New Consult
→ create consultation
→ chat normally
→ ask to book an appointment
→ see supported handoff CTA
→ generate/view summary
→ choose recommendation
→ existing booking form
→ create appointment
→ /appointments
→ Dashboard
```

## Dependencies

- ABH-001 through ABH-009

## Acceptance criteria

- All Feature 008 specification criteria pass.
- Features 001–007 regressions remain green.
- No migration, new booking API, AI tool runtime, or Feature 009 visual redesign appears in the diff.
- Feature 008 tracker is complete only after all checks pass.

## Testing requirements

Run applicable repository commands including:

- focused backend tests
- full backend tests
- focused frontend tests
- full frontend tests
- typecheck
- lint
- frontend build
- Alembic/current-head verification
- PostgreSQL integration
- Docker Compose config/build/start/smoke
- `git status --short`
- `git diff --stat`
- `git diff --check`

Do not use `docker compose down -v`.

## Definition of Done

ABH-010 is complete when Feature 008 is fully verified end to end, all required checks pass, the tracker is complete, and no Feature 009 work or unauthorized architecture expansion has occurred.
