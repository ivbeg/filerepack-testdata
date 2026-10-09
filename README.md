# filerepack-testdata

Checksummed corpus and independent preservation-aware benchmarks for
[filerepack](https://github.com/ivbeg/filerepack), hosted at
[ivbeg/filerepack-testdata](https://github.com/ivbeg/filerepack-testdata).
The harness measures output bytes, operation time and independently decoded content on disposable
copies. Corpus assets never enter the implementation's write path.

The corpus contains **477 cases**: 12 smoke, 440 extended, 24 rejection controls and one separate
16 MiB stress fixture. There are 54 pinned upstream originals across Office/OLE, documents,
images, scientific data and audio, with source commits and legal notices. They are upstream
regression samples, not a representative sample of production workloads.

The local catalog covers 312 extension routes, 102 handler groups and 28 compound/content-detected
filename paths. The pinned committed implementation `95827f3` has 311 extensions and 101 handlers;
RTF is an optional local capability. Coverage means a fixture exists, not that a writer is available
or output becomes smaller. GGUF, Safetensors and ONNX exercise inspection-only behavior.
Generic ZIPs under application suffixes are explicitly `container-only`; aliases are reported
separately. See [coverage](docs/COVERAGE.md), [methodology](docs/METHODOLOGY.md),
[qualification](docs/QUALIFICATION.md), [licenses](DATA-LICENSES.md) and
[the eleven OpenSpec changes](openspec/REMEDIATION.md).

## Quick start

From the corpus checkout with a filerepack checkout alongside it:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[verify,dev]'
python -m pip install -e '../filerepack[serialization]'
python -m frbench check
python -m frbench run --filerepack ../filerepack --tier smoke \
  --strict-verifiers --min-verified 12 --output results/smoke
```

Python 3.10+ is supported by the harness. `verify` installs independent readers; `corpus` adds
libraries needed to regenerate fixtures. External tools are separate dependencies. Missing
independent verifiers are explicit skips; `--strict-verifiers` fails on any skip. A run with
zero verified cases always fails. Missing optimizer backends can produce unchanged files;
inspect the packer reasons and tool inventory rather than treating unchanged as writer success.

`--filerepack` imports that checkout including working changes. For published measurements use
an immutable snapshot, as described below. Omit it to use the installed implementation.

On macOS, common tools can be installed with:

```sh
brew install sevenzip ffmpeg qpdf ghostscript imagemagick jpegoptim optipng gifsicle \
  webp zstd brotli lz4 lzip lzop hdf5 netcdf flac r
python -m frbench doctor
```

RAR, MP3Packer, OptiVorbis, JPEG XL/HEIF encoders, DICOM codecs and filerepack's native OLE writer
have separate backend requirements. `doctor` records availability, versions and executable hashes.
The benchmark records the Python packages, source identity, options and tool overrides.

## Installed artifacts and corpus location

The wheel contains the runtime harness and legal notices. The source distribution additionally
contains the dataset, tests and specifications. Install the wheel with an explicit corpus checkout:

```sh
frbench check --root /path/to/filerepack-testdata
# Alternatively set FILEREPACK_TESTDATA_ROOT=/path/to/filerepack-testdata
```

Without an explicit root, the current checkout and then the source package checkout are searched.
An installed wheel without corpus assets gives an actionable diagnostic. Packaging is tested in
fresh environments outside the checkout with imports verified to come from the installed artifact.

## Measure and compare

```sh
python scripts/current_baseline.py --filerepack ../filerepack \
  --revision 95827f3206d68760819d1a0f21ab9acfcf74313b \
  --output results/fixed --publish results/fixed-evidence.json

python -m frbench run --filerepack ../filerepack --repeat 3 --warmup 1 \
  --strict-verifiers --require-outcomes --output results/full
python -m frbench run --filerepack ../filerepack --tier control --output results/controls
python -m frbench run --filerepack ../filerepack --tier stress --output results/stress
python -m frbench run --filerepack ../filerepack --native-only --output results/native
python -m frbench compare results/full/report.json results/next/report.json
python -m frbench coverage --filerepack ../filerepack --strict
```

Filters include `--family`, `--ext` and case ID substrings in `--case`. Lossless, ultra,
experimental, checkpoint-load-only and dryrun profiles use the same independent contracts.
Lossy overrides require different oracles and are refused here. The default lossless profile
sets `keep_meta=True` and `wmv_lossless=True`.

Reports include per-attempt logs, JSON, CSV, Markdown, coverage and sampled process-tree RSS.
Output directories must be new. `--keep-work` retains failing disposable copies for diagnosis.
Exit code 1 reports preservation/growth failures, exceptions, timeouts, corpus changes, violated
outcome contracts or qualification gates. `--require-outcomes` enforces declared routing/refusal
contracts. Optional RTF routing is enforced only if that implementation registers RTF, and its
capability availability is recorded per attempt. It is still independently verified when unsupported.

Native/original/syntax, originals, generated cases and stress inputs have separate totals.
Alias/container-only cases, controls, failures and skips are excluded from native savings.
Comparisons flag corpus, options, selected cases, harness, environment and repetition mismatches.
The [current repeated baseline](docs/CURRENT-BASELINE.md) supersedes the
[historical single-attempt baseline](docs/BASELINE.md); neither estimates typical user-file savings.

## Validate and extend

```sh
python -m frbench check --strict-verifiers
python scripts/qualify_oracles.py --strict
python -m pytest -q
python -m ruff check frbench tests scripts
python scripts/validate_distribution.py
python -m frbench generate --extend --filerepack ../filerepack --strict
python scripts/update_coverage.py --filerepack ../filerepack
```

`--extend` stages new cases, preserves all existing bytes, checks collisions and verifies new
positive cases before publication. An error rolls back changes. Full `generate` explicitly
regenerates `corpus/generated/` and changes the dataset identity. `--scale N` increases record
counts and stress input size. `--minimal` records omitted optional generators as gaps.

Checked-in bytes and hashes are the stable reference. Binary regeneration can vary with tool
versions, timestamps, encryption randomness and ephemeral CRX test keys. Do not regenerate while
measuring. Originals are preserved and can be restored using `python scripts/fetch_originals.py`,
which requires the pinned size and SHA-256. See [CONTRIBUTING.md](CONTRIBUTING.md).
