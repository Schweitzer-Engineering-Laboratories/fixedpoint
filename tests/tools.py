#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
"""
Various tools for unit tests
"""
import os
import sys
import random
import unittest
import io
import logging, logging.handlers
import shutil
import traceback
import subprocess
import pathlib
import re
import traceback
import struct
import shlex
import platform
from typing import Any, Dict, Tuple, Union
import types
import functools
import copy

import tqdm
import nose

NUM_ITERATIONS = 1024

TQDMOPTS = {
    'leave': False,
    'position': 1,
    'total': NUM_ITERATIONS,
}

def test_iterator(iterator=None):
    if iterator is None:
        iterator = range(NUM_ITERATIONS)
        ret = tqdm.tqdm(iterator, **TQDMOPTS)
    else:
        opts = copy.deepcopy(TQDMOPTS)
        try:
            opts['total'] = len(iterator)
        except TypeError:
            pass
        ret = tqdm.tqdm(iterator, **opts)
    return ret

def verify_properties_exist(obj):
    """Verify expected properties

    This test will fail when new properties are added or taken away.
    """
    expected = {
        "_signed",
        "_m",
        "_n",
        "_bits",
        "_str_base",
        "_rounding",
        "_overflow",
        "_overflow_alert",
        "_mismatch_alert",
        "_implicit_cast_alert",
        "__id",
        "__cmstack",
        "__context",
    }

    actual = set(obj.__slots__)
    unexpected_attributes = expected - actual
    attributes_missing = actual - expected

    nose.tools.assert_false(unexpected_attributes,
        f"Unexpected attributes: {unexpected_attributes}")
    nose.tools.assert_false(attributes_missing,
        f"Attributes missing: {attributes_missing}")

def verify_attributes(obj, **props):
    """Verify that object has the attributes specified.
    """
    verify_properties_exist(obj)
    for attr in obj.__slots__:

        # Skip private attributes, or attributes we don't want to check
        if attr.startswith('__') or \
            (expected := props[(attr := attr.lstrip('_'))]) is NotImplemented:
            continue

        x = getattr(obj, attr) if hasattr(obj, attr) else getattr(obj, f"_{attr}")

        nose.tools.assert_equal(x, expected,
            f"{attr!r}, {obj._FixedPoint__id['extra']['sn']}")

def chunky(seq, n):
    """Breaks up a string into equally-sized chunks.

    If len(seq) % n != 0, the last element in the return list will be of length
    len(seq) % n

    Filched from
    https://bitbucket.metro.ad.selinc.com/users/zackshef/repos/zksutils/browse/zksutils/chunk.py#12

    Args:
        seq (str): string to chunkify
        n (int): size of chunk to create

    Yields:
        str: string of length n
    """
    for i in range(0, len(seq), n):
        yield seq[i : i+n]

def random_float(s, m, n, mutable):
    """Generate a float that fits in the given fixed point format.
    """
    posbits = m + n - (s := bool(s))
    _pos = random.getrandbits(posbits) if posbits else 0
    _neg = random.choice([0] + [-1] * s) << (m + n - 1)
    _ret = (_pos | _neg)
    mutable['bits'] = _ret & (2**(m + n) - 1)
    return float(_ret * 2**-n)

def random_int(s, m):
    """Generate an int that fits in the given fixed point format.
    """
    # Integer bits
    ret = random.getrandbits((m-1) or 1)
    # Sign weight
    ret -= 2**(m-1) if s else 0
    return ret

class CaptureWarnings:
    """Captures FixedPoint warning logs
    """
    def __new__(cls):
        """Generate a single instance and attach a handler to the logger
        """
        if not hasattr(cls, "instance"):
            inst = super(CaptureWarnings, cls).__new__(cls)
            cls.instance = inst
            cls.logger = logging.getLogger("FP.CONSOLE")
        return cls.instance

    def __init__(self):
        """Generate a StringIO stream to capture warnings.
        """
        import fixedpoint.logging
        self.stream = io.StringIO()
        self.handler = fixedpoint.logging.WARNER_CONSOLE_HANDLER
        self.fpstream = None

    @property
    def logs(self):
        """Get all the warnings out of the captured logs.

        This assumes that each warning is a single line (no newlines).
        """
        self.stream.flush()
        return self.stream.getvalue().splitlines()

    def __enter__(self):
        """Context manager to capture warnings.

        This will replace the warning handler stream with a StringIO stream
        for the scope of the with statement. Upon exit, the console will
        restore the warning handler stream to what it was before. Warnings
        logged inside the with scope are still available.
        """
        self.fpstream = self.handler.setStream(self.stream)
        return self

    def __exit__(self, *args, **kwargs):
        """Restore the warning handler stream to the rightful heir.
        """
        self.stream.flush()
        self.handler.setStream(self.fpstream)

    def __len__(self):
        """Number of logs captured.

        This assumes that each warning is a single line (no newlines).
        """
        return len(self.logs)

