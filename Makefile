# Makefile for common development tasks.

PROJECT_DIR := $(CURDIR)
APP_NAME := volt
# Latest version of supported Python.
PYTHON_VERSION := 3.10.0
# Name of virtualenv for development.
ENV_NAME ?= $(APP_NAME)-dev
# Non-pyproject.toml dependencies.
PIP_DEPS := poetry poetry-dynamic-versioning pre-commit
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


.PHONY: clean
clean:  ## Remove built artifacts.
	rm -rf .coverage.xml dist/


.PHONY: help
help:  ## Show this help.
	$(eval PADLEN=$(shell $(GREP_EXE) -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| cut -d':' -f1 \
		| awk '{cur = length($$0); lengths[cur] = lengths[cur] $$0 ORS; max=(cur > max ? cur : max)} END {printf "%s", max}' \
		|| (true && echo 0)))
	@($(GREP_EXE) --version > /dev/null 2>&1 || (>&2 "error: GNU grep not installed"; exit 1)) \
		&& printf "\033[33m⋄ %s dev console\033[0m\n" "$(APP_NAME)" >&2 \
		&& $(GREP_EXE) -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
			| sort \
			| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[33m» \033[36m%*-s\033[0m \033[33m· \033[0m%s\n", $(PADLEN), $$1, $$2}'


.PHONY: install-dev
install-dev:  ## Configure a local development setup.
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
		printf "Configuring a local, bare dev environment ...\n" >&2 \
			&& pip install $(PIP_DEPS) && pyenv rehash \
			&& poetry config experimental.new-installer false \
			&& poetry config virtualenvs.in-project true \
			&& poetry install && pyenv rehash \
			&& pre-commit install && pyenv rehash \
			&& printf "Done.\n" >&2; \
	fi


.PHONY: lint
lint:  lint-types lint-style lint-metrics -lint-sec  ## Lint the code.


.PHONY: lint-types
lint-types:  ## Lint the type hints.
	poetry run mypy volt tests


.PHONY: lint-style
lint-style:  ## Lint style conventions.
	poetry run flake8 --statistics volt tests && poetry run black -t py310 --check .


.PHONY: lint-metrics
lint-metrics:  ## Lint various metrics.
	poetry run radon cc --total-average --show-closures --show-complexity --min C volt


.PHONY: lint-sec
lint-sec:  ## Lint security.
	poetry run bandit -r volt


.PHONY: test
test:  ## Run the test suite.
	poetry run py.test --cov=volt --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml:.coverage.xml volt tests
