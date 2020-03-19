#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random
import re
import sys
from pathlib import Path
import struct
from typing import Tuple, Dict, Any, Union

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools

###############################################################################
# FLOAT TESTS
###############################################################################
@nose.tools.nottest
def initfloat_gen() -> Tuple[float, Tuple[Any, ...], Dict[str, Any], bool, int, int, int]:
    """Generates floats. Return style is:
    (init, *args, **kwargs, signed, m, n, bits)
    """
    ref = {}
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 52)
        n = random.randint(0, 52 - m)
        init = tools.random_float(s, m, n, ref)
        yield init, (), {}, bool(s), m, n, ref['bits']

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initfloat():
    """Verify FixedPoint(float): deduce Q format
    """
    sys.stderr.write(f'\b\b\b\b\b: deduce Q format ... ')
    for init, args, _, s, m, n, bits in initfloat_gen():
        x = uut.FixedPoint(init, *args)
        UTLOG.info("%sQ%d.%d \n%.52f\n%s",
            '' if (negative := (init < 0)) else 'U', m, n,
            init,
            binbits := bin(bits),
            **LOGID
        )

        tools.verify_attributes(x,
            signed=negative,
            str_base=16,
            rounding='convergent' if negative else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            # Checked below. Trailing/leading 0s are trimmed
            m=NotImplemented,
            n=NotImplemented,
            bits=NotImplemented,
        )
        nose.tools.assert_equal(float(x), init)
        nose.tools.assert_less_equal(x.m, m)
        nose.tools.assert_less_equal(x.n, n)
        nose.tools.assert_in(bin(x)[2:], binbits[2:])

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initfloat_partial_q():
    """Verify FixedPoint(float): incomplete Q format
    """
    sys.stderr.write(f'\b\b\b\b\b: incomplete Q format ... ')
    ref = {}
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 52)
        n = random.randint(0, 52 - m)
        init = tools.random_float(s, m, n, ref)

        # Choose which arguments are provided for Q format
        args = {}
        for arg, val in zip(['signed', 'm', 'n'], [s, m, n]):
            if random.getrandbits(1):
                args[arg] = val

        bits = ref['bits']
        UTLOG.info("%sQ%d.%d \n%.52f\n%s\n%r",
            '' if (negative := args.get('signed', init < 0)) else 'U', m, n,
            init,
            binbits := bin(ref['bits']),
            args,
            **LOGID
        )

        x = uut.FixedPoint(init, **args)
        sn = f"SN: {uut.FixedPoint._SERIAL_NUMBER}"

        tools.verify_attributes(x,
            signed=negative,
            str_base=16,
            rounding='convergent' if negative else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            # Checked below. Trailing/leading 0s are trimmed
            m=NotImplemented,
            n=NotImplemented,
            bits=NotImplemented,
        )
        nose.tools.assert_equal(float(x), init, sn)
        nose.tools.assert_less_equal(x.m, m, sn)
        nose.tools.assert_less_equal(x.n, n, sn)
        nose.tools.assert_in(bin(x)[2:], binbits[2:], sn)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initfloatlike():
    """Verify FixedPoint(float): floatable type
    """
    sys.stderr.write(f'\b\b\b\b\b: floatable type ... ')

    errmsg = r"Unsupported type [^;]+; cannot convert to float\."
    class NonFloatLike:
        def __init__(self, val):
            self.val = float(val)
        def __repr__(self):
            return f"{self.__class__.__name__}({self.val!r})"
    class FloatLike(NonFloatLike):
        def __float__(self):
            return self.val

    ref = {}
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 52)
        n = random.randint(0, 52 - m)
        init = tools.random_float(s, m, n, ref)

        # Choose which arguments are provided for Q format
        kwargs = {}
        for arg, val in zip(['signed', 'm', 'n'], [s, m, n]):
            if random.getrandbits(1):
                kwargs[arg] = val

        bits = ref['bits']
        UTLOG.info("%sQ%d.%d \n%.52f\n%s\n%r",
            '' if (negative := kwargs.get('signed', init < 0)) else 'U', m, n,
            init,
            binbits := bin(ref['bits']),
            kwargs,
            **LOGID
        )

        x = uut.FixedPoint(FloatLike(init), **kwargs)
        sn = f"SN: {uut.FixedPoint._SERIAL_NUMBER}"

        tools.verify_attributes(x,
            signed=negative,
            str_base=16,
            rounding='convergent' if negative else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            # Checked below. Trailing/leading 0s are trimmed
            m=NotImplemented,
            n=NotImplemented,
            bits=NotImplemented,
        )
        nose.tools.assert_equal(float(x), init, sn)
        nose.tools.assert_less_equal(x.m, m, sn)
        nose.tools.assert_less_equal(x.n, n, sn)
        nose.tools.assert_in(bin(x)[2:], binbits[2:], sn)

        # For weird data types that can't be converted to float
        with nose.tools.assert_raises_regex(TypeError, errmsg):
            uut.FixedPoint(NonFloatLike(init), **kwargs)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initfloat_clamp():
    """Verify FixedPoint(float) with clamp
    """
    sys.stderr.write(f'\b\b\b\b\b with clamp ... ')
    for _ in tools.test_iterator():
        L = random.randint(2, 52)
        s = random.randrange(2)
        m = random.randint(s, L)
        n = L - m
        bmax = 2**(m + n - s) - 1
        bmin = -(bmax + 1) * s
        lsb = 2**-n
        minimum = float(bmin * lsb)
        maximum = float(bmax * lsb)
        UTLOG.debug("%sQ%d.%d\n%.53f\n%.53f", '' if s else 'U', m, n,
            minimum, maximum, **LOGID)

        props = {'overflow': 'clamp'}

        # Minimum and maximum value should not produce a warning or exception
        with tools.CaptureWarnings() as warnings:
            tools.verify_attributes(uut.FixedPoint(maximum, s, m, n, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='clamp',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=n,
                bits=bmax,
            )
            tools.verify_attributes(uut.FixedPoint(minimum, s, m, n, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='clamp',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=n,
                bits=abs(bmin),
            )
        nose.tools.assert_equal(len(warnings), 0)

        # Default behavior is for overflows to raise an exception
        errmsg = r"\[SN\d+\] [\d.e+-]+ overflows in U?Q\d+\.\d+ format\."
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(maximum + lsb, s, m, n, **props)

        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(minimum - lsb, s, m, n, **props)

        # Allow overflow with warning and verify clamping
        props['overflow_alert'] = 'warning'
        wmsg = r"WARNING \[SN\d+\]: [\d.e+-]+ overflows in U?Q\d+\.\d+ format\."
        maxmsg = r"WARNING \[SN\d+\]: Clamped to maximum\."
        minmsg = r"WARNING \[SN\d+\]: Clamped to minimum\."
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), maximum)
            nose.tools.assert_true(x.clamped)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(maxmsg, second))

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), minimum)
            nose.tools.assert_true(x.clamped)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(minmsg, second))

        # Disable overflow alerts and verify clamping
        props['overflow_alert'] = 'ignore'
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), maximum)
            nose.tools.assert_true(x.clamped)
        nose.tools.assert_equal(len(warnings), 0)

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), minimum)
            nose.tools.assert_true(x.clamped)
        nose.tools.assert_equal(len(warnings), 0)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initfloat_wrap():
    """Verify FixedPoint(float) with wrap
    """
    sys.stderr.write(f'\b\b\b\b\b with wrap ... ')
    for _ in tools.test_iterator():
        L = random.randint(2, 52)
        s = random.randrange(2)
        m = random.randint(s, L)
        n = L - m
        bmax = 2**(m + n - s) - 1
        bmin = -(bmax + 1) * s
        lsb = 2**-n
        minimum = float(bmin * lsb)
        maximum = float(bmax * lsb)
        UTLOG.debug("%sQ%d.%d\n%.53f\n%.53f", '' if s else 'U', m, n,
            minimum, maximum, **LOGID)

        props = {'overflow': 'wrap'}

        # Minimum and maximum value should not produce a warning or exception
        with tools.CaptureWarnings() as warnings:
            tools.verify_attributes(uut.FixedPoint(maximum, s, m, n, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='wrap',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=n,
                bits=bmax,
            )
            tools.verify_attributes(uut.FixedPoint(minimum, s, m, n, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='wrap',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=n,
                bits=abs(bmin),
            )
        nose.tools.assert_equal(len(warnings), 0)

        # Default behavior is for overflows to raise an exception
        errmsg = r"\[SN\d+\] [\d.e+-]+ overflows in U?Q\d+\.\d+ format\."
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(maximum + lsb, s, m, n, **props)

        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(minimum - lsb, s, m, n, **props)

        # Allow overflow with warning and verify wrapping
        props['overflow_alert'] = 'warning'
        wmsg = r"WARNING \[SN\d+\]: [\d.e+-]+ overflows in U?Q\d+\.\d+ format\."
        maxmsg = r"WARNING \[SN\d+\]: Wrapped maximum\."
        minmsg = r"WARNING \[SN\d+\]: Wrapped minimum\."
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), minimum)
            nose.tools.assert_true(x.clamped)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(maxmsg, second))

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), maximum)
            nose.tools.assert_true(x.clamped)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(minmsg, second))

        # Disable overflow alerts and verify wrapping
        props['overflow_alert'] = 'ignore'
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), minimum)
            nose.tools.assert_true(x.clamped)
        nose.tools.assert_equal(len(warnings), 0)

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - lsb, s, m, n, **props)
            nose.tools.assert_equal(float(x), maximum)
            nose.tools.assert_true(x.clamped)
        nose.tools.assert_equal(len(warnings), 0)

