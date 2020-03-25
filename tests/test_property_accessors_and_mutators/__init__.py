#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random
import re

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools
from ..test_initialization_methods import initstr_gen

@tools.setup(progress_bar=True)
def test_signed():
    """Verify `signed` property/mutator

    Test cases of setting x.signed contain the following permutations:
        1.  signed=0, m=0, n>0
        2.1 signed=0, m>0, n=0, msb is 0
        2.2 signed=0, m>0, n=0, msb is 1, overflow_alert = error
        2.3 signed=0, m>0, n=0, msb is 1, overflow_alert = not error, overflow = clamp
        2.4 signed=0, m>0, n=0, msb is 1, overflow_alert = not error, overflow = wrap
        3.1 signed=0, m>0, n>0, msb is 0
        3.2 signed=0, m>0, n>0, msb is 1, overflow_alert = error
        3.3 signed=0, m>0, n>0, msb is 1, overflow_alert = not error, overflow = clamp
        3.4 signed=0, m>0, n>0, msb is 1, overflow_alert = not error, overflow = wrap
        4.  signed=1, m=0, n>0
        5.1 signed=1, m>0, n=0, msb is 0
        5.2 signed=1, m>0, n=0, msb is 1, overflow_aler = error
        5.3 signed=1, m>0, n=0, msb is 1, overflow_aler = not error, overflow = clamp
        5.4 signed=1, m>0, n=0, msb is 1, overflow_aler = not error, overflow = wrap
        6.1 signed=1, m>0, n>0, msb is 0
        6.2 signed=1, m>0, n>0, msb is 1, overflow_alert = error
        6.3 signed=1, m>0, n>0, msb is 1, overflow_alert = not error, overflow = clamp
        6.4 signed=1, m>0, n>0, msb is 1, overflow_alert = not error, overflow = wrap
    """
    warning = {'overflow_alert': 'warning'}
    wrap = {'overflow': 'wrap'}

    # Test case 1: signed=0, m=0, n>0
    x = uut.FixedPoint(random.random(), 0, 0, 42)
    nose.tools.assert_false(x.signed)
    x.signed = False
    nose.tools.assert_false(x.signed)
    errmsg = r"Cannot change sign with 0 integer bits\."
    with nose.tools.assert_raises_regex(uut.FixedPointError, errmsg):
        x.signed = True
    nose.tools.assert_false(x.signed)

    # Test case 4: signed=1, m=0, n>0
    errmsg = r"Number of integer bits must be at least 1 for signed numbers\."
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x = uut.FixedPoint(random.random(), 1, 0, 42)

    for i in tools.test_iterator():
        UTLOG.debug("Iteration %d of %d", i+1, tools.NUM_ITERATIONS, **LOGID)
        # Unsigned test cases
        for n in [0, random.randint(1, 1000)]:
            # Test case 2.1: signed=0, m>0, n=0, msb is 0
            # Test case 3.1 signed=0, m>0, n>0, msb is 0
            x = uut.FixedPoint(random.getrandbits(7) | 1, 0, 8, n)
            nose.tools.assert_false(x.signed)
            x.signed = False
            nose.tools.assert_false(x.signed)
            x.signed = True
            nose.tools.assert_true(x.signed)
            nose.tools.assert_true(x > 0)

            # Test case 2.2: signed=0, m>0, n=0, msb is 1, overflow_alert = error
            # Test case 3.2: signed=0, m>0, n>0, msb is 1, overflow_alert = error
            x = uut.FixedPoint(0x80 | random.getrandbits(7), 0, 8, n)
            nose.tools.assert_false(x.signed)
            x.signed = False
            nose.tools.assert_false(x.signed)
            errmsg = r'\[SN\d+\] Changing signedness on [\da-f]+ causes overflow\.'
            with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
                x.signed = True
            nose.tools.assert_false(x.signed)
            nose.tools.assert_true(x > 0)

            # Test case 2.3: signed=0, m>0, n=0, msb is 1, overflow_alert = not error, overflow = clamp
            # Test case 3.3: signed=0, m>0, n>0, msb is 1, overflow_alert = not error, overflow = clamp
            x = uut.FixedPoint(0x80 | random.getrandbits(7), 0, 8, 0, **warning)
            nose.tools.assert_false(x.signed)
            x.signed = False
            nose.tools.assert_false(x.signed)
            errmsg = [
                r'WARNING \[SN\d+\]: Changing signedness on [\da-f]+ causes overflow\.',
                r'WARNING \[SN\d+\]: Clamped to maximum\.'
            ]
            with tools.CaptureWarnings() as warn:
                x.signed = True
            nose.tools.assert_equal(len(warn), 2)
            logs = warn.logs
            nose.tools.assert_regex(warn.logs[-2], errmsg[-2])
            nose.tools.assert_regex(warn.logs[-1], errmsg[-1])
            nose.tools.assert_true(x.signed)
            nose.tools.assert_true(x > 0)
            nose.tools.assert_true(x.clamped)

            # Test case 2.4: signed=0, m>0, n=0, msb is 1, overflow_alert = not error, overflow = wrap
            # Test case 3.4: signed=0, m>0, n>0, msb is 1, overflow_alert = not error, overflow = wrap
            x = uut.FixedPoint(0x80 | random.getrandbits(7), 0, 8, 0, **warning, **wrap)
            nose.tools.assert_false(x.signed)
            x.signed = False
            nose.tools.assert_false(x.signed)
            errmsg = [
                r'WARNING \[SN\d+\]: Changing signedness on [\da-f]+ causes overflow\.',
                r'WARNING \[SN\d+\]: Wrapped maximum\.'
            ]
            with tools.CaptureWarnings() as warn:
                x.signed = True
            nose.tools.assert_equal(len(warn), 2)
            logs = warn.logs
            nose.tools.assert_regex(warn.logs[-2], errmsg[-2])
            nose.tools.assert_regex(warn.logs[-1], errmsg[-1])
            nose.tools.assert_true(x.signed)
            nose.tools.assert_true(x < 0)

            # Test case 5.1: signed=1, m>0, n=0, msb is 0
            # Test case 6.1 signed=1, m>0, n>0, msb is 0
            x = uut.FixedPoint(random.getrandbits(7) | 1, 1, 8, n)
            nose.tools.assert_true(x.signed)
            x.signed = True
            nose.tools.assert_true(x.signed)
            x.signed = False
            nose.tools.assert_false(x.signed)
            nose.tools.assert_true(x > 0)

            # Test case 5.2: signed=1, m>0, n=0, msb is 1, overflow_alert = error
            # Test case 6.2: signed=1, m>0, n>0, msb is 1, overflow_alert = error
            x = uut.FixedPoint(-(random.getrandbits(7) | 1), 1, 8, n)
            nose.tools.assert_true(x.signed)
            x.signed = True
            nose.tools.assert_true(x.signed)
            errmsg = r'\[SN\d+\] Changing signedness on [\da-f]+ causes overflow\.'
            with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
                x.signed = False
            nose.tools.assert_true(x.signed)
            nose.tools.assert_true(x < 0)

            # Test case 5.3: signed=1, m>0, n=0, msb is 1, overflow_alert = not error, overflow = clamp
            # Test case 6.3: signed=1, m>0, n>0, msb is 1, overflow_alert = not error, overflow = clamp
            x = uut.FixedPoint(-(random.getrandbits(7) | 1), 1, 8, n, **warning)
            nose.tools.assert_true(x.signed)
            x.signed = True
            nose.tools.assert_true(x.signed)
            errmsg = [
                r'WARNING \[SN\d+\]: Changing signedness on [\da-f]+ causes overflow\.',
                r'WARNING \[SN\d+\]: Clamped to minimum\.'
            ]
            with tools.CaptureWarnings() as warn:
                x.signed = False
            nose.tools.assert_equal(len(warn), 2)
            logs = warn.logs
            nose.tools.assert_regex(warn.logs[-2], errmsg[-2])
            nose.tools.assert_regex(warn.logs[-1], errmsg[-1])
            nose.tools.assert_false(x.signed)
            nose.tools.assert_equal(x, 0)
            nose.tools.assert_true(x.clamped)

            # Test case 5.4: signed=1, m>0, n=0, msb is 1, overflow_alert = not error, overflow = wrap
            # Test case 6.4: signed=1, m>0, n>0, msb is 1, overflow_alert = not error, overflow = wrap
            x = uut.FixedPoint(-(random.getrandbits(7) | 1), 1, 8, n, **warning, **wrap)
            nose.tools.assert_true(x.signed)
            x.signed = True
            nose.tools.assert_true(x.signed)
            errmsg = [
                r'WARNING \[SN\d+\]: Changing signedness on [\da-f]+ causes overflow\.',
                r'WARNING \[SN\d+\]: Wrapped minimum\.'
            ]
            with tools.CaptureWarnings() as warn:
                x.signed = False
            nose.tools.assert_equal(len(warn), 2)
            logs = warn.logs
            nose.tools.assert_regex(warn.logs[-2], errmsg[-2])
            nose.tools.assert_regex(warn.logs[-1], errmsg[-1])
            nose.tools.assert_false(x.signed)
            nose.tools.assert_not_equal(x, 0)

