## Context
Most routes have one example and the largest fixture is under two MiB.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Bounded synthetic controls cover parent paths, signatures, encryption, duplicate names and bad CRCs. Positive examples cover empty/Unicode/nested ZIP, linked TAR, rich PDF, JPEG metadata, RGB16/float images, exact Arrow numeric edges, scientific graphs/groups and multi-stream variable-frame-rate media. A 16 MiB TAR is a scalable stress-tier input; ordinary savings exclude stress, while its separate total and per-attempt RSS/time remain available.

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
