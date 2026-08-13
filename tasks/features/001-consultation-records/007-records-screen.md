# CR-007: Implement Consultation Records Screen and Navigation

**Task ID:** CR-007  
**Title:** Implement Consultation Records Screen and Navigation

## Purpose

Deliver the backend-driven Consultation Records UI with search, status
filtering, clear list states, and navigation to a selected record.

## Traceability

- Feature specification: §§2, 4, 6.1, 8, 10, 12.
- Implementation plan: §§2–4, 10, 12–16, 18.

## Scope

- Add the feature-oriented records route/screen using React, TypeScript,
  React Router, and MUI.
- Render patient name, primary concern, recommended procedure, and status in
  an accessible table or list.
- Manage temporary search and selected-status state; provide all-status plus
  only the three approved statuses.
- Request data through CR-006, including combined active criteria, and make a
  selected record navigate to its detail route.

## Expected files/areas affected

- Frontend consultation-records route, screen, and presentation-component
  areas.
- Existing frontend router registration area.
- React Testing Library records-screen tests.

## Implementation requirements

- Render returned service data only; never use hardcoded or mock consultation
  records as application data.
- Show explicit loading, successful empty, and recoverable error states.
- Do not add sorting, pagination, mutation, or client-side reimplementation of
  server filtering rules.

## Dependencies

- CR-006.
- May proceed in parallel with CR-008 after CR-006; live integration depends
  on CR-005.

## Acceptance criteria

- Returned records display all four required user-facing fields.
- Search, each status, and combined criteria invoke the service and present
  its returned result.
- Loading, empty, and recoverable error states are clear; record selection
  navigates to the configured detail route.

## Testing requirements

- Add React Testing Library coverage for rendering, service-boundary search,
  status, combined criteria, loading, empty, recoverable error, and detail
  navigation using deterministic service stubs.

## Definition of Done

- Screen tests and applicable type/lint checks pass; routing and API-service
  boundaries are preserved with no out-of-scope UI behavior.
