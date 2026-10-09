## Context
HDF5 link removal and NetCDF nested-group data corruption escape the current fingerprints.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
HDF5 object addresses are used only during traversal and replaced with deterministic canonical paths. Hard-link aliases/cycles, soft/external targets and object/region references are represented without opening external files. NetCDF traverses nested groups and records dimension ownership, type definitions, attributes and exact values without mask/scale conversion. Arrow floating arrays use native numeric buffers and validity masks to retain NaN payloads and signed zero; nested arrays recurse. Unsupported anonymous reference targets are refused.

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
