#!/usr/bin/env python3.8
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random
import re
import sys
from pathlib import Path
import struct
import math

sys.path.insert(1, str(Path('..').resolve()))
from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools
from ..test_initialization_methods import (
    initfloat_gen,
    initstr_gen,
)

@tools.setup(progress_bar=True, require_matlab=True)
def test_resize():
    """Verify resize
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'I' # unsigned int - signedness
        'I' # unsigned int - m
        'I' # unsigned int - n
        '4x' # 4 bytes of padding
        + (
            '16s' # 16-character string - rounding method
            '16s' # 16-character string - overflow method
            'Q' # unsigned long long - nint rounding
            'Q' # unsigned long long - nfrac rounding
            '64s' # rounded result hex strings
        ) * 4 # 4 resized results
    )
    pmap = {
        b'Nearest'.ljust(16, NULL := b'\x00') : 'nearest',
        b'Ceiling'.ljust(16, NULL) : 'up',
        b'Convergent'.ljust(16, NULL) : 'convergent',
        b'Zero'.ljust(16, NULL) : 'in',
        b'Floor'.ljust(16, NULL) : 'down',
        b'Round'.ljust(16, NULL) : 'out',
        b'Wrap'.ljust(16, NULL) : 'wrap',
        b'Saturate'.ljust(16, NULL) : 'clamp',
    }
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, *results = data

        # x.resize(nint, nfrac)
        # x.resize(x.m, nfrac, rounding)
        # x.resize(nint, x.n, overflow)
        # x.resize(nint, nfrac, rounding, overflow)
        for i, (r, o, nint, nfrac, result) in enumerate(tools.chunky(results, 5)):
            UTLOG.debug("Iteration %d: \n"
                "ROUNDING: %s\n"
                "OVERFLOW: %s\n"
                "NINT: %d\n"
                "NFRAC: %d\n"
                "RESULT: %s\n",
                i, pmap[r], pmap[o], nint, nfrac, result, **LOGID
            )
            # On the first iteration, generate the FixedPoint number
            if i == 0:
                x = uut.FixedPoint(init:= init.decode(), s, m, n,
                    overflow_alert='ignore',
                    str_base=2,
                    rounding=(rorig := pmap[r]),
                    overflow=(oorig := pmap[o]),
                )

                # Ensure that bit growth doesn't change value
                orig = int(x)
                x.resize(m + random.randrange(100), n + random.randrange(100))
                nose.tools.assert_equal(orig, int(x))

                # Shrink!
                x.resize(nint, nfrac)

            # On subsequent iterations, reset to original before resizing
            else:
                x.resize(m, n)
                x.from_string(init)

                if i == 1:
                    x.resize(m, nfrac, rounding=pmap[r])
                    nose.tools.assert_equal(x.n, nfrac)
                elif i == 2:
                    x.resize(nint, n, overflow=pmap[o])
                    nose.tools.assert_equal(x.m, nint)
                else:
                    x.resize(nint, nfrac, overflow=pmap[o], rounding=pmap[r])

            UTLOG.debug("Resized to %s bits:\n0b%s", x.qformat, x, **LOGID)

            nose.tools.assert_equal(rorig, x.rounding)
            nose.tools.assert_equal(oorig, x.overflow)

            try:
                nose.tools.assert_equal(x.bits, int(result.decode(), 16))
            except:
                UTLOG.exception("FAIL on iteration %d\n"
                    "init: %s\n"
                    "s: %d\n"
                    "m: %d\n"
                    "n: %d\n"
                    "nint: %d\n"
                    "nfrac: %d\n"
                    "overflow: %s\n"
                    "rounding: %s",
                    i, init, s, m, n, nint, nfrac, pmap[o], pmap[r], **LOGID)
                raise

    # Verify that passing in something other than an int throws an error
    x.overflow_alert = 'ignore'
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.resize(1.0, 1)
        x.resize(-111, 1.0)
        x.resize(11.0, 1.0)

@tools.setup(progress_bar=True)
def test_trim():
    """Verify trim
    """
    errfmt = r'Overflow in format %sQ%d\.%d\.'
    for init, args, _, s, m, n, bits in initstr_gen():
        x = uut.FixedPoint(init, *args)
        xx = uut.FixedPoint(x)

        # Fractional bit trimming
        x.trim(fracs=True)
        nose.tools.assert_equal(x, xx, f'\n{xx!r}\n')
        # If there are any fractional bits, LSB should be 1 unless there are
        # no integer bits
        if x.n and x.m != 0:
            nose.tools.assert_equal(x.bits['lsb'], 1)
        x.n = xx.n

        # Integer bit trimming
        x.trim(ints=True)
        nose.tools.assert_equal(x, xx)
        # Signed negative numbers must retain a '1' msb; signed positive
        # numbers must retain a '0' msb
        if x.signed:
            nose.tools.assert_equal(x.bits['msb'], xx.bits['msb'])
        # Unsigned numbers will have a '1' msb if there are any integer bits
        elif x.m:
            nose.tools.assert_equal(x.bits['msb'], 1)
        # Further trimming should result in overflow
        if x.m and not (x.m == 1 and x.signed):
            errmsg = errfmt % ('' if x.signed else 'U', x.m, xx.n)
            with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg, msg=f'\n{x!r}\n'):
                x.m -= 1
        x.m = xx.m

        # Integer and fractional bit trimming
        x.trim()
        nose.tools.assert_equal(x, xx)
        # If there are any fractional bits, LSB should be 1 unless there are
        # no integer bits
        if x.n and x.m != 0:
            nose.tools.assert_equal(x.bits['lsb'], 1)
        # Signed negative numbers must retain a '1' msb; signed positive
        # numbers must retain a '0' msb
        if x.signed:
            nose.tools.assert_equal(x.bits['msb'], xx.bits['msb'])
        # Unsigned numbers will have a '1' msb if there are any integer bits
        elif x.m:
            nose.tools.assert_equal(x.bits['msb'], 1)
        # Further trimming should result in overflow
        if x.m and not (x.m == 1 and x.signed):
            errmsg = errfmt % ('' if x.signed else 'U', x.m, x.n)
            with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
                x.m -= 1

    # Corner case: trim a Q0.n number
    x = uut.FixedPoint(random.random(), signed=0, m=0)
    x.trim()
    nose.tools.assert_equal(x.m, 0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_round_builtin():
    """Verify round()
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    rounding_map = {
        b'Nearest'.ljust(10, NULL := b'\x00') : 'nearest',
        b'Ceiling'.ljust(10, NULL) : 'up',
        b'Convergent'.ljust(10, NULL) : 'convergent',
        b'Zero'.ljust(10, NULL) : 'in',
        b'Floor'.ljust(10, NULL) : 'down',
        b'Round'.ljust(10, NULL) : 'out',
    }
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, rounding, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, rounding=rounding_map[rounding],
            overflow_alert='ignore', str_base=2)

        for result, nfrac in zip(results, nfracs):
            y = round(x, nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, y, **LOGID)

            nose.tools.assert_equal(y.n, nfrac)
            nose.tools.assert_equal(y.bits, int(result, 16))

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        round(x, 1.0)

