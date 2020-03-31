"""Retrieve test functions from submodules."""
from setuptools import find_packages
import pathlib
import importlib
import sys
import os
import re
import json

ROOT = pathlib.Path(__file__).parent.parent

# Filched from nose.config.Config().testMatch
TESTMATCH = re.compile(
    os.environ.get('NOSE_TESTMATCH', r'(?:^|[\b_\.%s-])[Tt]est' % os.sep))

# Add ROOT to sys.path if it doesn't exist
for path in sys.path:
    if ROOT.resolve() == pathlib.Path(path):
        break
else:
    sys.path.insert(1, str(ROOT.resolve()))
    print(f'inserted {ROOT.resolve()} in sys.path')

# Grab all the tests from subpackages and put them in this module. When
# tests from different modules have matching names (like test_str_base), an
# exception is raise and the conflicting tests are called out.
testmap = {}
failures = {}
fail = False
for subpackage in find_packages(str(pathlib.Path(__file__).parent.resolve())):
    module = importlib.import_module(f'tests.{subpackage}')

    try:
        symbols = module.__dict__['__all__']
    except KeyError:
        symbols = [x for x in module.__dict__ if not x.startswith('_')]

    for symbol in symbols:
        func = getattr(module, symbol)
        if TESTMATCH.search(symbol) and callable(func):
            if symbol in testmap:
                fail = True
                if symbol in failures:
                    failures[symbol].append(subpackage)
                else:
                    failures[symbol] = [subpackage]
                if not isinstance(testmap[symbol], list):
                    testmap[symbol] = [testmap[symbol]]
                testmap[symbol].append(subpackage)
            else:
                testmap[symbol] = subpackage

            # Import the symbol to this module.
            setattr(sys.modules[__name__], symbol, func)

if fail:
    failures = {x: y for x, y in testmap.items() if isinstance(y, list)}
    raise Exception("Conflicting test names (test name: [modules...]) "
                   f"{json.dumps(failures, indent=4, sort_keys=True)}")
