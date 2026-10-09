## Context
Wheels omit corpus assets and default discovery assumes an editable checkout; README still claims no remote exists.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Corpus lookup follows explicit --root, FILEREPACK_TESTDATA_ROOT, current checkout and source-package checkout. A runtime wheel without corpus gives a clear --root diagnostic; source distributions include dataset/specs/tests/notices. validate_distribution.py builds staged artifacts, creates clean environments, verifies installed import paths and CLI integrity checks, and checks the unpacked sdist dataset. POSIX environment executable symlinks support relocatable CPython distributions; host pip targets the fresh environment explicitly.

## Risks / Trade-offs
Codec representations can legitimately change. Compare semantic values and metadata rather than
layout bytes, except where signatures or an inspection-only contract require byte identity.
Unsupported variants must be rejected or scoped rather than silently certified.

## Migration Plan
Add regressions reproducing the audit finding, implement the contract, qualify existing fixtures
and then refresh generated/evidence documents. Existing original bytes remain pinned.

## Open Questions
Qualification outcomes depend on native backend/platform availability and must be recorded from
actual runs. These are execution facts, not additional approval gates.
