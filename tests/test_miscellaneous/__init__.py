#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import os
import doctest
import subprocess
import random
import json
import io
import pathlib
import sys
import pickle

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools
from ..test_initialization_methods import nondefault_props_gen

@tools.setup(progress_bar=True)
def test_context_manager():
    """Verify __call__, __enter__, __exit__
    """
    overflows = tuple(x.name for x in uut.properties.Overflow)
    roundings = tuple(x.name for x in uut.properties.Rounding)
    alerts = tuple(x.name for x in uut.properties.Alert)
    bases = tuple(uut.properties.StrConv.keys())

    for _ in tools.test_iterator():
        orig = uut.FixedPoint(x := uut.FixedPoint(random.random(), 0, 0))

        # Verify that changes can occur internally but get wiped out of context
        with x:
            x += random.getrandbits(30)
            nose.tools.assert_not_equal(x, orig)
        nose.tools.assert_equal(x, orig)

        # Verify the __call__ works as intended
        with x(m=1, signed=not x.signed):
            nose.tools.assert_not_equal(x.signed, orig.signed)
        nose.tools.assert_equal(x.signed, orig.signed)

        # Verify that attributes are still validated, even with __call__
        errmsg = r'Number of fractional bits must be non-negative\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=-2) as y:
                pass

        # Verify that "private" attributes are not accessible
        errmsg = r"Access to '_id' is prohibited\."
        with nose.tools.assert_raises_regex(PermissionError, errmsg):
            with x(_id=None):
                pass

        # Verify that non-existing attributes raise an exception
        errmsg = r"Invalid FixedPoint attribute 'bogus'\."
        with nose.tools.assert_raises_regex(AttributeError, errmsg):
            with x(bogus=42):
                pass

        # Verify that only properties with setters can be changed
        errmsg = r"'bits' is read-only\."
        with nose.tools.assert_raises_regex(PermissionError, errmsg):
            with x(bits=~x.bits & x.bitmask):
                pass

        # Change all possible properties
        newstuff = dict(
            overflow_alert='ignore',
            m=x.m + random.randrange(10) + 1,
            signed=not x.signed,
            n=random.randrange(x.n),
            mismatch_alert=random.choice(alerts),
            implicit_cast_alert=random.choice(alerts),
            overflow=random.choice(overflows),
            rounding=random.choice(roundings),
            str_base=random.choice(bases),
        )
        with x(**newstuff) as X:
            tools.verify_attributes(X, bits=NotImplemented, **newstuff)

            # Verify nested contexts
            morenewstuff = dict(
                overflow_alert='ignore',
                m=random.randrange(10) + 1,
                signed=not X.signed,
                n=random.randrange(X.n or 1)+ 1,
                mismatch_alert=random.choice(alerts),
                implicit_cast_alert=random.choice(alerts),
                overflow=random.choice(overflows),
                rounding=random.choice(roundings),
                str_base=random.choice(bases),
            )
            with X(**morenewstuff) as XX:
                tools.verify_attributes(XX, bits=NotImplemented, **morenewstuff)

            # Verify that first nested context was restored
            tools.verify_attributes(X, bits=NotImplemented, **newstuff)

            # Verify safe_retain
            morenewstuff['overflow_alert'] = 'ignore'
            try:
                with X(safe_retain=True, **morenewstuff) as XXX:
                    raise Exception
            except:
                pass
            tools.verify_attributes(X, bits=NotImplemented, **newstuff)

            with X(safe_retain=True, **morenewstuff) as XXXX:
                tools.verify_attributes(XXX, bits=NotImplemented, **morenewstuff)
            tools.verify_attributes(X, bits=NotImplemented, **morenewstuff)


            # Verify XXX context is retained
            tools.verify_attributes(XXX, bits=NotImplemented, **morenewstuff)

        # Verify context is completed restored
        tools.verify_attributes(x,
            bits=NotImplemented,
            signed=orig.signed,
            m=orig.m,
            n=orig.n,
            overflow_alert=orig.overflow_alert,
            mismatch_alert=orig.mismatch_alert,
            implicit_cast_alert=orig.implicit_cast_alert,
            overflow=orig.overflow,
            rounding=orig.rounding,
            str_base=orig.str_base,
        )

