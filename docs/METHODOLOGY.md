# Measurement and preservation contracts

The suite evaluates existing filerepack behavior without importing its test helpers or using its
validators as the benchmark oracle. `frbench/oracles.py` contains independent checks backed by
standard/native readers. It does not execute macros, serialized Python objects or application
scripts. Every attempt runs sequentially in a fresh child process and temporary directory.

## What the numbers mean

- Input/output bytes are measured from actual files (or summed files for a Zarr directory).
- Savings are `(input - output) / input`. No-growth policy rejects enlargement.
- `seconds` times only the filerepack API call. Imports, initial fingerprinting and independent
  output verification are outside that timer; `wall_seconds` includes all worker overhead.
- Medians/min/max are calculated per case across measured attempts. Warmups are discarded.
- Totals count each selected case once at its median output size. Repeats do not inflate bytes.
- Native aggregate excludes transport-only and alias fixtures. Safety controls, stress cases and verifier skips
  are excluded from ordinary savings aggregates. Originals, generated cases and stress inputs
  have separate totals. Family/extension columns allow further grouping.
- Process-tree RSS is sampled every 50 ms when psutil is installed. It can miss short peaks and
  double-count shared pages. It is not a peak allocated-memory guarantee.
- A hard timeout covers operation and verification. On POSIX the worker gets its own process
  group; timeout terminates that group. Windows uses `taskkill /T`.

`improved` means verified smaller output; `unchanged` means verified equality and zero savings.
Neither status asserts that every installed optimizer was invoked. `skipped-verifier` is excluded
and is not a preservation pass. Failures remain failures in a repeated case if any attempt fails.
Logs and detailed packer results distinguish missing backends, unsupported variants, experimental
gates and a candidate that was not smaller. A synthetic corpus cannot estimate savings for the
world's real files; original and generated evidence are clearly separated.

## Oracle scope

| Family | Independent comparison | Limits |
|---|---|---|
| JSON / JSONL | Exact non-whitespace lexical tokens, strings, duplicate keys, number spelling; JSONL line endings | No application-specific HAR/glTF behavior validation |
| XML | DOM elements/attributes, namespaces, text including whitespace, comments, PI and doctype | Syntax equivalence, not app rendering |
| Streams / R | Hash of complete decoded bytes, including `.rds/.rda/.rdata` inside gzip/bzip2/xz wrappers | R graph never instantiated; no native readRDS execution |
| ZIP / TAR | Member names, directories and decoded payloads; nested JSON/XML minification verified recursively; TAR links/mode/ownership/mtime/PAX | ZIP timestamps, member/archive comments, permissions, file type and DOS flags are compared; extra fields are opt-in; USDZ requires STORED members, 64-byte payload alignment and a first USD scene |
| NPZ | NumPy `load(..., allow_pickle=False)` keys, dtypes, shapes and exact numeric bits | Generated numeric fixture; object arrays are refused without unpickling |
| ODF / EPUB | Above plus first uncompressed mimetype and exact protected control manifests | Generated profiles include ODF text, spreadsheet, presentation, graphics, chart, image, formula, database and template MIME types; no office/reader render qualification |
| OOXML | XML trees and decoded thumbnail/image pixels, plus remaining member bytes | No Word/Excel/PowerPoint application render qualification |
| 7z / RAR / CAB / WIM | Integrity test, trusted fixture extraction and complete decoded member mapping | Uses 7zz (unrar for RAR); transport metadata not independently checked |
| Raster / animations | Every composited decoded frame, size, duration, loop, semantic background color, ICC/EXIF/text/XMP/color metadata | Palette indices and equivalent disposal/blend instructions may change; preserve_frame_controls optionally pins instructions. Native integer/float bits are retained; RGB16 PNG uses imagecodecs |
| TIFF / DNG | Arrays including bit patterns and non-layout tags | Flat multipage generated fixtures; no camera pipeline qualification |
| SVG / EXR / JXL | ImageMagick decoded pixels | SVG appearance only; no interactive behavior |
| Video / audio | ffmpeg decoded frame/PCM bytes, ordered streams, color/channel metadata, semantic tags, dispositions and rational presentation times | No perceptual lossy evaluation; encoder/statistical tags are excluded; qualified multi-track VFR profile remains bounded |
| PDF / AI | Ghostscript rendering at 72 dpi, page boxes/rotation, text extraction, docinfo, attachments and passive annotation/form/document graphs | Includes text, URI links and AcroForm fields; does not certify every application feature or higher-resolution rendering |
| SQLite | Schema, all rows including implicit rowids, application_id/user_version | Offline generated databases; GeoPackage/MBTiles aliases exercise SQLite storage |
| DuckDB | Native read-only schema/table content | Generated simple tables; no wider app behavior |
| Arrow / Parquet / ORC / Feather / Avro | Native schema/metadata and ordered decoded values | Arrow float NaN payloads and signed zero are compared as exact bits, including nested arrays; physical layout/compression may differ; Avro uses ordered native values |
| HDF5 / NetCDF4 | Cycle-safe HDF5 object identity, hard/soft/external links, reference targets/regions, attributes and exact array bits; recursive NetCDF groups/dimension ownership/types | External HDF5 links are recorded without dereferencing; anonymous reference targets and unsupported object variants are refused |
| FITS | Decoded image bits, custom ordered header cards/comments | Empty primary normalization allowed; no floating quantization |
| MAT / SPSS | SciPy / pyreadstat decoded arrays/values and selected metadata | Experimental filerepack gates may keep source unchanged |
| Checkpoint | Exact ordered ZIP member names/bytes without unpickling | Content preserved; independent mmap/alignment verification is future work |
| Zarr v2 | Array bit patterns, paths and attributes through zarr | Complete local offline store only; no object-store/concurrent writer tests |
| WOFF / WOFF2 | fontTools uncompressed table XML, including metadata/timestamps; calculated checksum excluded | Glyph encoding normalization beyond this generated profile may require a more specific oracle |
| OLE | olefile live streams and directory identity/CLSID/state/timestamps | Compaction only; content recompression needs a future intended-change oracle |
| Apple CAR | BOMStore block IDs and catalog variables, rendition keys, and decoded zlib content | One synthetic CoreUI rendition; writer qualification is measured separately |
| CRX3 | RSA signature, extension ID, ZIP member CRCs and decoded member profiles | Ephemeral test key; signed content must preserve the signature identity; the fixture does not claim successful writer support |
| CPIO+bzip2 | newc record framing plus exact decoded CPIO bytes | Synthetic files, directory, symlink and hard-link pair; outer bzip2 stream only |
| NRRD / Blender / SWF / TGS / PSB / Aseprite / NIB / WARC | Passive decoded payloads/records and relevant generated-profile metadata | Hand-authored structural profiles; limited oracle subsets explicitly reject other encodings |
| GGUF / Safetensors / ONNX | Bounded structural parsing and exact bytes; ONNX checker without execution | Inspection-only single-file profiles; external tensor loading and model execution are refused |
| tracev3 | Ordered chunks, headers/catalog, opaque records and decoded lz4 blocks | Bounded archived profile with dictionary blocks; not a full Apple log semantic parser |
| RTF | Balanced passive token tree, preserved text/controls/unknown destinations and decoded picture metadata/pixels | Hex and binary PNG pictures; malformed nesting/control extents are refused; embedded objects are never executed |
| Malformed / protected controls | Exact source byte identity | Rejection behavior, not a positive-format compression success |

