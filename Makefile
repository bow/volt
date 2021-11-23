# Makefile for common development tasks.

PROJECT_DIR := $(CURDIR)
APP_NAME := volt
# Latest version of supported Python.
PYTHON_VERSION := 3.10.0
# Name of virtualenv for development.
ENV_NAME ?= $(APP_NAME)-dev
# Non-pyproject.toml dependencies.
PIP_DEPS := poetry pre-commit tox
## Toggle for dev setup with pyenv.
WITH_PYENV ?= 1

# Cross-platform adjustments.
SYS := $(shell uname 2> /dev/null)
ifeq ($(SYS),Linux)
GREP_EXE := grep
else ifeq ($(SYS),Darwin)
GREP_EXE := ggrep
else
$(error Unsupported development platform)
endif


all: help


.PHONY: conf-dev
conf-dev:  ## Configure a local development setup.
	@if command -v pyenv virtualenv > /dev/null 2>&1 && [ "$(WITH_PYENV)" == "1" ]; then \
		printf "Configuring a local dev environment using pyenv ...\n" >&2 \
			&& pyenv install -s "$(PYTHON_VERSION)" \
			&& pyenv virtualenv -f "$(PYTHON_VERSION)" "$(ENV_NAME)" \
			&& printf "%s\n%s" "$(ENV_NAME)" "$(PYTHON_VERSION)" > .python-version \
			&& source "$(shell pyenv root)/versions/$(ENV_NAME)/bin/activate" \
			&& pip install --upgrade pip && pyenv rehash \
			&& pip install $(PIP_DEPS) && pyenv rehash \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.in-project true \
			&& poetry install && pyenv rehash \
			&& pre-commit install && pyenv rehash \
			&& printf "Done.\n" >&2; \
	else \
		printf "Configuring a local dev environment ...\n" >&2 \
			&& pip install $(PIP_DEPS) && pyenv rehash \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.in-project true \
			&& poetry install && pyenv rehash \
			&& pre-commit install && pyenv rehash \
			&& printf "Done.\n" >&2; \
	fi

.PHONY: help
help:  ## Show this help.
	@($(GREP_EXE) --version > /dev/null 2>&1 || (>&2 "error: GNU grep not installed"; exit 1)) \
		&& printf "\033[33m%s dev console\033[0m\n" "$(APP_NAME)" >&2 \
		&& $(GREP_EXE) -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%10s\033[0m · %s\n", $$1, $$2}' >&2
