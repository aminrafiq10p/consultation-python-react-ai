# AB-007: Add Appointment Booking Screen and Route Ownership

**Task ID:** AB-007  
**Title:** Add Appointment Booking Screen and Route Ownership

## Purpose

Replace the Feature 003 booking placeholder with the approved accessible form,
authoritative persisted recommendation context, and safe recovery behavior.

## Traceability

- Feature specification: §§4–6, §§8–9, §§14–16, and §19.
- Implementation plan: §§3 and 9, §10.3, §13 AB-007, and §§14–17.

## Scope

- Add `AppointmentBookingScreen` in the existing consultation-records feature
  and make it own the existing booking route.
- Validate route/query context, load the existing summary service, display the
  exact persisted recommendation, collect local date/time and location, and
  submit once through `bookAppointment`.
- Add focused React Testing Library and router regression tests; remove the old
  placeholder only after its route ownership is replaced.

## Expected files/areas affected

- New `frontend/src/app/features/consultation-records/AppointmentBookingScreen.tsx`.
- `frontend/src/app/core/App.tsx`.
- Removal of
  `frontend/src/app/features/consultation-records/AppointmentUnavailableScreen.tsx`.
- Focused `AppointmentBookingScreen.test.tsx`, router tests in
  `frontend/src/app/core/App.test.tsx`, and retained summary handoff tests.

## Implementation requirements

- Require a valid `consultationId` path UUID and exactly one valid
  `recommendation_id` query UUID before enabling submission.
- On mount/direct refresh, call only `consultationApi.summary(consultationId)`,
  rely on its consultation-link validation, find the exact recommendation ID,
  and display its persisted treatment read-only.
- Distinguish loading, missing consultation, unavailable summary, missing or
  mismatched recommendation, and recoverable retrieval failure with safe
  records/summary navigation and retry only for recoverable GET failure.
- Use accessible MUI date/time and location controls, preserve the 200-character
  limit/helper feedback, and never allow treatment editing.
- On confirmation, require both values, parse the browser-local datetime,
  require its instant to be strictly future for UX guidance, trim location,
  reject blank/over-200 Unicode code points, and convert the instant with
  `toISOString()` immediately before submitting the exact three request fields.
- Guard with one pending flag so repeated activation while pending sends at
  most one POST and disables inputs/confirmation.
- Preserve inputs for validation, conflict, transport, and server failures.
  Show distinct safe guidance for not-bookable outcomes, disable creation after
  already-exists, and warn that transport/`500` ambiguity should be checked in
  Consultation Records rather than blindly retried.
- Only a validated success calls
  `navigate("/consultations", { replace: true })`; do not mutate local record
  status or cache.

## Dependencies

- AB-006.

## Acceptance criteria

- The unchanged Feature 003 path/query handoff and a direct refresh load and
  display the exact persisted selected treatment.
- Invalid/missing/mismatched navigation context cannot submit and provides safe
  navigation; retrieval states and retry behavior are distinct and accessible.
- Valid normalized values produce one service call with the selected ID and an
  explicit-offset ISO instant; invalid/past/blank/overlong values do not call.
- Pending activation is single-shot, failures preserve fields and show the
  approved recovery, and success replaces history to `/consultations`.
- Routed records subsequently retrieve authoritative `BOOKED`; the screen
  performs no local status simulation.

## Testing requirements

- RTL-test valid handoff/direct load, summary call, exact treatment selection,
  invalid path, zero/multiple/invalid query values, mismatched summary and
  recommendation, and every retrieval state/navigation action.
- Test required/future/date parsing, local-to-ISO conversion, whitespace trim,
  Unicode length, pending disabling, duplicate activation, and exact request.
- Test every service error kind, preserved form values, ambiguity warning,
  disabled already-booked behavior, and replacement success navigation.
- Update router regression tests and retain Feature 003 summary-selection tests
  proving the route/query names and stable IDs are unchanged.

## Architecture and scope guards

- Use MUI, the existing feature root/router, and `consultationApi`; keep HTTP
  and ownership/business authority out of the component.
- Do not auto-submit or auto-retry POST, mutate records locally, create a success
  page, or add appointment retrieval/lifecycle, provider/availability/conflict/
  hours, calendar, notifications, payments, auth, dashboard, AI, or new infra.

## Definition of Done

- Screen and router tests prove authoritative navigation context, persisted
  treatment display, accessible validated single submission, safe recovery,
  replacement records navigation, and no local `BOOKED` mutation or expanded
  scope.