@nose.tools.nottest
@tools.setup(progress_bar=True, require_matlab=True)
def test_initfloat_convergent():
    """Verify FixedPoint(float) with convergent round
    """
    sys.stderr.write(f'\b\b\b\b\b with convergent round ... ')
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        'd' # double - initialization value
        'B' # unsigned char - signed
        'B' # unsigned char - m
        'B' # unsigned char - n
        '5x' # Byte alignment padding
        '16s' # 16-character string - expected hex value
        'd' # double - float expected
    )
    props = {'rounding': 'convergent', 'str_base': 16}
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, hexexp, floatexp = data
        UTLOG.debug("INIT: %.53f\n%sQ%d.%d",
            init, '' if s else 'U', m, n, **LOGID)
        tools.verify_attributes(x := uut.FixedPoint(init, s, m, n, **props),
            signed=s,
            str_base=16,
            rounding='convergent',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            n=n,
            bits=int(hexexp, 16),
        )
        nose.tools.assert_equal(float(x), floatexp)

@nose.tools.nottest
@tools.setup(progress_bar=True, require_matlab=True)
def test_initfloat_nearest():
    """Verify FixedPoint(float) with round to nearest
    """
    sys.stderr.write(f'\b\b\b\b\b with round to nearest ... ')
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        'd' # double - initialization value
        'B' # unsigned char - signed
        'B' # unsigned char - m
        'B' # unsigned char - n
        '5x' # Byte alignment padding
        '16s' # 16-character string - expected hex value
        'd' # double - float expected
    )
    props = {'rounding': 'nearest', 'str_base': 16}
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, hexexp, floatexp = data
        UTLOG.debug("INIT: %.53f\n%sQ%d.%d",
            init, '' if s else 'U', m, n, **LOGID)
        tools.verify_attributes(x := uut.FixedPoint(init, s, m, n, **props),
            signed=s,
            str_base=16,
            rounding='nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            n=n,
            bits=int(hexexp, 16),
        )
        nose.tools.assert_equal(float(x), floatexp)

