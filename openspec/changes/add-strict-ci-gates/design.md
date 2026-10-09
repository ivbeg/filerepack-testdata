## Context
CI exercises five cases and a run can succeed with no independently verified inputs.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Run/check provide --strict-verifiers; run additionally requires at least --min-verified cases (default 1) and can enforce declared routing/status/reason/attempt contracts via --require-outcomes. Per-case optional capabilities record availability. CI separates the Python 3.10/3.13, Linux/macOS/Windows portable matrix from a Linux native-reader smoke/control lane and scheduled/manual full repeated measurements. Reports and logs are retained even after failures.

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
