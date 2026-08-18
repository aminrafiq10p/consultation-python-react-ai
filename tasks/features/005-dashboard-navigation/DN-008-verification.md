# DN-008 Verification Evidence

Verified on 2026-08-18 against the repository implementation and the approved
Feature 005 specification and plan.

## Automated verification

- `backend/.venv/bin/pytest -q tests`: 327 passed before adding the final
  cross-feature scenario. The added focused scenario then passed with the two
  existing persisted-dashboard cases: 3 passed.
- `frontend: npm test -- --run`: 240 passed.
- `frontend: npm run lint`: passed.
- `frontend: npm run typecheck`: passed.
- `frontend: npm run build`: passed (Vite reported only its advisory bundle-size
  warning).
- `docker compose config --quiet`: passed.
- `docker compose build`: passed for backend and frontend.

## Vertical-slice evidence

`test_feature_004_booking_updates_fresh_dashboard_read_exactly_once` persists
three consultations in mixed states and an approved recommendation. It proves:

- initial dashboard metrics are `3`, `0`, and `0.0`;
- booking occurs through the existing Feature 004 HTTP/application boundary;
- one appointment persists and the eligible consultation becomes `BOOKED`;
- a fresh-session dashboard read returns `3`, `1`, and `33.33`;
- a duplicate booking returns `409` and the appointment count remains one.

The focused repository tests prove independent scalar counts, all-status
consultation inclusion, direct appointment counting, no join multiplication,
one read statement, and no mutation or commit. Application and API tests prove
Decimal `ROUND_HALF_UP` calculation, count invariants, exact safe request and
response contracts, and request-scoped composition. Frontend tests prove the
strict one-request service, all DashboardScreen states, root replacement,
existing deep routes, shared desktop/mobile navigation, active state, keyboard
operation, and mobile drawer closure.

## Runtime and scope review

An isolated Compose stack (temporary project and volumes) returned the exact
empty dashboard JSON from `/api/v1/dashboard`, and the frontend `/dashboard`
deep route returned HTTP 200. The temporary stack and volumes were removed.

The pre-existing default Compose PostgreSQL volume did not authenticate with
the current ignored `backend/.env`; it was left intact. This external-state
mismatch was bypassed only for smoke verification by using the isolated stack.

Review confirmed the Alembic head remains
`20260817_04_create_appointments.py`; Feature 005 adds no migration, table,
cache, dependency, AI call, browser secret, or forbidden screenshot-only
functionality. Secret-pattern matches were limited to deliberate test fixtures
and prior verification prose; no credential value was printed or committed.
