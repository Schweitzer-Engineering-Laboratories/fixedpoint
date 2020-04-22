#!/usr/bin/env python3.8
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random
import re
import unittest.mock as mock

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools

@tools.setup(progress_bar=False)
def test_constructor_overflow():
    """Verify constructor overflow alert

    1. float overflow due to undersized integer format
    2. float overflow due to rounding
    3. integer overflow due to undersized integer format
    """
    # Test case 1
    errmsg = r'\[SN\d+\]:? [\d.e+-]+ overflows in UQ1\.5 format\.'
    with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
        uut.FixedPoint(2.23, 0, 1, 5, overflow_alert='error')

    with tools.CaptureWarnings() as warn:
        x = uut.FixedPoint(2.23, 0, 1, 5, overflow_alert='warning', overflow='clamp')
    nose.tools.assert_regex(warn.logs[0], "WARNING " + errmsg)
    nose.tools.assert_regex(warn.logs[1], r"WARNING \[SN\d+\]: Clamped to maximum\.")
    nose.tools.assert_equals(x.bits, 0b111111)

    with tools.CaptureWarnings() as warn:
        x = uut.FixedPoint(2.23, 0, 1, 5, overflow_alert='warning', overflow='wrap')
    nose.tools.assert_regex(warn.logs[0], "WARNING " + errmsg)
    nose.tools.assert_regex(warn.logs[1], r"WARNING \[SN\d+\]: Wrapped maximum\.")
    nose.tools.assert_equals(x.bits, 0b000111)

    with tools.CaptureWarnings() as warn:
        x = uut.FixedPoint(2.23, 0, 1, 5, overflow_alert='ignore', overflow='clamp')
    nose.tools.assert_equals(len(warn.logs), 0)
    nose.tools.assert_equals(x.bits, 0b111111)

    with tools.CaptureWarnings() as warn:
        x = uut.FixedPoint(2.23, 0, 1, 5, overflow_alert='ignore', overflow='wrap')
    nose.tools.assert_equals(len(warn.logs), 0)
    nose.tools.assert_equals(x.bits, 0b000111)

    # Test case 2
    overflowers = ['up', 'convergent', 'out', 'nearest']
    roundings = [x.name for x in uut.properties.Rounding]
    overflows = [x.name for x in uut.properties.Overflow]
    errmsg = r'\[SN\d+\]:? [\d.e+-]+ overflows in UQ1\.5 format\.'
    warnmsg = {
        'clamp': r'WARNING \[SN\d+\]: Clamped to maximum\.',
        'wrap': r'WARNING \[SN\d+\]: Wrapped maximum\.',
    }
    expected = 0b111111
    for rmethod in roundings:
        for omethod in overflows:
            if rmethod in overflowers:
                # Error
                with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, r'\[SN\d+\]:? [\d.e+-]+ overflows in UQ1\.5 format\.'):
                # with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg[rmethod] % r"UQ1\.5"):
                    uut.FixedPoint(1.99, 0, 1, 5, overflow_alert='error',
                        overflow=omethod, rounding=rmethod)

                # Warning
                with tools.CaptureWarnings() as warn:
                    x = uut.FixedPoint(1.99, 0, 1, 5, overflow_alert='warning',
                        overflow=omethod, rounding=rmethod)
                nose.tools.assert_equals(len(logs := warn.logs), 2)
                nose.tools.assert_regex(logs[0], f'WARNING {errmsg}')
                nose.tools.assert_regex(logs[1], warnmsg[omethod])
                nose.tools.assert_equals(x.bits, expected)

                # Ignore
                with tools.CaptureWarnings() as warn:
                    x = uut.FixedPoint(1.99, 0, 1, 5, overflow_alert='ignore',
                        overflow=omethod, rounding=rmethod)
                nose.tools.assert_equals(len(warn.logs), 0)
                nose.tools.assert_equals(x.bits, expected)

    # Test case 3
    init = lambda: random.randint(2, 2**1000) * (2*random.randrange(2) - 1)
    errmsg = r'\[SN\d+\]:? Integer -?\d+ overflows in U?Q\d+\.\d+ format\.'
    warnmsg = lambda o, v: f"WARNING \\[SN\\d+\\]: {o.title()}p?ed{' to' if o == 'clamp' else ''} m{'ax' if v > 0 else 'in'}imum\\."
    for omethod in overflows:
        # Error
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(init(), m=1, overflow_alert='error')

        # Warning
        with tools.CaptureWarnings() as warn:
            x = uut.FixedPoint(val := init(), m=1,
                overflow_alert='warning', overflow=omethod)
        nose.tools.assert_equals(len(logs := warn.logs), 2)
        nose.tools.assert_regex(logs[0], 'WARNING ' + errmsg)
        nose.tools.assert_regex(logs[1], warnmsg(omethod, val))
        nose.tools.assert_equals(x.bits, (val % 2) if omethod == 'wrap' else 1, f'{omethod} {val}')

        # Ignore
        with tools.CaptureWarnings() as warn:
            x = uut.FixedPoint(val := init(), m=1,
                overflow_alert='ignore', overflow=omethod)
        nose.tools.assert_equals(len(warn.logs), 0)
        nose.tools.assert_equals(x.bits, (val % 2) if omethod == 'wrap' else 1, val)

