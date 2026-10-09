# Change: Support installed harness and current publication docs

## Why
Wheels omit corpus assets and default discovery assumes an editable checkout; README still claims no remote exists.

## What Changes
- Make external corpus discovery explicit for installed packages.
- Build/install and verify wheel and source distributions in isolated environments.
- Update installation/publication documentation without changing repository visibility.

## Impact
- Affected specs: `distribution`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
