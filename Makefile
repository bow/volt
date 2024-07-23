# Makefile for common development tasks.
#
# Copyright (c) 2022-2023 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of volt <https://github.com/bow/volt>.

APP_NAME := volt
DOCS_DIR := $(CURDIR)/docs
RTD_BUILD_API_URL := https://readthedocs.org/api/v3/projects/volt/versions/latest/builds/


all: help


.PHONY: build
build:  ## Build wheel and source dist.
	poetry build


.PHONY: clean
clean:  ## Remove build and test artifacts, including built Docker images.
	rm -rf build/ dist/ wheels/ \
			.coverage .coverage.xml .junit.xml htmlcov/ .cache/ .mypy_cache/ .pytest_cache/ \
			./tests/fixtures/ok_minimal/target \
			./tests/fixtures/ok_extended/target \
			result \
		&& (docker rmi $(IMG_NAME) 2> /dev/null || true)


.PHONY: dev
dev:  ## Configure local development environment with nix and direnv.
	@if command -v nix-env > /dev/null && command -v direnv > /dev/null; then \
		printf "Configuring a local dev environment and setting up git pre-commit hooks...\n" >&2 \
			&& direnv allow . > /dev/null \
			&& DIRENV_LOG_FORMAT="" direnv exec $(CURDIR) pre-commit install \
			&& printf "Done.\n" >&2; \
	elif command -v nix-env > /dev/null; then \
		printf "Error: direnv seems to be unconfigured or missing\n" >&2 && exit 1; \
	elif command -v direnv > /dev/null; then \
		printf "Error: nix seems to be unconfigured or missing\n" >&2 && exit 1; \
	else \
		printf "Error: both direnv and nix seem to be unconfigured and/or missing" >&2 && exit 1; \
	fi


.PHONY: dev-reset
dev-reset:  ## Resets the local development environment.
	rm -rf .venv .direnv && direnv reload


.PHONY: docs-html
docs-html:  ## Build HTML documentation.
	cd $(DOCS_DIR) && LC_ALL=C.UTF_8 make html


.PHONY: docs-html-serve
docs-html-serve:  ## Build HTML documentation and serve it.
	@if command -v entr > /dev/null 2>&1; then \
		find $(DOCS_DIR) -not \( -path "$(DOCS_DIR)/_build" -prune \) \
			| entr -rcdns '$(MAKE) -B docs-html && python -m http.server -d $(DOCS_DIR)/_build/html'; \
	else \
		make -B docs-html && python -m http.server -d $(DOCS_DIR)/_build/html; \
	fi


.PHONY: fmt
fmt:  ## Apply Black.
	black -t py312 volt tests


.PHONY: help
help:  ## Show this help.
	$(eval PADLEN=$(shell grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| cut -d':' -f1 \
		| awk '{cur = length($$0); lengths[cur] = lengths[cur] $$0 ORS; max=(cur > max ? cur : max)} END {printf "%s", max}' \
		|| (true && echo 0)))
	@(grep --version > /dev/null 2>&1 || (>&2 "error: GNU grep not installed"; exit 1)) \
		&& printf "\033[36m◉ %s dev console\033[0m\n" "$(APP_NAME)" >&2 \
		&& grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m» \033[33m%-*s\033[0m \033[36m· \033[0m%s\n", $(PADLEN), $$1, $$2}' \
			| sort


.PHONY: img
img:  ## Build a docker image and load it into a running daemon.
	nix build .#dockerArchiveStreamer && ./result | docker image load


.PHONY: lint
lint:  lint-types lint-style lint-metrics  ## Lint the code.


.PHONY: lint-types
lint-types:  ## Lint the type hints.
	mypy volt tests


.PHONY: lint-style
lint-style:  ## Lint style conventions.
	flake8 --statistics volt tests && black -t py312 --check volt tests


.PHONY: lint-metrics
lint-metrics:  ## Lint various metrics.
	python -m radon cc --total-average --show-closures --show-complexity --min C volt


.PHONY: scan-sec
scan-sec: scan-sec-ast scan-sec-deps  ## Perform all security analyses.


.PHONY: scan-sec-ast
scan-sec-ast:  ## Perform static security analysis on the AST.
	bandit -r crimson


.PHONY: scan-sec-deps
scan-sec-deps:  ## Scan dependencies for reported vulnerabilities.
	poetry export --without-hashes -f requirements.txt -o /dev/stdout | safety check --full-report --stdin


.PHONY: test
test:  ## Run the test suite.
	py.test --junitxml=.junit.xml --cov=volt --cov-report=term-missing --cov-report=xml:.coverage.xml --cov-report=html:htmlcov volt tests
