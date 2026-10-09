## Context
The 48 original fixtures all come from OLE/CFB; other families are synthetic.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Six original assets are pinned to commits from python-docx, qpdf, PngSuite/libpng, SciPy and Mutagen. Their original bytes, independent profiles, legal notice paths and descriptions are indexed. check_manifest requires exact agreement between original index and manifest and validates notice confinement/existence. Restoration verifies expected size/hash before writing. Upstream regression originals are explicitly distinguished from production workload samples, with separate size/timing totals.

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
