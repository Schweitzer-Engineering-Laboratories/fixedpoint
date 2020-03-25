#!/usr/bin/env python3
import setuptools
import pathlib
import re

def long_description():
    """Removes links from long_description.rst"""
    src = pathlib.Path(__file__).parent / 'docs' / 'source' / 'long_description.rst'
    with open(src) as f:
        rst = f.read()
    def repl(m):
        M = m.group(1)
        return M.split('.')[-1] if M.startswith('~') else M
    return re.sub(r':[^:]+:`([^`]+)`', repl, re.sub(r' <[^>]+>', '', rst))

# https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-values
# The file: directive is sandboxed and won’t reach anything outside the
# directory containing setup.py. Since long_description.rst is not in the same
# directory, it is specified here instead of in setup.cfg.
setuptools.setup(long_description=long_description(),
                 long_description_content_type='text/x-rst')
