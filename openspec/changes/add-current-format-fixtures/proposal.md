# Change: Cover current registry and detected routes

## Why
GGUF, ONNX, Safetensors, tracev3, gzip and local RTF capability have no fixtures.

## What Changes
- Add bounded passive model-format inspection fixtures and refusal controls.
- Add tracev3/gzip/RTF fixtures with independent oracles.
- Cover compound gzip aliases and content-detected inputs.

## Impact
- Affected specs: `format-fixtures`.
- Affected code: frbench, corpus, tests, CI and documentation as scoped in tasks.
- Implementation authorized by the user on 2026-10-09; validation evidence is required before completion.
