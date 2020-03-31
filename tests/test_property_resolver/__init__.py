#!/usr/bin/env python3.8
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
import random
import json
import itertools

from ..init import (
    uut,
    UTLOG,
    LOGID,
    nose,
)
from .. import tools

@tools.setup(progress_bar=True)
def test_str_base_resolution():
    """Verify str_base property resolution
    """
    # All possible permutations of mismatch_alerts
    bases = tuple(x for x in uut.properties.StrConv.keys())
    permutations = [
        (
            {'str_base': x},
            {'str_base': y},
        )
        for x, y in itertools.product(bases, repeat=2)
    ]

    # Instances to be used
    x = uut.FixedPoint(0)
    y = uut.FixedPoint(0)
    UUT = uut.properties.PropertyResolver()

    # Run the regressions
    for xkwargs, ykwargs in tools.test_iterator(permutations):
        UTLOG.debug("x: %s\ny: %s",
            json.dumps(xkwargs, indent=2),
            json.dumps(ykwargs, indent=2),
            **LOGID
        )

        with x(safe_retain=True, **xkwargs), y(safe_retain=True, **ykwargs):
            result = UUT.str_base(x, y)

            if result == 10:
                nose.tools.assert_equal(x.str_base, 10)
                nose.tools.assert_equal(y.str_base, 10)
            elif result == 8:
                nose.tools.assert_equal(x.str_base, 8)
                nose.tools.assert_equal(y.str_base, 8)
            elif result == 2:
                nose.tools.assert_equal(x.str_base, 2)
                nose.tools.assert_equal(y.str_base, 2)
            else:
                nose.tools.assert_equal(result, 16)

@tools.setup(progress_bar=True)
def test_implicit_cast_alert_resolution():
    """Verify implicit_cast_alert property resolution
    """
    # All possible permutations of overflow_alerts and mismatch_alerts
    alerts = tuple(x.name for x in uut.properties.Alert)
    permutations = [
        (
            {'implicit_cast_alert': xi, 'mismatch_alert': xm},
            {'implicit_cast_alert': yi, 'mismatch_alert': ym},
        )
        for xi, yi, xm, ym in itertools.product(alerts, repeat=4)
    ]

    # Error and warning messages.
    merrmsg = r"Non-matching mismatch_alert behaviors \[.*'error'.*\]."
    ierrmsg = r"Non-matching implicit_cast_alert behaviors"
    mwarnmsg = r"Using 'warning'\."
    def iwarnmsg(x, y):
        A = (x.implicit_cast_alert, y.implicit_cast_alert)
        return r'Using %r\.' % (
            'warning' if 'warning' in A else
            'error' if 'error' in A else 'ignore'
        )

    # Instances to be used
    x = uut.FixedPoint(0)
    y = uut.FixedPoint(0)
    UUT = uut.properties.PropertyResolver()

    # Run the regressions
    for xkwargs, ykwargs in tools.test_iterator(permutations):
        UTLOG.debug("x: %s\ny: %s",
            json.dumps(xkwargs, indent=2),
            json.dumps(ykwargs, indent=2),
            **LOGID
        )

        with x(safe_retain=True, **xkwargs), y(safe_retain=True, **ykwargs):
            args = (x, y)
            M = (x.mismatch_alert, y.mismatch_alert)

        if 'error' in M:
            try:
                result = UUT.implicit_cast_alert(*args)
            except uut.MismatchError as exc:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(str(exc), merrmsg)
                else:
                    nose.tools.assert_regex(str(exc), ierrmsg)
                continue
            else:
                nose.tools.assert_equal(x.implicit_cast_alert, y.implicit_cast_alert)

        elif 'warning' in M:
            with tools.CaptureWarnings() as warn:
                result = UUT.implicit_cast_alert(*args)
            UTLOG.debug('Warning logs (%d): %s',
                len(logs := warn.logs),
                json.dumps(logs, indent=2),
                **LOGID
            )

            if x.implicit_cast_alert != y.implicit_cast_alert:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(logs[0], merrmsg.replace('error', 'warning'))
                    nose.tools.assert_regex(logs[1], mwarnmsg)
                nose.tools.assert_regex(logs[-2], ierrmsg)
                nose.tools.assert_regex(logs[-1], iwarnmsg(*args))
            else:
                nose.tools.assert_equal(len(logs), 0)

        else:
            with tools.CaptureWarnings() as warn:
                result = UUT.implicit_cast_alert(*args)

            nose.tools.assert_equal(len(warn.logs), 0)

        # Validate property resolution
        if result == 'ignore':
            nose.tools.assert_not_equal(x.implicit_cast_alert, 'error')
            nose.tools.assert_not_equal(y.implicit_cast_alert, 'error')
            nose.tools.assert_not_equal(x.implicit_cast_alert, 'warning')
            nose.tools.assert_not_equal(y.implicit_cast_alert, 'warning')
        elif result == 'error':
            nose.tools.assert_not_equal(x.implicit_cast_alert, 'warning')
            nose.tools.assert_not_equal(y.implicit_cast_alert, 'warning')

