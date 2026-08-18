# DN-007: Add Reusable Responsive Application Navigation

**Task ID:** DN-007  
**Title:** Add Reusable Responsive Application Navigation

## Purpose

Extend the existing application shell with one logical responsive navigation
definition for Dashboard and Consultations, with exact accessible active state.

## Traceability

- Feature specification: §4, §§10–11, §§13–14, §§16–18.
- Implementation plan: §§3, 10–11, §13.3, §15 DN-007, and §§16–19.

## Scope

- Extend only the existing `AppLayout` shell for navigation behavior.
- Define Dashboard then Consultations once and render permanent desktop and
  temporary mobile surfaces from that definition.
- Add focused responsive, landmark, ordering, active-state, keyboard/control,
  drawer-close, and deep-route compatibility tests.

## Expected files/areas affected

- `frontend/src/app/layout/AppLayout.tsx`.
- `frontend/src/app/layout/AppLayout.test.tsx`.
- Router regression tests only where navigation integration requires them.

## Implementation requirements

- Define one module-level collection in order: Dashboard → `/dashboard`, then
  Consultations → `/consultations`; use router `Link`/`NavLink` and canonical
  `location.pathname`.
- Preserve the title, AppBar, one `main` content area, and `Outlet`.
- At MUI `md` and above show a permanent Drawer/sidebar; below `md` hide it and
  expose an accessible `Open navigation` control for a temporary Drawer.
- Render links within a meaningfully labelled `nav` landmark using normal
  focusable links and keyboard-operable MUI controls.
- Mark Dashboard selected/current only for exact `/dashboard`.
- Mark Consultations selected/current only for exact `/consultations` or a
  `/consultations/` prefix; unrelated lookalike paths select neither.
- Apply MUI selected state and `aria-current="page"` to only the active link.
- Close the temporary Drawer after either destination is activated; permanent
  navigation does not depend on mobile open state.
- Do not parse or rewrite nested paths/query strings or load application data.

## Dependencies

- DN-006.

## Acceptance criteria

- Desktop and mobile surfaces expose both destinations in approved order from
  one logical definition with an accessible navigation landmark.
- Exact dashboard, records, detail, summary, and booking active/current rules
  pass, while unrelated paths produce no incorrect selection.
- Mobile menu opening is accessible and selecting either link closes the
  temporary Drawer; normal keyboard/focus behavior is retained.
- The layout continues to render every nested route and preserves booking query
  handoff without becoming a router or data owner.

## Testing requirements

- Install deterministic `window.matchMedia` behavior for desktop/mobile MUI
  breakpoints and assert roles, names, destinations, order, selected/current
  semantics, and Drawer visibility/closure rather than generated CSS classes.
- Exercise dashboard, records, detail, summary, booking, and unrelated paths.
- Use `user-event` for mobile control/link and keyboard-accessible interactions;
  retain relevant route regressions.

## Architecture and scope guards

- Keep `AppLayout` as the single shared shell and React Router as the only
  location/history owner.
- Do not introduce duplicated route definitions, a second layout/router,
  pointer-only controls, data fetching, route/query rewriting, charts, auth,
  AI, analytics, or infrastructure changes.

## Definition of Done

- Deterministic responsive tests prove one ordered navigation source, permanent
  desktop and temporary mobile behavior, exact accessible active state, mobile
  closure, shared-shell ownership, and all deep-route compatibility.