@tools.setup(progress_bar=True)
def test_floor():
    """Verify math.floor()
    """
    for init, _, _, _, _, _, _ in initfloat_gen():
        x = uut.FixedPoint(init)
        y = math.floor(x)
        nose.tools.assert_equal(math.floor(float(x)), float(y))
        nose.tools.assert_equal(x.qformat, y.qformat)

        # If there are fractional bits, round_down and math.floor produce the
        # same value. Their q formats will be different
        if x.n:
            x.m += x.m == 0
            x.round_down(0)
            nose.tools.assert_equal(x, y)

@tools.setup(progress_bar=True, require_matlab=True)
def test_ceil():
    """Verify math.ceil()
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *allresults = data
        init = init.decode()
        result = int(allresults[-1].decode()[-Lresult:], 16)

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        y = math.ceil(x)
        UTLOG.debug("Rounded to %d bits:\n0b%s", 0, y, **LOGID)

        nose.tools.assert_equal(y.n, 0)
        nose.tools.assert_equal(y.bits, result)

        # math.ceil should be equivalent to round_up (with 0 fractional bits)
        x.round_up(0)
        nose.tools.assert_equal(x, y)

@tools.setup(progress_bar=True)
def test_trunc():
    """Verify math.trunc()
    """
    for init, _, _, _, _, _, _ in initfloat_gen():
        x = uut.FixedPoint(init)
        y = math.trunc(x)
        roundup = (uut.FixedPoint.sign(y) == -1) and ((init % 1.0) != 0.0)
        nose.tools.assert_equal(math.trunc(float(x)), float(y) + roundup)

        # Corner case, truncating a number with no integer bits.
        a = uut.FixedPoint(random.random())
        b = math.trunc(a)
        nose.tools.assert_equal(b, 0)
        nose.tools.assert_equal(b.qformat, 'UQ1.0')

@tools.setup(progress_bar=True, require_matlab=True)
def test_round():
    """Verify default round
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    rounding_map = {
        b'Nearest'.ljust(10, NULL := b'\x00') : 'nearest',
        b'Ceiling'.ljust(10, NULL) : 'up',
        b'Convergent'.ljust(10, NULL) : 'convergent',
        b'Zero'.ljust(10, NULL) : 'in',
        b'Floor'.ljust(10, NULL) : 'down',
        b'Round'.ljust(10, NULL) : 'out',
    }
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, rounding, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, rounding=rounding_map[rounding],
            overflow_alert='ignore', str_base=2)

        for result, nfrac in zip(results, nfracs):
            x.round(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))
            x.n = n
            x.from_string(init)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        round(x, 1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_convergent():
    """Verify convergent
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        for result, nfrac in zip(results, nfracs):
            x.convergent(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))

            x.n = n
            x.from_string(init)

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.convergent(0)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.convergent(11)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[0, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, m=1):
            x.convergent(11)

    # Corner case: overflow with wrapping
    x = uut.FixedPoint('0b111', 1, 2, 2, overflow='wrap', overflow_alert='ignore')
    x.convergent(0)
    nose.tools.assert_equal(x.bits, 0b10)

@tools.setup(progress_bar=True, require_matlab=True)
def test_round_in():
    """Verify round_in
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        for result, nfrac in zip(results, nfracs):
            x.round_in(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))

            x.n = n
            x.from_string(init)

        # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_in(0)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_in(11)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[0, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, m=1):
            x.round_in(11)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.convergent(1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_round_out():
    """Verify round_out
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        for result, nfrac in zip(results, nfracs):
            x.round_out(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))

            x.n = n
            x.from_string(init)

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_out(0)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_out(11)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[0, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, m=1):
            x.round_out(11)

    # Corner case: overflow with wrapping
    x = uut.FixedPoint('0b110', 1, 2, 2, overflow='wrap', overflow_alert='ignore')
    x.round_out(0)
    nose.tools.assert_equal(x.bits, 0b10)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.round_out(1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_round_nearest():
    """Verify round_nearest
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        for result, nfrac in zip(results, nfracs):
            x.round_nearest(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))

            x.n = n
            x.from_string(init)

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_nearest(0)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_nearest(11)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[0, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, m=1):
            x.round_nearest(11)

    # Corner case: overflow with wrapping
    x = uut.FixedPoint('0b110', 1, 2, 2, overflow='wrap', overflow_alert='ignore')
    x.round_nearest(0)
    nose.tools.assert_equal(x.bits, 0b10)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.round_nearest(1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_round_up():
    """Verify round_up
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        for result, nfrac in zip(results, nfracs):
            x.round_up(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))

            x.n = n
            x.from_string(init)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.round_up(1.0)

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_up(0)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_up(11)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[0, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, m=1):
            x.round_up(11)

    # Corner case: overflow with wrapping
    x = uut.FixedPoint('0b110', 1, 2, 2, overflow='wrap', overflow_alert='ignore')
    x.round_up(0)
    nose.tools.assert_equal(x.bits, 0b10)

@tools.setup(progress_bar=True, require_matlab=True)
def test_round_down():
    """Verify round_down
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    nvectors = 16
    Lresult = 64
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'H' # unsigned short - signedness
        'H' # unsigned short - m
        'H' # unsigned short - n
        '10s' # 10-character string - rounding method
        f'{nvectors}B' # nfrac locations
        f'{Lresult * nvectors}s' # rounded result hex strings
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, _, *nfracs, allresults = data
        init = init.decode()
        results = [x.decode() for x in tools.chunky(allresults, Lresult)]

        x = uut.FixedPoint(init, s, m, n, overflow_alert='ignore', str_base=2)
        for result, nfrac in zip(results, nfracs):
            x.round_down(nfrac)
            UTLOG.debug("Rounded to %d bits:\n0b%s", nfrac, x, **LOGID)

            nose.tools.assert_equal(x.n, nfrac)
            nose.tools.assert_equal(x.bits, int(result, 16))

            x.n = n
            x.from_string(init)

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_down(0)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, signed=0, m=0):
            x.round_down(11)

    errmsg = r'Number of fractional bits remaining after round must be in the range \[0, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=10, m=1):
            x.round_down(11)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.round_down(1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_keep_msbs():
    """Verify keep_msbs
    """
    pmap = {
        b'Nearest'.ljust(16, NULL := b'\x00') : 'nearest',
        b'Ceiling'.ljust(16, NULL) : 'up',
        b'Convergent'.ljust(16, NULL) : 'convergent',
        b'Zero'.ljust(16, NULL) : 'in',
        b'Floor'.ljust(16, NULL) : 'down',
        b'Round'.ljust(16, NULL) : 'out',
        b'Wrap'.ljust(16, NULL) : 'wrap',
        b'Saturate'.ljust(16, NULL) : 'clamp',
    }
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'i' # signed int - signedness & initial length
        'I' # unsigned int - resultant length
        '16s' # 16-character string - rounding method
        '16s' # 16-character string - overflow method
        '64s' # 64-character string - hex result
    )
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, L, LL, r, o, result = data
        init = init.decode()
        s = int(L < 0)
        L = abs(L)
        rounding = pmap[r]
        overflow = pmap[o]
        result = int(result.decode(), 16)

        m = random.randint(s, L)
        n = L - m

        x = uut.FixedPoint(init, s, m, n, str_base=2, overflow_alert='ignore')

        for _ in range(4):
            mm = random.randrange(s, LL)
            nn = LL - mm
            UTLOG.debug("OLD: %r\n"
                "%sQ%d.%d (length = %d)\n"
                "%sQ%d.%d (length = %d)\n"
                "%s %s",
                init,
                '' if s else 'U', m, n, L,
                '' if s else 'U', mm, nn, LL,
                rounding, overflow,
                **LOGID
            )
            with x:
                x.keep_msbs(mm, nn, rounding, overflow)
                nose.tools.assert_equal(x.bits, result & x.bitmask, f"\n{x!s}\n{bin(result)[2:].zfill(len(x))}")
                nose.tools.assert_equal(x.qformat, f"{'' if s else 'U'}Q{mm}.{nn}")

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Bit format specifications must be non-negative\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.keep_msbs(0, -1)
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.keep_msbs(-1, 1)

    errmsg = r'Signed number must have at least 1 integer bit\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', m=10, signed=1):
            x.keep_msbs(0, 42)

    errmsg = r'Total number of bits must be in the range \[2, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=5, m=5):
            x.keep_msbs(1, 0)

    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=5, m=5):
            x.keep_msbs(6, 6)

