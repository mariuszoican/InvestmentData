# Data Purchase — payment pipeline
# Run from the repo root.

PYTHON ?= .venv/bin/python
ifeq ($(wildcard $(PYTHON)),)
  PYTHON := python3
endif

export PYTHONPATH := src/build

.PHONY: payments panels help

help:
	@echo "Targets:"
	@echo "  make payments ID=20260824   Write data/payments/payments_YYYYMMDD.xlsx"
	@echo "  make panels                 Write data/processed/processed_panels.csv"

payments:
	@test -n "$(ID)" || (echo "Usage: make payments ID=20260824"; exit 1)
	$(PYTHON) src/build/process_payments.py --session $(ID)

panels:
	$(PYTHON) src/build/process_panels.py
