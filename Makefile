# Data Purchase — analysis pipeline
# Run from the repo root.

PYTHON ?= .venv/bin/python
ifeq ($(wildcard $(PYTHON)),)
  PYTHON := python3
endif

export PYTHONPATH := src/build

.PHONY: panels session payments analyze clean-interim help

help:
	@echo "Targets:"
	@echo "  make panels              Rebuild interim + full panels for include:true sessions"
	@echo "  make session ID=20260824 Process one session from config/sessions.yaml"
	@echo "  make payments ID=20260824  Same as session (log + payments + first-pass panels)"
	@echo "  make clean-interim       Delete rebuildable data/interim panels"

panels:
	$(PYTHON) src/build/build_panels.py

session:
	@test -n "$(ID)" || (echo "Usage: make session ID=20260824"; exit 1)
	$(PYTHON) src/build/process_session.py --session $(ID)

payments:
	@test -n "$(ID)" || (echo "Usage: make payments ID=20260824"; exit 1)
	$(PYTHON) src/build/process_session.py --session $(ID)

clean-interim:
	rm -rf data/interim/*
	@echo "Removed data/interim/* (raw and processed untouched)"