@tools.setup(progress_bar=True, require_matlab=True)
def test_clamp():
    """Verify clamp
    """
    alert_properties = [x.name for x in uut.properties.Alert]
    alert_method_props = alert_properties + ['']
    overflows = [x.name for x in uut.properties.Overflow]
    permutations = []
    for ameth in alert_method_props:
        for aprop in alert_properties:
                permutations.append((ameth, aprop))
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'I' # unsigned int - signedness
        'I' # unsigned int - initial length
        'I' # unsigned int - resultant length
        'I' # unsigned int - overflow
        '64s' # 64-character string - hex result from clamping
    )
    alert_properties = [x.name for x in uut.properties.Alert]
    alert_method_props = alert_properties + ['']

    errfmt = r'\[SN\d+\]:? Overflow in format %s\.'
    warnfmt = r'WARNING \[SN\d+\]: Clamped to %s\.'
    mmap = {
        -1: 'minimum',
        1: 'maximum',
    }
    x = uut.FixedPoint(0)
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, L, LL, overflow, result = data
        init = init.decode()
        result = int(result.decode(), 16)

        # Choose 6 permutations of property combinations to test
        for i, (ameth, aprop) in enumerate(permutations):
            # Random initial format
            n = random.randint(s, LL - s)
            m = L - n

            # Random result format
            mm = LL - n

            # Actual overflow and overflow_alert property value
            aact = ameth or aprop

            # Initialize FixedPoint objects
            if i == 0:
                x = uut.FixedPoint(init, s, m, n,
                    overflow_alert=aprop, str_base=2)
            else:
                x.from_string('0')
                if x.m == 0:
                    x.m, x.n = m, n
                else:
                    x.n, x.m = n, m
                x.from_string(init)
                x.overflow = random.choice(overflows)
                x.overflow_alert = aprop

            UTLOG.debug("ORIG: %s\n"
                "Clamping to %sQ%d.%d\n"
                "Method:   % 7r\n"
                "Property: % 7r\n"
                "Actual:   % 7r\n"
                "%s.%s",
                x.qformat, '' if s else 'U', mm, n,
                ameth, aprop, aact,
                str(x)[:x.m], str(x)[-x.n:],
                **LOGID
            )

            if overflow and aact == 'error':
                errmsg = errfmt % re.escape(x.qformat)
                with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
                    x.clamp(mm, ameth)
                continue

            elif overflow and aact == 'warning':
                errmsg = f"WARNING {errfmt}" % re.escape(x.qformat)
                warnmsg = warnfmt % mmap[uut.FixedPoint.sign(x)]
                with tools.CaptureWarnings() as warn:
                    x.clamp(mm, ameth)
                logs = warn.logs
                nose.tools.assert_equal(len(logs), 2)
                nose.tools.assert_regex(logs[0], errmsg)
                nose.tools.assert_regex(logs[1], warnmsg)

            else:
                with tools.CaptureWarnings() as warn:
                    x.clamp(mm, ameth)
                nose.tools.assert_equal(len(warn.logs), 0)

            nose.tools.assert_equal(x.signed, s)
            nose.tools.assert_equal(x.m, mm)
            nose.tools.assert_equal(x.n, n)

            nose.tools.assert_equal(x.bits, result)

    errmsg = r'Q20\.10 can only clamp between \[1, 20\) integer bits\.'
    # Corner case: negative bit format
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', m=20, n=10, signed=1):
            x.clamp(-1)

    # Corner case: clamping to 0 bits
    with nose.tools.assert_raises_regex(ValueError, 'U' + errmsg.replace('10', '0')):
        with x(overflow_alert='ignore', m=20, n=0, signed=0):
            x.clamp(0)

    # Corner case: clamping to 0 integer bits for signed
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', m=20, n=10, signed=1):
            x.clamp(0)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.clamp(1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_wrap():
    """Verify wrap
    """
    alert_properties = [x.name for x in uut.properties.Alert]
    alert_method_props = alert_properties + ['']
    overflows = [x.name for x in uut.properties.Overflow]
    permutations = []
    for ameth in alert_method_props:
        for aprop in alert_properties:
                permutations.append((ameth, aprop))
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'I' # unsigned int - signedness
        'I' # unsigned int - initial length
        'I' # unsigned int - resultant length
        'I' # unsigned int - overflow
        '64s' # 64-character string - hex result from clamping
    )
    alert_properties = [x.name for x in uut.properties.Alert]
    alert_method_props = alert_properties + ['']

    errfmt = r'\[SN\d+\]:? Overflow in format %s\.'
    warnfmt = r'WARNING \[SN\d+\]: Wrapped %s\.'
    mmap = {
        -1: 'minimum',
        1: 'maximum',
    }
    x = uut.FixedPoint(0)
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, L, LL, overflow, result = data
        init = init.decode()
        result = int(result.decode(), 16)

        # Choose 6 permutations of property combinations to test
        for i, (ameth, aprop) in enumerate(permutations):
            # Random initial format
            n = random.randint(s, LL - s)
            m = L - n

            # Random result format
            mm = LL - n

            # Actual overflow and overflow_alert property value
            aact = ameth or aprop

            # Initialize FixedPoint objects
            if i == 0:
                x = uut.FixedPoint(init, s, m, n,
                    overflow_alert=aprop, str_base=2)
            else:
                x.from_string('0')
                if x.m == 0:
                    x.m, x.n = m, n
                else:
                    x.n, x.m = n, m
                x.from_string(init)
                x.overflow = random.choice(overflows)
                x.overflow_alert = aprop

            UTLOG.debug("ORIG: %s\n"
                "Wrapping to %sQ%d.%d\n"
                "Method:   % 7r\n"
                "Property: % 7r\n"
                "Actual:   % 7r\n"
                "%s.%s",
                x.qformat, '' if s else 'U', mm, n,
                ameth, aprop, aact,
                str(x)[:x.m], str(x)[-x.n:],
                **LOGID
            )

            if overflow and aact == 'error':
                errmsg = errfmt % re.escape(x.qformat)
                with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
                    try:
                        x.wrap(mm, ameth)
                    except ValueError as exc:
                        raise type(exc)(str(exc) + f' Wrapped to {mm} bits.')

                continue

            elif overflow and aact == 'warning':
                errmsg = f"WARNING {errfmt}" % re.escape(x.qformat)
                warnmsg = warnfmt % mmap[uut.FixedPoint.sign(x)]
                with tools.CaptureWarnings() as warn:
                    x.wrap(mm, ameth)
                logs = warn.logs
                nose.tools.assert_equal(len(logs), 2)
                nose.tools.assert_regex(logs[0], errmsg)
                nose.tools.assert_regex(logs[1], warnmsg)

            else:
                with tools.CaptureWarnings() as warn:
                    x.wrap(mm, ameth)
                nose.tools.assert_equal(len(warn.logs), 0)

            nose.tools.assert_equal(x.signed, s)
            nose.tools.assert_equal(x.m, mm)
            nose.tools.assert_equal(x.n, n)

            nose.tools.assert_equal(x.bits, result)

    errmsg = r'Q20\.10 can only wrap between \[1, 20\) integer bits\.'
    # Corner case: negative bit format
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', m=20, n=10, signed=1):
            x.wrap(-1)

    # Corner case: wrapping to 0 bits
    with nose.tools.assert_raises_regex(ValueError, 'U' + errmsg.replace('10', '0')):
        with x(overflow_alert='ignore', m=20, n=0, signed=0):
            x.wrap(0)

    # Corner case: wrapping to 0 integer bits for signed
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', m=20, n=10, signed=1):
            x.wrap(0)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.wrap(1.0)

