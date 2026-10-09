# Change: Extend fixtures without replacing existing assets

## Why
The extend command recreates existing CRX assets with a fresh key before merging the manifest.

## What Changes
- Generate additions in staging and retain existing specimen hashes.
- Publish only complete validated additions; fail without partial corpus mutations.
- Keep regeneration explicit and record new dataset versions.

## Impact
- Affected specs: `corpus-generation`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
