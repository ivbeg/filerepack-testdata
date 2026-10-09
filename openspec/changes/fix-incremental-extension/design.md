## Context
The extend command recreates existing CRX assets with a fresh key before merging the manifest.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Generation occurs under .work on the same filesystem with copies of corpus and legal notices. Existing case IDs are ignored, colliding/overlapping new paths are refused, and pinned existing bytes are restored before combined inventory validation. New positive cases require independent decoding. Only new assets are moved; atomic metadata writes follow, with inventory/catalog backups and rollback on publication errors. Full regeneration remains an explicit different command.

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
