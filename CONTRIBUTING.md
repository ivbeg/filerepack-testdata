# Contributing

Run `python -m pytest -q`, `ruff check frbench tests scripts`, and `python -m frbench check`.
Run a focused benchmark when changing generators/oracles. Changes to filerepack belong in its
repository; this repository must remain independently runnable without its internal test package.

Each positive case needs an actual readable file, an independent oracle, explicit scope/tier,
license/provenance and inventory hashes. An extension alias does not establish application support.
Optional generator failures must be recorded, not silently dropped or replaced with renamed blobs.
Preserve every original's bytes. Use `expectation: unchanged` for malformed/protected controls.

New oracles should be tested with both a legitimate recompression and a deliberately corrupted
candidate. Use exact bits for lossless scientific values (including signed zero/NaN when present),
retain order and metadata required by the declared profile, and document narrower comparison limits.
Don't accept a file just because its magic bytes or parser opening succeeded.

To add an original, include upstream redistribution terms, legal notices, a commit-pinned URL and
SHA-256/size, and update `corpus/originals/index.json`. Keep small, meaningful assets. Generated
corpus bytes are checked in for stable comparison; use `--scale` for larger local experiments.
Never check in `.venv`, results/work directories or arbitrary downloaded/private documents.

The harness does not publish or commit results. Review the Git diff and licenses before
choosing to publish changes to this repository.
