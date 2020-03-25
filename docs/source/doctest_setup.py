import sys
import re
import logging
import unittest.mock

from fixedpoint import *
import fixedpoint.logging

def reset_sn(sn=0):
    """Resets the FixedPoint serial number"""
    FixedPoint._SERIAL_NUMBER = sn

def alphabetize_mismatches(record):
    """Filters a log record and alphabetizes mismatches"""
    newargs = list(record.args)
    for i, warning in enumerate(newargs):
        if not isinstance(warning, list):
            continue
        props = re.search(r"\['([a-z]+)', '([a-z]+)'\]", arg := str(warning))
        if not props:
            continue
        sub = sorted([props.group(x) for x in (1, 2)])
        newargs[i] = arg.replace(props.group(0), str(sub))

    record.args = tuple(newargs)

    return True

def patch_min_n(rval=2):
    """Patches FixedPoint.min_n to always return the same value"""
    patcher = unittest.mock.patch('fixedpoint.FixedPoint.min_n', return_value=rval)
    patcher.start()
    return patcher

def unpatch(patcher):
    """Returns the patched object to normal functionality"""
    patcher.stop()

# Make warnings print to stdout instead of stderr
fixedpoint.logging.WARNER_CONSOLE_HANDLER.stream = sys.stdout
fixedpoint.logging.WARNER.removeFilter(alphabetize_mismatches)
fixedpoint.logging.WARNER.addFilter(alphabetize_mismatches)