@tools.setup(progress_bar=True)
def test_signed_setter():
    """Verify overflow alerts from changing signedness
    """
    strbases = list(uut.properties.StrConv.keys())
    for _ in tools.test_iterator():
        L = random.randrange(2, 1000)
        s = random.randrange(2)
        m = random.randrange(1, L)
        n = L - m
        bits = random.getrandbits(L) | 2**(L-1)
        x = uut.FixedPoint(bin(bits), s, m, n,  overflow_alert='error',
            str_base=random.choice(strbases))

        errmsg = re.escape(f'Changing signedness on {x!s} causes overflow.')
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            x.signed = not x.signed
        nose.tools.assert_equals(s, x.signed)

        x.overflow_alert = 'warning'
        for overflow in uut.properties.Overflow:
            x.str_base = random.choice(strbases)
            x.overflow = overflow.name
            prefix = 'Clamped to' if overflow.name == 'clamp' else 'Wrapped'
            errmsg = [
                r'WARNING \[SN\d+\]: Changing signedness on %s causes overflow\.' % x,
                r'WARNING \[SN\d+\]: %s %s\.' % (prefix, 'minimum' if x.signed else 'maximum')
            ]
            signed = x.signed
            with tools.CaptureWarnings() as warn:
                x.signed = not x.signed
            for log, exp in zip(warn.logs, errmsg):
                nose.tools.assert_regex(log, exp)
            nose.tools.assert_not_equals(signed, x.signed)

            x.overflow_alert = 'ignore'
            x.str_base = random.choice(strbases)
            x.overflow = overflow.name
            signed = x.signed
            with tools.CaptureWarnings() as warn:
                x.signed = not x.signed
            nose.tools.assert_equals(len(warn.logs), 0)
            nose.tools.assert_not_equals(signed, x.signed)

@tools.setup(progress_bar=True)
def test_subtraction_alerts():
    """Verify overflow alerts from unsigned subtraction
    """
    def qrand():
        _m = random.randrange(51), random.randrange(51)
        return _m + tuple(random.randrange(_x == 0, 51 - _x) for _x in _m)

    for _ in tools.test_iterator():
        a, b = 1, 0
        while a > b:
            am, bm, an, bn = qrand()
            a = random.getrandbits(am + an) * 2**-an
            b = random.getrandbits(bm + bn) * 2**-bn

        x = uut.FixedPoint(a, 0, am, an, overflow_alert='error')
        y = uut.FixedPoint(b, 0, bm, bn, overflow_alert='error')

        errmsg = r'Unsigned subtraction causes overflow\.'
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            x - y

        for overflow in uut.properties.Overflow:
            x.overflow_alert, y.overflow_alert = 'warning', 'warning'
            x.overflow, y.overflow = overflow.name, overflow.name
            prefix = 'Clamped to' if overflow.name == 'clamp' else 'Wrapped'
            errmsg = [
                r'WARNING \[SN\d+\]: Unsigned subtraction causes overflow\.',
                r'WARNING \[SN\d+\]: %s minimum\.' % prefix,
            ]
            with tools.CaptureWarnings() as warn:
                z = x - y

            x.overflow_alert, y.overflow_alert = 'ignore', 'ignore'
            with tools.CaptureWarnings() as ignore:
                zz = x - y

            for log, exp in zip(warn.logs, errmsg):
                nose.tools.assert_regex(log, exp)
            nose.tools.assert_equals(len(ignore.logs), 0)

            if overflow.name == 'clamp':
                nose.tools.assert_equals(float(z), 0.0)
            else:
                nose.tools.assert_not_equals(float(z), 0.0)

