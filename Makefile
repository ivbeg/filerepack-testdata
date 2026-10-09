PYTHON ?= .venv/bin/python
FILEREPACK ?= ../filerepack
OUT ?= results/run

.PHONY: test check smoke benchmark generate extend coverage qualify distribution

test:
	$(PYTHON) -m pytest -q
	$(PYTHON) -m ruff check frbench tests scripts

check:
	$(PYTHON) -m frbench check

smoke:
	$(PYTHON) -m frbench run --filerepack $(FILEREPACK) --tier smoke --strict-verifiers --min-verified 12 --output $(OUT)

benchmark:
	$(PYTHON) -m frbench run --filerepack $(FILEREPACK) --repeat 3 --warmup 1 --strict-verifiers --require-outcomes --output $(OUT)

generate:
	$(PYTHON) -m frbench generate --filerepack $(FILEREPACK) --strict

extend:
	$(PYTHON) -m frbench generate --extend --filerepack $(FILEREPACK) --strict
	$(PYTHON) scripts/update_coverage.py --filerepack $(FILEREPACK)

coverage:
	$(PYTHON) -m frbench coverage --filerepack $(FILEREPACK)

qualify:
	$(PYTHON) -m frbench check --strict-verifiers
	$(PYTHON) scripts/qualify_oracles.py --strict

distribution:
	$(PYTHON) scripts/validate_distribution.py
