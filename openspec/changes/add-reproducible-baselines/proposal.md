# Change: Capture immutable repeated benchmark evidence

## Why
The published full baseline covers 403 older cases and a dirty implementation in one attempt.

## What Changes
- Record corpus/harness/implementation and tool identities consistently.
- Provide a repeatable baseline command using a fixed implementation snapshot.
- Publish repeated current-corpus summaries, separate original/stress results and platform qualification status.

## Impact
- Affected specs: `benchmark-evidence`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
