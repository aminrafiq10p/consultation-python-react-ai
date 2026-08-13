# ADR-003: PostgreSQL

## Status

Accepted

## Context

The application manages related consultations, messages, recommendations, and appointments, including persisted conversation state.

## Decision

Use PostgreSQL as the database.

## Alternatives Considered

Non-relational storage alternatives were not selected because the approved model has explicit relational requirements.

## Rationale

PostgreSQL fits the relational data model: consultations have many messages, one recommendation, and zero or one appointment.

## Consequences

PostgreSQL is the system of record. SQLAlchemy repositories access persistence and Alembic manages schema migrations.
