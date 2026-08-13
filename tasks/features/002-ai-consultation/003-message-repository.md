# AI-003: Add Consultation Message Repository

**Task ID:** AI-003  
**Title:** Add Consultation Message Repository

## Purpose

Provide focused persistence operations for individually committed messages and ordered consultation history.

## Traceability

- Feature specification: §§5–6, 12.
- Implementation plan: §§3, 5–6, 11, 12.2, 13–14.

## Scope

- Add `MessageRepository` beside the consultation repository with one-message persistence and consultation-scoped retrieval.
- Verify commit, rollback, isolation, reload, and ordering without AI.

## Expected files/areas affected

- `backend/app/repositories/message_repository.py`, exports, and backend repository tests/fixtures.

## Implementation requirements

- Use the same request-scoped SQLAlchemy session as `ConsultationRepository`.
- `persist_message(...)` adds, commits, refreshes, and returns the confirmed row; on failure it rolls back before re-raising.
- `list_messages(...)` filters by consultation and orders ascending `(created_at, id)`.
- A bounded query helper may preserve that order but must not decide semantic context.
- Preserve separate user and assistant units of work; hold no transaction over AI. Do not invoke AI or alter Feature 001 repositories.

## Dependencies

- AI-002.

## Acceptance criteria

- Messages survive a fresh session, remain consultation-isolated, and return in stable chronological/UUID order.
- Failed persistence rolls back only its unit of work.

## Testing requirements

- PostgreSQL tests cover commit/refresh, fresh-session retrieval, empty history, isolation, tied timestamps, and rollback failure for separate user/assistant operations.

## Definition of Done

- Repository tests pass, SQLAlchemy stays within persistence code, and independent commit boundaries are proven.