@tools.setup(progress_bar=True)
def test_m():
    """Verify `m` property/mutator

    Test cases include:
        1.    Bit growth
        1.1   Verify sign extension for negative signed numbers
        1.2   Verify 0-padding for non-negative signed numbers
        1.3   Verify 0-padding for unsigned numbers
        2.    No bit growth
        2.1   Verify no changes for negative signed numbers
        2.2   Verify no changes for non-negative signed numbers
        2.3   Verify no changes for unsigned numbers
        3.    Bit shrinking
        3.1   No overflow
        3.1.1 Verify shrinking without overflow for negative signed numbers
        3.1.2 Verify shrinking without overflow for non-negative signed numbers
        3.1.3 Verify shrinking without overflow for unsigned numbers
        3.2   Clamping
        3.2.1 Verify shrinking with clamp for negative signed numbers
        3.2.2 Verify shrinking with clamp for positive signed numbers
        3.2.3 Verify shrinking with clamp for unsigned numbers
        3.3   Wrapping
        3.3.1 Verify shrinking with wrap for negative signed numbers
        3.3.2 Verify shrinking with wrap for non-negative signed numbers
        3.3.3 Verify shrinking with wrap for unsigned numbers
    """
    positive = list(range(1, 16))
    natural = list(range(16))
    negative = list(range(-16, 0))

    for _ in tools.test_iterator():
        # Test case 1.1: Verify sign extension for negative signed numbers
        value = random.choice(negative) * random.random()
        x = uut.FixedPoint(value, str_base=2)
        ostr, ofloat = str(x), float(x)
        ext = random.randrange(1, 10)
        x.m += ext
        nose.tools.assert_equal(x.m, uut.FixedPoint.min_m(value, 1) + ext)
        nose.tools.assert_true(str(x).startswith('1' * ext))
        nose.tools.assert_true(str(x).endswith(ostr))
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 1.2 Verify sign 0-padding for non-negative signed numbers
        value = random.choice(natural) * random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, 1, minm, str_base=2)
        obin, ofloat = bin(x), float(x)
        ext = random.randrange(1, 10)
        x.m += ext
        nose.tools.assert_less_equal(x.m, minm + ext)
        nose.tools.assert_equal(bin(x), obin)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 1.3: Verify 0-padding for unsigned numbers
        value = random.choice(positive) * random.random()
        minm = uut.FixedPoint.min_m(value)
        x = uut.FixedPoint(value, 0, minm, str_base=2)
        obin, ofloat = bin(x), float(x)
        ext = random.randrange(1, 10)
        x.m += ext
        nose.tools.assert_equal(x.m, minm + ext)
        nose.tools.assert_equal(bin(x), obin)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 2.1: Verify no changes for negative signed numbers
        value = random.choice(negative) * random.random()
        x = uut.FixedPoint(value, str_base=2)
        ostr, ofloat = str(x), float(x)
        x.m = uut.FixedPoint.min_m(value, 1)
        nose.tools.assert_equal(x.m, uut.FixedPoint.min_m(value, 1))
        nose.tools.assert_equal(str(x), ostr)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 2.2: Verify no changes for non-negative signed numbers
        value = random.choice(natural) * random.random()
        x = uut.FixedPoint(value, 1, str_base=2)
        obin, ofloat = bin(x), float(x)
        minm = uut.FixedPoint.min_m(value, 1)
        x.m = minm
        nose.tools.assert_equal(x.m, minm)
        nose.tools.assert_equal(bin(x), obin)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 2.3: Verify no changes for unsigned numbers
        value = random.choice(positive) * random.random()
        x = uut.FixedPoint(value, 0, str_base=2)
        obin, ofloat = bin(x), float(x)
        x.m = uut.FixedPoint.min_m(value)
        nose.tools.assert_equal(x.m, uut.FixedPoint.min_m(value))
        nose.tools.assert_equal(bin(x), obin)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 3.1.1: Verify shrinking without overflow for negative signed
        # numbers
        value = random.choice(negative) * random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, m=minm + 1, str_base=2)
        ostr, ofloat = str(x), float(x)
        x.m = minm
        nose.tools.assert_equal(x.m, minm)
        nose.tools.assert_equal(f"1{x!s}", ostr)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 3.1.2: Verify shrinking without overflow for non-negative
        # signed numbers
        value = random.choice(natural) * random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, 1, minm + 1, str_base=2)
        obin, ofloat = bin(x), float(x)
        x.m = minm
        nose.tools.assert_equal(x.m, minm)
        nose.tools.assert_equal(bin(x), obin)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 3.1.3: Verify shrinking without overflow for unsigned
        # numbers
        value = random.choice(positive) * random.random()
        minm = uut.FixedPoint.min_m(value)
        x = uut.FixedPoint(value, 0, minm + 1, str_base=2)
        obin, ofloat = bin(x), float(x)
        x.m = minm
        nose.tools.assert_equal(x.m, minm)
        nose.tools.assert_equal(bin(x), obin)
        nose.tools.assert_equal(float(x), ofloat)

        # Test case 3.2.1: Verify shrinking with clamp for negative signed
        # numbers
        overflow = {'overflow_alert': 'warning', 'overflow': 'clamp'}
        value = -2**(1+random.choice(positive)) + random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, 1, minm, str_base=2, **overflow)
        errmsg = [r"Overflow in format Q\d+\.\d+\.", r"Clamped to minimum\."]
        with tools.CaptureWarnings() as warnings:
            x.m -= 1
            logs = warnings.logs
            nose.tools.assert_equal(len(logs), 2)
            nose.tools.assert_regex(logs[-2], errmsg[-2])
            nose.tools.assert_regex(logs[-1], errmsg[-1])
        nose.tools.assert_equal(x.bits['msb'], 1)
        nose.tools.assert_equal(str(x).count('0'), len(x) - 1)
        nose.tools.assert_true(x.clamped)

        # Test case 3.2.2: Verify shrinking with clamp for positive signed
        # numbers
        overflow = {'overflow_alert': 'warning', 'overflow': 'clamp'}
        value = 2**(1+random.choice(positive)) - 2 + random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, 1, minm, str_base=2, **overflow)
        errmsg = [r"Overflow in format Q\d+\.\d+\.", r"Clamped to maximum\."]
        with tools.CaptureWarnings() as warnings:
            x.m -= 1
            logs = warnings.logs
            nose.tools.assert_equal(len(logs), 2)
            nose.tools.assert_regex(logs[-2], errmsg[-2])
            nose.tools.assert_regex(logs[-1], errmsg[-1])
        nose.tools.assert_equal(x.bits['msb'], 0)
        nose.tools.assert_equal(str(x).count('1'), len(x) - 1)
        nose.tools.assert_true(x.clamped)

        # Test case 3.2.3: Verify shrinking with clamp for unsigned numbers
        overflow = {'overflow_alert': 'warning', 'overflow': 'clamp'}
        value = 2**(1+random.choice(positive)) - 2 + random.random()
        minm = uut.FixedPoint.min_m(value)
        x = uut.FixedPoint(value, 0, minm, str_base=2, **overflow)
        errmsg = [r"Overflow in format UQ\d+\.\d+\.", r"Clamped to maximum\."]
        with tools.CaptureWarnings() as warnings:
            x.m -= 1
            logs = warnings.logs
            nose.tools.assert_equal(len(logs), 2)
            nose.tools.assert_regex(logs[-2], errmsg[-2])
            nose.tools.assert_regex(logs[-1], errmsg[-1])
        nose.tools.assert_equal(str(x), '1' * len(x))
        nose.tools.assert_true(x.clamped)

        # Test case 3.3.1: Verify shrinking with wrap for negative signed
        # numbers
        overflow = {'overflow_alert': 'warning', 'overflow': 'wrap'}
        value = -2**(1+random.choice(positive)) + random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, 1, minm, str_base=2, **overflow)
        ostr = str(x)
        errmsg = [r"Overflow in format Q\d+\.\d+\.", r"Wrapped minimum\."]
        with tools.CaptureWarnings() as warnings:
            x.m -= 1
            logs = warnings.logs
            nose.tools.assert_equal(len(logs), 2)
            nose.tools.assert_regex(logs[-2], errmsg[-2])
            nose.tools.assert_regex(logs[-1], errmsg[-1])
        nose.tools.assert_equal(ostr[1:], str(x))

        # Test case 3.3.2: Verify shrinking with wrap for positive signed
        # numbers
        overflow = {'overflow_alert': 'warning', 'overflow': 'wrap'}
        value = 2**(1+random.choice(positive)) - 2 + random.random()
        minm = uut.FixedPoint.min_m(value, 1)
        x = uut.FixedPoint(value, 1, minm, str_base=2, **overflow)
        ostr = str(x)
        errmsg = [r"Overflow in format Q\d+\.\d+\.", r"Wrapped maximum\."]
        with tools.CaptureWarnings() as warnings:
            x.m -= 1
            logs = warnings.logs
            nose.tools.assert_equal(len(logs), 2)
            nose.tools.assert_regex(logs[-2], errmsg[-2])
            nose.tools.assert_regex(logs[-1], errmsg[-1])
        nose.tools.assert_equal(ostr[1:], str(x))

        # Test case 3.3.3: Verify shrinking with wrap for unsigned numbers
        overflow = {'overflow_alert': 'warning', 'overflow': 'wrap'}
        value = 2**(1+random.choice(positive)) - 2 + random.random()
        minm = uut.FixedPoint.min_m(value)
        x = uut.FixedPoint(value, 0, minm, str_base=2, **overflow)
        ostr = str(x)
        errmsg = [r"Overflow in format UQ\d+\.\d+\.", r"Wrapped maximum\."]
        with tools.CaptureWarnings() as warnings:
            x.m -= 1
            logs = warnings.logs
            nose.tools.assert_equal(len(logs), 2)
            nose.tools.assert_regex(logs[-2], errmsg[-2])
            nose.tools.assert_regex(logs[-1], errmsg[-1])
        nose.tools.assert_equal(ostr[1:], str(x))

    # Corner case: too few bits
    errmsg = r'Number of integer bits must be positive for signed numbers\.'
    x = uut.FixedPoint('0b101', 1, 1, 2, overflow_alert='ignore')
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.m = 0

    x.signed = 0 # Convert from Q1.2 to UQ1.2
    errmsg = r'Number of integer bits must be non-negative\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.m = -1

    x.n = 0 # Convert from UQ1.2 to UQ1.0
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        x.m = 0

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.m = 1.0

