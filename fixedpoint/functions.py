#!/usr/bin/env python3
"""Function versions of FixedPoint class methods."""
from typing import TYPE_CHECKING

# Avoid circular imports
if TYPE_CHECKING:  # pragma: no cover
    from fixedpoint.fixedpoint import FixedPoint

__all__ = (
    'resize',
    'trim',
    'convergent',
    'round_nearest',
    'round_in',
    'round_out',
    'round_up',
    'round_down',
    'keep_msbs',
    'clamp',
    'wrap',
    'keep_lsbs',
)


###############################################################################
# Bit resizing methods
###############################################################################
def resize(fp: "FixedPoint", m: int, n: int, /, rounding: str = None,
           overflow: str = None, alert: str = None) -> "FixedPoint":
    """Resize integer and fractional bit widths.

    Overflow handling, sign-extension, and rounding are employed.

    Override rounding, overflow, and overflow_alert settings for the scope of
    this function by specifying the appropriate arguments.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.resize(m, n, rounding, overflow, alert)
    return ret


def trim(fp: "FixedPoint", /, ints: bool = None,
         fracs: bool = None) -> "FixedPoint":
    """Trims off insignificant bits.

    This includes trailing 0s, leading 0s, and leading 1s as appropriate.

    Trim only integer bits or fractional bits by setting `fracs` or `ints`
    to True. By default, both integer and fractional bits are trimmed.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.trim(ints, fracs)
    return ret


def convergent(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Round half to even."""
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.convergent(nfrac)
    return ret


round_convergent = convergent


def round_nearest(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Round half up."""
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_nearest(nfrac)
    return ret


def round_in(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Round towards 0."""
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_in(nfrac)
    return ret


def round_out(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Round half away from zero."""
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_out(nfrac)
    return ret


def round_up(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Round towards infinity."""
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_up(nfrac)
    return ret


def round_down(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Round towards negative infinity."""
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_down(nfrac)
    return ret


def keep_msbs(fp: "FixedPoint", m: int, n: int, /, rounding: str = None,
              overflow: str = None, alert: str = None) -> "FixedPoint":
    """Round off MSbs, and reformat to the given number of bits.

    Override rounding, overflow, and overflow_alert settings for the scope of
    this function by specifying the appropriate arguments.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.keep_msbs(m, n, rounding, overflow, alert)
    return ret


###############################################################################
# Overflow handling
###############################################################################
def clamp(fp: "FixedPoint", nint: int, /, alert: str = None) -> "FixedPoint":
    """Remove integer bits and clamps if necessary.

    Override the overflow_alert setting for the scope of this method by
    specifying an alternative `alert`.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.clamp(nint, alert)
    return ret


def wrap(fp: "FixedPoint", nint: int, /, alert: str = None) -> "FixedPoint":
    """Remove integer bits by masking them away.

    Override the overflow_alert setting for the scope of this method by
    specifying an alternative `alert`.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.wrap(nint, alert)
    return ret


def keep_lsbs(fp: "FixedPoint", m: int, n: int, /, overflow: str = None,
              alert: str = None) -> "FixedPoint":
    """Remove MSbs, and reformat to the given number of bits.

    Override the overflow and overflow_alert setting for the scope of this
    function by specifying the appropriate arguments.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.keep_lsbs(m, n, overflow, alert)
    return ret
