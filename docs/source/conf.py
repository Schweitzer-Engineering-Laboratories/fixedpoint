# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
import pathlib


# -- Project information -----------------------------------------------------

project = 'fixedpoint'
copyright = '2020, Zack Sheffield'
author = 'Zack Sheffield'

# The full version, including alpha/beta/rc tags
release = '1.0.0'

# -- General configuration ---------------------------------------------------

master_doc = 'index'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
]

todo_include_todos = True

# Make sure the fixedpoint module is accessible
doctest_path = [
    str(pathlib.Path(__file__).parent.parent.parent.resolve()),
]

with open(pathlib.Path(__file__).parent / 'doctest_setup.py') as f:
    doctest_global_setup = f.read()

intersphinx_mapping = {
    'python': (
        'https://docs.python.org/3.8',
        (
            None,
            '_static/objects.inv',
        )
    ),
}

# http://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
extlinks = {
    'wikirounding': (
        # This is the permalink
        'https://en.wikipedia.org/w/index.php?title=Rounding&oldid=938336798#%s',
        None,
    ),
    'pylib': (
        'https://docs.python.org/3.8/library/%s',
        None,
    ),
    'pyref': (
        'https://docs.python.org/3.8/reference/%s',
        None,
    ),
    'pytut': (
        'https://docs.python.org/3.8/tutorial/%s',
        None,
    ),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# A string of reStructuredText that will be included at the end of every source
# file that is read. This is a possible place to add substitutions that should
# be available in every file
rst_epilog = """
..  _IEEE 754: https://ieeexplore.ieee.org/servlet/opac?punumber=8766227
"""

# The name of a reST role (builtin or Sphinx extension) to use as the default
# role, that is, for text marked up `like this`. This can be set to 'py:obj'
# to make `filter` a cross-reference to the Python function "filter". The
# default is None, which doesn’t reassign the default role.
default_role = "py:obj"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'classic'

html_theme_options = {
    'stickysidebar': 'true',
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = [
    'css/admonition-example.css',
]
