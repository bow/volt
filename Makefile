# Makefile for common development tasks.

PROJECT_DIR := $(CURDIR)
APP_NAME := volt
# Latest version of supported Python.
PYTHON_VERSION := 3.9.5
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


.PHONY: help
help:  ## Show this help.
	@($(GREP_EXE) --version > /dev/null 2>&1 || (>&2 "error: GNU grep not installed"; exit 1)) \
		&& printf "\033[33m%s dev console\033[0m\n" "$(APP_NAME)" >&2 \
		&& $(GREP_EXE) -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%10s\033[0m · %s\n", $$1, $$2}' >&2
