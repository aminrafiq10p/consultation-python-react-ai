# Feature 009 — Visual Alignment and Dashboard Enhancements Implementation Plan

## 1. Objective

Implement the final product feature by aligning the completed application with the five approved reference screens while preserving all Features 001–008 behavior and adding three real, read-only Dashboard projections:

- Consultation Trends
- Recent Activity
- Pending Clinical Reviews

Visual references are authoritative for presentation. Existing implemented features and the assignment remain authoritative for functionality, data, state, persistence, API behavior, and errors.

## 2. Architecture Decisions

### 2.1 Feature shape

Feature 009 is presentation-led and frontend-heavy. Backend changes are limited to extending the existing Dashboard read path for real persisted projections. No new write workflow is introduced.

### 2.2 No migration

No migration is planned.

The current lack of `Consultation.created_at` must be handled explicitly:
- use the earliest authoritative persisted timestamp available from message/summary/appointment lineage;
- exclude consultations from trend buckets when no authoritative timestamp exists;
- never assign synthetic dates.

If the contract cannot be met safely without schema change, stop and report the conflict rather than silently adding a migration.

### 2.3 Dashboard API strategy

Prefer extending the existing Dashboard repository/application/DTO/API/frontend-service contract rather than creating separate endpoints.

The enriched response should retain the existing metrics and add typed projections for:
- consultation trends;
- recent activity;
- pending clinical reviews.

All projections are read-only and PostgreSQL-backed.

### 2.4 Shared visual system

Use the existing `AppLayout` and MUI stack. Consolidate only the minimal shared visual primitives required for consistency:
- page container/gutters;
- page headings/subtitles;
- card/surface treatment;
- buttons;
- inputs;
- status chips;
- responsive content widths.

Do not create a second design system.

### 2.5 Visual authority

Reference mapping:

1. Dashboard → `docs/visual-references/dashboard.png`
2. Consultation Detail / AI Chat → `docs/visual-references/consultation-chat.png`
3. Consultation Summary / Recommendations → `docs/visual-references/consultation-summary.png`
4. Appointment Booking → `docs/visual-references/appointment-booking.png`
5. Consultation Records → `docs/visual-references/consultation-records.png`

Screens 2–5 are close-match targets. New Consultation and Appointments inherit the same visual language.

## 3. Dashboard Read Projections

### 3.1 Consultation Trends

Use a rolling 30-calendar-day daily series.

For each consultation, determine the earliest authoritative persisted timestamp from available lineage:
- first persisted message timestamp;
- persisted summary timestamp;
- persisted appointment timestamp.

Do not invent dates.

Return bounded daily buckets with deterministic ordering.

The frontend must distinguish loading, populated, no-data, and error states.

### 3.2 Recent Activity

Create a read projection from supported persisted events only:
- consultation conversation started → first message timestamp;
- consultation completed → summary creation timestamp;
- appointment booked → appointment creation timestamp.

Return a bounded recent set ordered descending by timestamp with deterministic tie-breaking.

No activity table, audit system, event bus, or migration.

### 3.3 Pending Clinical Reviews

Project current `PENDING` consultations only.

Return existing persisted fields needed for display and link each item to the existing consultation detail route.

This is presentation/read projection only, not a clinical-review workflow.

## 4. Implementation Stages

### Stage 1 — Confirm integration and visual boundaries

Inspect the five references, Dashboard backend/frontend seams, `AppLayout`, all target screens, theme/shared components, regression tests, migration head, and Docker commands.

Record:
- exact file-level change map;
- visual deviations by screen;
- Dashboard projection seams;
- timestamp sources;
- shared-file concurrency risks.

No product changes.

### Stage 2 — Extend Dashboard repository projections

Add deterministic read-only repository projections for:
- trends;
- recent activity;
- pending clinical reviews.

Requirements:
- no commit/mutation;
- no N+1;
- no synthetic timestamps;
- stable ordering;
- bounded results;
- request-scoped Session;
- no migration.

Add focused repository tests.

### Stage 3 — Extend Dashboard application/DTO/API

Extend the existing Dashboard service and response DTO with typed projections.

Preserve existing metric semantics exactly.

Add application/API tests for populated/empty projections, validation, and safe failures.

### Stage 4 — Extend frontend Dashboard service/runtime validation

Extend the existing Dashboard frontend types/service.

Runtime-validate metrics, trend buckets, activity items, and pending review items.

No frontend-derived authoritative values.

Add deterministic service tests.

### Stage 5 — Align shared shell and visual primitives

Align:
- desktop sidebar;
- brand/header;
- `+ New Consult`;
- Dashboard / Consultations / Appointments navigation;
- active state;
- content gutters/max-width;
- page background;
- headings;
- cards;
- buttons;
- inputs;
- status chips;
- mobile drawer/top bar;
- focus/disabled/loading styling.

Do not add unsupported screenshot navigation.

### Stage 6 — Align Dashboard

Match the Dashboard reference using real data:
- Total Consultations;
- Booked Appointments;
- Conversion Rate;
- Consultation Trends;
- Recent Activity;
- Pending Clinical Reviews.

Do not add Monthly Revenue, fake percentages, hardcoded activity, Invite Patient, or Generate Report.

### Stage 7 — Align Consultation Detail / AI Chat

