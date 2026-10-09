## 1. Implementation
- [x] 1.1 Implement cycle-safe HDF5 object/link traversal.
- [x] 1.2 Implement recursive NetCDF group/type/value comparison.
- [x] 1.3 Add graph/group and numeric-edge fixtures and corruption tests.
- [x] 1.4 Qualify scientific recompression and document unsupported variants.

## 2. Validation evidence

HDF5 hard/soft/external links, cycles and reference-target tests and NetCDF nested-data mutation tests passed. Arrow signed-zero and NaN-payload regressions and edge fixtures passed. HDF5/NetCDF graph/group fixtures passed full repeated verification and remained unchanged under size policy; simpler scientific profiles recompressed successfully. Unsupported anonymous references are refused and external links are not dereferenced.
