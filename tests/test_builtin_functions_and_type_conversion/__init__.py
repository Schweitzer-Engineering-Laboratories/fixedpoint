#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from ..test_initialization_methods import (
    initfloat_gen,
    nondefault_props_gen,
)
from .. import tools

@tools.setup(progress_bar=True)
def test_abs():
    """Verify __abs__
    """
    for init, args, kwargs, _, m, n, bits in nondefault_props_gen():
        kwargs['overflow_alert'] = 'ignore'
        x = uut.FixedPoint(init, *args, **kwargs)
        y = abs(x)
        if x.signed and x.bits['s'] == 1:
            nose.tools.assert_equal(y, -x)
        else:
            nose.tools.assert_equal(y, x)

@tools.setup(progress_bar=True)
def test_int():
    """Verify __int__
    """
    for init, args, kwargs, _, m, n, bits in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        nose.tools.assert_equal(int(x) & (2**m-1), bits >> n)

@tools.setup(progress_bar=True)
def test_float():
    """Verify __float__
    """
    for init, _, _, _, _, _, _ in initfloat_gen():
        x = uut.FixedPoint(init)
        nose.tools.assert_equal(float(x), init)

    # Corner case: giant positive number
    x = uut.FixedPoint('0x0' + ('f' * 1000), 1, 4001, 0)
    nose.tools.assert_equal(float(x), float('inf'))

    # Corner case: giant negative number
    nose.tools.assert_equal(float(-x), float('-inf'))

@tools.setup(progress_bar=True)
def test_bool():
    """Verify __bool__
    """
    # Make sure we hit some False cases
    from math import log2 as _log2
    Lmax = _log2(tools.NUM_ITERATIONS) // 1

    result = {True: 0, False: 0}
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, Lmax)
        n = random.randint(0, Lmax - m)
        init = tools.random_float(s, m, n, {})
        x = uut.FixedPoint(init)

        nose.tools.assert_equal(bool(x), bool(init))
        result[bool(x)] += 1

    UTLOG.debug("TRUE:  %d\nFALSE: %d", result[True], result[False], **LOGID)


@tools.setup(progress_bar=True)
def test_bin_oct_hex():
    """Verify __index__ via bin(), oct(), hex()
    """
    for init, args, kwargs, _, _, _, _ in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        nose.tools.assert_equal(bin(x), bin(x.bits))
        nose.tools.assert_equal(oct(x), oct(x.bits))
        nose.tools.assert_equal(hex(x), hex(x.bits))

@tools.setup(progress_bar=True)
def test_str():
    """Verify __str__
    """
    for init, args, kwargs, _, _, _, _ in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        string = str(x)
        nose.tools.assert_equal(int(string, x.str_base), x.bits)

@tools.setup(progress_bar=True)
def test_format():
    """Verify __format__
    """
    invalids = 'ABcCDhHiIjJkKlLMNpPQrRStTuUvVwWyYzZ'
    errmsg = r"Unknown format code '[%s]'\." % invalids
    for init, args, kwargs, s, m, n, bits in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)

        # No format spec, just the raw bits.
        nose.tools.assert_equal(format(x), str(x.bits))

        # Different conversions
        nose.tools.assert_equal('{!r}'.format(x), repr(x))
        nose.tools.assert_equal('{!a}'.format(x), repr(x))
        nose.tools.assert_equal(f'{x!s}', str(x))

        # Add attributes_name
        nose.tools.assert_equal(f'{x.signed!r}', repr(x.signed))
        nose.tools.assert_equal(f'{x.m!s}', str(x.m))
        nose.tools.assert_equal(f'{x.n!a}', repr(x.n))

        # Add element_index and index_string
        nose.tools.assert_equal(f'{x.bits[0]!r}', repr(x.bits[0]))
        nose.tools.assert_equal(f'{x.bits[0:1]!a}', repr(x.bits[0:1]))
        if x.m:
            nose.tools.assert_equal(f'{x.bits["int"]!s}', str(x.bits['m']))
        else:
            nose.tools.assert_equal(f'{x.bits["n"]!s}', str(x.bits['frac']))

        # Format specs
        nose.tools.assert_equal(f'{x:s}', str(x))
        nose.tools.assert_equal(f'{x:#b}', bin(x))
        nose.tools.assert_equal(f'{x:d}', str(x.bits))
        nose.tools.assert_equal(f'{x:#o}', oct(x))
        nose.tools.assert_equal(f'{x:#x}', hex(x))
        nose.tools.assert_equal(f'{x:#X}', hex(x).upper())
        if x.n:
            nose.tools.assert_equal(f'{x:#xn}', hex(x.bits['n']))
        if x.m:
            nose.tools.assert_equal(f'{x:#om}', oct(x.bits['m']))
        nose.tools.assert_equal(f'{x:q}', x.qformat)
        try:
            f = float(x)
        except OverflowError:
            pass
        else:
            nose.tools.assert_equal(f'{x:e}', '{:e}'.format(f))
            nose.tools.assert_equal(format(x, 'E'), f'{f:E}')
            nose.tools.assert_equal('{:f}'.format(x), format(f, 'f'))
            nose.tools.assert_equal(f'{x:F}', '{:F}'.format(f))
            nose.tools.assert_equal(format(x, 'g'), f'{f:g}')
            nose.tools.assert_equal('{:G}'.format(x), format(f, 'G'))
            nose.tools.assert_equal(f'{x:%}', '{:%}'.format(f))

        # Invalid!
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            format(x, random.choice(invalids))

@tools.setup(progress_bar=True)
def test_repr():
    """Verify __repr__
    """
    for init, args, kwargs, _, _, _, _ in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        tools.verify_attributes(
            eval(repr(x).replace('FixedPoint', 'uut.FixedPoint')),
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

