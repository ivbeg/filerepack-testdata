# Change: Preserve metadata and package constraints

## Why
Raster and ZIP comparisons can accept metadata loss; a USDZ candidate can violate its storage and alignment constraints.

## What Changes
- Compare declared image metadata without confusing codec layout metadata with semantic metadata.
- Preserve ZIP member metadata/order under profile-specific policies and validate USDZ STORED/alignment requirements.
- Expand PDF/media contracts for rich profiles and document narrower verified scopes.

## Impact
- Affected specs: `oracle-contracts`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
