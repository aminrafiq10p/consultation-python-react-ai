# CR-003: Implement Consultation Repository Retrieval and Criteria Queries

**Task ID:** CR-003  
**Title:** Implement Consultation Repository Retrieval and Criteria Queries

## Purpose

Provide the focused repository contract and SQLAlchemy implementation that
retrieves one consultation or a filtered consultation list from PostgreSQL.

## Traceability

- Feature specification: §§5–7, 10.
- Implementation plan: §§3, 6, 12, 14.2, 16–18.

## Scope

- Define the task-focused repository capability for detail retrieval and list
  retrieval with optional validated `search` and `status` criteria.
- Implement it in the SQLAlchemy infrastructure layer.
- Apply case-insensitive search to patient name, primary concern, and
  recommended procedure; combine supplied search and status with logical AND.

## Expected files/areas affected

- `backend/app/application/` or approved contract location for repository
  abstractions.
- `backend/app/infrastructure/` consultation repository implementation.
- Backend repository/persistence tests and deterministic consultation fixtures.

## Implementation requirements

- Return only the approved consultation data and represent an absent detail
  record without leaking database/session mechanics.
- Preserve the approved no-pagination and no-sorting contract.
- Do not implement client-side filtering, unrelated repositories, or AI work.

## Dependencies

- CR-002.

## Acceptance criteria

- A known persisted consultation is retrievable by identifier.
- List retrieval returns all eligible persisted records when no criterion is
  supplied.
- Search is case-insensitive across each approved text field, every approved
  status filters correctly, and combined criteria return only intersecting
  records.

## Testing requirements

- Add deterministic PostgreSQL repository tests for single retrieval, search
  inclusion/exclusion across all three fields, each status, empty results, and
  combined search plus status.

## Definition of Done

- The repository implementation and tests pass, SQLAlchemy stays in
  infrastructure, and the scope remains consultation retrieval only.
