"""Constant values."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause


# Prefix for build directory names.
BUILD_DIR_PREFIX = "volt-build-"

# Config file name.
CONFIG_FILE_NAME = "volt.toml"

# Default slug replacements.
SLUG_REPLACEMENTS = {
    ("I/O", "io"),
    ("'", ""),
    ('"', ""),
}

# Static directory name.
STATIC_DIR_NAME = "static"

# Separator string for text content front matter.
FRONT_MATTER_SEP = "---\n"

# Extension for Markdown source files.
MARKDOWN_EXT = ".md"

# Project source directory name.
PROJECT_SOURCES_DIR_NAME = "source"

# Project draft contents directory name.
PROJECT_DRAFTS_DIR_NAME = ".drafts"

# Project directory name for extension code.
PROJECT_EXTENSION_DIR_NAME = "extension"

# Qualified module name for the project.
PROJECT_MOD_QUAL_NAME = "volt.project"

# Qualified module name for project extensions.
PROJECT_EXTENSION_MOD_QUAL_NAME = (
    f"{PROJECT_MOD_QUAL_NAME}.{PROJECT_EXTENSION_DIR_NAME}"
)

# Module name for custom CLI.
CLI_MOD_NAME = "cli"

# Qualified module name for custom CLI.
PROJECT_CLI_MOD_QUAL_NAME = f"{PROJECT_EXTENSION_MOD_QUAL_NAME}.{CLI_MOD_NAME}"

# Module name for custom hooks.
HOOKS_MOD_NAME = "hooks"

# Qualified module name for custom hooks.
PROJECT_HOOKS_MOD_QUAL_NAME = f"{PROJECT_EXTENSION_MOD_QUAL_NAME}.{HOOKS_MOD_NAME}"

# Project output directory name.
PROJECT_TARGET_DIR_NAME = "target"

# Project static directory name.
PROJECT_STATIC_DIR_NAME = f"{PROJECT_SOURCES_DIR_NAME}/{STATIC_DIR_NAME}"

# Site theme directory name.
SITE_THEMES_DIR_NAME = "theme"

# CLI extension filename.
XCMD_FILE_NAME = f"{CLI_MOD_NAME}.py"

# Hooks filename.
HOOKS_FILE_NAME = f"{HOOKS_MOD_NAME}.py"

# Server run filename.
SERVER_RUN_FILE_NAME = ".volt-server.run"

###

# Root module name for the theme.
THEME_ROOT_MOD_QUAL_NAME = f"{PROJECT_MOD_QUAL_NAME}.{SITE_THEMES_DIR_NAME}"

# Theme engines module name.
ENGINES_MOD_NAME = "engines"

# File name for theme engines.
ENGINES_FILE_NAME = f"{ENGINES_MOD_NAME}.py"

# Theme base settings file name.
THEME_SETTINGS_FILE_NAME = "theme.toml"

# Site theme static directory name.
THEME_STATIC_DIR_NAME = f"{STATIC_DIR_NAME}"

# Theme templates directory name.
THEME_TEMPLATES_DIR_NAME = "templates"