class MATLAB:
    """API to call MATLAB and generate stimulus from python
    """
    def __new__(self) -> None:
        return None

    @staticmethod
    def exists() -> bool:
        return shutil.which('matlab')

    @staticmethod
    def generate_stimulus(seed: int, numits: int) -> None:
        """Generate MATLAB stimulus files.

        The MATLAB script used to generate stimulus is the name of the
        calling function with a '.m' extension.

        The stimulus file generated is expected to the be the name of the
        calling function with a '.stim' extension. Its file format is explained
        in the yield_stimulus method.

        Args:
            seed (int): random seed for MATLAB to use
            numits (int): number of iterations to MATLAB to use
        """
        # Get the name of the function requesting stimulus
        test = traceback.extract_stack(limit=2)[0]
        testdir = pathlib.Path(test.filename).parent

        # MATLAB is time consuming. Don't generate new stimulus if it already
        # exists
        if os.environ.get('FIXEDPOINTGENALL', ''):
            testdir = testdir.parent
            cmd = "gen_data;exit"
        else:
            # Don't regenerate stimulus if it already exists
            if (testdir / f'{test.name}.stim').exists():
                return
            cmd = f"{test.name};exit"

        # Print status message
        status = "MATLAB running"
        sys.stderr.write(status)

        # Pass test context to MATLAB via environment variables
        os.environ['FIXEDPOINTRANDOMSEED'] = str(seed)
        os.environ['FIXEDPOINTNUMITERATIONS'] = str(numits)

        # Generate stimulus
        subprocess.run(
            [
                'matlab',
                '-nosplash',
                '-wait',
                '-automation',
                '-sd', str(testdir),
                '-r', cmd,
            ],
            env=os.environ,
        )

        # Erase the status message
        sys.stderr.write('\b' * len(status))
        sys.stderr.write(' ' * len(status))
        sys.stderr.write('\b' * len(status))

    @staticmethod
    def yield_stimulus(spec: struct.Struct, stacklimit=2) -> Tuple[Any]:
        """Iterates over the generated stimulus generated by the
        generate_stimulus method.

        The calling function specifies the format of the binary file in which
        to find stimulus. The name of the parsed stimulus file is the name of
        the calling function with a '.stim' extension.

        Args:
            spec (struct.Struct): spec for how to unpack binary stimulus files

        Yields:
            tuple: a tuple of values specified by the spec argument
        """
        # Get the name of the function requesting stimulus
        test = traceback.extract_stack(limit=stacklimit)[0]
        stim_file = f"{pathlib.Path(test.filename).parent / test.name!s}.stim"
        with open(stim_file, 'rb') as f:
            binary = f.read(spec.size)
            while binary:
                yield spec.unpack(binary)
                binary = f.read(spec.size)

class TestCaseRotatingFileHandler(logging.handlers.BaseRotatingHandler):
    """Logging file handler that creates a new file for each new test that
    gets run. Assumes the tools.setup decorator
    is utilized.
    """
    DEFAULT_FILENAME = str(pathlib.Path('./../fixedpoint/fixedpoint.log').resolve())
    FUNCNAME = None
    def __init__(self):
        super().__init__(TestCaseRotatingFileHandler.DEFAULT_FILENAME, 'w', delay=True)

    def shouldRollover(self, *args, **kwargs):
        """By using the tools.setup decorator,
        new test cases generate new log files.
        """
        return TestCaseRotatingFileHandler.FUNCNAME is not None

    # filched from logging.handlers.RotatingFileHandler
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        self.baseFilename = TestCaseRotatingFileHandler.FUNCNAME
        TestCaseRotatingFileHandler.FUNCNAME = None
        if not self.delay:
            self.stream = self._open()

    @classmethod
    def newtest(cls, funcname):
        cls.FUNCNAME = funcname

    @classmethod
    def endtest(cls, funcname):
        cls.FUNCNAME = None

