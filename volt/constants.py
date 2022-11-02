"""Constant values."""
# Copyright (c) 2012-2022 Wibowo Arindrarto <contact@arindrarto.dev>
# SPDX-License-Identifier: BSD-3-Clause


# Prefix for build directory names.
BUILD_DIR_PREFIX = "volt-build-"

# Config file name.
CONFIG_FNAME = "volt.yaml"

# Default slug replacements.
DEFAULT_SLUG_REPLACEMENTS = {
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

# Site source directory name.
SITE_SOURCES_DIRNAME = "source"

# Site draft contents directory name.
SITE_DRAFTS_DIRNAME = ".drafts"

# Site directory name for extension code.
SITE_EXTENSION_DIRNAME = "extension"

# Site output directory name.
SITE_TARGET_DIRNAME = "target"

# Site user static directory name.
SITE_STATIC_DIRNAME = f"{SITE_SOURCES_DIRNAME}/{STATIC_DIRNAME}"

# Site project directory name.
SITE_PROJECT_DIRNAME = ""

# Site theme directory name.
SITE_THEMES_DIRNAME = "theme"

# Theme templates directory name.
SITE_THEME_TEMPLATES_DIRNAME = "templates"

# CLI extension filename.
SITE_XCMD_SCRIPT_FNAME = "cli.py"

# Hooks extension filename.
SITE_HOOKS_SCRIPT_FNAME = "hooks.py"

# Theme base settings file name.
THEME_SETTINGS_FNAME = "theme.yaml"

# Site theme static directory name.
THEME_STATIC_DIRNAME = f"{STATIC_DIRNAME}"

# Module name for the project.
PROJECT_MOD_QUALNAME = "volt.project"

# Module name for custom CLI.
PROJECT_CLI_MOD_QUALNAME = f"{PROJECT_MOD_QUALNAME}.{SITE_EXTENSION_DIRNAME}.cli"

# Root module name for the theme.
ROOT_THEME_MOD_QUALNAME = f"{PROJECT_MOD_QUALNAME}.{SITE_THEMES_DIRNAME}"

# Theme engines module name.
THEME_ENGINES_MOD_NAME = "engines"

# File name for theme engines.
ENGINES_FNAME = f"{THEME_ENGINES_MOD_NAME}.py"
