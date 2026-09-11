# VA-012 — Complete Responsive and Accessibility Alignment

**Task ID:** VA-012

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Verify all Feature 009 screens on desktop and narrow layouts.

Requirements:
- desktop sidebar/mobile drawer;
- usable gutters;
- stacked booking layout;
- safe records/appointments presentation;
- usable chat composer;
- no clipped Feature 008 CTA;
- semantic headings;
- labelled controls;
- keyboard actions;
- visible focus;
- status text beyond color;
- accessible chart summary;
- discoverable loading/error states.

Make only minimal adjustments required to satisfy these criteria.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
