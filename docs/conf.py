import pathlib


def get_version() -> str:
    path = pathlib.Path(__file__).parent.parent / "sqlalchemy_utils/__init__.py"
    content = path.read_text()
    for line in content.splitlines():
        if line.strip().startswith("__version__"):
            _, _, version_ = line.partition("=")
            return version_.strip("'\" ")


# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "SQLAlchemy-Utils"
copyright = "2013-2022, Konsta Vesterinen"

version = get_version()
release = version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
# pygments_style = "sphinx"

html_theme = "sphinx_rtd_theme"
