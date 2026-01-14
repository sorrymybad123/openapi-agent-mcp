.PHONY: help env install test lint fmt clean

CONDA_ENV_NAME ?= openapi-agent-mcp

test:
	poetry run python -m unittest

lint:
	poetry run python -m compileall -q src

fmt:
	@echo "No formatter configured yet."

help:
	@echo "Targets:"
	@echo "  make env       Create/update Conda env ($(CONDA_ENV_NAME)) from environment.yml"
	@echo "  make install   Install Python deps via Poetry (uses current environment)"
	@echo "  make test      Run unit tests (via Poetry)"
	@echo "  make lint      Compile-check (via Poetry)"
	@echo "  make clean     Remove local caches"

env:
	@command -v conda >/dev/null 2>&1 || (echo "conda not found; install Conda/Mamba first" && exit 1)
	@mkdir -p .cache/conda/pkgs
	@export CONDA_PKGS_DIRS="$(CURDIR)/.cache/conda/pkgs"; \
	conda env update -n $(CONDA_ENV_NAME) -f environment.yml --prune || conda env create -f environment.yml
	conda run -n $(CONDA_ENV_NAME) env PIP_REQUIRE_VIRTUALENV=0 python -m pip install -U pip poetry
	@echo "Conda env ready: $(CONDA_ENV_NAME)"
	@echo "Next: conda activate $(CONDA_ENV_NAME) && make install"

install:
	@command -v poetry >/dev/null 2>&1 || (echo "poetry not found; install it (see README.md)" && exit 1)
	poetry install

clean:
	rm -rf .cache
