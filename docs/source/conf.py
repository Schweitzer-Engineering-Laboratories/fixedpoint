"""Configuration file for the Sphinx documentation builder.

See https://www.sphinx-doc.org/en/master/usage/configuration.html for a
description of this file
"""
import pathlib
import doctest
import os

_thisdir = pathlib.Path(__file__).parent
_sourcedir = _thisdir
_rootdir = _thisdir.parent.parent
_fixedpointdir = _rootdir / 'fixedpoint'

# -- Project information ------------------------------------------------------

# The documented project's name.
project = 'fixedpoint'

# A copyright statement in the style '2008, Author Name'.
copyright = '2019-2020, Schweitzer Engineering Laboratories, Inc.'

# The author name(s) of the document.
author = 'Zack Sheffield'

# The full project version, used as the replacement for |release| and e.g. in
# the HTML templates. For example, for the Python documentation, this may be
# something like 2.6.0rc1. If you don't need the separation provided between
# version and release, just set them both to the same value.
version = release = '1.0.0b'

# -- General configuration ----------------------------------------------------

# A list of strings that are module names of extensions. These can be
# extensions coming with Sphinx (named sphinx.ext.*) or custom ones.
extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
]

# The document name of the "master" document, that is, the document that
# contains the root toctree directive.
master_doc = 'index'

# A list of paths that contain extra templates (or templates that overwrite
# builtin/theme-specific templates). Relative paths are taken as relative to
# the configuration directory.
templates_path = ['_templates']

# A string of reStructuredText that will be included at the end of every source
# file that is read. This is a possible place to add substitutions that should
# be available in every file (anothing being rst_prolog)
rst_epilog = '''
..  _IEEE 754: https://ieeexplore.ieee.org/servlet/opac?punumber=8766227

..  The attribute directive does not italicize or link the type parameter, so
    I'm doing it here

..  |bool| replace:: *bool*
..  _bool: https://docs.python.org/3.8/library/functions.html#bool

..  |int| replace:: *int*
..  _int: https://docs.python.org/3.8/library/functions.html#int

..  |str| replace:: *str*
..  _str: https://docs.python.org/3.8/library/stdtypes.html#str
'''

# The name of the default domain. Can also be None to disable a default domain.
# Those objects in other domains (whether the domain name is given explicitly,
# or selected by a default-domain directive) will have the domain name
# explicitly prepended when named (e.g., when the default domain is C, Python
# functions will be named "Python function", not just "function").
primary_domain = 'py'

# The name of a reST role (builtin or Sphinx extension) to use as the default
# role, that is, for text marked up `like this`. This can be set to 'py:obj' to
# make `filter` a cross-reference to the Python function "filter". The default
# is None, which doesn't reassign the default role. The default role can always
# be set within individual documents using the standard reST default-role
# directive.
default_role = 'py:obj'

# If set to a major.minor version string like '1.1', Sphinx will compare it
# with its version and refuse to build if it is too old. Default is no
# requirement.
needs_sphinx = '2.4'

# If true, Sphinx will warn about all references where the target cannot be
# found. You can activate this mode temporarily using the -n command-line
# switch.
nitpicky = True

# If true, figures, tables and code-blocks are automatically numbered if they
# have a caption. The numref role is enabled. Obeyed so far only by HTML and
# LaTeX builders.
numfig = True

# A dictionary mapping 'figure', 'table', 'code-block' and 'section' to strings
# that are used for format of figure numbers. As a special character, %s will
# be replaced to figure number.
numfig_format = {
    'figure': 'Figure %s',
    'table': 'Table %s',
    'code-block': 'Listing %s',
    'section': 'Section',
}

# If set to 0, figures, tables and code-blocks are continuously numbered
# starting at 1. If 1, numbers will be x.1, x.2, ... with x the section number
# (top level sectioning; no x. if no section). This naturally applies only if
# section numbering has been activated via the :numbered: option of the toctree
# directive. If set to 2, numbers will be x.y.1, x.y.2, ... if located in a
# sub-section (but still x.1, x.2, ... if located directly under a section and
# 1, 2, ... if not in any top level section).
numfig_secnum_depth = 1

