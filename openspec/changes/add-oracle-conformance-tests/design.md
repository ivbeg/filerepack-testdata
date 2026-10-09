## Context
Only a small subset of 44 oracle kinds has direct mutation regressions.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
docs/oracle-conformance.json inventories all used kind/format/codec combinations and selected checked fixtures. Executable qualification records the actual equivalent serialization strategy and detects bounded truncation, TAR member mutation or Zarr value mutation. Byte-identity acceptance is explicit for profiles without a reencoder and does not certify optimizer rewrites. Targeted regression tests supplement generic destructive mutations for metadata, graph/reference, numeric, document and media contracts. Strict qualification rejects optional-reader skips.

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