@tools.setup(progress_bar=True)
def test_mismatch_alert_resolution():
    """Verify mismatch_alert property resolution
    """
    # All possible permutations of mismatch_alerts
    alerts = tuple(x.name for x in uut.properties.Alert)
    permutations = [
        (
            {'mismatch_alert': xm},
            {'mismatch_alert': ym},
        )
        for xm, ym in itertools.product(alerts, repeat=2)
    ]

    # Error and warning messages.
    merrmsg = r"Non-matching mismatch_alert behaviors \[.*'error'.*\]."
    mwarnmsg = r"Using 'warning'\."

    # Instances to be used
    x = uut.FixedPoint(0)
    y = uut.FixedPoint(0)
    UUT = uut.properties.PropertyResolver()

    # Run the regressions
    for xkwargs, ykwargs in tools.test_iterator(permutations):
        UTLOG.debug("x: %s\ny: %s",
            json.dumps(xkwargs, indent=2),
            json.dumps(ykwargs, indent=2),
            **LOGID
        )

        with x(safe_retain=True, **xkwargs), y(safe_retain=True, **ykwargs):
            args = (x, y)
            M = (x.mismatch_alert, y.mismatch_alert)

        if 'error' in M:
            try:
                result = UUT.mismatch_alert(*args)
            except uut.MismatchError as exc:
                nose.tools.assert_regex(str(exc), merrmsg)
                nose.tools.assert_not_equal(*M)
                continue
            else:
                nose.tools.assert_equal(*M)

        elif 'warning' in M:
            with tools.CaptureWarnings() as warn:
                result = UUT.mismatch_alert(*args)
            UTLOG.debug('Warning logs (%d): %s',
                len(logs := warn.logs),
                json.dumps(logs, indent=2),
                **LOGID
            )

            if x.mismatch_alert != y.mismatch_alert:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(logs[0], merrmsg.replace('error', 'warning'))
                    nose.tools.assert_regex(logs[1], mwarnmsg)
            else:
                nose.tools.assert_equal(len(logs), 0)

        else:
            with tools.CaptureWarnings() as warn:
                result = UUT.mismatch_alert(*args)

            nose.tools.assert_equal(len(warn.logs), 0)

        # Validate property resolution
        if result == 'ignore':
            nose.tools.assert_not_equal(x.mismatch_alert, 'error')
            nose.tools.assert_not_equal(y.mismatch_alert, 'error')
            nose.tools.assert_not_equal(x.mismatch_alert, 'warning')
            nose.tools.assert_not_equal(y.mismatch_alert, 'warning')
        elif result == 'warning':
            nose.tools.assert_not_equal(x.mismatch_alert, 'error')
            nose.tools.assert_not_equal(y.mismatch_alert, 'error')

