# AP-012: Add Shared Desktop/Mobile Appointments Navigation

**Task ID:** AP-012  
**Title:** Add Shared Desktop/Mobile Appointments Navigation and Active State

## Objective

Add one Appointments destination to the existing shared navigation and preserve
all shell, active-state, and mobile-drawer behavior.

## Dependencies

AP-010; coordinate with AP-011 if route assertions overlap.

## Scope

Shared navigation definition, active helper, desktop/mobile tests, and route
integration only.

## Implementation requirements

- Define Dashboard, Consultations, Appointments once in the specified order;
  target `/appointments`.
- Match Appointments exactly and future descendants, never consultation paths;
  preserve consultation descendants, Dashboard exact match, and `+ New Consult`
  at `/consultations/new`.
- Reuse permanent desktop and temporary mobile drawers; mobile closes after
  navigation and accessibility semantics remain intact.

## Likely files/areas

`frontend/src/app/layout/AppLayout.tsx`, `AppLayout` tests, `App.tsx` route
tests, with explicit ownership coordination.

## Tests/checks

Desktop/mobile same order/destinations, active-state matrix, lookalike paths,
drawer close, New Consult functionality, and route reachability.

## Acceptance criteria

Both responsive modes expose the same three destinations from one definition;
only the correct section is active and all existing routes work.

## Explicit non-goals/scope guards

No router replacement, route flattening, navigation duplication, branding or
breakpoint redesign, or Feature 008 visual alignment.

## Completion evidence

Passing AppLayout/router tests and diff review showing one shared navigation
source.
