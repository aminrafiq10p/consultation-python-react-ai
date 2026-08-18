# NC-006: Activate Shared New Consult Navigation

**Task ID:** NC-006  
**Title:** Activate Shared New Consult Navigation

## Purpose

Turn the existing disabled shared sidebar action into the single accessible
desktop/mobile entry point for `/consultations/new` without redesigning the
application shell.

## Traceability

- Feature specification: §§5, 10.1–10.2, §11, §§14–15, and §17.
- Implementation plan: §§3 and 9, §§12.5, 14–16, and §§17–18.

## Scope

- Activate the existing `+ New Consult` control in shared `SidebarContent`.
- Preserve desktop/permanent and mobile/temporary drawer behavior, active
  navigation, destinations, order, and visual prominence.
- Extend AppLayout and routed integration tests only as needed.

## Expected files/areas affected

- `frontend/src/app/layout/AppLayout.tsx`.
- `frontend/src/app/layout/AppLayout.test.tsx`.
- `frontend/src/app/core/App.test.tsx` only for focused route integration.
- No creation screen/service, backend, dashboard, or infrastructure change.

## Implementation requirements

- Make the existing MUI button an enabled keyboard-accessible React Router
  action/link to exactly `/consultations/new`.
- Retain one `SidebarContent` definition for both responsive modes and the
  established contained prominent styling.
- Invoke the existing optional `onNavigate` callback so mobile activation
  closes the temporary drawer; preserve desktop behavior.
- Keep Dashboard and Consultations labels, targets, order, landmarks, and
  active styles unchanged.
- Preserve the current consultations descendant active rule so Consultations
  has `aria-current="page"` on `/consultations/new` and Dashboard does not.
- Ensure navigation activation itself never invokes the creation service or
  sends a POST.

## Dependencies

- NC-005.

## Acceptance criteria

- Desktop and mobile render one enabled, focusable New Consult destination and
  keyboard activation reaches the static screen.
- Mobile activation closes the temporary drawer; desktop navigation remains
  stable.
- Consultation active state is correct on the new route and remains unchanged
  across records/detail/summary/booking; Dashboard remains unchanged.
- Clicking the navigation action performs no creation request.

## Testing requirements

- Extend deterministic `matchMedia` AppLayout tests for desktop target,
  keyboard access, mobile drawer open/close, landmarks, focusability, and
  active state.
- Add/retain router integration proving the creation screen renders inside the
  shell and the navigation click makes zero service calls.
- Run focused AppLayout/router tests and relevant full navigation regressions.

## Architecture and scope guards

- `AppLayout` owns presentation/navigation only, never form state, HTTP,
  creation, or lifecycle decisions.
- Do not duplicate SidebarContent/actions, redesign branding/sidebar/
  breakpoints/order, or change existing destinations.
- Do not add Appointments navigation or any Feature 007 work.

## Definition of Done

- Responsive layout tests prove the shared accessible action reaches the new
  static route, closes the mobile drawer, preserves all active navigation, and
  performs no POST or shell redesign.
