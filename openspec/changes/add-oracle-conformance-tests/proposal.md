# Change: Qualify every independent oracle kind

## Why
Only a small subset of 44 oracle kinds has direct mutation regressions.

## What Changes
- Maintain an explicit per-oracle conformance inventory.
- Test legitimate envelope recompression and deliberate semantic corruption for every qualified oracle.
- Keep optional integration skips explicit and enforce conformance completeness in CI.

## Impact
- Affected specs: `oracle-conformance`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
