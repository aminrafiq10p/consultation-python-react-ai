# Feature 007 — Appointments Task Tracker

Authoritative inputs: `specs/features/007-appointments.md` and
`plans/features/007-appointments.md`. This tracker is a task-generation
artifact; it does not authorize implementation outside the listed tasks.

## Dependency graph

```text
AP-001 boundary confirmation
  ├── AP-002 joined repository read ──> AP-003 application operation ──> AP-004 API/DTO
  │                                      └──────────────────────────────> AP-005 composition
  │                                                                      └──> AP-006 backend tests
  │                                                                            └──> AP-007 booking→list PostgreSQL
  │                                                                                  └──> AP-008 Dashboard consistency
  └── AP-009 frontend types/service ──> AP-010 screen + route ──> AP-011 responsive presentation + consultation link
                                                                    └──> AP-012 shared navigation

AP-007 + AP-008 + AP-012 ──> AP-013 Features 001–006 regression
AP-013 + AP-009..AP-012 ──> AP-014 no-AI/no-migration/Docker/scope checks
AP-014 + all implementation/test tasks ──> AP-015 final vertical slice
```

## Task index

| ID | Title | Depends on | Safe parallelization | Status |
| --- | --- | --- | --- | --- |
| AP-001 | Confirm integration boundaries and test seams | Approved spec/plan | Initial gate; read-only | Complete |
| AP-002 | Add joined AppointmentRepository list read | AP-001 | Parallel with AP-009 | Complete |
| AP-003 | Add application appointment-list operation | AP-002 | Sequential backend | Complete |
| AP-004 | Add list DTOs and GET API contract | AP-003 | Sequential backend; API contract unblocks live integration | Complete |
| AP-005 | Verify request-scoped composition | AP-002–AP-004 | After backend path; owns composition tests | Complete |
| AP-006 | Complete backend unit/API/read tests | AP-005 | May split test work only with fixture ownership coordinated | Complete |
| AP-007 | Verify Feature 004 booking → Feature 007 PostgreSQL retrieval | AP-006 | Can prepare with AP-008, one fixture owner | Complete |
| AP-008 | Verify Dashboard booked-count consistency | AP-007 | Can prepare with AP-007, one fixture owner | Complete |
| AP-009 | Add frontend appointment types/service/runtime validation | AP-001 | Parallel with AP-002; owns feature-local API files | Complete |
| AP-010 | Build `/appointments` screen and route states | AP-009; route contract from AP-004 for live integration | Screen tests may use injected service while backend finishes | Complete |
| AP-011 | Add responsive presentation and consultation navigation | AP-010 | Owns appointment presentation files; coordinate route assertions | Complete |
| AP-012 | Add shared desktop/mobile Appointments navigation | AP-010 | Can overlap AP-011 only with explicit `App.tsx`/`AppLayout.tsx` ownership | Complete |
| AP-013 | Run Features 001–006 regression and lifecycle checks | AP-007, AP-008, AP-011, AP-012 | No concurrent edits to shared regression fixtures | Complete |
| AP-014 | Verify no AI, no migration, Docker, and scope isolation | AP-013 and implementation tasks | Verification only | Complete (2026-08-19) |
| AP-015 | Verify final Feature 007 vertical slice | AP-014 and all tasks | Final gate; cannot begin earlier | Complete (2026-08-19) |

## Ownership and parallel-work rules

- AP-002 owns `appointment_repository.py`; AP-003 owns the application service;
  AP-004 owns list DTO/API route changes; AP-005 owns only composition seams.
- AP-009 owns the feature-local appointment types/service. AP-010 owns the
  appointment route and screen state machine. AP-011 owns appointment row/card
  rendering and its single consultation action. AP-012 owns shared navigation
  definitions and active-state tests.
- Do not concurrently edit `consultation_routes.py`,
  `consultation_service.py`, `appointment_repository.py`, `App.tsx`,
  `AppLayout.tsx`, or shared PostgreSQL fixtures without transferring explicit
  ownership and reconciling the dependent task.
- AP-002 and AP-009 are the primary safe parallel pair after AP-001. AP-007 and
  AP-008 may be prepared in parallel but must converge on one committed fixture
  scenario and cleanup owner. AP-011 and AP-012 may overlap only after route
  registration ownership is agreed.

## Completion rule

AP-015 is the only task that can close the feature. It must verify the complete
flow `Feature 004 booking → persisted Appointment → GET /api/v1/appointments →
/appointments → related consultation → Dashboard booked_appointments`, plus
backend/frontend tests, PostgreSQL, type/lint/build, migration, Docker, no-AI,
regression, scope, and Git checks. No task permits a migration, AI call,
appointment write path, Feature 008 visual work, or automatic commit.
