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
"""
JSON encoder and decoder for FixedPoint object.

>>> import json, fixedpoint
>>> x = fixedpoint.FixedPoint(1/3)
>>> j = json.dumps(x, cls=fixedpoint.json.FixedPointEncoder)
>>> y = json.loads(j, cls=fixedpoint.json.FixedPointDecoder)
>>> x == y
True

"""
import json
from typing import (
    Any,
    Dict,
    List,
    Union,
    TYPE_CHECKING,
)

from fixedpoint.properties import PROPERTIES as _PROPERTIES

if TYPE_CHECKING: # pragma: no cover
    from fixedpoint.fixedpoint import FixedPoint

class FixedPointEncoder(json.JSONEncoder):
    """Encodes a FixedPoint object into a JSON object.
    """
    def default(self, o: "FixedPoint") -> List[Union[Dict[str, Union[str, int]], List[Union[int, bool]], int]]:
        """Generates a JSON-serializable object for FixedPoint object o.
        """
        return [
            {
                'str_base': o._str_base.value,
                'mismatch_alert': o._mismatch_alert.name,
                'overflow_alert': o._overflow_alert.name,
                'implicit_cast_alert': o._implicit_cast_alert.name,
                'overflow': o._overflow.name,
                'rounding': o._rounding.name,
            },
            [
                bool(o._signed),
                o._m,
                o._n,
            ],
            o._bits,
        ]

    def encode(self, o: "FixedPoint") -> str:
        """Returns a JSON string representation of a FixedPoint object o.
        """
        return super().encode(self.default(o))

class FixedPointDecoder(json.JSONDecoder):
    """Decodes a JSON object and returns a FixedPoint object.
    """
    def decode_attributes(self, s: str, *args: Any) -> List[Union[Dict[str, Union[str, int]], List[Union[int, bool]], int]]:
        ret: List[Union[Dict[str, Union[str, int]], List[Union[int, bool]], int]] = super().decode(s, *args)
        return ret

    def decode(self, s: str, *args: Any, **kwargs: Any) -> "FixedPoint":
        """Decodes a JSON document string s into a FixedPoint object.
        """
        largs = self.decode_attributes(s, *args)
        from fixedpoint import FixedPoint
        return FixedPoint(hex(largs.pop()), *largs.pop(), **largs.pop()) # type: ignore


DEFAULT_ENCODER = FixedPointEncoder(separators=(',', ':'))
DEFAULT_DECODER = FixedPointDecoder()
