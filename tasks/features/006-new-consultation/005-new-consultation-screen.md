# NC-005: Add New Consultation Screen and Static Route

**Task ID:** NC-005  
**Title:** Add New Consultation Screen and Static Route

## Purpose

Add the accessible MUI creation form inside the existing application shell and
navigate only after the frontend service returns a validated authoritative ID.

## Traceability

- Feature specification: §§5, §§10–12, §§14–15, and §17.
- Implementation plan: §§3 and 8, §§12.5, 14–16, and §§17–18.

## Scope

- Add `NewConsultationScreen` with explicit form states and service injection
  consistent with existing feature screens.
- Register static `/consultations/new` within the current `AppLayout` route
  tree ahead of/alongside the dynamic consultation detail ownership.
- Add focused RTL screen and router regression tests.

## Expected files/areas affected

- New
  `frontend/src/app/features/consultation-records/NewConsultationScreen.tsx`.
- New focused screen test module.
- `frontend/src/app/core/App.tsx` and `frontend/src/app/core/App.test.tsx`.
- No layout navigation edit; activation belongs to NC-006.

## Implementation requirements

- Render `New Consultation` as the page heading, required `Patient name` and
  multiline `Primary concern` fields, `Start Consultation`, and `Cancel` using
  the existing MUI/AppLayout visual language and a semantic form.
- Trim inputs and validate 1–200 and 1–4,000 Unicode code points using a
  JavaScript code-point-safe count; show associated per-field errors, focus the
  first invalid field, and make zero service calls for invalid input.
- Close the same-event duplicate window with a synchronous in-flight ref/guard,
  not React state alone. While pending, disable both inputs and both actions
  and expose accessible progress/status.
- Call the NC-004 service once with normalized values and never auto-retry.
- On confirmed validation failure, retain normalized useful values and show
  safe correctable guidance. On ambiguous failure, retain values and advise
  checking Consultation Records before deliberate retry; clear the guard on
  every failure.
- On success, navigate exactly once to `/consultations/{returned-id}` with
  `{ replace: true }`; do not fabricate/cache detail data.
- When not submitting, Cancel navigates to `/consultations` without a request.
- Ensure direct `/consultations/new` renders this screen rather than sending
  `new` through UUID detail handling; preserve every existing route string.

## Dependencies

- NC-004.
- Live backend integration may wait for NC-003; component/router tests use an
  injected service double.

## Acceptance criteria

- Initial, invalid, submitting, confirmed-failure, ambiguous-failure, retry,
  and success states are deterministic and accessible.
- Exact boundary values submit normalized data; blanks and over-bound values
  produce zero calls with correct focus/error association.
- Repeated click/Enter before rerender and throughout a deferred request causes
  exactly one call; pending controls remain disabled.
- Only the service-returned UUID triggers one replacement navigation; Cancel
  makes no request.
- Static and deep route tests preserve details, records, summary, booking,
  Dashboard, and root redirect behavior.

## Testing requirements

- RTL-test labels, required semantics, heading/actions, no premature errors,
  trimming, boundaries, supplementary Unicode, focus, Enter submission, and
  keyboard operation.
- Use a deferred promise to test progress, disabled controls, synchronous
  duplicate guarding, failure recovery, deliberate retry, and replace
  navigation/history behavior.
- Router-test `/consultations/new` versus a UUID detail and all existing deep
  routes; run focused and relevant frontend regressions from NC-001.

## Architecture and scope guards

- Keep local form/state/navigation in the screen and HTTP/runtime safety in the
  existing service; use MUI and the existing shell.
- Do not add direct `fetch`, local authoritative storage, optimistic dashboard
  state, automatic retry, AI/message/summary/recommendation/appointment work,
  a second shell/design system, patient picker, or Feature 007 route.

## Definition of Done

- Screen/router tests prove the static accessible form, code-point-safe
  validation, single pending request, safe recoveries, Cancel behavior, and
  authoritative replacement navigation inside the unchanged shell.
