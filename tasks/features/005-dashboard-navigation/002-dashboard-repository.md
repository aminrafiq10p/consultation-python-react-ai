# DN-002: Add Dashboard Metrics Repository

**Task ID:** DN-002  
**Title:** Add Dashboard Metrics Repository

## Purpose

Add the focused read-only PostgreSQL repository operation that returns the two
authoritative dashboard counts without loading or multiplying entity rows.

## Traceability

- Feature specification: §§5–6, §8, §13, §§14–17.
- Implementation plan: §§3–4, §12.1, §15 DN-002, and §§16–19.

## Scope

- Add `DashboardCounts` or an equivalent immutable count value.
- Add `DashboardRepository` over the existing SQLAlchemy `Session`.
- Add focused PostgreSQL repository tests for count semantics, query shape,
  read-only behavior, and related-row cardinality.

## Expected files/areas affected

- `backend/app/repositories/dashboard_repository.py`.
- `backend/app/repositories/__init__.py` only if existing exports require it.
- `backend/tests/test_dashboard_repository.py` and established PostgreSQL test
  helpers only where required.

## Implementation requirements

- Expose one count-pair method, such as `get_counts()`, that executes one outer
  `SELECT` containing independent scalar subqueries for
  `count(consultations.id)` and `count(appointments.id)`.
- Count every persisted consultation regardless of status, and count persisted
  appointment rows directly rather than interpreting `BOOKED` status.
- Use no consultation/appointment join, status predicate, mapped collection
  load, write lock, add, flush, commit, rollback, or mutation.
- Normalize returned database scalars to Python integers; do not clamp, repair,
  or compute conversion in the repository.
- Reuse the existing mappings, shared metadata, request session, migrated
  PostgreSQL schema, and Feature 004 Alembic head unchanged.

## Dependencies

- DN-001.

## Acceptance criteria

- Empty persistence returns exactly `0, 0` from one aggregate operation.
- All consultation statuses contribute to total; only appointment rows
  contribute to booked count, including deliberately inconsistent status data.
- Extra messages, summary, recommendations, and other related rows multiply
  neither aggregate.
- Repository reads load no entity collection and change no persisted row or
  transaction through an explicit commit.

## Testing requirements

- Run focused tests against migrated PostgreSQL 16 with appointments cleaned
  before consultations.
- Cover empty, mixed-status, `BOOKED` without appointment, appointment-backed,
  linked-booking, and related-row no-multiplication scenarios.
- Inspect executed statement/result behavior and compare fresh snapshots of
  consultations, appointments, messages, summary, recommendations, and
  projections before and after the read.

## Architecture and scope guards

- Keep SQLAlchemy mechanics in the focused repository; business validation and
  percentage calculation belong to DN-003.
- Create no mapping or migration and add no dashboard table, persistence,
  cache, materialized view, analytics framework, AI, or external call.
- Do not alter Feature 001–004 repositories, workflows, or data definitions.

## Definition of Done

- Focused PostgreSQL tests prove one independent non-joining scalar aggregate
  operation returns authoritative integer counts without entity loading,
  mutation, commit, migration, or expanded scope.
