## Context
AST extraction expects legacy constant assignments and handler coverage ignores the live registry.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
A trusted isolated subprocess imports public consts/formats/format_registry views and returns a JSON sentinel; legacy literal constants remain supported. The dispatch mapping is read from PackerSpec declarations without executing dispatch. One discovered catalog supplies extension, handler and filename-route coverage and records implementation/registry hashes. Strict coverage fails uncovered live routes and unresolved handlers; already-covered additional routes in a newer corpus are reported as explicit drift rather than missing coverage.

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
