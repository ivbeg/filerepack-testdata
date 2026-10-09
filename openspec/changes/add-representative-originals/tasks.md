## 1. Implementation
- [x] 1.1 Select and verify pinned redistributable upstream fixtures.
- [x] 1.2 Add bytes, index records and notices with independent profiles.
- [x] 1.3 Validate index/license consistency and restoration.
- [x] 1.4 Report original/generated subsets separately.

## 2. Validation evidence

Six commit-pinned originals added from python-docx, qpdf, PngSuite/libpng, SciPy and Mutagen with independent profiles and legal files; 54 total originals. Index/manifest/legal-reference integrity tests passed. Pinned qpdf PDF restoration was tested in a temporary root with matching size/hash. Final baseline separates 51 positive originals from generated cases; 3 original controls are separate.