@tools.setup(progress_bar=False)
def test_logging():
    """Verify debug logging
    """
    newstream = io.StringIO()
    handler = uut.logging.DEFAULT_FILE_HANDLER
    oldstream = handler.setStream(newstream)

    uut.FixedPoint.enable_logging()
    UTLOG.info('0123456789', **LOGID)
    uut.FixedPoint.disable_logging()
    UTLOG.info('abcdefghij', **LOGID)
    uut.FixedPoint.enable_logging()
    UTLOG.info('QRSTUVWXYZ', **LOGID)

    handler.setStream(oldstream)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def serialization(scheme, serialize, skwargs, deserialize, dkwargs):
    """Verify serialization
    """
    # Indicate the serialization scheme in the nose printout
    sys.stderr.write(f'\b\b\b\b\b: {scheme} ... ')

    for init, args, kwargs, _, _, _, _ in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        encoded = serialize(x, **skwargs)
        decoded = deserialize(encoded, **dkwargs)
        tools.verify_attributes(decoded,
            signed=x.signed,
            m=x.m,
            n=x.n,
            bits=x.bits,
            str_base=x.str_base,
            rounding=x.rounding,
            overflow=x.overflow,
            overflow_alert=x.overflow_alert,
            mismatch_alert=x.mismatch_alert,
            implicit_cast_alert=x.implicit_cast_alert,
        )
        nose.tools.assert_equal(x, decoded)


@tools.setup(progress_bar=True)
def test_serialization():
    """Verify serialization
    """

    yield (
        serialization, 'pickle',
            pickle.dumps, {},
            pickle.loads, {}
    )

    yield (
        serialization, 'json',
            json.dumps, dict(cls=uut.json.FixedPointEncoder),
            json.loads, dict(cls=uut.json.FixedPointDecoder)
    )

@nose.tools.nottest
def test_docstring(filename):
    """Runs docstring tests on the given filename
    """
    # Indicate which file we're testing in the nose printout
    paths = filename.split('\\fixedpoint\\')[-1]
    sys.stderr.write(f'\b\b\b\bin file fixedpoint\\{paths} ... ')

    tests = doctest.testfile(filename,
        name='\b',
        optionflags=doctest.IGNORE_EXCEPTION_DETAIL,
    )
    nose.tools.assert_equal(tests.failed, 0, filename)

@tools.setup(progress_bar=False)
def test_docstrings():
    """Verify docstring examples
    """
    # Iterates through the file structure and executes docstring tests on
    # .py files
    for dirname, _, files in os.walk(uut.__path__[0]):
        path = str(pathlib.Path(dirname).resolve())
        for file in files:
            if not file.endswith('.py'):
                continue
            filename = pathlib.Path(os.path.join(path, file)).resolve()
            yield test_docstring, str(filename)

    # Run docstring tests on documentation code. Can't do it with doctest because
    # because sphinx.ext.doctest supports the testcode directive, which
    # the doctest module does not recognize.
    def test_documentation_docstrings():
        docs = (pathlib.Path(__file__).parent.parent.parent / 'docs').resolve()
        path = str(docs / 'source').split('\\source\\')[-1]
        sys.stderr.write(f'\b\b\b\bin directory {path} ... ')
        doctest = subprocess.run(
            [
                'sphinx-build',
                '-M',
                'doctest',
                str(docs / 'source'),
                str(docs / 'build'),
            ],
            capture_output=True,
        )
        UTLOG.debug("Sphinx docstring test:\n%s",
            stdout := doctest.stdout.decode(), **LOGID)

        nose.tools.assert_equal(doctest.returncode, 0, stdout)

    yield test_documentation_docstrings


@tools.setup(progress_bar=False)
def test_typing():
    """Verify typing
    """
    testdir = pathlib.Path(__file__).parent.parent
    uutparent = testdir.parent
    config_file = testdir / 'mypy.ini'
    html_report = testdir / 'MYPY'
    cache_dir = testdir / 'MYPY'
    package = uut.__name__

    os.makedirs(html_report, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    mypy = subprocess.run(
        [
            'py', '-m', 'mypy',
            "--config-file", str(config_file.resolve()),
            "--html-report", str(html_report.resolve()),
            "--cache-dir", str(cache_dir.resolve()),
            "--package", str(package),
        ],
        capture_output=True,
        cwd=str(uutparent.resolve()),
    )

    # Mypy has a bug in their reporting that doesn't show in the individual
    # file view what lines are considered "imprecise". This appears to only be
    # the case in Firefox. Add a CSS rule to the HTML report to make this
    # work if it doesn't already exist.
    css = str((pathlib.Path(__file__).parent / '..' / 'MYPY' / 'mypy-html.css').resolve())

    with open(css) as f:
        imprecise = '.line-imprecise' in f.read()
    if not imprecise:
        with open(css, 'a') as f:
            f.write("\n.line-imprecise {\n    background-color: #ffa;\n}\n")

    UTLOG.info("mypy-html.css path: %s\n\nSTDERR:\n%s\n\nSTDOUT:\n%s\n",
        css,
        mypy.stderr.decode().replace('\r\n', '\n'),
        mypy.stdout.decode().replace('\r\n', '\n'), **LOGID
    )

    if mypy.returncode:
        raise subprocess.SubprocessError('mypy typing failure; '
            f'refer to "{UTLOG.parent.handlers[-1].baseFilename}" for details.')