@nose.tools.nottest
@tools.setup(progress_bar=True, require_matlab=True)
def test_initfloat_down():
    """Verify FixedPoint(float) with round down
    """
    sys.stderr.write(f'\b\b\b\b\b with round down ... ')
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        'd' # double - initialization value
        'B' # unsigned char - signed
        'B' # unsigned char - m
        'B' # unsigned char - n
        '5x' # Byte alignment padding
        '16s' # 16-character string - expected hex value
        'd' # double - float expected
    )
    props = {'rounding': 'down', 'str_base': 16}
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, hexexp, floatexp = data
        UTLOG.debug("INIT: %.53f\n%sQ%d.%d",
            init, '' if s else 'U', m, n, **LOGID)
        tools.verify_attributes(x := uut.FixedPoint(init, s, m, n, **props),
            signed=s,
            str_base=16,
            rounding='down',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            n=n,
            bits=int(hexexp, 16),
        )
        nose.tools.assert_equal(float(x), floatexp)

@nose.tools.nottest
@tools.setup(progress_bar=True, require_matlab=True)
def test_initfloat_out():
    """Verify FixedPoint(float) with round out
    """
    sys.stderr.write(f'\b\b\b\b\b with round out ... ')
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        'd' # double - initialization value
        'B' # unsigned char - signed
        'B' # unsigned char - m
        'B' # unsigned char - n
        '5x' # Byte alignment padding
        '16s' # 16-character string - expected hex value
        'd' # double - float expected
    )
    props = {'rounding': 'out', 'str_base': 16}
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, hexexp, floatexp = data
        UTLOG.debug("INIT: %.53f\n%sQ%d.%d",
            init, '' if s else 'U', m, n, **LOGID)
        tools.verify_attributes(x := uut.FixedPoint(init, s, m, n, **props),
            signed=s,
            str_base=16,
            rounding='out',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            n=n,
            bits=int(hexexp, 16),
        )
        nose.tools.assert_equal(float(x), floatexp)

