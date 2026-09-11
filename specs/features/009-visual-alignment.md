# Feature 009 — Visual Alignment and Dashboard Enhancements

**Status:** Proposed — specification only

## 1. Purpose

Define the visual-alignment and Dashboard enhancement work for the AI
Consultation Platform. The feature brings the existing Features 001–008 into
one coherent visual system and adds real, read-only Dashboard projections for
consultation trends, recent activity, and pending clinical reviews.

The existing functional flow remains authoritative:

```text
New Consultation → Persistent AI Chat → Summary → Appointment Booking
        ↓                 ↓                ↓              ↓
   PENDING          persisted chat     COMPLETED       BOOKED
        └────────────── Records / Dashboard read projections ──────────────┘
```

This feature is presentation-led. It must not replace working behavior with
data copied from screenshots, and it must not weaken the deterministic booking
or Feature 008 handoff workflow.

## 2. Authoritative sources and visual rules

The supplied reference mapping is:

| Reference | Screen | File |
| --- | --- | --- |
| Screen 1 | Dashboard | `docs/visual-references/dashboard.png` |
| Screen 2 | Consultation Detail / AI Chat | `docs/visual-references/consultation-chat.png` |
| Screen 3 | Consultation Summary / Recommendations | `docs/visual-references/consultation-summary.png` |
| Screen 4 | Appointment Booking | `docs/visual-references/appointment-booking.png` |
| Screen 5 | Consultation Records | `docs/visual-references/consultation-records.png` |

The references control presentation: geometry, hierarchy, spacing, controls,
cards, tables, colors, borders, radii, shadows, and responsive composition.
Features 001–008 and the original assignment control functionality, data,
state, persistence, API authority, and error behavior.

The following screenshot-only identities and features are not product
requirements: Patients, AI Insights, Archive, Support, Sign Out, admin
profiles, Invite Patient, Generate Report, Monthly Revenue, fake statistics,
fake clinical facts, fake costs, provider selection, availability, draft
appointments, pagination, and fabricated activity.

## 3. Scope

The feature shall provide:

- one consistent responsive application shell;
- close visual alignment of the five supplied screens;
- Dashboard metrics for Total Consultations, Booked Appointments, and
  Conversion Rate;
- a real-data Consultation Trends projection;
- a real-data Recent Activity projection;
- a Pending Clinical Reviews projection over existing `PENDING` consultations;
- preservation of all existing consultation, summary, booking, records,
  appointments, and Feature 008 handoff actions; and
- screen-by-screen visual verification and regression coverage.

Backend changes are limited to extending the existing Dashboard read model/API
when required for these projections. No new write workflow is part of this
feature.

## 4. Shared application shell

Use the existing `AppLayout` as the composition boundary and retain its real
routes: Dashboard, Consultations, Appointments, and `+ New Consult`.

The aligned shell shall define:

- a desktop left sidebar approximately 264px wide, with a branded header,
  `+ New Consult`, supported navigation, active route state, and a lower utility
  area only for supported items;
- a light page background, a consistent content offset, responsive gutters,
  and a bounded content width suitable for the supplied desktop proportions;
- a mobile top bar and drawer navigation using the existing mobile behavior;
- consistent page heading and subtitle conventions;
- a restrained typography hierarchy for page headings, section headings,
  labels, values, helper text, and body copy;
- one card treatment for white surfaces, subtle borders, modest radius, and
  restrained shadow; and
- shared styles for primary/secondary buttons, inputs, status chips, focus
  rings, and disabled/loading states.

Existing navigation must remain reachable. Unsupported screenshot navigation
must not be added merely to make the sidebar look fuller.

## 5. Dashboard requirements

The Dashboard retains the current API-backed metrics and presents the three
required metric cards:

- Total Consultations;
- Booked Appointments; and
- Conversion Rate, calculated from the authoritative metrics and displayed
  without inventing comparative percentages.

### 5.1 Consultation Trends

Add a responsive chart or equivalent trend visualization showing daily counts
for a bounded rolling 30-calendar-day range, with the range and bucket labels
clearly stated. Values must come from a Dashboard API read projection and must
not be hardcoded in React or copied from the reference.

Because `consultations` currently has no `created_at`, the projection may use
the earliest authoritative timestamp available for each consultation from its
persisted message, summary, or appointment lineage. A consultation with no
authoritative timestamp must not be assigned a synthetic date; the backend
must either omit it from the time-bucketed series or expose an explicit
incomplete-data condition. This limitation and the chosen query rule must be
documented in the implementation plan.

The chart needs loading, API-error, no-data, and responsive states. An empty
series must say that there is no trend data yet, not display zeroes that imply
recorded activity.

### 5.2 Recent Activity

Add a recent-activity list derived from existing authoritative timestamps and
state. Supported activity types are limited to meaningful existing events,
such as:

