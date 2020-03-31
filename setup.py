#!/usr/bin/env python3.8
"""Setup a fixedpoint distribution, test, or something else.

Supported/useful COMMAND arguments:

dist -        create a python distribution (sdist and wheel); this is an alias
              for "setup.py sdist bdist_wheel"

sdist -       use this if you want to specify options, otherwise use dist
              https://docs.python.org/3/distutils/sourcedist.html

bdist_wheel - use this if you want to specify options, otherwise use dist
              https://setuptools.readthedocs.io/en/latest/setuptools.html#bdist-egg-create-a-python-egg-for-the-project

nosetests -   install test dependencies and execute tests

develop -     installs like 'pip install fixedpoint' would, but without making
              files read-only; for more options, see
              https://setuptools.readthedocs.io/en/latest/setuptools.html#develop-deploy-the-project-source-in-development-mode

install -     install like 'pip install fixedpoint' would
"""
import setuptools
import pathlib
import re

ROOT = pathlib.Path(__file__).parent


def long_description() -> str:
    """Compile the long description."""
    # Removes links from long_description.rst
    with open(ROOT / 'docs' / 'source' / 'long_description.rst') as f:
        rst = f.read()

    def repl(m: re.Match) -> str:
        """Remove all decoration from rst role object.

        E.g.: :attr:`~fixedpoint.FixedPoint.bits` converts to bits
        """
        M = m.group(1)
        return M.split('.')[-1] if M.startswith('~') else M

    nolinks = re.sub(r' <[^>]+>', '', rst)
    noroles = re.sub(r':[^:]+:`([^`]+)`', repl, nolinks)

    # Append the license file
    license = '\nThe fixedpoint package is released under the BSD license.'
    with open(ROOT / 'LICENSE') as f:
        license += f'\n\n{f.read()}'

    return noroles + license


def get_version() -> str:
    """Retrieve the version from fixedpoint/__init__.py.

    The version is stored in one place in this repository, and since the
    version can't be retrieved by the fixedpoint module during installation
    (e.g., pip install fixedpoint), it will hold the master copy.
    """
    src = ROOT / 'fixedpoint' / '__init__.py'
    # https://www.python.org/dev/peps/pep-0440/#version-scheme
    # https://regex101.com/r/Ly7O1x/319
    # See readme.md for the Versioning Public API
    regex = (r"""__version__\s*=\s*['"]{1,3}"""
             r"(?P<release>(?:0|[1-9])\d*(?:\.(?:0|[1-9]\d*)){2})"
             r"(?:-(?P<pre>(?P<prel>a|b|rc)(?P<pren>(?:0|[1-9])\d*)))?"
             r"(?:\+(?P<local>[a-z\d]+(?:[-_\.][a-z\d]+)*))?"
             r"""['"]{1,3}""")

    with open(src) as f:
        vsrc = re.search(regex, f.read())

    if not vsrc:
        raise ValueError(f"Invalid __version__ in '{f.name}'.")

    version = vsrc.group('release')
    if vsrc.group('pre'):
        version += vsrc.group('pre')
    if vsrc.group('local'):
        version += f"+{vsrc.group('local')}"
    return version


if __name__ == '__main__':

    # https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-values
    # The file: directive is sandboxed and won’t reach anything outside the
    # directory containing setup.py. Since long_description.rst is not in the
    # same directory, it is specified here instead of in setup.cfg.
    setuptools.setup(long_description=long_description(),
                     long_description_content_type='text/x-rst',
                     version=get_version())
