# filerepack-testdata

A public-ready corpus and benchmark harness for [filerepack](https://github.com/ivbeg/filerepack).
It measures **actual output size, compression time and decoded-content preservation** on fresh
copies of checksummed files. Original corpus assets never enter filerepack's write path.

The checked-in corpus includes synthetic files, 48 pinned upstream OLE/Office originals,
compression opportunities, already compact and high-entropy examples, and malformed/protected
rejection controls. `corpus/manifest.json` is the authoritative inventory. No network is needed
for generation or benchmarking after dependencies are installed.

Coverage distinguishes native/original files, text syntax profiles, routing aliases and generic
ZIP/container transport fixtures. A generic ZIP renamed `.sketch` exercises transport and nested
walking; it does not demonstrate Sketch application compatibility. See [coverage](docs/COVERAGE.md),
[methodology](docs/METHODOLOGY.md) and [data licensing](DATA-LICENSES.md).

The [local baseline](docs/BASELINE.md) ran all 403 cases: 263 improved, 139 stayed unchanged,
and one WOFF2 case failed the strict embedded-timestamp check. A separate 12-case smoke suite
passed all three measured repeats. Coverage currently reaches 302/303 extension routes and all
94 named handler groups; 139 extensions have native/original fixtures.

## Quick start

From this repository, with a filerepack checkout alongside it:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[corpus,dev]'
python -m pip install -e '../filerepack[serialization]'
python -m frbench check
python -m frbench run --filerepack ../filerepack --tier smoke --output results/smoke
```

`--filerepack` imports that checkout directly, including uncommitted changes. Omit the flag to
benchmark the filerepack version installed in the environment. The corpus/harness itself needs
Python 3.10+; Python 3.13 has been used for the local full run.

Optional tools determine which optimizers can run. On macOS, the following Homebrew tools cover
most exercised paths; on Ubuntu install the equivalents with apt. Use `filerepack doctor` and
`python -m frbench doctor` to inspect availability rather than interpreting unchanged files as
successful compression:

```sh
brew install sevenzip ffmpeg qpdf ghostscript imagemagick jpegoptim optipng gifsicle \
  webp zstd brotli lz4 lzip lzop hdf5 netcdf flac r
```

RAR, Monkey's Audio, MP3Packer, OptiVorbis, JPEG XL/HEIF encoders and DICOM JPEG-LS backends have
separate installation/licensing requirements; absence remains visible in inventory/logs.
Legacy Office compaction also needs filerepack's optional native writer. Build it in the
filerepack checkout and expose it for this run:

```sh
cargo build --release --locked --manifest-path ../filerepack/tools/ole-compactor/Cargo.toml
export FILEREPACK_OLE_COMPACTOR="$PWD/../filerepack/tools/ole-compactor/target/release/filerepack-ole"
```

## Measure effectiveness

```sh
# Full corpus. Three measurements and one discarded warmup per case; each starts from a fresh copy.
python -m frbench run --filerepack ../filerepack --repeat 3 --warmup 1 --output results/full

# Native/original/syntax cases only; omit generic transports and routing aliases.
python -m frbench run --filerepack ../filerepack --native-only --output results/native

# Focus on a family, extension, case substring, or safety controls.
python -m frbench run --filerepack ../filerepack --family scientific,data --output results/data
python -m frbench run --filerepack ../filerepack --ext png,jpg,pdf --output results/images
python -m frbench run --filerepack ../filerepack --case original- --output results/originals
python -m frbench run --filerepack ../filerepack --tier control --output results/controls

# Separate opt-in profiles use the same exact-content oracles.
python -m frbench run --filerepack ../filerepack --profile ultra --output results/ultra
python -m frbench run --filerepack ../filerepack --profile experimental --family scientific --output results/experimental
python -m frbench run --filerepack ../filerepack --profile checkpoint-load-only --ext pt,pth --output results/checkpoints

# Compare versions/options; mismatched corpus/options/environment are reported explicitly.
python -m frbench compare results/full/report.json results/new-version/report.json
python -m frbench coverage --filerepack ../filerepack
```

Every result directory contains `report.md`, `report.json`, `cases.csv`, `coverage.json`,
`attempts.jsonl`, `progress.json` and per-attempt logs. Report JSON includes versions, tool
availability, source commit/dirty flag and a content hash of all filerepack Python source files.
Directories must be new: the runner refuses to overwrite existing results. `--keep-work` retains
failed work for diagnosis; otherwise all operation copies are deleted.

Exit status is 1 for preservation failures, growth, exceptions, timeouts or corpus corruption.
An unchanged result is valid observable behavior and contributes zero savings. Missing independent
verifier dependencies are **explicit skips**, excluded from savings. Missing optimizer tools often
produce unchanged results; inspect the reason, detailed packer results and captured log.
Compression opportunity is measured, not enforced as a universal minimum saving.

The default `lossless` profile explicitly sets `keep_meta=True` and `wmv_lossless=True` because
filerepack's video defaults and image metadata policy need those options for these comparisons.
Lossy overrides are refused: exact decoded equality is not a perceptual quality metric.
Opt-in OLE content transforms are intentionally outside the current strict live-stream oracle.

## Regenerate and extend

For the exact locally validated Python packages, use `python -m pip install -r requirements-lock.txt`.
This snapshot was produced on Python 3.13 / macOS arm64; other platforms may need compatible versions.

The corpus is already included. Regeneration is optional and replaces only `corpus/generated/`:

```sh
python -m frbench generate --filerepack ../filerepack --strict
python -m frbench check --decode
python -m frbench coverage --filerepack ../filerepack --json > coverage.json
python -m pytest -q
```

The extension catalog is refreshed from the provided checkout, or reused from `corpus/catalog.json`
when `--filerepack` is omitted. Optional generator errors are recorded in the manifest and printed.
`--strict` exits 1 if any generator failed; `--minimal` generates the core fixtures without the
large optional library-based families. `--scale N` increases synthetic record counts without
multiplying image dimensions. Treat a regenerated manifest as a new dataset version.

Seeds, data values and profiles are reproducible. Exact binary regeneration additionally depends
on library/tool versions, creation times and encrypted-envelope randomness; the checked-in bytes and hashes
are the stable benchmark reference. Do not regenerate while benchmarking.

Originals remain byte-identical and can be restored with `python scripts/fetch_originals.py`
using commit-pinned URLs and mandatory size/SHA-256 verification. Add an original only with known
redistribution terms, a license/notice, a pinned source and a checksum. See [CONTRIBUTING.md](CONTRIBUTING.md).

This is a local Git repository on `main`; no remote or public publication is configured.