- a consultation conversation started, based on its first persisted message;
- a consultation completed, based on persisted summary creation; and
- an appointment booked, based on persisted appointment creation.

Each item must identify the real consultation where the existing contract
supports it, include a real timestamp, and link only to an existing supported
destination. The list is a read projection, not an event log. It must not add
an activity table, audit subsystem, event bus, or migration.

The projection should return a bounded recent set in descending timestamp
order. Items without an authoritative timestamp are excluded rather than
given relative-time text from fabricated data.

### 5.3 Pending Clinical Reviews

Display this label as a presentation of existing pending work. The source is
the current `PENDING` consultation records, not a new review entity or status.
Each displayed item must link to its consultation detail route and use only
existing patient, concern, procedure, and status data. Empty, loading, and
error states are required.

No clinical review workflow, approval action, new status, or migration may be
introduced.

## 6. Consultation Detail / AI Chat

Align the existing detail screen with Screen 2 while preserving:

- persisted chronological multi-message history;
- context-aware AI responses and structured payload rendering;
- loading and recoverable error behavior;
- conversation-closed behavior for `COMPLETED` and `BOOKED` consultations;
- summary eligibility and the existing summary operation; and
- Feature 008 typed booking handoff metadata and state-specific CTA behavior.

The visual target includes a patient/consultation header, conversation canvas,
distinct user and assistant alignment, constrained message widths, assistant
cards, structured response presentation, a scrollable message area, and a
composer anchored below the conversation. Feature 008 CTAs must be visually
consistent with the shared button system and must be rendered from validated
typed metadata, never from assistant prose.

Do not add microphone, attachment, upload, patient-photo, or other unsupported
controls because they appear in the reference.

## 7. Consultation Summary / Recommendations

Align the existing summary screen with Screen 3 while preserving its
authoritative persisted summary and recommendations, including:

- Patient Summary;
- optional recommendation rationale only when supplied by the API;
- ordered recommendation selection using persisted recommendation IDs;
- `Book Appointment`; and
- `Restart Consultation`.

The layout should use a prominent summary card, recommendation cards or an
equivalent selectable treatment presentation, clear selected/priority state,
and a distinct next-steps action area. The visual design may use headings such
as AI Insight or Recommended Treatments only where the underlying API data
supports the content.

Do not fabricate confidence, history, reasoning, prices, durations, treatment
metadata, or clinical claims. Booking continues to navigate to the existing
form and does not create an appointment from the summary screen.

## 8. Appointment Booking

Align the existing booking screen with Screen 4 while preserving Feature 004
as the only appointment write path. The screen must retain:

- selected persisted treatment;
- date/time and location inputs;
- client-side validation and clear validation errors;
- authoritative backend validation;
- atomic appointment persistence and `COMPLETED` → `BOOKED` transition;
- duplicate/concurrent-book protection; and
- approved post-booking navigation.

Use a desktop two-column composition with procedure/form cards and a summary
card, stacking safely on smaller screens. Match the reference's heading,
back-navigation treatment, field sizing, labels, primary confirmation action,
spacing, and surface hierarchy without adding target area, duration, provider,
estimated cost, clinic management, Save as Draft, or availability behavior.

## 9. Consultation Records

Align the existing records screen with Screen 5 while preserving API-backed
search, status filtering, and record-to-detail navigation. Retain the required
fields: Patient Name, Primary Concern, Recommended Procedure, and Status.

Use the shared heading/subtitle, search control, status filter pills or
equivalent accessible controls, bordered table/card container, readable row
height, separators, initials/avatar treatment derived from the actual patient
name, and status chips whose labels remain `PENDING`, `COMPLETED`, or `BOOKED`.

Date may be shown only when an authoritative timestamp is available through
the existing contract or an approved read projection. Do not invent dates,
records, procedures, counts, pagination, sorting, or patient identities.
On narrow screens, use a safe responsive list/card treatment or horizontal
scrolling that does not cause page-wide overflow.

## 10. New Consultation and Appointments

New Consultation has no supplied reference. Retain all Feature 006 behavior and
apply the shared shell, typography, card, form, spacing, validation, and
responsive rules.

Appointments has no supplied reference. Retain all Feature 007 behavior and
derive its presentation primarily from the aligned records table/list. It must
remain a real API-backed read of persisted appointments and must not gain
editing, cancellation, rescheduling, or synthetic rows.

## 11. Backend and API/read-model requirements

Extend the existing Dashboard application service, repository, DTO, and
frontend service boundaries as needed; do not query SQLAlchemy directly from
Flask routes and do not create unrelated endpoints. The Dashboard response
may contain the existing metrics plus typed projection fields for trends,
activity, and pending consultations. Runtime validation must reject malformed
or extra data according to the established API conventions.

All projections must use PostgreSQL-backed rows and request-scoped
composition. Read operations must not mutate, commit, or create domain data.
The existing consultation and appointment repositories/services remain the
authorities for their respective flows.

