"""Constant values."""
# (c) 2012-2020 Wibowo Arindrarto <contact@arindrarto.dev>

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

# Separator string for text content front matter.
FRONT_MATTER_SEP = "---\n"

# Extension for Markdown source files.
MARKDOWN_EXT = ".md"

# Site source directory name.
SITE_SOURCES_DIRNAME = "source"

# Site draft contents directory name.
SITE_DRAFTS_DIRNAME = ".drafts"

# Site directory name for extension code.
SITE_EXT_DIRNAME = "extension"

# Site output directory name.
SITE_OUT_DIRNAME = "target"

# Site static directory name.
SITE_STATIC_DIRNAME = "static"

# Site project directory name.
SITE_PROJECT_DIRNAME = ""

# Site theme directory name.
SITE_THEMES_DIRNAME = "theme"

# Theme templates directory name.
SITE_THEME_TEMPLATES_DIRNAME = "templates"

# Theme engines directory name.
SITE_THEME_ENGINES_DIRNAME = "engines"

# CLI extension filename.
SITE_XCMD_SCRIPT_FNAME = "cmd.py"

# Theme base settings file name.
THEME_SETTINGS_FNAME = "theme.yaml"
