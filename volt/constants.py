"""Constant values."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause


# Prefix for build directory names.
BUILD_DIR_PREFIX = "volt-build-"

# Config file name.
CONFIG_FNAME = "volt.yaml"

# Default slug replacements.
SLUG_REPLACEMENTS = {
    ("I/O", "io"),
    ("'", ""),
    ('"', ""),
}

# Static directory name.
STATIC_DIRNAME = "static"

# Separator string for text content front matter.
FRONT_MATTER_SEP = "---\n"

# Extension for Markdown source files.
MARKDOWN_EXT = ".md"

# Project source directory name.
PROJECT_SOURCES_DIRNAME = "source"

# Project draft contents directory name.
PROJECT_DRAFTS_DIRNAME = ".drafts"

# Project directory name for extension code.
PROJECT_EXTENSION_DIRNAME = "extension"

# Qualified module name for the project.
PROJECT_MOD_QUALNAME = "volt.project"

# Qualified module name for project extensions.
PROJECT_EXTENSION_MOD_QUALNAME = f"{PROJECT_MOD_QUALNAME}.{PROJECT_EXTENSION_DIRNAME}"

# Module name for custom CLI.
CLI_MOD_NAME = "cli"

# Qualified module name for custom CLI.
PROJECT_CLI_MOD_QUALNAME = f"{PROJECT_EXTENSION_MOD_QUALNAME}.{CLI_MOD_NAME}"

# Module name for custom hooks.
HOOKS_MOD_NAME = "hooks"

# Qualified module name for custom hooks.
PROJECT_HOOKS_MOD_QUALNAME = f"{PROJECT_EXTENSION_MOD_QUALNAME}.{HOOKS_MOD_NAME}"

# Project output directory name.
PROJECT_TARGET_DIRNAME = "target"

# Project static directory name.
PROJECT_STATIC_DIRNAME = f"{PROJECT_SOURCES_DIRNAME}/{STATIC_DIRNAME}"

# Site theme directory name.
SITE_THEMES_DIRNAME = "theme"

# CLI extension filename.
XCMD_FNAME = f"{CLI_MOD_NAME}.py"

# Hooks filename.
HOOKS_FNAME = f"{HOOKS_MOD_NAME}.py"

# Server run filename.
SERVER_RUN_FNAME = ".volt-server.run"

###

# Root module name for the theme.
THEME_ROOT_MOD_QUALNAME = f"{PROJECT_MOD_QUALNAME}.{SITE_THEMES_DIRNAME}"

# Theme engines module name.
ENGINES_MOD_NAME = "engines"

# File name for theme engines.
ENGINES_FNAME = f"{ENGINES_MOD_NAME}.py"

# Theme base settings file name.
THEME_SETTINGS_FNAME = "theme.yaml"

# Site theme static directory name.
THEME_STATIC_DIRNAME = f"{STATIC_DIRNAME}"

# Theme templates directory name.
THEME_TEMPLATES_DIRNAME = "templates"
