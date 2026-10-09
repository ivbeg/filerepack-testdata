# Qualification evidence · 2026-10-09

Configuration and executed results are distinct. The local results below were actually obtained
on macOS arm64; the new GitHub Actions matrix has not been executed remotely in this change.

| Check | Executed result |
|---|---|
| OpenSpec strict validation | 11 changes passed |
| Full harness suite, Python 3.13.7 with native readers | 119 passed; one netCDF/NumPy ABI warning, no test skips |
| Ruff | Passed |
| Manifest/provenance integrity | 477 inventories match; all 432 previously published assets unchanged |
| Independent preflight | 453 positive cases decoded; zero failures or missing-reader skips |
| Oracle conformance | 71 profiles covering all 47 kinds passed; zero missing-reader skips |
| Portable harness, Python 3.10.20 | 81 passed; 38 explicit optional-reader skips |
| Wheel and sdist, Python 3.10.20 and 3.13.7 | Installed outside checkout; imports, explicit corpus and missing-root diagnostics passed |
| Upstream restoration | Pinned qpdf PDF re-downloaded in a temporary root; size/hash match |
| Local optional RTF capability | Two PNG-picture profiles improved in all three measured attempts after warmup; malformed control unchanged |
| Current repeated fixed-source baseline | See [CURRENT-BASELINE.md](CURRENT-BASELINE.md) and its portable JSON |

The conformance [inventory](oracle-conformance.json) and [measured results](conformance-results.json)
record the acceptance strategy and corruption check for each profile. 28 profiles use independent
re-encoding/serialization/layout changes; 43 use explicit byte-identity acceptance. Generic tests
exercise destructive truncation, TAR member payload mutation and Zarr array-value mutation.
Targeted regressions exercise PNG/JPEG metadata and high depth, ZIP metadata, USDZ constraints,
HDF5 graphs/references, NetCDF nested values, Arrow signed zero/NaN payloads, PDF text/forms/links,
media tracks/tags/presentation time, and equivalent GIF palette/disposal representations.
This coverage does not certify every subtle mutation or every application feature.

The local RTF measurement used the user's current, dirty filerepack tree, whose source hash is
recorded separately in `rtf-capability.json`. The main repeated baseline uses the immutable
committed `95827f3` snapshot, which does not register RTF. Optional capability absence is explicit
per attempt and does not waive content verification.

## Configured CI

The portable matrix covers Linux/macOS/Windows with Python 3.10 and 3.13, including corpus integrity,
harness tests, lint and isolated distributions. Optional native dependency skips remain visible
in the JUnit report. This matrix is configured; it is not claimed as remotely passed.

The Linux native lane installs independent readers and external tools, then enforces full positive
preflight, all conformance profiles, live coverage, the 12-case smoke set and 24 rejection controls.
Scheduled/manual runs add the complete three-repeat/one-warmup baseline. All result/log artifacts
are uploaded even after failures. Native qualification rejects any missing verifier.
Reader success does not certify that every optimizer backend is installed or attempted.

A run with zero verified cases always fails; stricter minimum-case requirements catch partial runs.
Case-specific routing/status/reason contracts are enabled by `--require-outcomes`. A reported
unchanged file is valid preservation evidence, but is not evidence of a successful optimizer.

## Remaining breadth limits

Originals still consist mainly of small Office/OLE regression samples; original video and wider
user-authored workloads remain useful future additions. Application rendering, high-resolution
PDF render equivalence, all camera pipelines, arbitrary model variants, external tensor bundles,
and intended OLE content transforms are outside the qualified profiles. The 16 MiB stress fixture
is separate from ordinary totals and is not a substitute for a production workload study.