@nose.tools.nottest
@tools.setup(progress_bar=True, require_matlab=True)
def test_initfloat_in():
    """Verify FixedPoint(float) with round in
    """
    sys.stderr.write(f'\b\b\b\b\b with round in ... ')
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        'd' # double - initialization value
        'B' # unsigned char - signed
        'B' # unsigned char - m
        'B' # unsigned char - n
        '5x' # Byte alignment padding
        '16s' # 16-character string - expected hex value
        'd' # double - float expected
    )
    props = {'rounding': 'in', 'str_base': 16}
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, hexexp, floatexp = data
        UTLOG.debug("INIT: %.53f\n%sQ%d.%d",
            init, '' if s else 'U', m, n, **LOGID)
        tools.verify_attributes(x := uut.FixedPoint(init, s, m, n, **props),
            signed=s,
            str_base=16,
            rounding='in',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            n=n,
            bits=int(hexexp, 16),
        )
        nose.tools.assert_equal(float(x), floatexp)

@nose.tools.nottest
@tools.setup(progress_bar=True, require_matlab=True)
def test_initfloat_up():
    """Verify FixedPoint(float) with round up
    """
    sys.stderr.write(f'\b\b\b\b\b with round up ... ')
    seed = random.getrandbits(31)
    UTLOG.debug("MATLAB RANDOM SEED: %d", seed, **LOGID)
    tools.MATLAB.generate_stimulus(seed, tools.NUM_ITERATIONS)
    unpacker = struct.Struct(
        'd' # double - initialization value
        'B' # unsigned char - signed
        'B' # unsigned char - m
        'B' # unsigned char - n
        '5x' # Byte alignment padding
        '16s' # 16-character string - expected hex value
        'd' # double - float expected
    )
    props = {'rounding': 'up', 'str_base': 16}
    for data in tools.test_iterator(tools.MATLAB.yield_stimulus(unpacker, 3)):
        init, s, m, n, hexexp, floatexp = data
        UTLOG.debug("INIT: %.53f\n%sQ%d.%d",
            init, '' if s else 'U', m, n, **LOGID)
        tools.verify_attributes(x := uut.FixedPoint(init, s, m, n, **props),
            signed=s,
            str_base=16,
            rounding='up',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            n=n,
            bits=int(hexexp, 16),
        )
        nose.tools.assert_equal(float(x), floatexp)

