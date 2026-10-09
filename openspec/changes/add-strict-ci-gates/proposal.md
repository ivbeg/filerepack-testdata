# Change: Require meaningful verification in CI

## Why
CI exercises five cases and a run can succeed with no independently verified inputs.

## What Changes
- Add explicit strict-verifier and minimum verified-case gates.
- Run smoke, rejection controls and qualified optional-reader lanes.
- Add platform/minimum-Python lanes and periodic full qualification.

## Impact
- Affected specs: `qualification`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