@tools.setup(progress_bar=True)
def test_overflow_alert_resolution():
    """Verify overflow_alert property resolution
    """
    # All possible permutations of overflow_alerts and mismatch_alerts
    alerts = tuple(x.name for x in uut.properties.Alert)
    permutations = [
        (
            {'overflow_alert': xo, 'mismatch_alert': xm},
            {'overflow_alert': yo, 'mismatch_alert': ym},
        )
        for xo, yo, xm, ym in itertools.product(alerts, repeat=4)
    ]

    # Error and warning messages.
    merrmsg = r"Non-matching mismatch_alert behaviors \[.*'error'.*\]."
    oerrmsg = r"Non-matching overflow_alert behaviors"
    mwarnmsg = r"Using 'warning'\."
    def owarnmsg(x, y):
        A = (x.overflow_alert, y.overflow_alert)
        return r'Using %r\.' % (
            'error' if 'error' in A else
            'warning' if 'warning' in A else 'ignore'
        )

    # Instances to be used
    x = uut.FixedPoint(0)
    y = uut.FixedPoint(0)
    UUT = uut.properties.PropertyResolver()

    # Run the regressions
    for xkwargs, ykwargs in tools.test_iterator(permutations):
        UTLOG.debug("x: %s\ny: %s",
            json.dumps(xkwargs, indent=2),
            json.dumps(ykwargs, indent=2),
            **LOGID
        )

        with x(safe_retain=True, **xkwargs), y(safe_retain=True, **ykwargs):
            args = (x, y)
            M = (x.mismatch_alert, y.mismatch_alert)

        if 'error' in M:
            try:
                result = UUT.overflow_alert(*args)
            except uut.MismatchError as exc:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(str(exc), merrmsg)
                else:
                    nose.tools.assert_regex(str(exc), oerrmsg)
                continue
            else:
                nose.tools.assert_equal(x.overflow_alert, y.overflow_alert)

        elif 'warning' in M:
            with tools.CaptureWarnings() as warn:
                result = UUT.overflow_alert(*args)
            UTLOG.debug('Warning logs (%d): %s',
                len(logs := warn.logs),
                json.dumps(logs, indent=2),
                **LOGID
            )

            if x.overflow_alert != y.overflow_alert:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(logs[0], merrmsg.replace('error', 'warning'))
                    nose.tools.assert_regex(logs[1], mwarnmsg)
                nose.tools.assert_regex(logs[-2], oerrmsg)
                nose.tools.assert_regex(logs[-1], owarnmsg(*args))
            else:
                nose.tools.assert_equal(len(logs), 0)

        else:
            with tools.CaptureWarnings() as warn:
                result = UUT.overflow_alert(*args)

            nose.tools.assert_equal(len(warn.logs), 0)

        # Validate property resolution
        if result == 'ignore':
            nose.tools.assert_not_equal(x.overflow_alert, 'error')
            nose.tools.assert_not_equal(y.overflow_alert, 'error')
            nose.tools.assert_not_equal(x.overflow_alert, 'warning')
            nose.tools.assert_not_equal(y.overflow_alert, 'warning')
        elif result == 'warning':
            nose.tools.assert_not_equal(x.overflow_alert, 'error')
            nose.tools.assert_not_equal(y.overflow_alert, 'error')

