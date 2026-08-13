# ADR-007: Specification-Driven Development

## Status

Accepted

## Context

The project needs a clear source of truth and focused delivery under a two-day constraint.

## Decision

Follow this workflow:

```text
Requirement
→ Architecture
→ Specification
→ Plan
→ Tasks
→ Implementation
→ Tests
→ Definition of Done
```

## Alternatives Considered

Implementing features without an approved specification was considered and rejected.

## Rationale

An approved feature specification provides one source of truth and helps keep implementation within agreed scope.

## Consequences

Work begins from an approved specification. Tasks may be divided into backend, frontend, AI, database, testing, and integration work. Completion requires relevant tests, applicable lint/type checks, and verification against acceptance criteria.