@tools.setup(progress_bar=True)
def test_negation_alerts():
    """Verify overflow alerts from negation
    """
    errfmt = r"Negating 0?[xob]?%s \(%s\) causes overflow\."
    strbases = list(uut.properties.StrConv.keys())
    for _ in tools.test_iterator():
        L = random.randrange(2, 1000)
        m = random.randrange(1, L)
        n = L - m
        sbits = 2**(L-1)
        while (ubits := random.getrandbits(L-1)) == 0:
            pass
        ubits |= sbits

        # Unsigned with MSB set to 1
        u = uut.FixedPoint(bin(ubits), 0, m, n, overflow_alert='error',
            str_base=random.choice(strbases))

        # Signed, max negative
        s = uut.FixedPoint(bin(sbits), 1, max(m, 1), n - (m == 0),
            overflow_alert='error', str_base=random.choice(strbases))

        errmsg = r'Unsigned numbers cannot be negated\.'
        with nose.tools.assert_raises_regex(uut.FixedPointError, errmsg):
            -u

        errmsg = errfmt % (re.escape(str(s)), re.escape(s.qformat))
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            -s

        s.overflow_alert = 'warning'
        s.str_base = random.choice(strbases)
        errmsg = [
            r'WARNING \[SN\d+\]: ' + (errfmt % (re.escape(str(s)), re.escape(s.qformat))),
            r'WARNING \[SN\d+\]: Adjusting Q format to Q%d\.%d to allow negation\.' % (m+1, n),
        ]
        with tools.CaptureWarnings() as warn:
            y = -s

        s.overflow_alert = 'ignore'
        with tools.CaptureWarnings() as ignore:
            z = -s

        for log, exp in zip(warn.logs, errmsg):
            nose.tools.assert_regex(log, exp)
        nose.tools.assert_equals(len(ignore.logs), 0)

        nose.tools.assert_equals(abs(s), y)
        nose.tools.assert_equals(abs(s), z)

@tools.setup(progress_bar=False)
def test_implicit_cast_alerts():
    """Verify implicit cast alerts
    """
    errmsg = r"Casting 0\.625 to %s introduces an error of 1\.250*e-01"
    x = uut.FixedPoint(-2, rounding='up')
    f = 0b101 * 2**-3

    # Patch min_n to always return 2
    with mock.patch(f'{uut.__name__}.FixedPoint.min_n', return_value=2) as min_n:

        x.implicit_cast_alert = 'error'
        with nose.tools.assert_raises_regex(uut.ImplicitCastError, errmsg % r'UQ0\.2'):
            x + f
        with nose.tools.assert_raises_regex(uut.ImplicitCastError, errmsg % r'UQ0\.2'):
            f + x
        with nose.tools.assert_raises_regex(uut.ImplicitCastError, errmsg % r'Q1\.1'):
            x - f
        with nose.tools.assert_raises_regex(uut.ImplicitCastError, errmsg % r'Q1\.1'):
            f - x
        with nose.tools.assert_raises_regex(uut.ImplicitCastError, errmsg % r'UQ0\.2'):
            x * f
        with nose.tools.assert_raises_regex(uut.ImplicitCastError, errmsg % r'UQ0\.2'):
            f * x

        x.implicit_cast_alert = 'warning'
        with tools.CaptureWarnings() as warn:
            x + f, f + x
            x - f, f - x
            x * f, f * x
        nose.tools.assert_equal(len(logs := warn.logs), 6)
        for i in [0, 1, 4, 5]:
            nose.tools.assert_regex(logs[0], errmsg % r'UQ0\.2')
        nose.tools.assert_regex(logs[2], errmsg % r'Q1\.1')
        nose.tools.assert_regex(logs[3], errmsg % r'Q1\.1')

        x.implicit_cast_alert = 'ignore'
        with tools.CaptureWarnings() as warn:
            x + f, f + x
            x - f, f - x
            x * f, f * x
        nose.tools.assert_equal(len(warn.logs), 0)
