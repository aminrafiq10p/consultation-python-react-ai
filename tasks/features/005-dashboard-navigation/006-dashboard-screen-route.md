# DN-006: Add Dashboard Screen and Route

**Task ID:** DN-006  
**Title:** Add Dashboard Screen and Route

## Purpose

Add the accessible dashboard loading/success/zero/error experience and make it
the root destination while preserving every existing consultation route.

## Traceability

- Feature specification: §4, §9, §§11–14, §§16–18.
- Implementation plan: §§3, 9–10, §§13.2–13.3, §15 DN-006, and §§16–19.

## Scope

- Add `DashboardScreen` with an injectable narrow dashboard service.
- Render loading, three-card success, all-zero, safe error, and explicit Retry
  states without stale metrics.
- Add `/dashboard`, change only the root replacement redirect to `/dashboard`,
  and retain all Feature 001–004 consultation declarations.
- Add focused screen and router tests.

## Expected files/areas affected

- `frontend/src/app/features/dashboard/DashboardScreen.tsx`.
- `frontend/src/app/features/dashboard/DashboardScreen.test.tsx`.
- `frontend/src/app/core/App.tsx`.
- `frontend/src/app/core/App.test.tsx`.

## Implementation requirements

- Use one explicit loading/success/error state machine; request once on mount
  and suppress obsolete/unmounted promise resolutions.
- Set loading and clear old metrics before each explicit load; retain no stale
  cards after a failed or superseded request.
- Render an `h1` Dashboard heading, accessible `role="status"` loading state,
  and MUI cards in order: Total consultations, Booked appointments, Conversion
  rate.
- Render counts as integers and the received conversion with `toFixed(2) + "%"`;
  render zero as `0`, `0`, and `0.00%` without deriving the percentage.
- Show one safe retrieval error and labelled Retry button; each activation
  starts exactly one new service call with no loop or background refresh.
- Add the nested `dashboard` route and change the index `Navigate` target to
  `/dashboard` while retaining `replace`.
- Leave `/consultations`, detail, summary, and appointment booking routes and
  booking query handoff unchanged.

## Dependencies

- DN-005.

## Acceptance criteria

- Pending, populated, zero, and zero-booking success states render accessibly
  with exact labels/order/formatting and no `undefined` or `NaN`.
- Safe failure contains no transport detail; Retry clears stale output, makes
  one call, and can recover without obsolete results overwriting current state.
- `/` replaces to `/dashboard`, direct `/dashboard` renders inside the shared
  layout, and all existing consultation routes remain direct-link reachable.
- The component performs no authoritative conversion calculation, record
  fetch, mutation, AI call, chart rendering, or navigation ownership change.

## Testing requirements

- Use deferred promises for loading and obsolete/unmounted-result coverage;
  cover valid, zero, zero-booking, rejection, Retry recovery, and exact
  `25.00%`, `33.33%`, and `0.00%` formatting.
- Use a location-aware router harness to prove replacement redirect and direct
  dashboard/layout rendering.
- Retain deep records/detail/summary/booking route tests, including unchanged
  `recommendation_id` query handoff.

## Architecture and scope guards

- Use MUI, React state/effects, the dedicated dashboard service, the existing
  nested router, and the existing `AppLayout`/`Outlet` shell.
- Do not add navigation UI here, another router/layout, cached metrics, polling,
  automatic retry, local formula, chart/filter, AI, or infrastructure changes.

## Definition of Done

- Screen and router tests prove accessible non-stale states, explicit one-shot
  recovery, exact backend-value formatting, root/dashboard routing, and full
  Feature 001–004 route compatibility.