Rejection controls have no minimum compression target. Already compact and high-entropy cases
show acceptance behavior. There is no image/audio/video quality threshold for lossy output.

## Reproducibility

Keep the exact checked-in manifest/assets, Python environment, tool versions, profile and options
when comparing versions. Reports identify the harness commit/source hash, implementation commit/source hash, corpus manifest, package versions and executable hashes. Source/harness drift during a run fails qualification. `current_baseline.py` extracts an explicit committed revision without copying working changes or ignored native builds.
Sequential runs avoid benchmark contention; close unrelated heavy jobs for timing comparisons.
Use at least three attempts and one warmup for published timing claims. The historical baseline is a single-attempt functionality observation. Current evidence uses three measured attempts and one discarded warmup, and records failures rather than relaxing oracle contracts. Timings on a development machine remain descriptive, not controlled microbenchmark claims.

The manifest pins hashes of every file and every member of a directory fixture. Checks run before
and after the suite. Originals have commit-pinned upstream provenance. Large data, passwords,
URLs, names and medical identifiers in generated fixtures are synthetic.

## Conformance and qualification

`docs/oracle-conformance.json` covers all 47 used kinds across 71 kind/format/codec profiles.
Executable tests check accepted equivalent representations and destructive payload corruption.
Independent re-encoders cover JSON/XML, streams, ZIP/NPZ/checkpoints, PDF, Arrow, MAT and fonts;
OLE unused sectors exercise layout independence. Other profiles explicitly use byte-identity
acceptance, without claiming nonidentical rewrite qualification. General corruption checks use
bounded truncation, TAR member mutation and Zarr array-value mutation. Targeted tests additionally
exercise image/ZIP metadata, USDZ constraints, scientific links/groups/references, floating bits,
PDF forms/links/text and media tracks/tags/timelines. Passing generic truncation checks does not
claim detection of every subtle metadata mutation in every format.

Strict native qualification rejects missing readers and zero/insufficient verified cases.
The portable Python/OS matrix deliberately exposes optional skips. Configuration is distinguished
from actual executed platform results in `QUALIFICATION.md`. Stress inputs are kept separate so
scaling cannot dominate normal compression totals.
