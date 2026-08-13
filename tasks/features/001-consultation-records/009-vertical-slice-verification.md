# CR-009: Verify Consultation Records Vertical Slice

**Task ID:** CR-009  
**Title:** Verify Consultation Records Vertical Slice

## Purpose

Verify the completed backend/frontend contract and persistence-to-UI slice
against every approved Consultation Records acceptance criterion.

## Traceability

- Feature specification: §§4, 6, 8, 10, 12.
- Implementation plan: §§12–18, especially §§13–16 and 18.

## Scope

- Verify persisted consultation retrieval through repository, service, and API
  boundaries.
- Verify frontend service compatibility with the approved response/error
  contract and records/detail user behavior.
- Run focused backend, frontend, integration, type/lint, and Docker Compose
  compatibility checks appropriate to the completed slice.
- Review the delivered change for scope and architecture compliance.

## Expected files/areas affected

- Feature-focused backend, frontend, and integration test areas.
- No new product source, migration, infrastructure, configuration, ADR, plan,
  or specification files are expected solely from this verification task.

## Implementation requirements

- Use deterministic persisted consultation data and deterministic frontend
  service/transport stubs where a live backend is not required.
- Verify only approved consultation persistence and retrieval behavior.
- Do not add end-to-end infrastructure, external AI services, credentials, or
  unapproved workflow data to satisfy tests.

## Dependencies

- CR-005, CR-007, and CR-008.

## Acceptance criteria

- Known persisted consultations flow through repository, service, and API;
  search, each status, combined criteria, existing detail, and missing detail
  behave as specified.
- The records UI verifies loading, data, empty, error, filtering/search, and
  navigation; the detail UI verifies loading, data, unavailable, and error.
- The completed slice retains PostgreSQL authority, the frontend service
  boundary, no hardcoded frontend dataset, no AI use, and Docker Compose
  compatibility.

## Testing requirements

- Run the focused Pytest repository/service/API/integration suites, React
  Testing Library feature suites, and relevant frontend type/lint and backend
  checks.
- Confirm tests are repeatable and require no external AI provider or
  credentials.

## Definition of Done

- All applicable checks pass, every feature acceptance criterion is verified,
  and scope/architecture review confirms no unauthorized change remains.
