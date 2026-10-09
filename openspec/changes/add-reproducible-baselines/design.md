## Context
The published full baseline covers 403 older cases and a dirty implementation in one attempt.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Reports capture start/end harness and implementation hashes, corpus identity, packages and executable hashes. current_baseline.py extracts an explicit Git commit into a temporary immutable source snapshot, excluding working changes/build artifacts, and measures every selected case three times after one discarded warmup. Comparisons flag missing/incompatible harness/environment/selection/repetition identities while allowing implementation-version comparisons. Portable evidence preserves failures and separate original/generated/stress totals; configured remote platforms are not claimed as executed.

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
