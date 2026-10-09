## 1. Implementation
- [x] 1.1 Capture harness/tool/source identity and strengthen comparisons.
- [x] 1.2 Add fixed-revision baseline workflow/script and portable summaries.
- [x] 1.3 Run repeated current-corpus baseline on an immutable checkout.
- [x] 1.4 Update baseline, methodology and actual platform qualification evidence.

## 2. Validation evidence

Final complete run: 477 cases, 1 discarded warmup and 3 measured attempts each, immutable implementation commit 95827f3206d68760819d1a0f21ab9acfcf74313b. Source and harness hashes stayed stable. 297 improved, 179 unchanged, 1 routing qualification failure; no preservation failures or verifier skips. Identity/comparison tests passed. Portable evidence and separate original/generated/stress totals are in docs/current-baseline.json and docs/CURRENT-BASELINE.md. Remote platform configuration is explicitly distinguished from executed local qualification.
