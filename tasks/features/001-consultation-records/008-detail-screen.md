# CR-008: Implement Consultation Detail Route and States

**Task ID:** CR-008  
**Title:** Implement Consultation Detail Route and States

## Purpose

Deliver the read-only consultation detail view for a selected persisted record,
including clear loading, unavailable, and recoverable error experiences.

## Traceability

- Feature specification: §§2, 4, 6.2–6.3, 8, 10, 12.
- Implementation plan: §§2–4, 11–16, 18.

## Scope

- Add the approved React Router detail route carrying the consultation
  identifier according to existing routing conventions.
- Retrieve detail through CR-006 and render patient name, primary concern,
  recommended procedure, and status with MUI components.
- Render distinct loading, unavailable-detail (`404`), and recoverable error
  states.

## Expected files/areas affected

- Frontend consultation-records detail route, screen, and presentation areas.
- Existing frontend router registration area.
- React Testing Library detail-screen tests.

## Implementation requirements

- Keep the view read-only and limited to the five approved consultation data
  values.
- The unavailable-detail state must be visibly distinct from a generic
  retrieval error.
- Use only the feature service; do not add AI chat, summary, booking,
  persistence, or direct HTTP logic.

## Dependencies

- CR-006.
- May proceed in parallel with CR-007 after CR-006; live integration depends
  on CR-005.

## Acceptance criteria

- An existing selected record displays the four required user-facing fields.
- The configured route supplies the stable identifier to the feature service.
- Loading, missing-detail, and recoverable error states are safe, clear, and
  distinguishable.

## Testing requirements

- Add React Testing Library coverage for route-parameter retrieval, successful
  field rendering, loading, unavailable detail, and recoverable detail error,
  using deterministic service stubs.

## Definition of Done

- Detail behavior tests and applicable type/lint checks pass, and the view
  remains within the approved read-only Consultation Records scope.
