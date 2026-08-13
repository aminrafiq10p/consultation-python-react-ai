# CR-004: Add Consultation Read Application Service

**Task ID:** CR-004  
**Title:** Add Consultation Read Application Service

## Purpose

Coordinate the list and detail retrieval use cases independently of Flask and
SQLAlchemy mechanics.

## Traceability

- Feature specification: §§6.3, 7, 9–10.
- Implementation plan: §§3, 7, 12, 14.3, 16–18.

## Scope

- Add the consultation read application service.
- Accept validated search/status criteria and delegate them unchanged to the
  repository.
- Translate an absent detail result into an application-level not-found
  outcome suitable for API translation.

## Expected files/areas affected

- `backend/app/application/` consultation read-service area.
- Related repository contract types if required by established conventions.
- Backend application-service tests.

## Implementation requirements

- Keep the service deterministic and independent of Flask requests/responses,
  SQLAlchemy sessions, LangChain, and AI providers.
- Do not introduce mutation, status-transition, recommendation, appointment,
  summary, or message behavior.

## Dependencies

- CR-003.

## Acceptance criteria

- Valid list criteria reach the repository without altered search/filter
  semantics.
- Detail retrieval returns feature data for an existing record and an explicit
  application-level not-found outcome for an absent record.

## Testing requirements

- Add isolated deterministic service tests using a controlled repository test
  double for criteria forwarding, list outcomes, existing detail, and missing
  detail behavior.

## Definition of Done

- Service tests pass and the service retains the approved application-layer
  boundary with no Flask, SQLAlchemy, or AI dependency.
