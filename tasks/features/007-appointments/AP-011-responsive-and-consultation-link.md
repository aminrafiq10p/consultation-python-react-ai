# AP-011: Add Responsive Appointment Presentation and Consultation Navigation

**Task ID:** AP-011  
**Title:** Add Responsive Appointment Presentation and Consultation Navigation

## Objective

Make each appointment readable across viewport sizes and provide exactly one
clear action to its persisted related consultation.

## Dependencies

AP-010.

## Scope

Appointment row/card presentation and one keyboard-accessible navigation
interaction.

## Implementation requirements

- Use existing MUI/application visual conventions: restrained table at desktop
  and readable stacked/card/list adaptation at narrow widths without overflow.
- Show patient, selected treatment, date/time, location, appointment identity,
  and consultation relationship.
- Choose one item interaction (link/card or one explicit action) navigating
  exactly to `/consultations/{consultationId}` from returned data.
- Do not duplicate row/patient/action navigation.

## Likely files/areas

Feature screen/presentation components and focused RTL tests; existing router
integration tests.

## Tests/checks

Desktop content, narrow-width usability/no horizontal overflow, keyboard
activation, exact destination, and unchanged consultation detail route.

## Acceptance criteria

One accessible interaction reaches the existing related consultation route and
all approved values remain readable without a second data source.

## Explicit non-goals/scope guards

No screenshot matching, screen-by-screen polish, shell redesign, provider,
calendar, status, or Feature 008 work.

## Completion evidence

Passing presentation/navigation tests and review of the single interaction.
