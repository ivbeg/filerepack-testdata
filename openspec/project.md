# Project Context

## Purpose
filerepack-testdata is a checksummed, licensed corpus and an independent preservation-aware
benchmark harness for filerepack. Input coverage, accepted rewriting, verifier availability and
real-workload representativeness are distinct claims.

## Tech Stack
Python 3.10+, setuptools, pytest, Ruff, optional native format readers and external codecs.
The Python sources are in `frbench/`, fixtures in `corpus/`, evidence in `docs/`.

## Conventions
UTF-8, LF, four-space Python indentation, 100-column target. Synthetic fixture values are public
and deterministic. Originals have immutable upstream URLs, exact hashes and legal notices.
Oracles never execute macros, unpickle arbitrary objects or execute model graphs.

## Validation
Run pytest and Ruff; verify checksums and decode qualified profiles. Run focused recompression
when an oracle or generator changes. Keep absent dependencies explicit. OpenSpec changes use
strict validation; completion checkboxes require direct implementation/test evidence.

## Scope and authorization
The 2026-10-09 repository audit is the source of the eleven remediation changes. The user
explicitly requested proposals for all findings and immediate implementation. Work is authorized
locally on `codex/testdata-audit-remediation`; no release or public visibility change is implied.
Do not modify the sibling filerepack checkout, which contains user changes. Qualification must
identify a fixed upstream revision or a complete source snapshot, plus corpus and harness hashes.
