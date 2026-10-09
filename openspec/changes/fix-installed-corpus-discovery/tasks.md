## 1. Implementation
- [x] 1.1 Add corpus-root discovery/configuration and actionable diagnostics.
- [x] 1.2 Add isolated wheel/sdist installation validation.
- [x] 1.3 Update quick start and repository publication documentation.
- [x] 1.4 Run distribution and minimum-Python checks.

## 2. Validation evidence

Explicit/env/default discovery and actionable missing-root tests passed. Wheel/sdist built, installed outside checkout, verified import confinement and corpus CLI, and unpacked sdist dataset checked on Python 3.10.20 and 3.13.7. Python 3.10 portable suite: 81 passed/38 explicit optional-reader skips. Python 3.13 native suite: 119 passed. README now links the configured GitHub repository and documents external wheel datasets. Evidence: docs/distribution-results.json.
