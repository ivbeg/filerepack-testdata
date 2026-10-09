# Current repeated baseline · 2026-10-09

All **477 cases** were measured three times after one discarded warmup each: 1,431 measured attempts and 477 warmups, every attempt on a fresh copy. The implementation is the immutable Git archive of commit `95827f3206d68760819d1a0f21ab9acfcf74313b`; working changes and ignored native build artifacts were excluded. The same available external backends were inventoried by version and executable hash.

Local platform: macOS arm64 / CPython 3.13.7. Source and harness hashes stayed stable. The harness was an uncommitted remediation tree based on `5ca79e8`; its full Python source hash identifies the actual code measured. Timings are descriptive results from a development machine, not controlled microbenchmark or production-workload estimates.

| Outcome | Cases |
|---|---:|
| improved | 297 |
| qualification-failure | 1 |
| unchanged | 179 |

**476 cases independently qualified; one routing contract failed.** There were zero preservation/growth failures, worker errors, timeouts or missing-verifier skips. All 24 controls remained byte-identical. The strict command exits 1 because the required minimum was 477 and the routing expectation below was violated. The failure is retained in the [portable JSON](current-baseline.json); it is excluded from qualified savings.

## Observed route gap

`archives-detected-tar-gzip` is a valid gzip-compressed TAR named only `.gzip`. `identify_filename` reports `family=standalone, packer=gzip`, while its declared detected-route contract expects `family=tar.gz`. All three measured attempts preserved the decoded TAR content and reduced the wrapper, but failed that routing contract. The explicit `.tar.gzip` alias passed. This identifies a gap in the pinned filerepack revision; this repository does not modify the sibling implementation.

## Verified observations

| Subset | Cases | Input bytes | Output bytes | Weighted savings |
|---|---:|---:|---:|---:|
| Native/original/syntax | 295 | 28,202,287 | 20,805,691 | 26.23% |
| Upstream originals | 51 | 3,110,222 | 3,063,360 | 1.51% |
| Generated native/syntax | 244 | 25,092,065 | 17,742,331 | 29.29% |
| All qualified ordinary cases | 451 | 69,021,778 | 36,444,730 | 47.20% |
| Separate stress tier | 1 | 16,783,360 | 16,783,360 | 0.00% |

Ordinary totals exclude controls and stress. Native totals also exclude alias/container-only inputs. The original subtotal contains 51 positive original files; three additional original controls are counted only as preservation/refusal evidence. Original and synthetic results are not interchangeable.

The 16 MiB stress TAR stayed unchanged; operation time and sampled process-tree RSS are recorded separately. Unchanged does not establish that a writer attempted a useful transformation. The simple scientific graph/group fixtures were independently verified and unchanged under the size policy. tracev3 improved; the three model inspector fixtures stayed unchanged with explicit inspection-only reasons.

Optional RTF is absent from this committed implementation; its two positive profiles were independently verified unchanged and report capability absence. The separate [local RTF qualification](rtf-capability.json) used the current dirty source snapshot and verified both picture profiles improving across three repeats while its malformed control stayed unchanged.

The optimized GIF uses a different palette index for the same background color and equivalent disposal instructions. Decoded frames, timing, loop and semantic metadata remain identical. A regression checks this normalization and another checks that an actual background color change fails; arbitrary metadata loss is not waived.

## Identities

- Implementation Python SHA-256: `036ebe35cc38529a9965086eacb8f7323dab683f16a9e8c8d040707228ca10fb`
- Harness Python SHA-256: `d913478958bb29ece545f97e5102686bfb1440c94ea36d3965b623ce9a060154`
- Corpus manifest SHA-256: `80266e09e673e787937b8de6770e6a9367557b861b8075046f9c2f9a2257745d`

Exact local packages are in [`requirements-lock.txt`](../requirements-lock.txt). The portable JSON contains options, tool/package identities, per-attempt times/RSS, verification, outcome contracts and accepted-result evidence; raw logs, temporary files and duplicated detailed options remain under ignored `results/final-477/`.

Reproduce with:

```sh
python scripts/current_baseline.py --filerepack ../filerepack \
  --revision 95827f3206d68760819d1a0f21ab9acfcf74313b \
  --output results/repeated --publish results/repeated-evidence.json
```

Remote CI configurations and actually executed local qualification are described separately in [QUALIFICATION.md](QUALIFICATION.md). The [historical baseline](BASELINE.md) describes an older corpus/dirty source and is not directly comparable.
