#!/usr/bin/env python3
"""JSON encoding and decoding classes."""
import json
from typing import Any, List, TYPE_CHECKING, cast

import fixedpoint.properties

__all__ = ('FixedPointEncoder', 'FixedPointDecoder',
           'DEFAULT_ENCODER', 'DEFAULT_DECODER')

if TYPE_CHECKING:  # pragma: no cover
    from fixedpoint.fixedpoint import FixedPoint
properties = fixedpoint.properties.PropertyResolver().all


class FixedPointEncoder(json.JSONEncoder):
    """Encodes a FixedPoint object into a JSON object."""

    def default(self, o: "FixedPoint") -> List[Any]:
        """Generate a JSON-serializable object for FixedPoint object o."""
        return [properties(o), [bool(o._signed), o._m, o._n], o._bits]

    def encode(self, o: "FixedPoint") -> str:
        """Return a JSON string representation of a FixedPoint object o."""
        return super().encode(self.default(o))


class FixedPointDecoder(json.JSONDecoder):
    """Decodes a JSON object into a FixedPoint object."""

    def decode_attributes(self, s: str, *args: Any) -> List[Any]:
        """Decode a JSON string `s` but return a list of attributes.

        Can be used directly in FixedPoint instantiation.
        """
        return cast(List[Any], super().decode(s, *args))

    def decode(self, s: str, *args: Any, **kwargs: Any) -> "FixedPoint":
        """Decode a JSON document string s into a FixedPoint object."""
        largs = self.decode_attributes(s, *args)
        from fixedpoint import FixedPoint
        return FixedPoint(hex(largs.pop()), *largs.pop(),
                          **largs.pop())


DEFAULT_ENCODER = FixedPointEncoder(separators=(',', ':'))
DEFAULT_DECODER = FixedPointDecoder()
