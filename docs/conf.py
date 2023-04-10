# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "plantuml-sequence"
copyright = "2023, Jonas Ehrlich"
author = "Jonas Ehrlich"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "myst_parser",
    "autodoc2",
]
templates_path = ["_templates"]
exclude_patterns = []

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# -- Options for myst-parser -------------------------------------------------

# -- Options for autodoc2 extension ------------------------------------------
autodoc2_packages = [
    "../plantuml_sequence",
]
autodoc2_render_plugin = "myst"
# autodoc2_module_all_regexes = [
#     r"plantuml_sequence\..*",
# ]
autodoc2_module_summary = False
autodoc2_hidden_objects = ["dunder", "private", "inherited"]
