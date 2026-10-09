# Change: Verify scientific graphs and nested data

## Why
HDF5 link removal and NetCDF nested-group data corruption escape the current fingerprints.

## What Changes
- Record HDF5 hard/soft/external link identities without unsafe dereferencing.
- Recursively compare NetCDF groups, dimensions, variables and attributes.
- Preserve exact scientific value/attribute bits and reject unqualified layouts explicitly.

## Impact
- Affected specs: `scientific-oracles`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
