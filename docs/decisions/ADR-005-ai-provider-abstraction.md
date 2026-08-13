# ADR-005: AI Provider Abstraction

## Status

Accepted

## Context

The platform must run without an external AI API while retaining the option to use OpenAI and future providers.

## Decision

Use an AI provider abstraction with `MockAIProvider` and `OpenAIProvider`.

## Alternatives Considered

Binding the application directly to one external provider was considered and rejected.

## Rationale

The abstraction supports a local mock runtime and optional provider integrations without changing core application behavior.

## Consequences

Mock AI support is mandatory. OpenAI is optional. An `AzureOpenAIProvider` may be added later through the abstraction; Azure OpenAI is not required.
