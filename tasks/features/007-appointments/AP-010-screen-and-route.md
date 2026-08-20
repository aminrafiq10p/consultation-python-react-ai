# AP-010: Build the `/appointments` Screen and Route State Machine

**Task ID:** AP-010  
**Title:** Build the `/appointments` Screen and Route State Machine

## Objective

Render the Appointments destination inside the existing `AppLayout` with clear
loading, populated, empty, recoverable-error, and explicit-retry states.

## Dependencies

AP-009; AP-004 for live API wiring. Screen tests may use an injected service.

## Scope

Route registration under the existing router and screen state behavior.

## Implementation requirements

- Load once on entry through the dedicated service; show accessible loading.
- Render approved persisted fields and stable identity; distinguish empty from
  failure; never fabricate data or show stale data while retrying.
- Retry invokes exactly one service call, with no automatic retry or polling.
- Keep `/appointments` nested in `AppLayout`; preserve all existing routes and
  root redirect behavior.

## Likely files/areas

`frontend/src/app/core/App.tsx`, feature screen files, screen/router tests.

## Tests/checks

Deferred loading, populated, empty, error, retry count, failure-not-empty,
accessibility, direct route, and existing route reachability tests.

## Acceptance criteria

Every required state is visible and safe; `/appointments` renders within the
unchanged shell and uses the dedicated endpoint only.

## Explicit non-goals/scope guards

No direct fetch, local authority, calendar, booking flow, shell redesign,
consultation-detail architecture, or Feature 008 polish.

## Completion evidence

Passing RTL/router tests with request-count assertions and route screenshots
not required or introduced.
