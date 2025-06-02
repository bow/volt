#!/usr/bin/env -S just --justfile
# Justfile for common development tasks.
#
# Copyright (c) 2022-2025 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of volt <https://github.com/bow/volt>.

app-id   := 'volt'
src-dir  := 'src' / app-id
test-dir := 'tests'
docs-dir := 'docs'

python-ver        := 'py313'
rtd-build-api-url := "https://readthedocs.org/api/v3/projects/{{app-id}}/versions/latest/builds/"

# Show this help and exit.
default:
    @just --list --justfile {{justfile()}} --list-heading $'{{BOLD}}{{CYAN}}◉ {{YELLOW}}{{app-id}}{{CYAN}} dev console{{NORMAL}}\n'

# Build wheel and source dist.
build:
    uv build

# Remove build and test artifacts.
clean:
    @rm -rf build/ dist/ wheels/ \
        .coverage .coverage.xml .junit.xml htmlcov/ .cache/ .mypy_cache/ .pytest_cache/ .ruff_cache/ \
        ./{{test-dir}}/fixtures/ok_minimal/target \
        ./{{test-dir}}/fixtures/ok_extended/target \
        result
    @docker rmi ghcr.io/bow/{{app-id}} 2> /dev/null || true

# Set local development environment with nix and direnv.
dev:
    #!/usr/bin/env bash
    if command -v nix-env > /dev/null && command -v direnv > /dev/null; then
        printf "Configuring a local dev environment and setting up git pre-commit hooks...\n" >&2 \
            && direnv allow . > /dev/null \
            && DIRENV_LOG_FORMAT="" direnv exec {{justfile_directory()}} pre-commit install \
            && printf "Done.\n" >&2
    elif command -v nix-env > /dev/null; then
        printf "Error: direnv seems to be unconfigured or missing\n" >&2 && exit 1
    elif command -v direnv > /dev/null; then
        printf "Error: nix seems to be unconfigured or missing\n" >&2 && exit 1
    else
        printf "Error: both direnv and nix seem to be unconfigured and/or missing" >&2 && exit 1
    fi

# Reset local development environment.
dev-reset:
    rm -rf .venv .direnv
    direnv reload

# Build HTML documentation.
[working-directory: 'docs']
docs-html:
    make html

# Build HTML documentation and serve it.
docs-html-serve:
    #!/usr/bin/env bash
    if command -v entr > /dev/null 2>&1; then
        find {{docs-dir}} -not \( -path "{{docs-dir}}/_build" -prune \) \
            | entr -rcdns '$(MAKE) -B docs-html && python -m http.server -d {{docs-dir}}/_build/html'
    else
        make -B docs-html && python -m http.server -d {{docs-dir}}/_build/html
    fi

# Reorder imports with ruff then apply black.
fmt:
    ruff check --fix
    black -t {{python-ver}} {{src-dir}} {{test-dir}}

# Build a docker image and load it into a running daemon.
img:
    nix build .#dockerArchiveStreamer
    ./result | docker image load

# Lint the code.
lint: lint-types lint-style lint-metrics

# Lint the type hints.
lint-types:
    mypy {{src-dir}} {{test-dir}}

# Lint style conventions.
lint-style:
    ruff check
    black -t {{python-ver}} --check {{src-dir}} {{test-dir}}

# Lint various metrics.
lint-metrics:
    radon cc --total-average --show-closures --show-complexity --min C {{src-dir}}

# Perform all security analyses.
scan-sec: scan-sec-ast scan-sec-deps

# Perform static security analysis on the AST.
scan-sec-ast:
    bandit -c pyproject.toml -r {{src-dir}}

# Scan dependencies for reported vulnerabilities.
scan-sec-deps:
    uv export --no-hashes | safety check --full-report --stdin

# Run the test suite.
test:
    py.test \
        --junitxml=.junit.xml \
        --cov={{src-dir}} \
        --cov-report=term-missing \
        --cov-report=xml:.coverage.xml \
        --cov-report=html:htmlcov \
        {{src-dir}} {{test-dir}}

# Update flake and Python dependencies.
update:
    nix flake update
    uv sync -U
    rm -rf .venv
    direnv reload
    just fmt
