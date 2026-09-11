# VA-008 — Align Consultation Summary and Recommendations

**Task ID:** VA-008

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Close-match Screen 3 while preserving Feature 003 behavior.

Align:
- Patient Summary;
- optional real rationale/AI insight;
- recommendation cards;
- selected/priority treatment state;
- Next Steps;
- Book Appointment;
- Restart Consultation.

Do not fabricate confidence, history, cost, duration, clinical facts, or rationale.
Add focused summary regressions.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
