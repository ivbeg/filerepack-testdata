# Audit remediation · 2026-10-09

Implementation was explicitly authorized by the user when requesting OpenSpec proposals and
immediate implementation. Each change below owns a separate capability and records its tests
in `tasks.md`. Proposals remain active until publication/archive is requested.

| Change | Audit finding | Priority |
|---|---|---|
| fix-preservation-metadata | Raster/ZIP metadata and USDZ constraints can escape comparison | P1 |
| fix-live-format-catalog | Current registry extraction fails; live handler coverage is stale | P1 |
| fix-incremental-extension | Extension overwrites existing CRX assets | P1 |
| add-strict-ci-gates | Five-case CI and zero-verification success | P1 |
| add-current-format-fixtures | Model formats, tracev3, gzip, RTF and detected routes are absent | P2 |
| add-representative-originals | All upstream originals are OLE/CFB | P2 |
| add-adversarial-scale-fixtures | Boundary, protected, nested and larger inputs are sparse | P2 |
| add-scientific-graph-verification | HDF5 links and nested NetCDF data are unverified | P2 |
| add-oracle-conformance-tests | Most independent oracle kinds lack corruption regressions | P2 |
| add-reproducible-baselines | Current corpus lacks immutable repeated baseline/platform qualification | P2 |
| fix-installed-corpus-discovery | Wheel corpus discovery and publication documentation are incomplete | P3 |

Order: repair verification/generation and strict gates; add format/depth/original fixtures;
qualify oracle corruption detection; then run and publish reproducible evidence.

## Implemented evidence

All eleven implementation checklists are complete and strict OpenSpec validation passes.
The corpus contains 477 cases and preserves every previously published asset. Native qualification
passes 119 tests and all 71 conformance profiles. See [qualification](../docs/QUALIFICATION.md)
and the [final repeated baseline](../docs/CURRENT-BASELINE.md). One declared TAR-in-gzip routing
contract fails in the fixed filerepack revision; decoded content is preserved. This is an
implementation finding recorded by the completed testdata changes, not a waived pass.

The changes remain active until publication/archive is requested; the sibling filerepack working
tree has not been modified by this work.
