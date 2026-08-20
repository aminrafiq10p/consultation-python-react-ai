# AP-013: Run Features 001–006 Regression and Lifecycle Verification

**Task ID:** AP-013  
**Title:** Run Features 001–006 Regression and Lifecycle Verification
**Status:** Complete (2026-08-19)

## Objective

Demonstrate that existing consultation, booking, Dashboard, root, and shell
behavior remains compatible after Feature 007 changes.

## Dependencies

AP-007, AP-008, AP-011, AP-012.

## Scope

Cross-feature automated suites and direct route/lifecycle verification.

## Implementation requirements

Run backend/frontend regressions and direct checks for `/`, Dashboard,
consultation records/new/detail/summary/booking, and `/appointments`. Confirm
Feature 004 POST response and `BOOKED` behavior are unchanged, Dashboard still
reads persisted rows, and the Appointments screen uses only its new endpoint.

## Likely files/areas

Existing backend/frontend test suites, route tests, booking/Dashboard tests,
Compose configuration, and deterministic fixtures.

## Tests/checks

Features 001–006 backend/frontend tests; root redirect, navigation, booking,
Dashboard, consultation route, and direct Appointments checks.

## Acceptance criteria

Existing suites pass without loosening assertions or changing earlier feature
contracts; all required routes remain reachable.

## Explicit non-goals/scope guards

Do not fix unrelated failures by expanding Feature 007 or altering approved
earlier contracts; document pre-existing failures separately.

## Completion evidence

Regression command/result log and route/lifecycle evidence with failure
classification.
