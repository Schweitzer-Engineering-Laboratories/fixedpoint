#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random
import math
import re
import sys

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools
from ..test_initialization_methods import nondefault_props_gen

@tools.setup(progress_bar=True)
def test_resize():
    """Verify functions.resize
    """
    overflows = [x.name for x in uut.properties.Overflow] + ['']
    roundings = [x.name for x in uut.properties.Rounding] + ['']
    alerts = [x.name for x in uut.properties.Alert] + ['']
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        mm = random.randrange(max(1, 2 * x.m))
        nn = random.randrange(max(1, 2 * x.n))

        o = random.choice(overflows)
        r = random.choice(roundings)
        a = random.choice(alerts)
        UTLOG.debug("%s\nresize(%d, %d, %s, %s, %s)",
            x.qformat, mm, nn, o, r, a, **LOGID)

        # Attempt resizing. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.resize(x, mm, nn, r, o, a)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.resize(mm, nn, r, o, a)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.resize(mm, nn, r, o, a)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

@tools.setup(progress_bar=True)
def test_trim():
    """Verify functions.trim
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')
    kwargs = {}

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if random.randrange(2):
            kwargs['ints'] = bool(random.randrange(2))
        else:
            kwargs.pop('ints', None)
        if random.randrange(2):
            kwargs['fracs'] = bool(random.randrange(2))
        else:
            kwargs.pop('fracs', None)

        # Attempt trimming. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.trim(x, **kwargs)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.trim(**kwargs)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.trim(**kwargs)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: trim unsinged number with no integer bits
    x = uut.FixedPoint(random.random())
    nose.tools.assert_equal(x.m, 0)
    x.trim()
    nose.tools.assert_equal(x.m, 0)

@tools.setup(progress_bar=True)
def test_convergent():
    """Verify functions.convergent
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.n == 0:
            continue
        nn = random.randrange(x.n)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.convergent(x, nn)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.convergent(nn)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.convergent(nn)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: round with overflow
    x = uut.FixedPoint('0b111', 0, 1, 2, overflow_alert='ignore')
    for overflow in ['clamp', 'wrap']:
        with x(overflow=overflow):
            y = uut.functions.convergent(x, 1)
            x.convergent(1)
            tools.verify_attributes(y,
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

        with x(overflow_alert='ignore', overflow='wrap'):
            y = uut.functions.convergent(x, 1)
            x.convergent(1)
            tools.verify_attributes(y,
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

        # Corner case: cause ValueErrors
        errmsg = r'Word size \(integer and fractional\) must be positive\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=10, signed=0, m=0):
                uut.functions.convergent(x, 0)
        errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=10, signed=0, m=0):
                uut.functions.convergent(x, 11)
        with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
            with x(m=1, signed=1, n=10):
                x.convergent(12)

@tools.setup(progress_bar=True)
def test_nearest():
    """Verify functions.round_nearest
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.n == 0:
            continue
        nn = random.randrange(x.n)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.round_nearest(x, nn)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.round_nearest(nn)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.round_nearest(nn)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: round with overflow
    x = uut.FixedPoint('0b111', 0, 1, 2, overflow_alert='ignore')
    for overflow in ['clamp', 'wrap']:
        with x(overflow=overflow):
            y = uut.functions.round_nearest(x, 1)
            x.round_nearest(1)
            tools.verify_attributes(y,
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

        with x(overflow_alert='ignore', overflow='wrap'):
            y = uut.functions.round_nearest(x, 1)
            x.round_nearest(1)
            tools.verify_attributes(y,
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

        # Corner case: cause ValueErrors
        errmsg = r'Word size \(integer and fractional\) must be positive\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=10, signed=0, m=0):
                uut.functions.round_nearest(x, 0)
        errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=10, signed=0, m=0):
                uut.functions.round_nearest(x, 11)
        with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
            with x(m=1, signed=1, n=10):
                x.round_nearest(12)

@tools.setup(progress_bar=True)
def test_in():
    """Verify functions.round_in
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.n == 0:
            continue
        nn = random.randrange(x.n)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.round_in(x, nn)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.round_in(nn)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.round_in(nn)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: cause ValueErrors
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    x.overflow_alert = 'ignore'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(n=10, signed=0, m=0):
            uut.functions.round_in(x, 0)
    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(n=10, signed=0, m=0):
            uut.functions.round_in(x, 11)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(m=1, signed=1, n=10):
            x.round_in(12)

@tools.setup(progress_bar=True)
def test_out():
    """Verify functions.round_out
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.n == 0:
            continue
        nn = random.randrange(x.n)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.round_out(x, nn)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.round_out(nn)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.round_out(nn)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: round with overflow
    x = uut.FixedPoint('0b111', 0, 1, 2, overflow_alert='ignore')
    for overflow in ['clamp', 'wrap']:
        with x(overflow=overflow):
            y = uut.functions.round_out(x, 1)
            x.round_out(1)
            tools.verify_attributes(y,
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

        with x(overflow_alert='ignore', overflow='wrap'):
            y = uut.functions.round_out(x, 1)
            x.round_out(1)
            tools.verify_attributes(y,
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

    # Corner case: cause ValueErrors
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    x.overflow_alert = 'ignore'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(n=10, signed=0, m=0):
            uut.functions.round_out(x, 0)
    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(n=10, signed=0, m=0):
            uut.functions.round_out(x, 11)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(m=1, signed=1, n=10):
            x.round_out(12)

@tools.setup(progress_bar=True)
def test_up():
    """Verify functions.round_up
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.n == 0:
            continue
        nn = random.randrange(x.n)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.round_up(x, nn)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.round_up(nn)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.round_up(nn)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: round with overflow
    x = uut.FixedPoint('0b111', 0, 1, 2, overflow_alert='ignore')
    for overflow in ['clamp', 'wrap']:
        with x(overflow=overflow):
            y = uut.functions.round_up(x, 1)
            x.round_up(1)
            tools.verify_attributes(y,
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

        with x(overflow_alert='ignore', overflow='wrap'):
            y = uut.functions.round_up(x, 1)
            x.round_up(1)
            tools.verify_attributes(y,
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

        # Corner case: cause ValueErrors
        errmsg = r'Word size \(integer and fractional\) must be positive\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=10, signed=0, m=0):
                uut.functions.round_up(x, 0)
        errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
        with nose.tools.assert_raises_regex(ValueError, errmsg):
            with x(n=10, signed=0, m=0):
                uut.functions.round_up(x, 11)
        with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
            with x(m=1, signed=1, n=10):
                x.round_up(12)

@tools.setup(progress_bar=True)
def test_down():
    """Verify functions.round_down
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.n == 0:
            continue
        nn = random.randrange(x.n)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.round_down(x, nn)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.round_down(nn)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.round_down(nn)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: cause ValueErrors
    errmsg = r'Word size \(integer and fractional\) must be positive\.'
    x.overflow_alert = 'ignore'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(n=10, signed=0, m=0):
            uut.functions.round_down(x, 0)
    errmsg = r'Number of fractional bits remaining after round must be in the range \[1, 10\)\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        with x(n=10, signed=0, m=0):
            uut.functions.round_down(x, 11)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(m=1, signed=1, n=10):
            x.round_down(12)

@tools.setup(progress_bar=True)
def test_keep_msbs():
    """Verify functions.keep_msbs
    """
    overflows = [x.name for x in uut.properties.Overflow] + ['']
    roundings = [x.name for x in uut.properties.Rounding] + ['']
    alerts = [x.name for x in uut.properties.Alert] + ['']
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        mm = random.randrange(max(1, 2 * x.m))
        nn = random.randrange(max(1, 2 * x.n))

        o = random.choice(overflows)
        r = random.choice(roundings)
        a = random.choice(alerts)

        # Attempt resizing. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.keep_msbs(x, mm, nn, o, r, a)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.keep_msbs(mm, nn, o, r, a)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.keep_msbs(mm, nn, o, r, a)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: cause ValueErrors
    errmsg = r'Bit format specifications must be non-negative\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.keep_msbs(x, 0, -1)
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.keep_msbs(x, -2, -3)

@tools.setup(progress_bar=True)
def test_keep_lsbs():
    """Verify functions.keep_lsbs
    """
    overflows = [x.name for x in uut.properties.Overflow] + ['']
    alerts = [x.name for x in uut.properties.Alert] + ['']
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        mm = random.randrange(max(1, 2 * x.m))
        nn = random.randrange(max(1, 2 * x.n))

        o = random.choice(overflows)
        a = random.choice(alerts)

        # Attempt resizing. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.keep_lsbs(x, mm, nn, o, a)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.keep_lsbs(mm, nn, o, a)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.keep_lsbs(mm, nn, o, a)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: cause ValueErrors
    errmsg = r'Bit format specifications must be non-negative\.'
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.keep_lsbs(x, 0, -1)
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.keep_lsbs(x, -2, -3)

    # Corner case: no overflow
    x = uut.FixedPoint('0b00111', 0, 4, 1)
    y = uut.functions.keep_lsbs(x, 0, 3)
    x.keep_lsbs(0, 3)
    tools.verify_attributes(y,
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

@tools.setup(progress_bar=True)
def test_clamp():
    """Verify functions.clamp
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')
    alerts = [x.name for x in uut.properties.Alert]

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.m == int(x.signed):
            continue
        mm = random.randrange(x.signed, x.m)
        if random.randrange(2):
            kwargs['alert'] = random.choice(alerts)
        else:
            kwargs.pop('alert', None)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.clamp(x, mm, **kwargs)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.clamp(mm, **kwargs)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.clamp(mm, **kwargs)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: invalid arguments
    errmsg = r'Q2\.2 can only clamp between \[1, 2\) integer bits\.'
    x = uut.FixedPoint('0b1100', 1, 2, 2, overflow_alert='ignore')
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.clamp(x, 0)
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.clamp(x, 2)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(signed=0):
            uut.functions.clamp(x, -1)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(signed=0):
            uut.functions.clamp(x, 2)

    # Corner case: clamp without overflow
    y = uut.functions.clamp(x, 1)
    nose.tools.assert_equal(y, x)


@tools.setup(progress_bar=True)
def test_wrap():
    """Verify functions.wrap
    """
    strip_sn = lambda s: s.split('SN')[-1].lstrip('0123456789]: ')
    alerts = [x.name for x in uut.properties.Alert]

    for init, args, kwargs, *ignored in nondefault_props_gen():
        x = uut.FixedPoint(init, *args, **kwargs)
        if x.m == int(x.signed):
            continue
        mm = random.randrange(x.signed, x.m)
        if random.randrange(2):
            kwargs['alert'] = random.choice(alerts)
        else:
            kwargs.pop('alert', None)

        # Attempt rounding. Make sure warnings/errors are equivalent between
        # the method and function.
        try:
            with tools.CaptureWarnings() as funcwarn:
                y = uut.functions.wrap(x, mm, **kwargs)

        # An exception occurred. Make sure the method generates the same
        # exception and message as the function
        except Exception as exc:
            UTLOG.debug("Got an exception:\n", exc_info=True, **LOGID)
            with nose.tools.assert_raises_regex(type(exc), re.escape(strip_sn(str(exc)))):
                x.wrap(mm, **kwargs)

        # No exception occurred. Verify that warnings of the function match the
        # warnings of the method. Then compare the objects to make sure they're
        # equivalent
        else:
            with tools.CaptureWarnings() as methwarn:
                x.wrap(mm, **kwargs)

            nose.tools.assert_count_equal(flogs := funcwarn.logs, mlogs := methwarn.logs)
            for flog, mlog in zip(flogs, mlogs):
                nose.tools.assert_regex(mlog, re.escape(strip_sn(flog)))

            tools.verify_attributes(y,
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

    # Corner case: invalid arguments
    errmsg = r'Q2\.2 can only wrap between \[1, 2\) integer bits\.'
    x = uut.FixedPoint('0b1100', 1, 2, 2, overflow_alert='ignore')
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.wrap(x, 0)
    with nose.tools.assert_raises_regex(ValueError, errmsg):
        uut.functions.wrap(x, 2)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(signed=0):
            uut.functions.wrap(x, -1)
    with nose.tools.assert_raises_regex(ValueError, errmsg.replace('1,', '0,')):
        with x(signed=0):
            uut.functions.wrap(x, 2)

    # Corner case: wrap without overflow
    y = uut.functions.wrap(x, 1)
    nose.tools.assert_equal(y, x)

@tools.setup(progress_bar=True)
def test_sign():
    """Verify FixedPoint.sign
    """
    bitsize = min(50, math.ceil(math.log2(tools.NUM_ITERATIONS)) // 2)
    for _ in tools.test_iterator():
        init = random.getrandbits(bitsize) * (2*random.randrange(2) - 1)
        x = uut.FixedPoint(init * 2**-random.randrange(bitsize))

        nose.tools.assert_equal(init < 0, uut.FixedPoint.sign(init) < 0)
        nose.tools.assert_equal(init == 0, uut.FixedPoint.sign(init) == 0)
        nose.tools.assert_equal(init > 0, uut.FixedPoint.sign(init) > 0)

        nose.tools.assert_equal(x < 0, uut.FixedPoint.sign(x) < 0)
        nose.tools.assert_equal(x == 0, uut.FixedPoint.sign(x) == 0)
        nose.tools.assert_equal(x > 0, uut.FixedPoint.sign(x) > 0)

@tools.setup(progress_bar=True)
def test_min_m():
    """Verify FixedPoint.min_m
    """
    for _ in tools.test_iterator():
        init = random.getrandbits(L := random.randrange(tools.NUM_ITERATIONS) + 1)
        init *= 2*random.randrange(2) - 1
        if L <= 50:
            init *= 2**-random.randrange(50)

        m = uut.FixedPoint.min_m(init)

        # Signed numbers
        if init < 0:
            minimum = -2**(m-1)
            nose.tools.assert_less_equal(minimum, math.floor(init))
            nose.tools.assert_equal(m, uut.FixedPoint.min_m(init, False))
            nose.tools.assert_equal(m, uut.FixedPoint.min_m(init, True))

        # Unsigned
        else:
            minimum = 0
            maximum = 2**m
            nose.tools.assert_greater(maximum, math.ceil(init))
            nose.tools.assert_less_equal(minimum, math.floor(init))

            # Explicitly unsigned
            nose.tools.assert_equal(m, uut.FixedPoint.min_m(init, False))

            # Assume it could be signed
            m = uut.FixedPoint.min_m(init, True)
            minimum = -2**(m-1)
            maximum = 2**(m-1)
            nose.tools.assert_greater_equal(maximum, math.ceil(init), init)
            nose.tools.assert_less(minimum, math.floor(init), init)

@tools.setup(progress_bar=True)
def test_min_n():
    """Verify FixedPoint.min_n
    """
    for exp in tools.test_iterator(range(sys.float_info.min_exp, sys.float_info.max_exp)):
        # Test powers of 2 which can be super big or super tiny
        val = 2**exp * (random.randrange(2)*2-1)
        minn = uut.FixedPoint.min_n(val)
        x = uut.FixedPoint(val, n=minn)
        nose.tools.assert_equal(float(x), val)
        # When there are fractional bits, the lsb should be 1
        if x.n:
            nose.tools.assert_equal(x.bits['lsb'], 1, repr(x))

        # Test random floats
        s = random.randrange(2)
        m = random.randrange(s, sys.float_info.mant_dig - 1)
        n = random.randrange(1, sys.float_info.mant_dig - m)
        init = tools.random_float(s, m, n, {})
        minn = uut.FixedPoint.min_n(init)
        x = uut.FixedPoint(init, n=minn)
        nose.tools.assert_equal(float(x), init)
        if x.n:
            nose.tools.assert_equal(x.bits['lsb'], 1, repr(x))