@tools.setup(progress_bar=True)
def test_from_float():
    """Verify from_float
    """
    ref = {}
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 52)
        n = random.randint(0, 52 - m)
        init = tools.random_float(s, m, n, ref)

        x = uut.FixedPoint(0, s, m, n)
        x.from_float(init)

        bits = ref['bits']
        UTLOG.info("%sQ%d.%d \n%.52f\n%s",
            '' if s else 'U', m, n,
            init,
            bin(ref['bits']),
            **LOGID
        )

        tools.verify_attributes(x,
            signed=s,
            m=m,
            n=n,
            bits=bits,
            str_base=16,
            rounding='convergent' if s else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
        )
        nose.tools.assert_equal(float(x), init)

    # Verify that passing in something other than a float throws an error
    errmsg = re.escape(f'Expected {type(1.0)}; got {type(13)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.from_float(13)

@tools.setup(progress_bar=True)
def test_float():
    """Verify FixedPoint(float)
    """
    for test in [
    test_initfloat,
    test_initfloat_partial_q,
    test_initfloatlike,
    test_initfloat_clamp,
    test_initfloat_wrap,
    test_initfloat_convergent,
    test_initfloat_nearest,
    test_initfloat_down,
    test_initfloat_out,
    test_initfloat_in,
    test_initfloat_up,
    ]:
        yield test

###############################################################################
# INT TESTS
###############################################################################
@nose.tools.nottest
def initint_gen() -> Tuple[int, Tuple[Any, ...], Dict[str, Any], bool, int, int, int]:
    """Generates ints. Return style is:
    (init, *args, **kwargs, signed, m, n, bits)
    """
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 1000)
        init = tools.random_int(s, m)
        yield init, (), {}, bool(s), m, 0, init & (2**m-1)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initint():
    """Verify FixedPoint(int): deduce Q format
    """
    sys.stderr.write(f'\b\b\b\b\b: deduce Q format ... ')
    # Trim of trailing 0s  and leading 1s (except for 1) for negative numbers
    for init, args, _, s, m, _, _ in initint_gen():
        x = uut.FixedPoint(init)

        tools.verify_attributes(x,
            signed=(s := bool(s and init)),
            n=0,
            str_base=16,
            rounding='convergent' if s else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            # Checked below. Trailing/leading 0s are trimmed
            m=NotImplemented,
            bits=NotImplemented,
        )
        nose.tools.assert_less_equal(x.m, m)
        nose.tools.assert_in(bin(x)[2:], bin(init & (2**m-1))[2:])

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initint_partial_q():
    """Verify FixedPoint(int): incomplete Q format
    """
    sys.stderr.write(f'\b\b\b\b\b: incomplete Q format ... ')
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 1000)
        n = random.randint(0, 1000)
        init = tools.random_int(s, m)

        bits = (init << n) & (2**(m+n)-1)
        # Choose which arguments are provided for Q format
        args = {}
        for arg, val in zip(['signed', 'm', 'n'], [s, m, n]):
            if random.getrandbits(1):
                args[arg] = val

        x = uut.FixedPoint(init, **args)
        sn = f"SN: {uut.FixedPoint._SERIAL_NUMBER}"

        tools.verify_attributes(x,
            signed=(negative := args.get('signed', init < 0)),
            str_base=16,
            rounding='convergent' if negative else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            # Checked below. Trailing/leading 0s may be trimmed
            m=NotImplemented,
            n=args.get('n', 0),
            bits=NotImplemented,
        )
        nose.tools.assert_less_equal(x.m, m, sn)
        nose.tools.assert_in(bin(x)[2:], bin(bits)[2:], sn)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initint_clamp():
    """Verify FixedPoint(int) with clamp
    """
    sys.stderr.write(f'\b\b\b\b\b with clamp ... ')
    for _ in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 1000)
        n = random.randint(0, 1000)
        maximum = 2**(m - s) - 1
        minimum = -2**(m - 1) * s

        props = {'overflow': 'clamp'}

        # Minimum and maximum value should not produce a warning or exception
        with tools.CaptureWarnings() as warnings:
            tools.verify_attributes(
                uut.FixedPoint(maximum, s, m, 0, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='clamp',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=0,
                bits=maximum,
            )
            tools.verify_attributes(
                uut.FixedPoint(minimum, s, m, n, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='clamp',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=n,
                bits=s << (m + n - 1),
            )
        nose.tools.assert_equal(len(warnings), 0)

        # Default behavior is for overflows to raise an exception
        errmsg = r"\[SN\d+\] Integer -?\d+ overflows in U?Q\d+\.\d+ format\."
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(maximum + 1, s, m, 0, **props)

        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(minimum - 1, s, m, n, **props)

        # Allow overflow with warning and verify clamping
        props['overflow_alert'] = 'warning'
        wmsg = r"WARNING \[SN\d+\]: Integer -?\d+ overflows in U?Q\d+\.\d+ format\."
        maxmsg = r"WARNING \[SN\d+\]: Clamped to maximum\."
        minmsg = r"WARNING \[SN\d+\]: Clamped to minimum\."
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + 1, s, m, 0, **props)
            nose.tools.assert_equal(int(x), maximum)
            nose.tools.assert_true(x.clamped)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(maxmsg, second))

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - 1, s, m, n, **props)
            nose.tools.assert_equal(int(x), minimum)
            nose.tools.assert_true(x.clamped)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(minmsg, second))

        # Disable overflow alerts and verify clamping
        props['overflow_alert'] = 'ignore'
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + 1, s, m, 0, **props)
            nose.tools.assert_equal(int(x), maximum)
            nose.tools.assert_true(x.clamped)
        nose.tools.assert_equal(len(warnings), 0)

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - 1, s, m, n, **props)
            nose.tools.assert_equal(int(x), minimum)
            nose.tools.assert_true(x.clamped)
        nose.tools.assert_equal(len(warnings), 0)

