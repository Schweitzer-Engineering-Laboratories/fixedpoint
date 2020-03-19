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
import enum as _enum
import logging as _logging
from typing import (
    Callable,
    Dict,
    Mapping,
    NewType,
    Set,
    Tuple,
    Union,
    TYPE_CHECKING,
)

__all__ = [
    'PROPERTIES',
    'StrConv',
    'StrBase',
    'Alert',
    'Overflow',
    'Rounding',
    'PropertyResolver',
]

# Avoid circular imports
if TYPE_CHECKING: # pragma: no cover
    from fixedpoint.fixedpoint import FixedPoint

PROPERTIES: Tuple[str, ...] = (
    'str_base',
    'mismatch_alert',
    'overflow_alert',
    'implicit_cast_alert',
    'overflow',
    'rounding',
)

StrConv: Mapping[int, Callable[[int], str]] = {
    2: bin,
    8: oct,
    10: str,
    16: hex,
}
StrBase = _enum.Enum('str_base', { # type: ignore # (too many arguments)
        'binary': 2,
        'octal': 8,
        'decimal': 10,
        'hexadecimal': 16,
    },
    module=__name__,
    qualname="StrBase",
)

Alert: _enum.Enum = _enum.Enum('alert', { # type: ignore # (too many arguments)
        'error': _logging.ERROR,
        'warning': _logging.WARNING,
        'ignore': _logging.DEBUG,
    },
    module=__name__,
    qualname="Alert",
)

Overflow: _enum.Enum = _enum.Enum('overflow', { # type: ignore # (too many arguments)
        'clamp': 100,
        'wrap': 101,
    },
    module=__name__,
    qualname="Overflow",
)

# This is especially ordered for signed numbers.
Rounding: _enum.Enum = _enum.Enum('rounding', { # type: ignore # (too many arguments)
        'convergent': 200,
        'nearest': 201,
        'down': 202,
        'in': 203,
        'out': 204,
        'up': 205,
    },
    module=__name__,
    qualname="Rounding",
)

Property = Union[StrBase, Alert, Overflow, Rounding]

