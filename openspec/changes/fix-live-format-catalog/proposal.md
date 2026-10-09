# Change: Refresh coverage from the current registry

## Why
AST extraction expects legacy constant assignments and handler coverage ignores the live registry.

## What Changes
- Read registry facts through an isolated public metadata import and retain snapshot compatibility.
- Compute handler and special filename-route coverage from current facts.
- Record registry identity and make requested missing coverage fail explicitly.

## Impact
- Affected specs: `format-coverage`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