@tools.setup(progress_bar=True)
def test_rounding_resolution():
    """Verify rounding property resolution
    """
    # All possible permutations of roundings and mismatch_alerts
    roundings = tuple(x.name for x in uut.properties.Rounding)
    alerts = tuple(x.name for x in uut.properties.Alert)
    permutations = [
        (
            {'rounding': x, 'mismatch_alert': xm, 'signed': xs},
            {'rounding': y, 'mismatch_alert': ym, 'signed': ys},
        )
        for x, y in itertools.product(roundings, repeat=2)
        for xm, ym in itertools.product(alerts, repeat=2)
        for xs, ys in itertools.product((True, False), repeat=2)
    ]

    # Error and warning messages.
    merrmsg = r"Non-matching mismatch_alert behaviors \[.*'error'.*\]."
    rerrmsg = r"Non-matching rounding behaviors"
    mwarnmsg = r"Using 'warning'\."
    def rwarnmsg(x, y):
        R = (x.rounding, y.rounding)
        return r"Using %r\." % (
            (
                (
                    'convergent' if 'convergent' in R else
                    'nearest' if 'nearest' in R else
                    'down' if 'down' in R else
                    'in' if 'in' in R else
                    'out' if 'out' in R else 'up'
                ) if x.signed or y.signed else (
                    'nearest' if 'nearest' in R else
                    'convergent' if 'convergent' in R else
                    'down' if 'down' in R else
                    'in' if 'in' in R else
                    'out' if 'out' in R else 'up'
                )
            )
        )

    # Instances to be used
    x = uut.FixedPoint(0, m=1)
    y = uut.FixedPoint(0, m=1)
    UUT = uut.properties.PropertyResolver()

    # Run the regressions
    for xkwargs, ykwargs in tools.test_iterator(permutations):
        UTLOG.debug("x: %s\ny: %s",
            json.dumps(xkwargs, indent=2),
            json.dumps(ykwargs, indent=2),
            **LOGID
        )

        with x(safe_retain=True, **xkwargs), y(safe_retain=True, **ykwargs):
            args = (x, y)

        if any(a.mismatch_alert == 'error' for a in args):
            try:
                result = UUT.rounding(x, y)
            except uut.MismatchError as exc:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(str(exc), merrmsg)
                else:
                    nose.tools.assert_regex(str(exc), rerrmsg)
                continue
            else:
                nose.tools.assert_equal(x.rounding, y.rounding)

        elif any(a.mismatch_alert == 'warning' for a in args):
            with tools.CaptureWarnings() as warn:
                result = UUT.rounding(x, y)
            UTLOG.debug('Warning logs (%d): %s',
                len(logs := warn.logs),
                json.dumps(logs, indent=2),
                **LOGID
            )

            if x.rounding != y.rounding:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(logs[0], merrmsg.replace('error', 'warning'))
                    nose.tools.assert_regex(logs[1], mwarnmsg)
                nose.tools.assert_regex(logs[-2], rerrmsg)
                nose.tools.assert_regex(logs[-1], rwarnmsg(x, y))
            else:
                nose.tools.assert_equal(len(logs), 0)

        else:
            with tools.CaptureWarnings() as warn:
                result = UUT.rounding(x, y)

            nose.tools.assert_equal(len(warn.logs), 0)

        # Validate property resolution
        R = (x.rounding, y.rounding)
        signed = (x.signed, y.signed)
        if result == 'up':
            nose.tools.assert_not_in('out', R)
            nose.tools.assert_not_in('in', R)
            nose.tools.assert_not_in('down', R)
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif result == 'out':
            nose.tools.assert_not_in('in', R)
            nose.tools.assert_not_in('down', R)
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif result == 'in':
            nose.tools.assert_not_in('down', R)
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif result == 'down':
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif result == 'nearest' and any(signed):
            nose.tools.assert_not_in('convergent', R)
        elif result == 'convergent' and not any(signed):
            nose.tools.assert_not_in('nearest', R)

