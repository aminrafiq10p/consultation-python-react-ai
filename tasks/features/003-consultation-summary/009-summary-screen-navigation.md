# CS-009: Add Consultation Summary Screen and Navigation Boundaries

**Task ID:** CS-009  
**Title:** Add Consultation Summary Screen and Navigation Boundaries
**Status:** Complete  

## Purpose

Deliver direct persisted-summary viewing, recommendation selection, restart
navigation, and the booking navigation boundary only.

## Traceability

- Feature specification: §§4, 9, 12–16.
- Implementation plan: §§3, 9, 11, 13–14, 16–20.

## Scope

- Add `ConsultationSummaryScreen` and its nested summary route.
- Add one recommendation selection, Restart Consultation, Book Appointment
  navigation, and the approved unavailable appointment placeholder.
- Add focused component/router tests.

## Expected files/areas affected

- Existing frontend consultation feature summary/placeholder components and
  tests.
- `frontend/src/app/core/App.tsx` route registration.

## Implementation requirements

- Direct load performs summary GET only and never regenerates implicitly.
- Render patient summary, ordered treatment choices, and optional rationale as
  safe plain React text with distinct loading/unavailable/missing/error states.
- Restart is enabled only after load, sends one non-retried request, disables
  duplicates, preserves source UI data, and navigates using returned ID.
- Book remains disabled until a stable recommendation UUID is selected and
  navigates only to the approved path/query boundary.
- The placeholder contains no appointment form, fields, API call, persistence,
  status mutation, or scheduling behavior.

## Dependencies

- CS-007.
- Coordinate shared route/navigation behavior with CS-008.

## Acceptance criteria

- Reload renders the same persisted IDs/order without AI generation.
- Restart and its error states preserve source data and navigate correctly.
- Booking carries consultation/recommendation IDs only and causes no product
  side effect.

## Testing requirements

- RTL/router tests for direct loading, rendering/order/null rationale,
  plain-text safety, all retrieval states, stable single selection, action
  enablement, restart duplicate/error/navigation behavior, exact booking URL,
  and absence of appointment HTTP/form/status behavior.

## Definition of Done

- Screen/router tests plus type/lint checks pass and the result contains only
  the approved summary, restart, and navigation-boundary scope.
