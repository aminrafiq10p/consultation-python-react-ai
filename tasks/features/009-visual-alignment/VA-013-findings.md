# VA-013 Findings — Screen-by-Screen Visual Verification

## Result

Visual verification of Feature 009 is complete for the five approved desktop
references. The implementation preserves the shared shell and visual system
introduced by VA-005, uses API-backed data/state, and does not add unsupported
screenshot-only functionality. No product-code correction was required for
VA-013.

VA-013 is accepted. The tracker is checked because the visual-verification
criteria pass and the remaining backend findings are not Feature 009 defects:
five failures are pre-existing Feature 008 implementation gaps, and 92 test
errors are blocked by Docker API permissions. Neither was silently fixed or
worked around here. The Feature 008 gaps remain a prerequisite for final
vertical-slice acceptance; VA-014 is not started or marked complete.

## Reference screen verification

| Screen | Result | Alignment observations | Remaining deviations and authority note | Narrow fix |
| --- | --- | --- | --- | --- |
| Dashboard | PASS | Shared 264px desktop sidebar, light page background, bounded content area, page heading/subtitle, three metric cards, two-column trend/activity region, pending-review surface, restrained borders/radii/shadows, real loading/error/empty states, and accessible trend summary are present. | The reference's fourth Monthly Revenue card, Invite Patient, Generate Report, unsupported sidebar items, comparative percentages, fabricated activity, and screenshot identities are intentionally absent. Trend/activity/pending values come from the Dashboard read projection. | None. |
| Consultation Detail / AI Chat | PASS | Patient/detail header, bounded chronological conversation region, distinct user/assistant message alignment, assistant structured surface, typed handoff CTA, scrollable history, composer, loading/error, and closed-state presentation are implemented with the shared card/button/input language. | Reference microphone, attachment/upload, patient-photo, and prose-derived actions are intentionally absent. Text and clinical payloads remain persisted/API-authoritative rather than screenshot content. | None. |
| Consultation Summary / Recommendations | PASS | Persisted patient summary, optional rationale surface, ordered selectable recommendation cards, selected state, and distinct Next Steps action area align with the reference hierarchy and shared surfaces. Book Appointment and Restart Consultation retain their existing routes/semantics. | Confidence, history, prices, duration, treatment metadata, and unsupported clinical claims are intentionally absent unless supplied by the API. | None. |
| Appointment Booking | PASS | Back navigation, heading/subtitle, desktop two-column composition, Procedure Details and Logistics surfaces, supported treatment/date-time/location controls, Summary aside, validation/error states, and primary confirmation hierarchy align with the reference composition. | Provider, target area, duration, estimated cost, Save as Draft, availability, and clinic-management controls are intentionally absent. Booking remains the deterministic Feature 004 write path. | None. |
| Consultation Records | PASS | Shared heading/subtitle, search field, status filter pills, bordered table surface, readable row height/separators, initials derived from real names, API-backed required fields, status chips, detail navigation, and narrow-screen horizontal-safe table treatment are present. | Date is omitted because the existing Records contract has no approved authoritative date projection. Reference pagination, record totals, sorting, fake identities, and fabricated dates are intentionally absent. | None. |

## Screens without supplied references

| Screen | Result | Verification |
| --- | --- | --- |
| New Consultation consistency | PASS | Uses the shared shell, PageHeader, Surface, MUI input/button treatment, validation/error/loading states, responsive form spacing, and Feature 006 creation/navigation behavior. |
| Appointments consistency | PASS | Uses the shared shell, PageHeader, records-derived table/card language, API-backed persisted appointment fields, loading/empty/error states, consultation links, and responsive stacked cards. No edit/cancel/reschedule behavior was introduced. |

## Unsupported screenshot-only feature audit

No unsupported screenshot-only features were introduced. In particular, the
implementation does not add Patients, AI Insights, Archive, Support, Sign
Out/authentication, a fake admin profile, Invite Patient, Generate Report,
Monthly Revenue, fake statistics/comparison percentages, fake clinical
facts/costs, provider selection, availability, Save as Draft, target area,
duration, clinic management, fake pagination/record counts, or fake activity.

## Functional regression spot checks

- Frontend screen/service tests cover Dashboard projections and real metric
  formatting, records search/filter/detail navigation, persisted chat and
  typed handoff rendering, summary-to-booking continuity, booking validation
  and success/error behavior, BOOKED-facing appointment listing, and New
  Consultation behavior; all frontend tests passed.
- Headless Chrome desktop smoke captures confirmed the shared shell and
  loading/error states at 1440x1000 for `/dashboard`, `/consultations`,
  `/consultations/new`, and `/appointments`. The API was unavailable during
  this smoke run, so populated runtime records were not fabricated.
- Feature 008 focused rerun: **21 passed, 5 failed** in
  `tests/application/test_booking_handoff_workflow.py` plus
  `tests/application/test_booking_handoff.py`. The five failures are all
  classification **B — pre-existing Feature 008 implementation defects**, not
  Feature 009 regressions:
  - the two pending-lifecycle cases produce no typed handoff because
    `ConsultationApplicationService.submit_message` never invokes booking
    intent evaluation or persists application-owned handoff markers;
  - the provider action-like payload case has the same missing workflow
    integration, so no authoritative handoff is produced; and
  - the two closed-lifecycle cases call the expected
    `_evaluate_booking_handoff` seam, but that method is absent from the
    current Feature 008 implementation.
  The Feature 008 commit contains the classifier, marker helper, and these
  tests, but does not integrate the workflow into `consultation_service.py`.
  No Feature 009 change touches that path. Fixing it would be Feature 008
  implementation work, so no fix was made during VA-013. The deterministic
  authority remains unchanged: only Feature 004 may create appointments.
- Full backend suite result: **367 passed, 5 failed, 92 errors**. The same
  five Feature 008 failures are described above. The 92 errors are confirmed
  PostgreSQL-backed fixture setup failures: `tests/conftest.py` invokes
  `docker run ... postgres:16-alpine`, and the actual Docker error is
  `permission denied while trying to connect to the Docker API at
  unix:///var/run/docker.sock`. These are environment-blocked verification,
  not product failures. PostgreSQL was not replaced with SQLite and no
  product workaround was added. Preserve this evidence for VA-014.
- Migration verification: `.venv/bin/alembic heads` reports
  `20260817_04 (head)`; no migration was added.

## Checks

- `cd frontend && npm test -- --run --testTimeout=15000` — PASS (318 tests;
  14 files). The default 5-second timeout caused three booking-screen timeout
  failures under the full suite; the affected file passed **22/22** with the
  same assertions and the timeout override. No test or product code was
  changed to obtain the pass.
- `cd frontend && npm run typecheck` — PASS.
- `cd frontend && npm run lint` — PASS.
- `cd frontend && npm run build` — PASS; Vite emitted only its existing chunk
  size advisory.
- `docker compose -f compose.yaml config --quiet` — PASS.
- `cd backend && .venv/bin/pytest -q tests` — **367 passed, 5 failed, 92
  errors**, as dispositioned above.
- `cd backend && .venv/bin/alembic heads` — PASS.
- `git diff --check` — PASS.

## Scope and handoff

No narrow fixes were made. No commit was created. VA-014 is **not unblocked**
because the Feature 008 handoff implementation defects remain unresolved and
PostgreSQL integration still requires Docker API access. VA-014 was not
started. The VA-013 checkbox is complete.