def get_terminal_size() -> Tuple[int, int]:
    """Get width and height of console. Works on Linux, OS X, Windows, and
    Cygwin(windows). Filched from
    https://gist.githubusercontent.com/jtriley/1108174/raw/6ec4c846427120aa342912956c7f717b586f1ddb/terminalsize.py
    """
    #__________________________________________________________________________
    def _get_terminal_size_windows():
        retx, rety = None, None
        try:
            from ctypes import windll, create_string_buffer
            # stdin handle is -10
            # stdout handle is -11
            # stderr handle is -12
            hand = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(hand, csbi)
            if res:
                (_bufx, _bufy, _curx, _cury, _wattr,
                 _left, _top, _right, _bottom,
                 _maxx, _maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
                sizex = _right - _left + 1
                sizey = _bottom - _top + 1
                retx, rety = sizex, sizey
        except: # pylint: disable=bare-except
            pass
        return retx, rety
    #__________________________________________________________________________
    def _get_terminal_size_tput():
        # get terminal width
        # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
        retx, rety = None, None
        try:
            cols = int(subprocess.check_call(shlex.split('tput cols')))
            rows = int(subprocess.check_call(shlex.split('tput lines')))
            retx, rety = cols, rows
        except: # pylint: disable=bare-except
            pass
        return retx, rety
    #__________________________________________________________________________
    def _get_terminal_size_linux():
        retx = None

        def _ioctl_gwinsz(fdx):
            ret = None
            try:
                import fcntl # pylint: disable=import-error
                import termios # pylint: disable=import-error
                ret = struct.unpack('hh',
                                   fcntl.ioctl(fdx, termios.TIOCGWINSZ, '1234'))
            except: # pylint: disable=bare-except
                pass
            return ret

        retx = _ioctl_gwinsz(0) or _ioctl_gwinsz(1) or _ioctl_gwinsz(2)
        if not retx:
            try:
                fdx = os.open(os.ctermid(), os.O_RDONLY) # pylint: disable=no-member
                retx = _ioctl_gwinsz(fdx)
                os.close(fdx)
            except: # pylint: disable=bare-except
                pass
        if not retx:
            try:
                retx = (os.environ['LINES'], os.environ['COLUMNS'])
            except: # pylint: disable=bare-except
                return None
        return int(retx[1]), int(retx[0])
    #__________________________________________________________________________
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy

def setup(progress_bar=True, skip=False, require_matlab=False):
    """Each test should use this decorator to set up tests.

    Args:
        progress_bar (bool): set this to True to ensure cleanup after test is
            finished. Assumes that tqdm is being used.
        skip (bool or str): Set to False to run the test. Provide a (str) reason
            for skipping otherwise.
    """

    if skip or (require_matlab and not MATLAB.exists()):
        skip = str(skip) if skip else "MATLAB required"
        # Filched from unittest.case.skip
        def decorator(test_item):
            if not isinstance(test_item, type):
                @functools.wraps(test_item)
                def skip_wrapper(*args, **kwargs):
                    raise unittest.case.SkipTest(str(skip))
                test_item = skip_wrapper
            test_item.__unittest_skip__ = True
            test_item.__unittest_skip_why__ = skip
            return test_item
        if isinstance(skip, types.FunctionType):
            test_item = skip
            skip = ''
            return decorator(test_item)
        return decorator

    # Filched from nose.tools.nontrivial.with_setup
    def decorate(func, progress_bar=progress_bar):
        frame = traceback.extract_stack(limit=2)[0]
        directory = re.search(r'^(.+)\\__init__\.py', frame.filename)[1]
        filename = str((pathlib.Path(directory) / f"{func.__name__}.log").resolve())

        def nothing():
            pass

        # If func is being used as a generator, don't create a new log file
        _old_setup = func.setup if hasattr(func, 'setup') else nothing
        def _new_setup():
            # Register new test with unit test logger
            TestCaseRotatingFileHandler.newtest(filename)
            # Do other setup stuff
            _old_setup()
        func.setup = _new_setup

        _old_teardown = func.teardown if hasattr(func, 'teardown') else nothing
        if progress_bar:
            def pbar_teardown():
                # Assumes tqdm progress bar is being used. Prints out backspaces
                # so progress bar disappears nicely.
                ldoc = len(func.__doc__.splitlines()[0])
                lwindow = get_terminal_size()[0]
                # For skipped functions, don't worry about the progress bar
                sys.stderr.write('\b' * (lwindow - ldoc - 11))
                sys.stderr.flush()
        else:
            pbar_teardown = nothing
        def _new_teardown():
            # Signal to unit test logger that we're done with the test
            TestCaseRotatingFileHandler.endtest(filename)
            pbar_teardown()
            # Do other teardown stuff
            _old_teardown()
        func.teardown = _new_teardown

        return func

    return decorate