Close-match Screen 2 while preserving:
- persistent chat;
- structured payloads;
- Feature 008 handoff CTA;
- summary eligibility;
- closed states;
- loading/errors.

Align conversation geometry, message styling, assistant cards, composer, scrolling, and CTA styling.

### Stage 8 — Align Consultation Summary / Recommendations

Close-match Screen 3.

Preserve persisted summary/recommendations, selection, Restart Consultation, and Book Appointment.

Do not fabricate cost, confidence, history, or clinical facts.

### Stage 9 — Align Appointment Booking

Close-match Screen 4.

Preserve Feature 004 semantics and only supported fields:
- selected treatment;
- date/time;
- location.

Align two-column desktop composition, summary card, field treatment, CTA, and responsive stacking.

Do not add provider/target-area/duration/cost/draft/availability workflows.

### Stage 10 — Align Consultation Records

Close-match Screen 5.

Preserve search, filters, required fields, and record-to-detail navigation.

Align heading, search/filter controls, table/card surface, row sizing, initials/avatar treatment, status chips, and responsive presentation.

Do not fabricate dates, pagination, counts, sorting, or records.

### Stage 11 — Align New Consultation and Appointments

New Consultation inherits form/card language from Booking.

Appointments inherits table/list language from Consultation Records.

No new functionality.

### Stage 12 — Responsive and accessibility pass

Verify:
- desktop sidebar/mobile drawer;
- usable gutters;
- stacked booking layout;
- safe records/appointments presentation;
- usable chat composer;
- no clipped Feature 008 CTA;
- semantic headings;
- labels;
- keyboard actions;
- focus states;
- accessible chart summary;
- loading/error announcements.

### Stage 13 — Screen-by-screen visual verification

Compare all five references for:
- page geometry;
- sidebar;
- content position/width;
- major component placement;
- spacing;
- typography;
- control sizing;
- border/radius/shadow treatment;
- status/button styling;
- responsive composition.

Document intentional deviations caused by unsupported functionality.

### Stage 14 — Final vertical-slice verification

Run focused/full backend and frontend tests, typecheck, lint, build, PostgreSQL integration, migration-head verification, Docker Compose checks, Features 001–008 regressions, visual comparison, and git diff checks.

Manual flow:

```text
Dashboard
→ New Consultation
→ AI Chat
→ Feature 008 handoff
→ Summary / Recommendations
→ Appointment Booking
→ Consultation Records
→ Appointments
→ Dashboard
```

Stop after Feature 009.

## 5. Dependency Order

```text
VA-001 Integration boundaries
        ↓
        ├── VA-002 Dashboard repository projections
        │       ↓
        │   VA-003 Dashboard application/API
        │       ↓
        │   VA-004 Frontend Dashboard service
        │       ↓
        │   VA-006 Dashboard screen alignment
        │
        └── VA-005 Shared shell / visual primitives
                ↓
        ┌───────┼────────┬────────┬────────┐
        ↓       ↓        ↓        ↓        ↓
     VA-007  VA-008   VA-009   VA-010   VA-011
      Chat    Summary   Booking   Records   Derived screens
        └───────┴────────┴────────┴────────┘
                        ↓
                    VA-012
              Responsive/accessibility
                        ↓
                    VA-013
               Visual verification
                        ↓
                    VA-014
             Final vertical-slice verification
```

## 6. Safe Parallelization

After VA-001:
- Dashboard backend work and shared-shell work can proceed in parallel.
- After the Dashboard API contract is stable, frontend Dashboard service can proceed.
- After shared visual primitives stabilize, Chat, Summary, Booking, Records, and derived-screen alignment may proceed in parallel if each task owns separate screen files.
- Do not parallel-edit AppLayout/theme/shared primitive files without one owner.
- Responsive/accessibility and final visual verification happen after screen convergence.

## 7. Testing Strategy

Backend:
- existing metrics unchanged;
- trend bucketing and timestamp authority;
- recent activity derivation/ordering;
- pending-only review projection;
- read-only behavior;
- DTO/API serialization and safe errors.

Frontend:
- Dashboard service validation;
- shell/navigation;
- Dashboard states;
- chat and Feature 008 CTA;
- summary actions;
- booking;
- records filters/search/navigation;
- New Consultation/Appointments regressions;
- responsive/accessibility-critical behavior.

Visual:
- compare structure and layout against the five references;
- avoid brittle pixel snapshots unless the repo already uses visual regression tooling.

## 8. Migration Decision

No migration.

No `Consultation.created_at`, activity table, review table, or new status is authorized.

If trend requirements cannot be met safely, stop and request a separate schema decision.

## 9. Explicit Exclusions

Do not add:
- Patients;
- AI Insights;
- Archive;
- Support;
- Sign Out/authentication;
- admin profile;
- Invite Patient;
- Generate Report;
- Monthly Revenue;
- fake trend deltas;
- hardcoded activity;
- provider selection;
- availability;
- draft appointments;
- fake costs;
- fake pagination;
- fake clinical data.

## 10. Definition of Done

Feature 009 is complete when all five reference screens are structurally aligned, Screens 2–5 are close-match implementations, Dashboard shows only real persisted projections, Features 001–008 remain intact, Feature 008 handoffs remain functional, no unsupported domain workflow or migration is introduced, responsive/accessibility requirements pass, and all backend/frontend/build/PostgreSQL/Docker checks pass.