@tools.setup(progress_bar=True)
def test_n():
    """Verify `n` property/mutator

    Test cases include:
        1.    Bit growth
        1.1   Verify 0-padding
        2.    No bit growth
        2.1   Verify no changes
        3.    Bit shrinking
        3.1   No overflow (oversize m to ensure no overflow)
        3.2   Clamping
        3.2.1 Convergent rounding
        3.2.2 Round out
        3.2.3 Round nearest
        3.2.4 Round up
        3.3   Wrapping
        3.2.1 Convergent rounding
        3.2.2 Round out
        3.2.3 Round nearest
        3.2.4 Round up
    """
    errmsg = [
        r'WARNING \[SN\d+\]: {round} {post:q} causes overflow\.',
        r'WARNING \[SN\d+\]: {overflow} maximum\.',
        r'Word size \(integer and fractional\) must be positive\.',
        r'Number of fractional bits must be non-negative\.'
    ]

    rounding_conv = {
        'convergent': 'Convergent round to',
        'out': 'Rounding out to',
        'nearest': 'Rounding to nearest',
        'up': 'Rounding up to',
    }

    overflow_conv = {
        'clamp': 'Clamped to',
        'wrap': 'Wrapped',
    }

    for _ in tools.test_iterator():
        # Test case 1.1: Verify 0-padding on bit growth
        x = uut.FixedPoint(init := 2 * random.random() - 1, str_base=2)
        s, m, n = x.signed, x.m, x.n
        x.n += (nbits := random.randrange(10) + 1)
        nose.tools.assert_equal(x.bits[nbits-1: 0: -1], 0)

        # Test case 2.1: Verify no changes when n doesn't change
        pre = str(x)
        x.n = x.n
        nose.tools.assert_equal(pre, str(x))

        # Test case 3.1: Verify rounding methods without overflow
        for scheme in rounding_conv.keys():
            x.rounding = scheme
            x.resize(m + 1, n)
            x.from_float(init)
            pre = round(x, nround := random.randrange(n))
            x.n = nround
            nose.tools.assert_equal(pre, x)

        # Test case 3.2 & 3.3: Verify rounding methods with overflow
        kwargs = {}
        x.overflow_alert = 'warning'
        for overflow in uut.properties.Overflow:
            x.overflow = overflow.name
            kwargs['overflow'] = overflow_conv[overflow.name]
            for scheme, errsub in rounding_conv.items():
                x.rounding = kwargs['rounding'] = scheme
                kwargs['round'] = errsub
                x.from_int(0)
                x.resize(m, n)
                x.from_string(hex(x._maximum))
                kwargs['pre'] = uut.FixedPoint(x)
                with tools.CaptureWarnings() as warn:
                    key = round(x, nround := random.randrange(x.m == 0, n))
                    x.n = nround # errmsg 1 and 2
                for i, log in enumerate(warn.logs):
                    nose.tools.assert_regex(log, errmsg[i % 2].format(post=x, **kwargs), str(i))
                nose.tools.assert_equal(key, x)

        if x.m == 0:
            with nose.tools.assert_raises_regex(ValueError, errmsg[2]):
                x.n = 0
        with nose.tools.assert_raises_regex(ValueError, errmsg[3]):
            x.n = -random.randrange(100) - 1

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(1.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.n = 1.0

@tools.setup(progress_bar=False)
def test_str_base():
    """Verify `str_base` property/mutator
    """
    errmsg = 'Invalid str_base setting: %d\\.'
    x = uut.FixedPoint(random.random())
    for base in range(20):
        if base in uut.properties.StrConv.keys():
            x.str_base = base
            nose.tools.assert_equal(x.str_base, base)
            tmp = uut.FixedPoint(random.random(), str_base=base)
            nose.tools.assert_equal(tmp.str_base, base)
        else:
            with nose.tools.assert_raises_regex(ValueError, errmsg % base):
                x.str_base = base

@tools.setup(progress_bar=False)
def test_overflow_alert():
    """Verify `overflow_alert` property/mutator
    """
    random.shuffle(testvec := (
            list(uut.properties.Rounding) +
            list(uut.properties.Alert) +
            list(uut.properties.Overflow) +
            list(uut.properties.StrBase)
        )
    )
    x = uut.FixedPoint(random.random())
    errmsg = "Invalid overflow_alert setting: %r\\."
    for value in testvec:
        if value in uut.properties.Alert:
            x.overflow_alert = value.name
            nose.tools.assert_equal(x.overflow_alert, value.name)
            tmp = uut.FixedPoint(random.random(), overflow_alert=value.name)
            nose.tools.assert_equal(tmp.overflow_alert, value.name)
        else:
            with nose.tools.assert_raises_regex(ValueError, errmsg % value.name):
                x.overflow_alert = value.name

@tools.setup(progress_bar=False)
def test_implicit_cast_alert():
    """Verify `implicit_cast_alert` property/mutator
    """
    random.shuffle(testvec := (
            list(uut.properties.Rounding) +
            list(uut.properties.Alert) +
            list(uut.properties.Overflow) +
            list(uut.properties.StrBase)
        )
    )
    x = uut.FixedPoint(random.random())
    errmsg = "Invalid implicit_cast_alert setting: %r\\."
    for value in testvec:
        if value in uut.properties.Alert:
            x.implicit_cast_alert = value.name
            nose.tools.assert_equal(x.implicit_cast_alert, value.name)
            tmp = uut.FixedPoint(random.random(), implicit_cast_alert=value.name)
            nose.tools.assert_equal(tmp.implicit_cast_alert, value.name)
        else:
            with nose.tools.assert_raises_regex(ValueError, errmsg % value.name):
                x.implicit_cast_alert = value.name

@tools.setup(progress_bar=False)
def test_mismatch_alert():
    """Verify `mismatch_alert` property/mutator
    """
    random.shuffle(testvec := (
            list(uut.properties.Rounding) +
            list(uut.properties.Alert) +
            list(uut.properties.Overflow) +
            list(uut.properties.StrBase)
        )
    )
    x = uut.FixedPoint(random.random())
    errmsg = "Invalid mismatch_alert setting: %r\\."
    for value in testvec:
        if value in uut.properties.Alert:
            x.mismatch_alert = value.name
            nose.tools.assert_equal(x.mismatch_alert, value.name)
            tmp = uut.FixedPoint(random.random(), mismatch_alert=value.name)
            nose.tools.assert_equal(tmp.mismatch_alert, value.name)
        else:
            with nose.tools.assert_raises_regex(ValueError, errmsg % value.name):
                x.mismatch_alert = value.name

@tools.setup(progress_bar=False)
def test_rounding():
    """Verify `rounding` property/mutator
    """
    random.shuffle(testvec := (
            list(uut.properties.Rounding) +
            list(uut.properties.Alert) +
            list(uut.properties.Overflow) +
            list(uut.properties.StrBase)
        )
    )
    x = uut.FixedPoint(random.random())
    errmsg = "Invalid rounding setting: %r\\."
    for value in testvec:
        if value in uut.properties.Rounding:
            x.rounding = value.name
            nose.tools.assert_equal(x.rounding, value.name)
            tmp = uut.FixedPoint(random.random(), rounding=value.name)
            nose.tools.assert_equal(tmp.rounding, value.name)
        else:
            with nose.tools.assert_raises_regex(ValueError, errmsg % value.name):
                x.rounding = value.name

@tools.setup(progress_bar=False)
def test_overflow():
    """Verify `overflow` property/mutator
    """
    random.shuffle(testvec := (
            list(uut.properties.Rounding) +
            list(uut.properties.Alert) +
            list(uut.properties.Overflow) +
            list(uut.properties.StrBase)
        )
    )
    x = uut.FixedPoint(random.random())
    errmsg = "Invalid overflow setting: %r\\."
    for value in testvec:
        if value in uut.properties.Overflow:
            x.overflow = value.name
            nose.tools.assert_equal(x.overflow, value.name)
            tmp = uut.FixedPoint(random.random(), overflow=value.name)
            nose.tools.assert_equal(tmp.overflow, value.name)
        else:
            with nose.tools.assert_raises_regex(ValueError, errmsg % value.name):
                x.overflow = value.name

@tools.setup(progress_bar=True)
def test_clamped():
    """Verify `clamped` property
    """
    # Figure out bit size for random number generation such that a portion of
    # the random numbers are clamped
    L = max(uut.FixedPoint.min_m(tools.NUM_ITERATIONS) // 2, 1)
    sclamped = [2**(L - 1), 2**(L - 1) - 1]
    uclamped = [0, 2**L - 1]
    for _ in tools.test_iterator():
        bits = random.getrandbits(L)
        s = random.randrange(2)
        m = random.randrange(s, L)
        n = L - m
        x = uut.FixedPoint(hex(bits), s, m, n)
        if bits in (sclamped if s else uclamped):
            nose.tools.assert_true(x.clamped)
            UTLOG.info("CLAMPED", **LOGID)
        else:
            nose.tools.assert_false(x.clamped)

@tools.setup(progress_bar=True)
def test_qformat():
    """Verify `qformat` property
    """
    for _ in tools.test_iterator():
        s = random.randrange(2)
        m = random.randrange(s, 1000)
        n = random.randrange(m == 0, 1000)
        x = uut.FixedPoint(0, s, m, n)
        q = f"{'' if s else 'U'}Q{m}.{n}"
        nose.tools.assert_equal(x.qformat, q)

@tools.setup(progress_bar=True)
def test_bitmask():
    """Verify `bitmask` property
    """
    for _ in tools.test_iterator():
        s = random.randrange(2)
        m = random.randrange(s, 1000)
        n = random.randrange(m == 0, 1000)
        x = uut.FixedPoint(0, s, m, n)
        bitmask = 2**(m + n) - 1
        nose.tools.assert_equal(x.bitmask, bitmask)
        nose.tools.assert_equal(x._bits, x._bits & x.bitmask)
        nose.tools.assert_equal(0, x._bits & ~x.bitmask)

@tools.setup(progress_bar=True)
def test_bits():
    """Verify `bits` property
    """
    for init, args, _, s, m, n, bits in initstr_gen():
        x = uut.FixedPoint(init, *args)
        nose.tools.assert_equal(x.bits, bits)

@tools.setup(progress_bar=True)
def test_len():
    """Verify __len__
    """
    for _ in tools.test_iterator():
        s = random.randrange(2)
        m = random.randrange(s, 1000)
        n = random.randrange(m == 0, 1000)
        x = uut.FixedPoint(0, s, m, n)
        nose.tools.assert_equal(len(x), m + n)

@tools.setup(progress_bar=True)
def test_getitem():
    """Verify __getitem__
    """
    for _ in tools.test_iterator():
        s = random.randrange(2)
        m = random.randrange(s, 10)
        n = random.randrange(m == 0, 10)
        L = m + n
        bits = random.getrandbits(L)
        x = uut.FixedPoint(bin(bits), s, m, n)

        for i in range(L):
            # Bit index out of range
            errmsg = f"Bit {L} does not exist in {'' if s else 'U'}Q{m}\\.{n} format\\."
            with nose.tools.assert_raises_regex(IndexError, errmsg):
                x.bits[L]
            errmsg = f"Bit -{L+1} does not exist in {'' if s else 'U'}Q{m}\\.{n} format\\."
            with nose.tools.assert_raises_regex(IndexError, errmsg):
                x.bits[-L-1]

            # Not an int, str, or slice
            errmsg = "<class 'float'> not supported\\."
            with nose.tools.assert_raises_regex(TypeError, errmsg):
                x.bits[1.2]

            # Access individual bits as a std_logic_vector(L-1 downto 0)
            nose.tools.assert_equal(x.bits[i] << i, bits & 2**i, f'bit {i}')

            # Access a slice as a std_logic_vector
            for hi in range(i, L):
                lo = i
                mask = 2**(hi-lo+1)-1
                shift = lo

                # Descending
                nose.tools.assert_equal(x.bits[hi : lo : -1 if lo == hi else None],
                                        (bits & (mask << shift)) >> i,
                                        f'{hi} downto {lo}')

                # Ascending
                lo, hi = -hi + L-1, -lo + L-1
                nose.tools.assert_equal(x.bits[lo : hi : 1 if lo == hi else None],
                                       (bits & (mask << shift)) >> i,
                                       f'{lo} to {hi}')

                # Equal start/stop but no direction
                if lo == hi:
                    errmsg = r'Step must be 1 or -1 for equivalent start and stop bound %d\.' % hi
                    with nose.tools.assert_raises_regex(IndexError, errmsg):
                        x.bits[lo : hi]

                # Python string
                if i:
                    nose.tools.assert_equal(x.bits[-i], (bits & 2**(i-1)) >> (i-1), f'bit -{i}')
                    nose.tools.assert_equal(x.bits[-i:], bits & (2**i-1), f'bit -{i}:')

            # Bit masks
            nose.tools.assert_equal(x.bits['lsb'], bits % 2)

            if m:
                nose.tools.assert_equal(x.bits['m'], bits >> n, 'm')
                nose.tools.assert_equal(x.bits['int'], bits >> n, 'int')
            else:
                errmsg = f"Invalid bit specification 'm' for UQ0\\.{n} format\\."
                with nose.tools.assert_raises_regex(KeyError, errmsg):
                    x.bits['m']
                errmsg = errmsg.replace("'m'", "'int'")
                with nose.tools.assert_raises_regex(KeyError, errmsg):
                    x.bits['int']

            if n:
                nose.tools.assert_equal(x.bits['n'], bits & (2**n-1), 'n')
                nose.tools.assert_equal(x.bits['frac'], bits & (2**n-1), 'frac')
            else:
                errmsg = f"Invalid bit specification 'n' for {'' if s else 'U'}Q{m}\\.0 format\\."
                with nose.tools.assert_raises_regex(KeyError, errmsg):
                    x.bits['n']
                errmsg = errmsg.replace("'n'", "'frac'")
                with nose.tools.assert_raises_regex(KeyError, errmsg):
                    x.bits['frac']

            if s:
                nose.tools.assert_equal(x.bits['s'], bits >> (L-1), 's')
                nose.tools.assert_equal(x.bits['sign'], bits >> (L-1), 'sign')
                nose.tools.assert_equal(x.bits['msb'], x.bits['s'], 'msb')
            else:
                errmsg = f"Invalid bit specification 's' for UQ{m}\\.{n} format\\."
                with nose.tools.assert_raises_regex(KeyError, errmsg):
                    x.bits['s']
                errmsg = errmsg.replace("'s'", "'sign'")
                with nose.tools.assert_raises_regex(KeyError, errmsg):
                    x.bits['sign']
                nose.tools.assert_equal(x.bits['msb'], bits >> (L-1), 'msb')