@nose.tools.nottest
@tools.setup(progress_bar=True)
def test_initint_wrap():
    """Verify FixedPoint(int) with wrap
    """
    sys.stderr.write(f'\b\b\b\b\b with wrap ... ')
    for _ in tools.test_iterator():
        s = random.randrange(2);
        m = random.randint(1, 1000)
        n = random.randint(0, 1000)
        maximum = max(0, 2**(m - s) - 1) # Will be 0 for Q1.n
        minimum = -2**(m - 1) * s

        props = {'overflow': 'wrap'}

        # Minimum and maximum value should not produce a warning or exception
        with tools.CaptureWarnings() as warnings:
            tools.verify_attributes(
                uut.FixedPoint(maximum, s, m, 0, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='wrap',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=0,
                bits=maximum,
            )
            tools.verify_attributes(
                uut.FixedPoint(minimum, s, m, n, **props),
                signed=s,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='wrap',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
                m=m,
                n=n,
                bits=s << (m + n - 1),
            )
        nose.tools.assert_equal(len(warnings), 0)

        # Default behavior is for overflows to raise an exception
        errmsg = r"\[SN\d+\] Integer -?\d+ overflows in U?Q\d+\.\d+ format\."
        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(maximum + 1, s, m, 0, **props)

        with nose.tools.assert_raises_regex(uut.FixedPointOverflowError, errmsg):
            uut.FixedPoint(minimum - 1, s, m, n, **props)

        # Allow overflow with warning and verify clamping
        props['overflow_alert'] = 'warning'
        wmsg = r"WARNING \[SN\d+\]: Integer -?\d+ overflows in U?Q\d+\.\d+ format\."
        maxmsg = r"WARNING \[SN\d+\]: Wrapped maximum\."
        minmsg = r"WARNING \[SN\d+\]: Wrapped minimum\."
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + 1, s, m, 0, **props)
            nose.tools.assert_equal(int(x), minimum)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(maxmsg, second))

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - 1, s, m, n, **props)
            nose.tools.assert_equal(int(x), maximum)
            first, second = warnings.logs
            nose.tools.assert_true(re.search(wmsg, first))
            nose.tools.assert_true(re.search(minmsg, second))

        # Disable overflow alerts and verify clamping
        props['overflow_alert'] = 'ignore'
        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(maximum + 1, s, m, 0, **props)
            nose.tools.assert_equal(int(x), minimum)
        nose.tools.assert_equal(len(warnings), 0)

        with tools.CaptureWarnings() as warnings:
            x = uut.FixedPoint(minimum - 1, s, m, n, **props)
            nose.tools.assert_equal(int(x), maximum)
        nose.tools.assert_equal(len(warnings), 0)

@tools.setup(progress_bar=True)
def test_int():
    """Verify FixedPoint(int)
    """
    for test in [
    test_initint,
    test_initint_partial_q,
    test_initint_clamp,
    test_initint_wrap,
    ]:
        yield test

