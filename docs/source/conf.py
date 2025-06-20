# Configuration file for the Sphinx documentation builder.

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# Project information
project = "jetraw_tools"
copyright = "2025, Boeck Lab"
author = "Boeck Lab"
release = "0.7.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = []
language = "en"

# HTML output options
html_theme = "furo"
html_static_path = ["_static"]

# Autodoc configuration
autodoc_typehints = "description"
autodoc_class_signature = "separated"
autodoc_mock_imports = ["dpcore"]
autoclass_content = 'class'
autosummary_generate = True

# Warning suppression
suppress_warnings = ["autosummary.import_cycle", "autodoc.import_object"]
nitpicky = False

# Autodoc default options
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}
