## 1. Implementation
- [x] 1.1 Stage extension generation and filter existing IDs/paths.
- [x] 1.2 Implement validation, collision handling and rollback.
- [x] 1.3 Test repeated extension and failure/collision cases.
- [x] 1.4 Document explicit regeneration versus extension.

## 2. Validation evidence

Regression tests prove byte stability/idempotence, optional-generator failure isolation, path collision rejection and rollback after a publication error. Actual repeated --extend preserved all 477 assets and the exact manifest, including signed CRX. All 432 prior published inventories remain unchanged.