@tools.setup(progress_bar=True)
def test_from_int():
    """Verify from_int
    """
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(1, 1000)
        n = random.randint(0, 1000)
        init = tools.random_int(s, m)

        x = uut.FixedPoint(0, s, m, n)
        x.from_int(init)

        tools.verify_attributes(x,
            signed=s,
            n=n,
            str_base=16,
            rounding='convergent' if s else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
            m=m,
            bits=(init << n) & (2**(m+n)-1),
        )

    # Verify that passing in something other than an int throws an error
    errmsg = re.escape(f'Expected {type(1)}; got {type(13.0)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.from_int(13.0)

###############################################################################
# STRING TESTS
###############################################################################
@nose.tools.nottest
def initstr_gen(one_per_yield=False) -> Tuple[int, Tuple[Any, ...], Dict[str, Any], bool, int, int, int]:
    """Generates strings. Return style is:
    (init, *args, **kwargs, signed, m, n, bits)
    """
    base_conversion = list(uut.properties.StrConv.values())
    for nbit in tools.test_iterator():
        random.shuffle(base_conversion)
        s = random.randrange(2)
        m = random.randint(s, 1000)
        n = random.randint(m == 0, 1000 - m)
        init = random.getrandbits(L := m + n) | (s << (L-1))
        for conv in base_conversion:
            yield conv(init), (bool(s), m, n), {}, bool(s), m, n, init
            if one_per_yield:
                break

@tools.setup(progress_bar=True)
def test_initstr():
    """Verify FixedPoint(str)
    """
    base_conversion = list(uut.properties.StrConv.values())
    errmsg = r"^Superfluous bits detected in string literal '0?[box]?[0-9a-f]+' for U?Q\d+\.\d+ format\.$"
    for init, args, _, s, m, n, bits in initstr_gen():
        x = uut.FixedPoint(init, *args)
        tools.verify_attributes(x,
            signed=s,
            m=m,
            n=n,
            bits=bits,
            str_base=16,
            rounding='convergent' if s else 'nearest',
            overflow='clamp',
            overflow_alert='error',
            mismatch_alert='warning',
            implicit_cast_alert='warning',
        )

        init = random.choice(base_conversion)(bits | 2**(m+n+2))
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            uut.FixedPoint(init, s, m, n)

@tools.setup(progress_bar=True)
def test_from_str():
    """Verify from_str
    """
    base_conversion = list(uut.properties.StrConv.values())
    errmsg = r"^Superfluous bits detected in string literal '0?[box]?[0-9a-f]+' for U?Q\d+\.\d+ format\.$"
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(s, 1000)
        n = random.randint(m == 0, 1000 - m)
        L = m + n
        init = random.getrandbits(L) | (s << (L-1))

        for conv in base_conversion:
            x = uut.FixedPoint(0, s, m, n)
            x.from_string(conv(init))
            tools.verify_attributes(x,
                signed=s,
                m=m,
                n=n,
                bits=init,
                str_base=16,
                rounding='convergent' if s else 'nearest',
                overflow='clamp',
                overflow_alert='error',
                mismatch_alert='warning',
                implicit_cast_alert='warning',
            )

        init = random.choice(base_conversion)(init + 2**(m+n+2))
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            x.from_string(init)

    # Verify that passing in something other than a string throws an error
    errmsg = re.escape(f'Expected {type("")}; got {type(13)}.')
    with nose.tools.assert_raises_regex(TypeError, errmsg):
        x.from_string(13)

###############################################################################
# FIXEDPOINT TESTS
###############################################################################
@tools.setup(progress_bar=True)
def test_initFixedPoint():
    """Verify constructor FixedPoint(FixedPoint)
    """
    iterators = [
        initfloat_gen,
        initint_gen,
        initstr_gen,
        nondefault_props_gen,
    ]
    for iterator in iterators:
        for init, args, kwargs, _, _, _, _ in iterator():
            x = uut.FixedPoint(init, *args, **kwargs)
            tools.verify_attributes(uut.FixedPoint(x),
                signed=x.signed,
                m=x.m,
                n=x.n,
                bits=x._bits,
                str_base=x.str_base,
                rounding=x.rounding,
                overflow=x.overflow,
                overflow_alert=x.overflow_alert,
                mismatch_alert=x.mismatch_alert,
                implicit_cast_alert=x.implicit_cast_alert,
            )

###############################################################################
# MISCELLANEOUS TESTS
###############################################################################
@nose.tools.nottest
def nondefault_props_gen() -> Tuple[Union[float, int, str], Tuple[Any, ...], Dict[str, Any], bool, int, int, int]:
    """Generates ints, floats, and strings with non-deafult properties.
    Return style is: (init, *args, **kwargs, signed, m, n, bits)
    """
    ref = {}
    choices = {
        'overflow': [x.name for x in uut.properties.Overflow],
        'rounding': [x.name for x in uut.properties.Rounding],
        'str_base': list(uut.properties.StrConv.keys()),
        'overflow_alert': [x.name for x in uut.properties.Alert],
        'implicit_cast_alert': [x.name for x in uut.properties.Alert],
        'mismatch_alert': [x.name for x in uut.properties.Alert],
    }
    iterator = zip(initfloat_gen(), initint_gen(), initstr_gen(one_per_yield=1))
    for f, i, s in tools.test_iterator(iterator):
        x = random.choice([f, i, s])

        # Generate random properties
        kwargs = {}
        for key in list(uut.properties.PROPERTIES):
            if random.getrandbits(1):
                kwargs[key] = (value := random.choice(choices[key]))

        yield x[:2] + (kwargs,) + x[3:]

@tools.setup(progress_bar=True)
def test_nondefault_properties():
    """Verify non-default property specs
    """
    expected = {}
    for init, args, kwargs, s, m, n, bits in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)

        # expected values
        expected['overflow'] = kwargs.get('overflow', 'clamp')
        expected['rounding'] = kwargs.get('rounding', 'convergent' if (s if isinstance(init, str) else (init < 0)) else 'nearest')
        expected['str_base'] = kwargs.get('str_base', 16)
        expected['overflow_alert'] = kwargs.get('overflow_alert', 'error')
        expected['mismatch_alert'] = kwargs.get('mismatch_alert', 'warning')
        expected['implicit_cast_alert'] = kwargs.get('implicit_cast_alert', 'warning')

        if isinstance(init, int):
            expected['signed'] = bool(s and init)
            expected['m'] = NotImplemented
            expected['n'] = 0
            expected['bits'] = NotImplemented
            tools.verify_attributes(x, **expected)
            nose.tools.assert_less_equal(x.m, m)
            nose.tools.assert_in(bin(x)[2:], bin(init & (2**m-1))[2:])
        elif isinstance(init, float):
            expected['signed'] = init < 0
            expected['m'] = NotImplemented
            expected['n'] = NotImplemented
            expected['bits'] = NotImplemented
            tools.verify_attributes(x, **expected)
            nose.tools.assert_equal(float(x), init)
            nose.tools.assert_less_equal(x.m, m)
            nose.tools.assert_less_equal(x.n, n)
            nose.tools.assert_in(bin(x)[2:], bin(bits)[2:])
        else: # string
            expected['signed'] = s
            expected['m'] = m
            expected['n'] = n
            expected['bits'] = bits
            tools.verify_attributes(x, **expected)