@tools.setup(progress_bar=True, require_matlab=True)
def test_keep_lsbs():
    """Verify keep_lsbs
    """
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        '256s' # 256-character binary string
        'I' # unsigned int - signedness
        'I' # unsigned int - initial length
        'I' # unsigned int - resultant length
        'I' # unsigned int - overflow
        '64s' # 64-character string - hex result from clamping
        '64s' # 64-character string - hex result from wrapping
    )
    alert_properties = [x.name for x in uut.properties.Alert]
    alert_method_props = alert_properties + ['']
    overflow_properties = [x.name for x in uut.properties.Overflow]
    overflow_method_props = overflow_properties + ['']
    permutations = []
    for ometh in overflow_method_props:
        for oprop in overflow_properties:
            for ameth in alert_method_props:
                for aprop in alert_properties:
                    permutations.append((ometh, oprop, ameth, aprop))

    errfmt = r'\[SN\d+\]:? Overflow in format %s\.'
    warnfmt = {
        'clamp': r'WARNING \[SN\d+\]: Clamped to %s\.',
        'wrap': r'WARNING \[SN\d+\]: Wrapped %s\.',
    }
    mmap = {
        -1: 'minimum',
        1: 'maximum',
    }
    rmap = {}
    x = uut.FixedPoint(0)
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, L, LL, overflow, cresult, wresult = data
        init = init.decode()
        rmap['clamp'] = int(cresult.decode(), 16)
        rmap['wrap'] = int(wresult.decode(), 16)

        # Choose 6 permutations of property combinations to test
        for i, (ometh, oprop, ameth, aprop) in enumerate(random.sample(permutations, 6)):
            # Random initial format
            n = random.randint(0, L-s)
            m = L - n

            # Random result format
            nn = random.randint(0, LL-s)
            mm = LL - nn

            # Actual overflow and overflow_alert property value
            oact, aact = ometh or oprop, ameth or aprop

            # Initialize FixedPoint objects
            if i == 0:
                x = uut.FixedPoint(init, s, m, n,
                    overflow=oprop, overflow_alert=aprop, str_base=2)
            else:
                x.from_string('0')
                if x.m == 0:
                    x.m, x.n = m, n
                else:
                    x.n, x.m = n, m
                x.from_string(init)
                x.overflow = oprop
                x.overflow_alert = aprop

            UTLOG.debug("ORIG: %s\n"
                "Keeping %d LSBs in format %sQ%d.%d\n"
                "Method:   % 7r, % 9r\n"
                "Property: % 7r, % 9r\n"
                "Actual:   % 7r, % 9r\n"
                "%s.%s",
                x.qformat, LL, '' if s else 'U', mm, nn,
                ometh, ameth, oprop, aprop, oact, aact,
                str(x)[:x.m], str(x)[-x.n:],
                **LOGID
            )

            if overflow and aact == 'error':
                errmsg = errfmt % re.escape(x.qformat)
                with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
                    x.keep_lsbs(mm, nn, ometh, ameth)
                continue

            elif overflow and aact == 'warning':
                errmsg = f"WARNING {errfmt}" % re.escape(x.qformat)
                warnmsg = warnfmt[oact] % mmap[uut.FixedPoint.sign(x)]
                with tools.CaptureWarnings() as warn:
                    x.keep_lsbs(mm, nn, ometh, ameth)
                logs = warn.logs
                nose.tools.assert_equal(len(logs), 2)
                nose.tools.assert_regex(logs[0], errmsg)
                nose.tools.assert_regex(logs[1], warnmsg)

            else:
                with tools.CaptureWarnings() as warn:
                    x.keep_lsbs(mm, nn, ometh, ameth)
                nose.tools.assert_equal(len(warn.logs), 0)

            nose.tools.assert_equal(x.signed, s)
            nose.tools.assert_equal(x.m, mm)
            nose.tools.assert_equal(x.n, nn)

            nose.tools.assert_equal(x.bits, rmap[oact])

    # Corner case: non-positive word size or invalid rounding range
    errmsg = r'Bit format specifications must be non-negative\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.keep_lsbs(0, -1)
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.keep_lsbs(-1, 1)

    errmsg = r'Signed number must have at least 1 integer bit\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', m=10, signed=1):
            x.keep_lsbs(0, 42)

    errmsg = r'Total number of bits must be in the range \[2, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=5, m=5):
            x.keep_lsbs(1, 0)

    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(overflow_alert='ignore', n=5, m=5):
            x.keep_lsbs(6, 6)

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.keep_lsbs(1.0, 1)
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.keep_lsbs(1.0, 1.0)
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.keep_lsbs(-123, 1.0)
