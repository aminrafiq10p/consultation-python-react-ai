# CS-008: Add Consultation Detail Completion Behavior

**Task ID:** CS-008  
**Title:** Add Consultation Detail Completion Behavior
**Status:** Complete

## Purpose

Extend Consultation Detail with eligible summary generation and completed
read-only behavior while preserving persisted conversation history.

## Traceability

- Feature specification: §§4–5, 8, 12–16.
- Implementation plan: §§3, 6.3, 9–10, 13–14, 16–20.

## Scope

- Share loaded conversation role/history state with Consultation Detail.
- Add Generate/View Summary actions, pending/error handling, and navigation.
- Make completed/booked conversation controls read-only and add RTL coverage.

## Expected files/areas affected

- `ConsultationDetailScreen.tsx`, `ConsultationConversation.tsx`, and related
  tests in the existing frontend consultation feature.

## Implementation requirements

- Show Generate Summary only as a UI hint for `PENDING` history containing
  both roles and ending assistant; backend remains authoritative.
- Disable duplicate generation while pending and navigate successful results
  to `/consultations/:consultationId/summary`.
- Present distinct safe not-eligible, generation, missing, and generic errors.
- Retain ordered history for `COMPLETED`; hide/disable composer and show View
  Summary. `BOOKED` permits neither generation nor messaging.
- Never clear messages, fabricate completion, call HTTP/OpenAI directly, or
  add appointment/status behavior.

## Dependencies

- CS-007.

## Acceptance criteria

- Eligible, ineligible, pending, success, and failure states behave through the
  service boundary with duplicate prevention.
- Completed history remains visible/read-only and stale closed submissions are
  handled safely.
- Existing Feature 001 detail and pending Feature 002 conversation behavior
  remains intact.

## Testing requirements

- RTL tests for role/status eligibility combinations, loading, one pending
  activation, successful route navigation, each safe error, completed View
  Summary/read-only state, booked state, and stale closed response.

## Definition of Done

- Focused UI tests/type/lint checks pass and no history deletion, direct
  transport/provider call, appointment UI, or unauthorized mutation is added.
