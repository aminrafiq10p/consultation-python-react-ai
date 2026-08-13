# System Overview

## Purpose

The AI Consultation Platform supports consultations, persisted conversation history, AI-assisted recommendations and summaries, and deterministic appointment booking.

## Approved Architecture

The system consists of a React + TypeScript frontend, a Flask REST API, PostgreSQL persistence, and Docker Compose runtime infrastructure. LangChain is contained within the AI layer. The initial AI implementation uses a mock provider; OpenAI is an optional provider.

```text
React
  ↓
REST API
  ↓
Flask API layer
  ↓
Application services
  ↓
Domain/business logic
  ↓
Repositories
  ↓
PostgreSQL
```

## Architectural Requirements

- Frontend, backend, AI, and infrastructure concerns remain separate.
- Conversation state is persisted in PostgreSQL.
- API routes do not directly manipulate persistence.
- Appointment creation is deterministic and is never autonomously performed by an LLM.
- Docker Compose is mandatory; Azure deployment is optional and not required.

## Delivery Approach

The project follows specification-driven development. Given the two-day delivery constraint, implementation should remain focused on approved scope and avoid unapproved technologies or architecture changes.
