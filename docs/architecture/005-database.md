# Database Architecture

## Platform

PostgreSQL is the system of record. SQLAlchemy accesses persistence through repositories, and Alembic manages schema migrations.

## Core Data

- `consultations`
- `messages`
- `recommendations`
- `appointments`

## Relationships

```text
consultation → messages        (1:N)
consultation → recommendation  (1:1)
consultation → appointment     (1:0..1)
```

The business relationship is:

```text
consultation
  ↓
recommendation
  ↓
appointment
```

## Requirements

Conversation state must be persisted in PostgreSQL. Application code accesses it through the repository layer; Flask API routes do not directly manipulate database persistence.
