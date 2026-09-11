# VA-001 Findings — Feature 009 Integration and Visual Boundaries

## Result

VA-001 inspection is complete. No product code was changed. The repository
contains the current root Compose definition at `compose.yaml`, and
`docker compose -f compose.yaml config --quiet` passes. The `alembic`
executable is unavailable in the current environment, so the migration chain
was verified directly from the revision files as permitted by the task.

## Reference mapping and current visual deviations

| Reference | Application screen and boundary | Major current deviations |
| --- | --- | --- |
| `dashboard.png` | `DashboardScreen` at `/dashboard` | Current screen has only a heading and three metric cards. It lacks the trends visualization, recent activity, pending-review projection, range/status states, and reference-like page hierarchy. It currently uses lowercase metric labels and no subtitle/card visual system. Reference-only revenue, comparative deltas, report, invite, and unsupported navigation are intentionally excluded. |
| `consultation-chat.png` | `ConsultationDetailScreen` plus `ConsultationConversation` at `/consultations/:consultationId` | Existing screen is functional but not reference-composed: no reference patient header geometry, bounded conversation canvas styling, aligned message bubbles/assistant surface, or reference composer treatment. Existing structured payloads, persisted history, loading/errors, closed states, summary action, and Feature 008 handoff remain authoritative. Reference microphone/attachment/photo controls are unsupported and must not be added. |
| `consultation-summary.png` | `ConsultationSummaryScreen` at `/consultations/:consultationId/summary` | Existing summary is API-backed but does not yet match the reference’s summary/recommendation card composition, selected/priority treatment, or next-steps action area. Reference confidence, history, pricing, and clinical claims are unsupported unless supplied by the API. |
| `appointment-booking.png` | `AppointmentBookingScreen` at `/consultations/:consultationId/appointments/new` | Existing booking is functional but lacks the reference two-column procedure/logistics/summary composition and shared visual treatment. Only persisted treatment, date/time, and location are supported; reference provider, target area, duration, cost, draft, and availability controls are explicitly out of scope. |
| `consultation-records.png` | `ConsultationRecordsScreen` plus `ConsultationRecordsTable` at `/consultations` | Existing records table has the required API-backed fields, search/status behavior, and detail navigation, but lacks the reference heading/subtitle, search/filter presentation, initials/avatar treatment, status chips, date projection, bordered visual hierarchy, and narrow-screen safe presentation. Reference pagination, totals, sorting, and fabricated dates/identities are unsupported. |

New Consultation is `NewConsultationScreen` at `/consultations/new`; it has no
supplied reference and inherits shared form/card alignment. Appointments is
`AppointmentsScreen` at `/appointments`; it is a real API-backed read and
inherits the records list/table language. Neither may gain screenshot-only
workflows.

## Shared shell, theme, and visual primitives

- `frontend/src/app/layout/AppLayout.tsx` owns the shell, desktop 264px
  permanent sidebar, mobile temporary drawer, mobile top `AppBar`, supported
  navigation, active-route state, `+ New Consult`, page background, content
  gutters, and max-width (`1280`).
- Supported routes are Dashboard, Consultations, Appointments, and New
  Consultation. `frontend/src/app/core/App.tsx` owns the route boundaries.
- There is no centralized `createTheme`, `ThemeProvider`, or shared visual
  primitive module. MUI defaults and per-component `sx` styles currently own
  typography, cards, buttons, inputs, and status presentation. `AppLayout`
  contains shell-local colors, selected navigation styling, and drawer sizes.
- `AppLayout.test.tsx` verifies supported links, active route behavior, and
  mobile drawer navigation. Existing behavior already closes the drawer after
  navigation.

## Dashboard seams and projection strategy

Current seam:

`backend/app/repositories/dashboard_repository.py` →
`DashboardRepository.get_counts()` →
`backend/app/application/dashboard_service.py` →
`DashboardApplicationService.get_metrics()` →
`backend/app/api/dashboard_dtos.py:DashboardResponse` →
`backend/app/api/dashboard_routes.py:get_dashboard()` →
`frontend/src/app/features/dashboard/dashboardApi.ts:createDashboardApi().getMetrics()` →
`frontend/src/app/features/dashboard/DashboardScreen.tsx`.

Composition is request-scoped in `backend/app/__init__.py`: a SQLAlchemy
`Session` is opened per request and injected into `DashboardRepository`, then
closed during teardown. Routes do not query SQLAlchemy directly.

Recommended later extension is one enriched Dashboard read contract through
these existing seams, retaining the three current metrics and adding typed
trend, activity, and pending-review fields. Do not add separate endpoints
unless a later approved specification requires them.

### Authoritative timestamps

`Consultation` has no `created_at`. Available persisted sources are:

- first `Message.created_at` in `messages`, ordered by
  `consultation_id`, `created_at`, `id`;
- `ConsultationSummary.created_at` in `consultation_summaries`;
- `Appointment.created_at` in `appointments`.

For trends, use the minimum available timestamp across that consultation’s
message/summary/appointment lineage; omit consultations with no timestamp.
For recent activity, project only first-message conversation-started, summary-
created completed, and appointment-created booked items, each with its real
timestamp, descending order, bounded and deterministically tie-broken. No
activity table, audit subsystem, event bus, synthetic date, or migration is
needed for the approved strategy.

### Pending clinical reviews

Project `Consultation` rows where `status == ConsultationStatus.PENDING` from
`backend/app/infrastructure/consultation_models.py`. Use existing patient name,
primary concern, recommended procedure, status, and consultation ID; link to
`/consultations/:consultationId`. This is not a `ClinicalReview` entity,
workflow, action, or new status.

