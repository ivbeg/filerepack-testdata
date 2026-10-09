## 1. Implementation
- [x] 1.1 Define a machine-readable oracle conformance inventory.
- [x] 1.2 Add equivalence/corruption regressions for all used kinds.
- [x] 1.3 Add completeness and optional-dependency CI gates.
- [x] 1.4 Publish qualification results and limits.

## 2. Validation evidence

Machine inventory covers all 47 used kinds across 71 profiles. All 71 conformance profiles passed with zero missing-reader skips, using 28 independent re-encoding/layout strategies and 43 explicit byte-identity acceptance profiles. Generic truncation/member/value corruption is supplemented by targeted metadata/graph/numeric/document/media regressions. Completeness and strict skip gates are executable. Limits/results are in docs/oracle-conformance.json, docs/conformance-results.json and docs/QUALIFICATION.md.
