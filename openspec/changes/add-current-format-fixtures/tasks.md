## 1. Implementation
- [x] 1.1 Implement passive generators/oracles for current formats.
- [x] 1.2 Add valid, protected/malformed and detected-route fixtures.
- [x] 1.3 Check live coverage and run focused implementation measurements.
- [x] 1.4 Document inspection-only and optional capability behavior.

## 2. Validation evidence

Bounded passive model, tracev3, gzip/compound/detected routes and RTF fixtures plus malformed controls added and preflight/conformance passed. Repeated fixed baseline records model inspection-only unchanged outcomes and tracev3 improvement. Optional local RTF: two positive profiles improved across 3 attempts after warmup; malformed control unchanged. TAR named only .gzip fails the declared routing contract in pinned filerepack; content preservation passes. See docs/CURRENT-BASELINE.md and docs/rtf-capability.json.
