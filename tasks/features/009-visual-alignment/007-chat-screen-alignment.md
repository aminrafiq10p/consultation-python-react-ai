# VA-007 — Align Consultation Detail and AI Chat

**Task ID:** VA-007

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Close-match Screen 2 while preserving Feature 002 and Feature 008 behavior.

Align:
- patient/consultation header;
- conversation canvas;
- user/assistant alignment;
- assistant card treatment;
- structured payloads;
- scroll area;
- composer;
- send action;
- Feature 008 CTA styling.

Do not add unsupported microphone/attachment/upload/photo features.
Do not alter chat persistence, summary eligibility, closed-state behavior, or booking authority.
Add focused regressions.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
