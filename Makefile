PYTHON ?= .venv/bin/python
FILEREPACK ?= ../filerepack
OUT ?= results/run

.PHONY: test check smoke benchmark generate extend coverage

test:
	$(PYTHON) -m pytest -q
	$(PYTHON) -m ruff check frbench tests scripts

check:
	$(PYTHON) -m frbench check

smoke:
	$(PYTHON) -m frbench run --filerepack $(FILEREPACK) --tier smoke --output $(OUT)

benchmark:
	$(PYTHON) -m frbench run --filerepack $(FILEREPACK) --repeat 3 --warmup 1 --output $(OUT)

generate:
	$(PYTHON) -m frbench generate --filerepack $(FILEREPACK) --strict

extend:
	$(PYTHON) -m frbench generate --extend --filerepack $(FILEREPACK) --strict
	$(PYTHON) scripts/update_coverage.py --filerepack $(FILEREPACK)

coverage:
	$(PYTHON) -m frbench coverage --filerepack $(FILEREPACK)
