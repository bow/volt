# Makefile for common development tasks.
#
# Copyright (c) 2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of Volt <https://github.com/bow/volt>.

# Cross-platform adjustments.
SYS := $(shell uname 2> /dev/null)
ifeq ($(SYS),Linux)
GREP_EXE := grep
DATE_EXE := date
else ifeq ($(SYS),Darwin)
GREP_EXE := ggrep
DATE_EXE := gdate
else
$(error Unsupported development platform)
endif

# Application name.
APP_NAME := volt

# Latest version of supported Python.
PYTHON_VERSION := 3.11.0

# Name of virtualenv for development.
VENV_NAME ?= $(APP_NAME)-dev

# Non-pyproject.toml dependencies.
PIP_DEPS := poetry==1.2.2 poetry-dynamic-versioning==0.19.0 twine==4.0.1

# Non-pyproject.toml dev dependencies.
PIP_DEV_DEPS := pre-commit

## Toggle for dev setup with pyenv.
WITH_PYENV ?= 1

# Various build info.
GIT_TAG    := $(shell git describe --tags --always --dirty 2> /dev/null || echo "untagged")
GIT_COMMIT := $(shell git rev-parse --quiet --verify HEAD || echo "?")
GIT_DIRTY  := $(shell test -n "$(shell git status --porcelain)" && echo "-dirty" || true)
BUILD_TIME := $(shell $(DATE_EXE) -u '+%Y-%m-%dT%H:%M:%SZ')
IS_RELEASE := $(shell ((echo "${GIT_TAG}" | $(GREP_EXE) -qE "^v?[0-9]+\.[0-9]+\.[0-9]+$$") && echo '1') || true)

IMG_NAME   := ghcr.io/bow/$(APP_NAME)
ifeq ($(IS_RELEASE),1)
IMG_TAG    := $(GIT_TAG)
else
IMG_TAG    := latest
endif

WHEEL_DEPS_DIR ?= $(CURDIR)/wheels/deps

## Rules ##

all: help


.PHONY: build
build: build-deps  ## Build wheel and source dist.
	poetry build
	twine check dist/*

.PHONY: build-deps
build-deps: | $(WHEEL_DEPS_DIR)  ## Build wheels of dependencies.
	poetry export --without dev --without-hashes -f requirements.txt -o /dev/stdout | \
		pip wheel -r /dev/stdin --wheel-dir=$(WHEEL_DEPS_DIR)

$(WHEEL_DEPS_DIR):
	mkdir -p $@


.PHONY: clean
clean:  ## Remove build and test artifacts, including built Docker images.
	rm -rf build/ dist/ htmlcov/ .coverage.xml .junit.xml && (docker rmi $(IMG_NAME) 2> /dev/null || true)


.PHONY: clean-pyenv
clean-pyenv:  ## Remove the created pyenv virtualenv.
	pyenv virtualenv-delete -f $(VENV_NAME) && rm -f .python-version


.PHONY: env
env:  ## Configure a local development environment.
	@if command -v pyenv virtualenv > /dev/null 2>&1 && [ "$(WITH_PYENV)" == "1" ]; then \
		printf "Configuring a local dev environment using pyenv ...\n" >&2 \
			&& pyenv install -s "$(PYTHON_VERSION)" \
			&& pyenv virtualenv -f "$(PYTHON_VERSION)" "$(VENV_NAME)" \
			&& printf "%s\n%s" "$(VENV_NAME)" "$(PYTHON_VERSION)" > .python-version \
			&& . "$(shell pyenv root)/versions/$(VENV_NAME)/bin/activate" \
			&& pip install --upgrade pip && pyenv rehash \
			&& pip install $(PIP_DEPS) $(PIP_DEV_DEPS) && pyenv rehash \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.create false \
			&& poetry install && pyenv rehash \
			&& pre-commit install && pyenv rehash \
			&& printf "Done.\n" >&2; \
	else \
		printf "Configuring a local, bare dev environment ...\n" >&2 \
			&& pip install $(PIP_DEPS) $(PIP_DEV_DEPS) \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.create false \
			&& poetry install \
			&& pre-commit install \
			&& printf "Done.\n" >&2; \
	fi


.PHONY: fmt
fmt:  ## Apply Black.
	poetry run black -t py311 volt tests


.PHONY: help
help:  ## Show this help.
	$(eval PADLEN=$(shell $(GREP_EXE) -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| cut -d':' -f1 \
		| awk '{cur = length($$0); lengths[cur] = lengths[cur] $$0 ORS; max=(cur > max ? cur : max)} END {printf "%s", max}' \
		|| (true && echo 0)))
	@($(GREP_EXE) --version > /dev/null 2>&1 || (>&2 "error: GNU grep not installed"; exit 1)) \
		&& printf "\033[36m◉ %s dev console\033[0m\n" "$(APP_NAME)" >&2 \
		&& $(GREP_EXE) -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m» \033[33m%*-s\033[0m \033[36m· \033[0m%s\n", $(PADLEN), $$1, $$2}' \
			| sort


.PHONY: img
img:  ## Build and tag the Docker container.
	docker build --build-arg REVISION=$(GIT_COMMIT)$(GIT_DIRTY) --build-arg BUILD_TIME=$(BUILD_TIME) --tag $(IMG_NAME):$(IMG_TAG) .


.PHONY: install-build
install-build:  ## Install dependencies required only for building.
	pip install $(PIP_DEPS)


.PHONY: lint
lint:  lint-types lint-style lint-metrics  ## Lint the code.


.PHONY: lint-types
lint-types:  ## Lint the type hints.
	poetry run mypy volt tests


.PHONY: lint-style
lint-style:  ## Lint style conventions.
	poetry run flake8 --statistics volt tests && poetry run black -t py311 --check .


.PHONY: lint-metrics
lint-metrics:  ## Lint various metrics.
	poetry run radon cc --total-average --show-closures --show-complexity --min C volt


.PHONY: scan-security
scan-security: scan-security-ast scan-security-deps  ## Perform all security analyses.


.PHONY: scan-security-ast
scan-security-ast:  ## Perform static security analysis on the AST.
	poetry run bandit -r crimson


.PHONY: scan-security-deps
scan-security-deps:  ## Scan dependencies for reported vulnerabilities.
	poetry export --without-hashes -f requirements.txt -o /dev/stdout | poetry run safety check --full-report --stdin


.PHONY: test
test:  ## Run the test suite.
	poetry run py.test --junitxml=.junit.xml --cov=volt --cov-report=term-missing --cov-report=xml:.coverage.xml --cov-report=html:htmlcov volt tests
