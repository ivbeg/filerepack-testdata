# Contributing

Run `python -m pytest -q`, `ruff check frbench tests scripts`, and `python -m frbench check`.
Run a focused benchmark when changing generators/oracles. Changes to filerepack belong in its
repository; this repository must remain independently runnable without its internal test package.
Run `python scripts/qualify_oracles.py --strict` in an environment with all independent readers,
`python -m frbench check --strict-verifiers`, and the isolated artifact test
`python scripts/validate_distribution.py`. Native optional skips are acceptable in the portable
harness lane and rejected by native qualification. Add every new `(kind, format, codec)` profile
to `docs/oracle-conformance.json`; inventory completeness is tested.

Each positive case needs an actual readable file, an independent oracle, explicit scope/tier,
license/provenance and inventory hashes. An extension alias does not establish application support.
Optional generator failures must be recorded, not silently dropped or replaced with renamed blobs.
Preserve every original's bytes. Use `expectation: unchanged` for malformed/protected controls.

New oracles should be tested with both a legitimate recompression and a deliberately corrupted
candidate. Use exact bits for lossless scientific values (including signed zero/NaN when present),
retain order and metadata required by the declared profile, and document narrower comparison limits.
Don't accept a file just because its magic bytes or parser opening succeeded.

To add an original, include upstream redistribution terms, legal notices, a commit-pinned URL and
SHA-256/size, and update `corpus/originals/index.json`. Keep small, meaningful assets.
Manifest/index records must match exactly. Link included legal notices in `provenance.license_files`;
the integrity check requires them to exist under `licenses/`.
Generated corpus bytes are checked in for stable comparison; use `--scale` for larger local experiments.
Never check in `.venv`, results/work directories or arbitrary downloaded/private documents.

The harness does not publish or commit results. Review the Git diff and licenses before
choosing to publish changes to this repository.
`generate --extend` stages and qualifies only new case IDs, restores existing pinned bytes in its
staging area, rejects path collisions, and rolls back a failed publication. Full `generate` is
explicit regeneration and produces a new dataset identity. The 16 MiB stress TAR is in a separate
`stress` tier and excluded from ordinary compression aggregates.
