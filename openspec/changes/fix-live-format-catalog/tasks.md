## 1. Implementation
- [x] 1.1 Replace legacy-only extraction and centralize metadata discovery.
- [x] 1.2 Use live handler/compound metadata in coverage and add strict gates.
- [x] 1.3 Test current and legacy registries plus drift handling.
- [x] 1.4 Refresh catalog and coverage documentation.

## 2. Validation evidence

Modern derived-view and legacy registry tests passed; live-handler coverage does not reuse cached mappings. Strict live coverage: 312/312 extensions, 102/102 handlers, 28/28 filename paths. Pinned committed baseline has 311 extensions/101 handlers; optional RTF is explicitly distinguished. docs/coverage.json records the registry identity.