@tools.setup(progress_bar=True)
def test_init_invalid_q():
    """Verify constructor invalid q
    """
    # String not fully specified
    base_conversion = list(uut.properties.StrConv.values())
    errmsg = r"^When initializing with a string literal, Q format must be fully constrained\.$"
    for nbit in tools.test_iterator():
        s = random.randrange(2)
        m = random.randint(s, 1000)
        n = random.randint(m == 0, 1000 - m)
        L = m + n
        init = random.getrandbits(L) | (s << (L-1))

        invalid_arguments = [
            {},
            {'n': n},
            {'m': m},
            {'m': m, 'n': n},
            {'signed': s},
            {'signed': s, 'n': n},
            {'signed': s, 'm': m},
        ]

        conv = random.choice(base_conversion)
        for args in invalid_arguments:
            with nose.tools.assert_raises_regex(ValueError, errmsg):
                uut.FixedPoint(conv(init), **args)

    # Negative n
    errmsg = r"^Number of fractional bits must be non-negative\.$"
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.FixedPoint(init, n=-1)

    # Negative m
    errmsg = r"^Number of integer bits must be non-negative\.$"
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.FixedPoint(init, m=-max(m, 1))

    # m=0 for signed
    errmsg = r"^Number of integer bits must be at least 1 for signed numbers\.$"
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.FixedPoint(init, signed=1, m=0, n=max(n, 1))

    # Zero word length
    errmsg = r"^Word size \(integer and fractional\) must be positive\.$"
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.FixedPoint(init, m=0, n=0)
