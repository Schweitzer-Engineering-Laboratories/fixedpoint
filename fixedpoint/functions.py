#!/usr/bin/env python3
# Copyright (c) 2019-2020, Schweitzer Engineering Laboratories, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Schweitzer Engineering Laboratories, Inc. nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL SCHWEITZER ENGINEERING LABORATORIES, INC.
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
from typing import (
    Optional,
    TYPE_CHECKING,
)
from math import (
    log2 as _log2,
    ceil as _ceil,
)

__all__ = [
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
]

# Avoid circular imports
if TYPE_CHECKING: # pragma: no cover
    from fixedpoint.fixedpoint import FixedPoint

###############################################################################
# Bit resizing methods
###############################################################################
def resize(fp: "FixedPoint", m: int, n: int, /,
rounding: str = None, overflow: str = None, alert: str = None) -> "FixedPoint":
    """Create a new FixedPoint number resized to the specified width. The
    number of fractional bits remaining after rounding is nfrac. The number of
    integer bits remaining after rounding is nint.

    If nint is less than the current number of integer bits, overflow behavior
    is specified by the overflow argument.

    If nfrac is less than the current number of fractional bits, rounding
    behavior is specified by on the rounding argument. No rounding occurs if
    overflow happens.

    If no overflow or rounding argument is provided, the current overflow
    and rounding scheme is used.

    The overflow and rounding arguments are local only to this function. I.e.,
    the return object will have its rounding and overflow properties equivalent
    to the given FixedPoint object.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.resize(m, n, rounding, overflow, alert)
    return ret

def trim(fp: "FixedPoint", /, ints: bool = None, fracs: bool = None) -> "FixedPoint":
    """Creates a new FixedPoint number with insignificant bits trimmed off
    (i.e., truncates trailing 0s, leading 0s, and leading 1s for signed
    numbers). If integer and fractional bits can both be trimmed to 0 length,
    integer bits will remain at 1, unless it's already at 0.

    You can opt to trim only integer bits or fractional bits by setting fracs
    or ints, respectively, to False.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.trim(ints, fracs)
    return ret

def convergent(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Create a new FixedPoint object rounded to the nearest bit; ties round to
    the nearest even bit. The number of fractional bits remaining after
    rounding is nfrac.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.convergent(nfrac)
    return ret
round_convergent = convergent

def round_nearest(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Create a new FixedPoint object rounded to the nearest bit; ties round to
    positive infinity. The number of fractional bits remaining after rounding
    is nfrac.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_nearest(nfrac)
    return ret

def round_in(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Create a new FixedPoint object rounding toward 0. The number of
    fractional bits remaining after rounding is nfrac.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_in(nfrac)
    return ret

def round_out(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Create a new FixedPoint object rounded to the nearest bit; ties round
    away from 0. The number of fractional bits remaining after rounding is
    nfrac.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_out(nfrac)
    return ret

def round_up(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Create a new FixedPoint object rounded to positive infinity. The number
    of fractional bits remaining after rounding is nfrac.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_up(nfrac)
    return ret

def round_down(fp: "FixedPoint", nfrac: int, /) -> "FixedPoint":
    """Create a new FixedPoint object rounded to positive infinity. The number
    of fractional bits remaining after rounding is nfrac.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.round_down(nfrac)
    return ret

def keep_msbs(fp: "FixedPoint", m: int, n: int, /,
rounding: str = None, overflow: str = None, alert: str = None) -> "FixedPoint":
    """Create a new FixedPoint object rounded to positive infinity. Round off
    LSbs, even if they're integer bits. The number of bits left after rounding
    is nbits. Uses the indicated rounding scheme if specified, otherwise uses
    fp.rounding. The rounding property of the return value will be fp.rounding.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.keep_msbs(m, n, rounding, overflow, alert)
    return ret

###############################################################################
# Overflow handling
###############################################################################
def clamp(fp: "FixedPoint", nint: int, /, alert: str = None) -> "FixedPoint":
    """Create a new FixedPoint object and remove integer bits; clamps if
    overflow occurs. The number of integer bits remaining after rounding is
    nint. For signed numbers, nint does not include the sign bit. You can
    locally change the overflow alert level by specifying alert, otherwise the
    fp.overflow_alert setting is used.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.clamp(nint, alert)
    return ret

def wrap(fp: "FixedPoint", nint: int, /, alert: str = None) -> "FixedPoint":
    """Creates a new FixedPoint object and removes integer bits. The number of
    integer bits left after clamping is nint. For signed numbers, nint includes
    the sign bit. You can locally change the overflow alert level by specifying
    alert, otherwise the fp.overflow_alert setting is used.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.wrap(nint, alert)
    return ret

def keep_lsbs(fp: "FixedPoint", m: int, n: int, /,
overflow: str = None, alert: str = None) -> "FixedPoint":
    """rflow_alert property can be modified too if needed. Specifying a
    overflow or overflow_alert property is local to this method; it will
    not change the object's properties permanently.
    """
    from fixedpoint.fixedpoint import FixedPoint
    ret = FixedPoint(fp)
    ret.keep_lsbs(m, n, overflow, alert)
    return ret
