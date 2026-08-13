# ADR-001: React + TypeScript + MUI over Angular

## Status

Accepted

## Context

The project has a two-day delivery constraint and requires a relatively small frontend UI.

## Decision

Use React with TypeScript and MUI rather than Angular.

## Alternatives Considered

Angular was considered.

## Rationale

React enables faster implementation for the approved UI scope while TypeScript and MUI provide typed development and consistent components.

## Consequences

The frontend will use React, TypeScript, React Router, MUI, feature-oriented organization, and dedicated API/service modules. The UI must not own persistence business logic.
