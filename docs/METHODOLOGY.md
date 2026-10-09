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
- Native aggregate excludes transport-only and alias fixtures. Safety controls and verifier skips
  are excluded from both savings aggregates. Family/extension columns allow further grouping.
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
| ZIP / TAR | Member names, directories and decoded payloads; nested JSON/XML minification verified recursively; TAR links/mode/ownership/mtime/PAX | ZIP filesystem metadata not independently compared in this version |
| NPZ | NumPy `load(..., allow_pickle=False)` keys, dtypes, shapes and exact numeric bits | Generated numeric fixture; object arrays are refused without unpickling |
| ODF / EPUB | Above plus first uncompressed mimetype and exact protected control manifests | Generated profiles include ODF text, spreadsheet, presentation, graphics, chart, image, formula, database and template MIME types; no office/reader render qualification |
| OOXML | XML trees and decoded thumbnail/image pixels, plus remaining member bytes | No Word/Excel/PowerPoint application render qualification |
| 7z / RAR / CAB / WIM | Integrity test, trusted fixture extraction and complete decoded member mapping | Uses 7zz (unrar for RAR); transport metadata not independently checked |
| Raster / animations | Every Pillow-decoded RGBA frame, size, duration, loop, disposal/blend | Metadata/ICC/EXIF not independently compared; native high-bit-depth TIFF has a separate oracle |
| TIFF / DNG | Arrays including bit patterns and non-layout tags | Flat multipage generated fixtures; no camera pipeline qualification |
| SVG / EXR / JXL | ImageMagick decoded pixels | SVG appearance only; no interactive behavior |
| Video / audio | ffmpeg decoded frame/PCM bytes and ordered stream dimensions/rate/channels | No perceptual lossy evaluation; container timestamps and tags not fully compared |
| PDF / AI | Ghostscript rendering at 72 dpi, page boxes/rotation, docinfo and attachment bytes | Shape-only fixture pages; no text/links/forms/object-graph equivalence claim |
| SQLite | Schema, all rows including implicit rowids, application_id/user_version | Offline generated databases; GeoPackage/MBTiles aliases exercise SQLite storage |
| DuckDB | Native read-only schema/table content | Generated simple tables; no wider app behavior |
| Arrow / Parquet / ORC / Feather / Avro | Native schema/metadata and ordered decoded values | The checked corpus omits NaN values in these profiles; physical layout/compression is allowed to differ |
| HDF5 / NetCDF4 | Attributes, dimensions and array bit patterns | Generated tree/root profiles; no graph references/links/groups in this first corpus |
| FITS | Decoded image bits, custom ordered header cards/comments | Empty primary normalization allowed; no floating quantization |
| MAT / SPSS | SciPy / pyreadstat decoded arrays/values and selected metadata | Experimental filerepack gates may keep source unchanged |
| Checkpoint | Exact ordered ZIP member names/bytes without unpickling | Content preserved; independent mmap/alignment verification is future work |
| Zarr v2 | Array bit patterns, paths and attributes through zarr | Complete local offline store only; no object-store/concurrent writer tests |
| WOFF / WOFF2 | fontTools uncompressed table XML, including metadata/timestamps; calculated checksum excluded | Glyph encoding normalization beyond this generated profile may require a more specific oracle |
| OLE | olefile live streams and directory identity/CLSID/state/timestamps | Compaction only; content recompression needs a future intended-change oracle |
| Apple CAR | BOMStore block IDs and catalog variables, rendition keys, and decoded zlib content | One synthetic CoreUI rendition; the current local filerepack checkout rejects the rewritten CSI body length and leaves the source unchanged |
| CRX3 | RSA signature, extension ID, ZIP member CRCs and decoded member profiles | Ephemeral test key; the current local filerepack checkout leaves the signed CRX wrapper unchanged |
| CPIO+bzip2 | newc record framing plus exact decoded CPIO bytes | Synthetic files, directory, symlink and hard-link pair; outer bzip2 stream only |
| NRRD / Blender / SWF / TGS / PSB / Aseprite / NIB / WARC | Passive decoded payloads/records and relevant generated-profile metadata | Hand-authored structural profiles; limited oracle subsets explicitly reject other encodings |
| Malformed / protected controls | Exact source byte identity | Rejection behavior, not a positive-format compression success |

Rejection controls have no minimum compression target. Already compact and high-entropy cases
show acceptance behavior. There is no image/audio/video quality threshold for lossy output.

## Reproducibility

Keep the exact checked-in manifest/assets, Python environment, tool versions, profile and options
when comparing versions. The source tree hash identifies local uncommitted implementation changes.
Sequential runs avoid benchmark contention; close unrelated heavy jobs for timing comparisons.
Use at least three attempts and one warmup for published timing claims. The local baseline is a
single-attempt functionality/effectiveness observation, not statistically stable performance evidence.

The manifest pins hashes of every file and every member of a directory fixture. Checks run before
and after the suite. Originals have commit-pinned upstream provenance. Large data, passwords,
URLs, names and medical identifiers in generated fixtures are synthetic.