## 12. Data, state, and persistence rules

No screenshot value is domain data. No browser state, local storage, mock
records, or hardcoded chart/activity values may be authoritative.

Pending reviews are a projection of `ConsultationStatus.PENDING`. Recent
activity is a projection of existing message, summary, and appointment
timestamps. Trends are a projection of real consultation lineage timestamps
under the rule in §5.1. The three status values remain exactly `PENDING`,
`COMPLETED`, and `BOOKED`.

### Migration decision

The preferred implementation requires **no migration**. Existing tables
already provide message, summary, and appointment timestamps and all required
Dashboard domain rows. The current lack of a consultation creation timestamp
is a real limitation that must be handled in the read projection, not silently
filled with a fabricated value. If implementation proves that the requested
projection cannot meet its contract without adding `consultations.created_at`,
the conflict must be documented and brought back as a separate approved
schema decision; Feature 009 does not authorize that migration automatically.

## 13. Loading, empty, error, and validation states

Every aligned screen must preserve or add clear states for loading, API
failure, retry, empty data, unavailable/incomplete consultation, closed
conversation, summary unavailable, no recommendations, invalid booking input,
booking conflict, and successful booking. States must retain the page's visual
structure and must not be replaced by static screenshot content.

## 14. Responsive and accessibility requirements

The desktop sidebar becomes the existing mobile drawer/navigation. Content
gutters remain usable at narrow widths; cards and booking columns stack; chat
composer controls remain visible and usable; tables are horizontally safe or
converted to accessible records; and no CTA or page content is clipped.

Use semantic headings, labelled form controls, keyboard-operable navigation and
actions, visible focus states, meaningful status text in addition to color,
reasonable contrast, accessible chart summaries or tabular equivalents, and
proper table/list semantics. Loading and error announcements must be
discoverable by assistive technology.

## 15. Testing requirements

Add or update deterministic tests for:

- shell geometry contracts, supported navigation, active state, and mobile
  navigation;
- Dashboard metrics and exact conversion-rate behavior;
- trend projection grouping, timestamp authority, no-data, malformed-data,
  loading, and error behavior;
- recent-activity ordering, supported event derivation, links, and empty state;
- pending-review projection from only `PENDING` consultations;
- records search/filter/navigation and responsive presentation;
- persisted chat rendering, composer behavior, structured output, and closed
  states;
- Feature 008 typed handoff CTA rendering and activation;
- summary persistence display, selection, restart, and booking navigation;
- booking validation, API failure/conflict, confirmation, and post-booking
  state;
- New Consultation and Appointments regressions; and
- accessibility-relevant labels, roles, keyboard actions, and focus behavior
  where practical.

Backend tests must cover repository/service/API projections, read-only
behavior, request-scoped composition, exact DTO validation, and safe 500/error
responses. Frontend tests must use service fakes or mocked transports and must
not depend on live OpenAI or screenshot data.

## 16. Visual verification and acceptance criteria

Verification must compare each supplied screen against the implementation for
page geometry, sidebar, content position and width, major card/table/form
placement, whitespace, typography hierarchy, control sizing,
border/radius/shadow treatment, status styling, and responsive behavior.
Structural/layout similarity has priority over matching screenshot text or
identities.

The feature is accepted only when:

- all five reference screens are visually aligned without unsupported
  screenshot-only functionality;
- Dashboard enhancements show only real persisted projections;
- the existing end-to-end flow from new consultation through booked
  appointment remains functional and authoritative;
- Feature 008 handoffs remain typed, safe, reloadable, and downstream-validated;
- no fake domain data, migration, activity subsystem, or new unsupported
  status is introduced; and
- the complete regression suite for Features 001–008 passes, with relevant
  frontend lint/type checks and backend tests run before implementation is
  declared complete.

## Implementation Tasks

- [x] VA-001 — Confirm Feature 009 Integration and Visual Boundaries
- [x] VA-002 — Add Dashboard Read Projections
- [x] VA-003 — Extend Dashboard Application and API Contract
- [x] VA-004 — Extend Frontend Dashboard Types and Runtime Validation
- [x] VA-005 — Align Shared Application Shell and Visual Primitives
- [x] VA-006 — Align Dashboard Screen and Enhancements
- [x] VA-007 — Align Consultation Detail and AI Chat
- [x] VA-008 — Align Consultation Summary and Recommendations
- [x] VA-009 — Align Appointment Booking Screen
- [x] VA-010 — Align Consultation Records Screen
- [x] VA-011 — Align New Consultation and Appointments Screens
- [x] VA-012 — Complete Responsive and Accessibility Alignment
- [x] VA-013 — Run Screen-by-Screen Visual Verification
- [x] VA-014 — Verify Feature 009 Final Vertical Slice