## Screen/component and API boundaries

- Chat: `ConsultationDetailScreen` loads detail, summary eligibility, summary
  generation, and handoff state; `ConsultationConversation` owns message
  history, structured payload rendering, composer, submission, and closed/error
  behavior. `consultationApi.ts` and `consultationTypes.ts` own transport and
  types.
- Summary: `ConsultationSummaryScreen` owns summary loading, persisted
  recommendation selection, restart, and booking navigation through
  `consultationApi.ts`.
- Booking: `AppointmentBookingScreen` owns summary loading, client validation,
  booking submission, conflict/error states, and post-book navigation. The
  backend authority is the appointment repository/application workflow already
  covered by Feature 004.
- Records: `ConsultationRecordsScreen` owns search/status loading and routing;
  `ConsultationRecordsTable` owns tabular rendering. `consultationApi.ts` and
  `consultationTypes.ts` are the read contract.
- New Consultation: `NewConsultationScreen` and its
  `NewConsultationService` boundary call the existing consultation creation
  API and navigate to the detail route.
- Appointments: `AppointmentsScreen`, `appointmentApi.ts`, and
  `appointmentTypes.ts` own the read-only appointments list and consultation
  links; no edit/cancel/reschedule boundary exists.

Feature 008 handoff metadata is already typed through the consultation API /
types and consumed by the detail/conversation boundary; later visual work must
not infer CTAs from assistant prose.

## Tests, commands, and migration

Relevant backend coverage includes `tests/test_dashboard_repository.py`,
`tests/test_dashboard_composition.py`, `tests/application/test_dashboard_service.py`,
`tests/api/test_dashboard_routes.py`, and
`tests/api/test_dashboard_persistence_api.py`, plus consultation/message/
summary/appointment repository and API regressions.

Relevant frontend coverage includes `DashboardScreen.test.tsx`,
`dashboardApi.test.ts`, `AppLayout.test.tsx`, all target screen tests,
`consultationApi.test.ts`, and `appointmentApi.test.ts`.

Documented commands are `cd backend && pytest -q tests`, `cd frontend && npm
test`, `npm run typecheck`, `npm run lint`, `npm run build`, and root
`docker compose up --build`. The current project Compose definition is
`compose.yaml` at the repository root. It defines the `postgres`, `backend`,
and `frontend` services, with PostgreSQL 16, backend/frontend builds, health-
checked database dependency, ports, bind mounts, and named volumes.
`docker compose -f compose.yaml config --quiet` exited 0. Relevant Docker
commands remain `docker compose config --quiet`, `docker compose build`, and
`docker compose up --build`; full build/start was intentionally not required
for this read-only VA-001 check. Backend README documents `alembic upgrade
head`. `cd backend && alembic heads` cannot run because `alembic` is not
available in the current environment; direct revision-chain inspection is
acceptable and shows a single linear head:
`20260817_04` (`20260817_04_create_appointments.py`). No Feature 009
migration is planned or indicated by the current data model.

## Ownership and concurrency map

| Later task | Primary ownership | Safe parallelism after VA-001 |
| --- | --- | --- |
| VA-002 | `dashboard_repository.py` and repository tests | Parallel with VA-005 and screen-only alignment tasks; precedes VA-003. |
| VA-003 | dashboard application service, DTO, route, backend tests | After VA-002; parallel with VA-005. |
| VA-004 | dashboard frontend types/API and tests | After VA-003; parallel with VA-005. |
| VA-005 | `AppLayout.tsx` and new/shared frontend visual primitives | Parallel with VA-002/003/004; high conflict risk with every screen task. |
| VA-006 | `DashboardScreen.tsx` and dashboard tests | After VA-004 and VA-005. |
| VA-007–VA-011 | respective screen files/tests | Can run in parallel with one another after VA-005, but must avoid editing `AppLayout`, shared primitives, or shared API/type files concurrently. VA-006 additionally waits for VA-004. |
| VA-012 | responsive/accessibility cross-screen tests and fixes | After VA-005 and target screen tasks; likely conflicts with all screen files. |
| VA-013–VA-014 | verification only | After all implementation tasks. |

Highest-risk shared files are `AppLayout.tsx`, `App.tsx`, `consultationApi.ts`,
`consultationTypes.ts`, shared MUI/theme/primitives if introduced, and shared
screen test setup. Keep Dashboard backend changes isolated from consultation
repositories and keep visual tasks from changing API contracts.

## Architecture guard confirmation

- No migration: consistent with current schema and plan.
- No fake/hardcoded Dashboard data: required; current Dashboard contains none.
- No activity/audit subsystem: required; use read projection only.
- No ClinicalReview entity/workflow: required; use pending consultations.
- No new consultation status: required; retain `PENDING`, `COMPLETED`, `BOOKED`.
- No unsupported screenshot functionality: required; reference-only controls and
  identities are explicitly excluded.

## Blockers and tracker

Compose validation is complete. The Alembic CLI is unavailable, but direct
inspection confirms migration head `20260817_04`, and no Feature 009 migration
is required. The repository uses
`plans/features/009-visual-alignment-plan.md` as the existing Feature 009 plan
path; the requested unsuffixed `plans/features/009-visual-alignment.md` path
does not exist. VA-001 acceptance is otherwise satisfied and its tracker entry
is marked complete. Later task checkboxes remain unchanged.
