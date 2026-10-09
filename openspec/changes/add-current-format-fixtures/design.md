## Context
GGUF, ONNX, Safetensors, tracev3, gzip and local RTF capability have no fixtures.

## Goals / Non-Goals
Implement the capability's requirements with independent passive verification and meaningful
regression evidence. Do not change filerepack behavior or weaken a preservation contract to
make an optimizer appear successful.

## Decisions
Models use bounded passive GGUF/Safetensors parsing and ONNX structural checking, with exact bytes and unchanged inspection contracts; no tensor execution/loading is permitted. tracev3 compares ordered chunks and dictionary-decoded LZ4 payloads. RTF uses bounded balanced token parsing and independently decoded PNG pictures, retaining opaque objects and unknown destinations. Generic gzip, TAR/WARC detection and R gzip aliases have routing contracts. RTF routing is conditional on the implementation registry, and unsupported-capability preservation remains visible.

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
