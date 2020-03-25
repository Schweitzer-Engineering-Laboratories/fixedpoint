#!/usr/bin/env python3
import setuptools
import pathlib
import re

def long_description():
    """Compile the long description."""
    # Removes links from long_description.rst
    src = pathlib.Path(__file__).parent / 'docs' / 'source' / 'long_description.rst'
    with open(src) as f:
        rst = f.read()
    def repl(m):
        M = m.group(1)
        return M.split('.')[-1] if M.startswith('~') else M
    desc = re.sub(r':[^:]+:`([^`]+)`', repl, re.sub(r' <[^>]+>', '', rst))

    # Append the license file
    with open(pathlib.Path(__file__).parent / 'LICENSE') as f:
        desc += '\nThe fixedpoint package is released under the BSD license.'
        desc += f'\n\n{f.read()}'

    return desc


# https://setuptools.readthedocs.io/en/latest/setuptools.html#specifying-values
# The file: directive is sandboxed and won’t reach anything outside the
# directory containing setup.py. Since long_description.rst is not in the same
# directory, it is specified here instead of in setup.cfg.
setuptools.setup(long_description=long_description(),
                 long_description_content_type='text/x-rst')
