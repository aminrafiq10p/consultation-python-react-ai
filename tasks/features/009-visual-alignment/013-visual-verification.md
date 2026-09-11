# VA-013 — Run Screen-by-Screen Visual Verification

**Task ID:** VA-013

## Authoritative Sources

- `specs/features/009-visual-alignment.md`
- `plans/features/009-visual-alignment.md`
- the five files under `docs/visual-references/`

Features 001–008 remain authoritative for behavior and persistence.

## Scope Guard

Visual references control presentation. Do not introduce hardcoded screenshot data, unsupported workflows, migrations, or unrelated refactors. Preserve unrelated working-tree changes and do not commit automatically.

## Objective and Requirements

Compare implementation against all five approved references.

Verify:
- page geometry;
- sidebar;
- content position/width;
- major component placement;
- whitespace;
- typography hierarchy;
- control sizing;
- borders/radii/shadows;
- status/button styling;
- responsive composition.

Document intentional deviations caused by unsupported screenshot-only functionality.

Do not add fake data to improve visual resemblance.

## Progress Tracking

Update only this task's checkbox in `specs/features/009-visual-alignment.md` after every acceptance criterion and required check passes. Do not mark later tasks complete.

## Completion Evidence

Report files changed, implementation/verification summary, tests/checks and exact results, tracker status, blockers/deviations, and the next unblocked task(s).