class PropertyResolver:
    """Resolves properties between two FixedPoint objects.
    """
    def __new__(cls) -> "PropertyResolver":
        """There will be only one PropertyResolver instance ever.
        """
        try:
            cls.__instance
        except AttributeError:
            cls.__instance: "PropertyResolver" = super(PropertyResolver, cls).__new__(cls)
            cls.__instance.__ignore_mismatch: bool = False # type: ignore

        return cls.__instance

    def str_base(self, *args: "FixedPoint") -> int:
        '''Resolve str_base properties between 2 FixedPoint objects. If they
        don't match, then 16 is used. No warning is issued because it's not
        that big of a deal.
        '''
        if len(checkset := {obj._str_base.value for obj in args}) == 1:
            ret = checkset.pop()
        else:
            ret = 16

        return int(ret)

    def implicit_cast_alert(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        '''Resolve implicit_cast_alert properties between 2 FixedPoint objects.
        If they don't match, then the priority is:
            1. warning
            2. error
            3. ignore
        A MismatchWarning is issued if they don't match.
        '''
        if len(checkset := {obj._implicit_cast_alert for obj in args}) == 1:
            ret = checkset.pop()
        # If there's a mismatch, handle it based on mismatch_alert property.
        else:
            ret = Alert['warning'] if Alert['warning'] in checkset else Alert['error']
            _, warner = self._mismatch_alert(*args, stacklevel=stacklevel + 1)
            warner("Non-matching implicit_cast_alert behaviors %s.",
                [alert.name for alert in checkset], stacklevel=stacklevel)
            warner("Using %r.", ret.name, stacklevel=stacklevel)

        return ret.name

    def overflow_alert(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        '''Resolve overflow_alert properties between 2 FixedPoint objects. If
        they don't match, then the priority is:
            1. error
            2. warning
            3. ignore
        A MismatchWarning is issued if they don't match.
        '''
        if len(checkset := {obj._overflow_alert for obj in args}) == 1:
            ret = checkset.pop()
        # If there's a mismatch, handle it based on mismatch_alert property.
        else:
            ret = Alert['error'] if Alert['error'] in checkset else Alert['warning']
            _, warner = self._mismatch_alert(*args, stacklevel=stacklevel + 1)
            warner("Non-matching overflow_alert behaviors %s.",
                [alert.name for alert in checkset], stacklevel=stacklevel)
            warner("Using %r.", ret.name, stacklevel=stacklevel)

        return ret.name

    def _mismatch_alert(self, *args: "FixedPoint", stacklevel: int = 5) -> Tuple[str, Callable[..., None]]:
        '''Resolve mismatch_alert properties between 2 FixedPoint objects. If
        they don't match, the most severe alarm between them is triggered. As
        long as the triggered alert is not an error, the priority is:
            1. warning
            2. ignore
        '''
        if len(set(checklist := [obj._mismatch_alert for obj in args])) == 1:
            alert = args[0]._mismatch_alert
            warnerfunc = args[0]._mwarn
        else:
            # First make sure the mismatches don't trigger a warning
            warner = args[0]._mwarn
            for name in ('error', 'warning'): # pragma: no branch
                for i, alert in enumerate(checklist):
                    if alert == Alert[name]:
                        warner = args[i]._mwarn
                        break
                else:
                    continue
                break

            # Prioritize for return value
            for name in ('warning', 'error'): # pragma: no branch
                for i, alert in enumerate(checklist):
                    if alert == Alert[name]:
                        warnerfunc = args[i]._mwarn
                        break
                else:
                    continue
                break

            # Since every resolver method must check for mismatch, only trigger
            # a warning on the first detected mismatch_alert mismatch,
            # subsequent mismatch_alert warnings are ignored.
            if not self.__ignore_mismatch:
                warner('Non-matching mismatch_alert behaviors %s.',
                    [x.name for x in checklist], stacklevel=stacklevel)
                warner('Using %r.', alert.name)

        return alert.name, warnerfunc

    def mismatch_alert(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        '''Resolve mismatch_alert properties between 2 FixedPoint objects. If
        they don't match, the most severe alarm between them is triggered. As
        long as the triggered alert is not an error, the priority is:
            1. warning
            2. ignore
        '''
        return self._mismatch_alert(*args, stacklevel=stacklevel + 1)[0]

    def rounding(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        '''Resolve rounding properties between 2 FixedPoint objects. If they
        don't match, then the priority is:
            1. convergent if either are signed, nearest otherwise
            2. nearest if either are signed, convergent otherwise
            3. down
            4. in
            5. out
            6. up
        A MismatchWarning is issued if they don't match.
        '''
        if len(checkset := {obj._rounding for obj in args}) == 1:
            ret = checkset.pop()
        else:
            # If all values are unsigned, resolved rounding method is 'nearest'
            # if any argument has this attribute set.
            if any([x._signed for x in args]) or (ret := Rounding['nearest']) not in checkset:
                for rounding in Rounding: # pragma: no branch
                    if rounding in checkset:
                        ret = rounding
                        break

            # There's a mismatch, decide how to handle it base on mismatch_alert
            _, warner = self._mismatch_alert(*args, stacklevel=stacklevel + 1)
            warner("Non-matching rounding behaviors %s.",
                [val.name for val in checkset], stacklevel=stacklevel)
            warner("Using %r.", ret.name, stacklevel=stacklevel)

        return ret.name

    def overflow(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        '''Resolve overflow properties between 2 FixedPoint objects. If they
        don't match, then the priority is:
            1. clamp
            2. wrap
        A MismatchWarning is issued if they don't match.
        '''
        if len(checkset := {obj._overflow for obj in args}) == 1:
            ret = checkset.pop()
        else:
            ret = Overflow['clamp']

            # There's a mismatch, decide how to handle it base on mismatch_alert
            _, warner = self._mismatch_alert(*args, stacklevel=stacklevel + 1)
            warner("Non-matching overflow behaviors %s.",
                [val.name for val in checkset], stacklevel=stacklevel)
            warner("Using %r.", ret.name, stacklevel=stacklevel)

        return ret.name

    def all(self, *args: "FixedPoint", stacklevel: int = 4) -> Dict[str, Union[str, int]]:
        """Resolves all properties in the correct order.
        """
        level = stacklevel + 1
        ret: Dict[str, Union[str, int]] = {
            "mismatch_alert": self.mismatch_alert(*args, stacklevel=level)
        }
        self.__ignore_mismatch = True
        try:
            ret.update(
                {
                    "overflow": self.overflow(*args, stacklevel=level),
                    "rounding": self.rounding(*args, stacklevel=level),
                    "overflow_alert": self.overflow_alert(*args, stacklevel=level),
                    "implicit_cast_alert": self.implicit_cast_alert(*args, stacklevel=level),
                    "str_base": self.str_base(*args),
                }
            )
        finally:
            self.__ignore_mismatch = False
        return ret