@tools.setup(progress_bar=True)
def test_overflow_resolution():
    """Verify overflow property resolution
    """
    # All possible permutations of overflows and mismatch_alerts
    overflows = tuple(x.name for x in uut.properties.Overflow)
    alerts = tuple(x.name for x in uut.properties.Alert)
    permutations = [
        (
            {'overflow': x, 'mismatch_alert': xx},
            {'overflow': y, 'mismatch_alert': yy},
        )
        for x, y in itertools.product(overflows, repeat=2)
        for xx, yy in itertools.product(alerts, repeat=2)
    ]

    # Error and warning messages.
    merrmsg = r"Non-matching mismatch_alert behaviors \[.*'error'.*\]."
    oerrmsg = r"Non-matching overflow behaviors"
    mwarnmsg = r"Using 'warning'\."
    owarnmsg = r"Using 'clamp'\."

    # Instances to be used
    x = uut.FixedPoint(0)
    y = uut.FixedPoint(0)
    UUT = uut.properties.PropertyResolver()

    # Run the regressions
    for xkwargs, ykwargs in tools.test_iterator(permutations):
        UTLOG.debug("x: %s\ny: %s",
            json.dumps(xkwargs, indent=2),
            json.dumps(ykwargs, indent=2),
            **LOGID
        )

        with x(safe_retain=True, **xkwargs), y(safe_retain=True, **ykwargs):
            args = (x, y)

        if any(a.mismatch_alert == 'error' for a in args):
            try:
                result = UUT.overflow(x, y)
            except uut.MismatchError as exc:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(str(exc), merrmsg)
                else:
                    nose.tools.assert_regex(str(exc), oerrmsg)
                continue
            else:
                nose.tools.assert_equal(x.overflow, y.overflow)

        elif any(a.mismatch_alert == 'warning' for a in args):
            with tools.CaptureWarnings() as warn:
                result = UUT.overflow(x, y)
            UTLOG.debug('Warning logs (%d): %s',
                len(logs := warn.logs),
                json.dumps(logs, indent=2),
                **LOGID
            )

            if x.overflow != y.overflow:
                if x.mismatch_alert != y.mismatch_alert:
                    nose.tools.assert_regex(logs[0], merrmsg.replace('error', 'warning'))
                    nose.tools.assert_regex(logs[1], mwarnmsg)
                nose.tools.assert_regex(logs[-2], oerrmsg)
                nose.tools.assert_regex(logs[-1], owarnmsg)
            else:
                nose.tools.assert_equal(len(logs), 0)

        else:
            with tools.CaptureWarnings() as warn:
                result = UUT.overflow(x, y)

            nose.tools.assert_equal(len(warn.logs), 0)

        # Validate property resolution
        if result == 'wrap':
            nose.tools.assert_equal(x.overflow, 'wrap')
            nose.tools.assert_equal(y.overflow, 'wrap')
        else:
            nose.tools.assert_equal(result, 'clamp')