# If true, the Docutils Smart Quotes transform, originally based on SmartyPants
# (limited to English) and currently applying to many languages, will be used
# to convert quotes and dashes to typographically correct entities.
smartquotes = True

# The current time is formatted using time.strftime() and the format given in
# today_fmt.
today_fmt = '%d %b %Y %I:%M:%S %p'

# The default language to highlight source code in.
highlight_language = 'python3'

# The style name to use for Pygments highlighting of source code.
pygments_style = 'monokai'

# A boolean that decides whether parentheses are appended to function and
# method role text (e.g. the content of :func:`input`) to signify that the name
# is callable.
add_function_parentheses = True

# A boolean that decides whether module names are prepended to all object names
# (for object types where a "module" of some kind is defined), e.g. for
# py:function directives.
add_module_names = True

# A boolean that decides whether codeauthor and sectionauthor directives
# produce any output in the built files.
show_authors = True

# A list of prefixes that are ignored for sorting the Python module index
# (e.g., if this is set to ['foo.'], then foo.bar is shown under B, not F).
# This can be handy if you document a project that consists of a single
# package. Works only for the HTML builder currently.
modindex_common_prefix = [
    'fixedpoint.'
]

# If true, doctest flags (comments looking like # doctest: FLAG, ...) at the
# ends of lines and <BLANKLINE> markers are removed for all code blocks showing
# interactive Python sessions (i.e. doctests).
trim_doctest_flags = True

# -- Options for HTML output -------------------------------------------------

# The "theme" that the HTML output should use.
try:
    import sphinx_rtd_theme  # type: ignore
except Exception:
    html_theme = 'default'
else:
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
    extensions.append('sphinx_rtd_theme')

# A dictionary of options that influence the look and feel of the selected
# theme. These are theme-specific.
theme_options = {
    'classic': {
        'stickysidebar': True,
    },
    'sphinx_rtd_theme': {
        # This will specify a canonical URL meta link element to tell search
        # engines which URL should be ranked as the primary URL for your
        # documentation. This is important if you have multiple URLs that your
        # documentation is available through. The URL points to the root path of
        # the documentation and requires a trailing slash.
        'canonical_url': '',
        # If specified, Google Analytics' javascript is included in your pages.
        # Set the value to the ID provided to you by google (like UA-XXXXXXX).
        # 'analytics_id': 'UA-XXXXXXX-1',
        # Only display the logo image, do not display the project name at the
        # top of the sidebar
        'logo_only': True,
        # If True, the version number is shown at the top of the sidebar.
        'display_version': True,
        # Location to display Next and Previous buttons. This can be either
        # bottom, top, both , or None.
        'prev_next_buttons_location': 'both',
        # Add an icon next to external links.
        'style_external_links': True,
        # Changes how to view files when using display_github, display_gitlab,
        # etc. When using GitHub or GitLab this can be: blob (default), edit,
        # or raw. On Bitbucket, this can be either: view (default) or edit.
        # 'vcs_pageview_mode': 'blob',
        # Changes the background of the search area in the navigation bar. The
        # value can be anything valid in a CSS background property.
        'style_nav_header_background': 'white',
        # With this enabled, navigation entries are not expandable - the [+]
        # icons next to each entry are removed.
        'collapse_navigation': True,
        # Scroll the navigation with the main page content as you scroll the
        # page.
        'sticky_navigation': False,
        # The maximum depth of the table of contents tree. Set this to -1 to
        # allow unlimited depth.
        'navigation_depth': 4,
        # Specifies if the navigation includes hidden table(s) of contents -
        # that is, any toctree directive that is marked with the :hidden:
        # option.
        'includehidden': True,
        # When enabled, page subheadings are not included in the navigation.
        'titles_only': False,
    }
}

html_theme_options = theme_options.get(html_theme, 'sphinx_rtd_theme')

# The "title" for HTML documentation generated with Sphinx's own templates.
# This is appended to the <title> tag of individual pages, and used in the
# navigation bar as the "topmost" element.
html_title = f'fixedpoint v{release} documentation'

