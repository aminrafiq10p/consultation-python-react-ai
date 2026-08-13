# ADR-004: LangChain Inside the AI Layer

## Status

Accepted

## Context

The application needs agent, tool, and LLM orchestration without coupling those details to routes or general business services.

## Decision

Use LangChain only inside the AI layer.

## Alternatives Considered

Allowing LangChain-specific implementation throughout the application was considered and rejected.

## Rationale

Isolation preserves a clean boundary between the Flask API, application services, and AI orchestration.

## Consequences

The AI layer owns the Consultation Agent, skills, tools where appropriate, and provider interaction. This separation is an architectural requirement. LLMs cannot autonomously create appointments.