@tools.setup(progress_bar=True)
def test_all():
    """Verify resolution of all properties
    """

    mmerrmsg = r"Non-matching mismatch_alert behaviors \[.*'error'.*\]."
    moerrmsg = r"Non-matching overflow behaviors"
    mrerrmsg = r"Non-matching rounding behaviors"
    maerrmsg = r"Non-matching overflow_alert behaviors"
    mierrmsg = r"Non-matching implicit_cast_alert behaviors"

    mmwarnmsg = r"Using 'warning'\."
    mowarnmsg = r"Using 'clamp'\."
    mrwarnmsg = r"Using %r\."
    mawarnmsg = r"Using %r\."
    miwarnmsg = r"Using %r\."

    str_bases = tuple(uut.properties.StrConv.keys())
    alerts = tuple(x.name for x in uut.properties.Alert)
    overflows = tuple(x.name for x in uut.properties.Overflow)
    roundings = tuple(x.name for x in uut.properties.Rounding)
    x = uut.FixedPoint('0b0110', 0, 2, 2)
    y = uut.FixedPoint('0b0110', 0, 2, 2)
    UUT = uut.properties.PropertyResolver()

    for _ in tools.test_iterator():
        x.signed, y.signed = signed = random.randrange(2), random.randrange(2)
        x.str_base, y.str_base = S = random.choices(str_bases, k=2)
        x.mismatch_alert, y.mismatch_alert = M = random.choices(alerts, k=2)
        x.overflow_alert, y.overflow_alert = A = random.choices(alerts, k=2)
        x.implicit_cast_alert, y.implicit_cast_alert = I = random.choices(alerts, k=2)
        x.overflow, y.overflow = O = random.choices(overflows, k=2)
        x.rounding, y.rounding = R = random.choices(roundings, k=2)

        UTLOG.debug("x: %s\ny: %s",
            json.dumps(UUT.all(x), indent=2),
            json.dumps(UUT.all(y), indent=2),
            **LOGID
        )

        if 'error' in M:
            if len(set(M)) != 1:
                errmsg = mmerrmsg
            elif len(set(O)) != 1:
                errmsg = moerrmsg
            elif len(set(R)) != 1:
                errmsg = mrerrmsg
            elif len(set(A)) != 1:
                errmsg = maerrmsg
            elif len(set(I)) != 1:
                errmsg = mierrmsg
            else:
                errmsg = 'no mismatches!'
            try:
                result = UUT.all(x, y)
            except uut.MismatchError as exc:
                nose.tools.assert_regex(str(exc), errmsg)
                continue
            else:
                nose.tools.assert_equal(errmsg, 'no mismatches!')

        elif 'warning' in M:
            errmsg, warnmsg = [], []
            if len(set(M)) != 1:
                errmsg.append(mmerrmsg.replace('error', 'warning'))
                warnmsg.append(mmwarnmsg)
            if len(set(O)) != 1:
                errmsg.append(moerrmsg)
                warnmsg.append(mowarnmsg)
            if len(set(R)) != 1:
                errmsg.append(mrerrmsg)
                warnmsg.append(mrwarnmsg % (
                        (
                            'convergent' if 'convergent' in R else
                            'nearest' if 'nearest' in R else
                            'down' if 'down' in R else
                            'in' if 'in' in R else 'out'
                        ) if any(signed) else (
                            'nearest' if 'nearest' in R else
                            'convergent' if 'convergent' in R else
                            'down' if 'down' in R else
                            'in' if 'in' in R else 'out'
                        )
                    )
                )
            if len(set(A)) != 1:
                errmsg.append(maerrmsg)
                warnmsg.append(mawarnmsg % ('error' if 'error' in A else 'warning'))
            if len(set(I)) != 1:
                errmsg.append(mierrmsg)
                warnmsg.append(miwarnmsg % ('warning' if 'warning' in I else 'error'))

            with tools.CaptureWarnings() as warn:
                result = UUT.all(x, y)

            for i, log in enumerate(warn.logs):
                nose.tools.assert_regex(log, (warnmsg if i % 2 else errmsg)[i // 2],
                    f'{i}:\n{json.dumps(errmsg, indent=2)}\n{json.dumps(warnmsg, indent=2)}\n')

        # mismatch_alert set to 'ignore'
        else:
            with tools.CaptureWarnings() as warn:
                result = UUT.all(x, y)
            nose.tools.assert_equal(len(warn.logs), 0)

        # Verify results
        if (rM := result['mismatch_alert']) == 'ignore':
            nose.tools.assert_not_in('warning', M)
            nose.tools.assert_not_in('error', M)
        elif rM == 'error':
            nose.tools.assert_not_in('warning', M)

        if result['overflow'] == 'wrap':
            nose.tools.assert_not_in('clamp', O)

        if (rR := result['rounding']) == 'up':
            nose.tools.assert_not_in('out', R)
            nose.tools.assert_not_in('in', R)
            nose.tools.assert_not_in('down', R)
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif rR == 'out':
            nose.tools.assert_not_in('in', R)
            nose.tools.assert_not_in('down', R)
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif rR == 'in':
            nose.tools.assert_not_in('down', R)
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif rR == 'down':
            nose.tools.assert_not_in('nearest', R)
            nose.tools.assert_not_in('convergent', R)
        elif rR == 'nearest' and any(signed):
            nose.tools.assert_not_in('convergent', R)
        elif rR == 'convergent' and not any(signed):
            nose.tools.assert_not_in('nearest', R)

        if (rA := result['overflow_alert']) == 'ignore':
            nose.tools.assert_not_in('warning', A)
            nose.tools.assert_not_in('error', A)
        elif rA == 'warning':
            nose.tools.assert_not_in('error', A)

        if (rI := result['implicit_cast_alert']) == 'ignore':
            nose.tools.assert_not_in('warning', I)
            nose.tools.assert_not_in('error', I)
        elif rI == 'error':
            nose.tools.assert_not_in('warning', I)

        if (rS := result['str_base']) != 16:
            nose.tools.assert_not_in(16, S)