# If given, this must be the name of an image file (path relative to the
# configuration directory) that is the logo of the docs. It is placed at the
# top of the sidebar; its width should therefore not exceed 200 pixels.
html_logo = str((_thisdir / '_static' / 'fixedpoint.png').resolve())

# A shorter "title" for the HTML docs. This is used in for links in the header
# and in the HTML Help docs.
html_short_title = 'fixedpoint'

# This must be the name of an image file (path relative to the configuration
# directory) that is the favicon of the docs. Modern browsers use this as the
# icon for tabs, windows and bookmarks. It should be a Windows-style icon file
# (.ico), which is 16x16 or 32x32 pixels large.
html_favicon = str((_thisdir / '_static' / 'favicon.ico').resolve())

# A list of CSS files. The entry must be a filename string or a tuple
# containing the filename string and the attributes dictionary. The filename
# must be relative to the html_static_path, or a full URI with scheme like
# http://example.org/style.css. The attributes is used for attributes of
# <link> tag.
html_css_files = [
    'css/admonition-example.css',
    # 'css/purple-text.css',
]

# A list of paths that contain custom static files (such as style sheets or
# script files). Relative paths are taken as relative to the configuration
# directory. They are copied to the output's _static directory after the
# theme's static files, so a file named default.css will overwrite the theme's
# default.css.
html_static_path = ["_static"]

# If this is not None, a 'Last updated on:' timestamp is inserted at every page
# bottom, using the given strftime() format. The empty string is equivalent to
# '%b %d, %Y' (or a locale-dependent equivalent).
html_last_updated_fmt = '%d %b %Y'

# If true, the reST sources are included in the HTML build as _sources/name.
html_copy_source = True

# If true (and html_copy_source is true as well), links to the reST sources
# will be added to the sidebar.
html_show_sourcelink = True

# Suffix to be appended to source links (see html_show_sourcelink), unless
# they have this suffix already.
html_sourcelink_suffix = '.rst'

# If true, "(C) Copyright ..." is shown in the HTML footer.
html_show_copyright = True

# If true, "Created using Sphinx" is shown in the HTML footer.
html_show_sphinx = True

# If true, a list all whose items consist of a single paragraph and/or a
# sub-list all whose items etc... (recursive definition) will not use the
# <p> element for any of its items. This is standard docutils behavior.
html_compact_lists = True

# -- Options for doctest extension --------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/doctest.html

doctest_default_flags = (
    doctest.ELLIPSIS |
    doctest.IGNORE_EXCEPTION_DETAIL |
    doctest.DONT_ACCEPT_TRUE_FOR_1 |
    0
)

# A list of directories that will be added to sys.path when the doctest builder
# is used. (Make sure it contains absolute paths.)
doctest_path = [
    str(_rootdir.resolve()),
]

# Python code that is treated like it were put in a testsetup directive for
# every file that is tested, and for every group. You can use this to e.g.
# import modules you will always need in your doctests.
with open(_thisdir / 'doctest_setup.py') as f:
    doctest_global_setup = f.read()

# -- Options for extlinks extension --------------------------------------------
# http://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

extlinks = {
    'wikirounding': (
        # This is the permalink
        ('https://en.wikipedia.org/w/index.php?'
         'title=Rounding&oldid=938336798#%s'),
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

# -- Options for intersphinx extension ----------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html

intersphinx_mapping = {
    'python': (
        'https://docs.python.org/3.8',
        (
            None,
            '_static/objects.inv',
        )
    ),
}

# -- Options for todo extension -----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/todo.html

# If this is True, todo and todolist produce output, else they produce nothing.
todo_include_todos = os.environ.get('READTHEDOCS', None) != 'True'

# If this is True, todo emits a warning for each TODO entries.
todo_emit_warnings = True

# If this is True, todolist produce output without file path and line,
todo_link_only = False

# -- Additional setup ---------------------------------------------------------

# Copy fixedpoint.py over into the static folder because code snippits are
# taken from it
with open(_fixedpointdir / 'fixedpoint.py') as r, \
        open(_thisdir / 'fixedpoint', 'w') as w:
    w.write(r.read())
