## 1. Implementation
- [x] 1.1 Implement image metadata and ZIP profile contracts.
- [x] 1.2 Implement rich PDF/media comparisons with qualified fixtures.
- [x] 1.3 Add legitimate-recompression and corruption regressions; run focused benchmarks.
- [x] 1.4 Update methodology and qualification limits.

## 2. Validation evidence

119 tests passed. PNG metadata/high-depth, JPEG EXIF/ICC removal without pixel changes, ZIP mode/date/comment, USDZ rejection, rich PDF form/link/text, media streams/tags/timing and equivalent GIF palette/disposal regressions passed. Final full baseline: zero preservation failures across 477 cases, 3 attempts plus warmup. See docs/METHODOLOGY.md and docs/CURRENT-BASELINE.md.
