# Change: Add boundary, rich and scale scenarios

## Why
Most routes have one example and the largest fixture is under two MiB.

## What Changes
- Add bounded nested, duplicate-name, protected and malformed archive scenarios.
- Add rich PDF, image, multi-stream media and scientific value edge cases.
- Add a separate scalable stress tier with explicit resource and size metadata.

## Impact
- Affected specs: `scenario-corpus`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
