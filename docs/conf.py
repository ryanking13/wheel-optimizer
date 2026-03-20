import os
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path

project = "wheel-optimizer"
copyright = "2026, Pyodide contributors"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_autodoc_typehints",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.13", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".*"]

# -- Options for HTML output -------------------------------------------------

html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

html_css_files = [
    "css/pyodide.css",
]

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]

html_theme_options = {
    "repository_url": "https://github.com/pyodide/wheel-optimizer",
    "use_repository_button": True,
}

sys.path.append(Path(__file__).parent.parent.as_posix())

try:
    release = importlib_metadata.version("wheel-optimizer")
except importlib_metadata.PackageNotFoundError:
    print(
        "Could not find package version, please install wheel-optimizer to build docs"
    )
    release = "0.0.0"

version = release
