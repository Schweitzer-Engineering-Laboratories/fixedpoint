"""FixedPoint property validation and handling."""
from enum import Enum
from logging import ERROR, WARNING, DEBUG
from typing import (Callable, ClassVar, Mapping, Tuple, Union, TYPE_CHECKING)

__all__ = ('PROPERTIES', 'StrConv', 'StrBase', 'Alert', 'Overflow', 'Rounding',
           'PropertyResolver')

# Avoid circular imports
if TYPE_CHECKING:  # pragma: no cover
    from fixedpoint.fixedpoint import FixedPoint

PROPERTIES = ('str_base', 'mismatch_alert', 'overflow_alert',
              'implicit_cast_alert', 'overflow', 'rounding')

StrConv: Mapping[int, Callable[[int], str]] = {2: bin, 8: oct, 10: str, 16: hex}
StrBase = Enum('str_base',  # type: ignore # (too many arguments)
               {'0b': 2, '0o': 8, ' ': 10, '0x': 16},
               module=__name__, qualname="StrBase")

Alert = Enum('alert',  # type: ignore # (too many arguments)
             {'error': ERROR, 'warning': WARNING, 'ignore': DEBUG},
             module=__name__, qualname="Alert")

Overflow = Enum('overflow',  # type: ignore # (too many arguments)
                {'clamp': 100, 'wrap': 101},
                module=__name__, qualname="Overflow")

# This is especially ordered for signed numbers.
Rounding = Enum('rounding',  # type: ignore # (too many arguments)
                {'convergent': 200, 'nearest': 201, 'down': 202, 'in': 203,
                 'out': 204, 'up': 205}, module=__name__, qualname="Rounding")

Property = Union[StrBase, Alert, Overflow, Rounding]
ResolvedProps = Mapping[str, Union[str, int]]


class PropertyResolver:
    """Resolves properties between two FixedPoint objects."""

    __instance: ClassVar["PropertyResolver"]
    __ignore_mismatch: bool

    def __new__(cls) -> "PropertyResolver":
        """Initialize and force only a single instance."""
        try:
            cls.__instance
        except AttributeError:
            cls.__instance = super().__new__(cls)
            cls.__instance.__ignore_mismatch = False

        return cls.__instance

    def str_base(self, *args: "FixedPoint") -> int:
        """Resolve str_base properties between 2 FixedPoint objects.

        If they don't match, then 16 is used. No warning is issued.
        """
        if len(checkset := {obj._str_base.value for obj in args}) == 1:
            ret = checkset.pop()
        else:
            ret = 16

        return int(ret)

    def implicit_cast_alert(self, *args: "FixedPoint",
                            stacklevel: int = 4) -> str:
        """Resolve implicit_cast_alert properties between 2 FixedPoint objects.

        If they don't match, then the priority is:
            1. warning
            2. error
            3. ignore
        A MismatchWarning is issued if they don't match.
        """
        if len(checkset := {obj._implicit_cast_alert for obj in args}) == 1:
            ret = checkset.pop()
        # If there's a mismatch, handle it based on mismatch_alert property.
        else:
            ret = (Alert['warning'] if Alert['warning'] in checkset
                   else Alert['error'])
            _, warner = self._mismatch_alert(*args, stacklevel=stacklevel + 1)
            warner("Non-matching implicit_cast_alert behaviors %s.",
                   [alert.name for alert in checkset], stacklevel=stacklevel)
            warner("Using %r.", ret.name, stacklevel=stacklevel)

        return ret.name

    _ialert = implicit_cast_alert

    def overflow_alert(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        """Resolve overflow_alert properties between 2 FixedPoint objects.

        If they don't match, then the priority is:
            1. error
            2. warning
            3. ignore
        A MismatchWarning is issued if they don't match.
        """
        if len(checkset := {obj._overflow_alert for obj in args}) == 1:
            ret = checkset.pop()
        # If there's a mismatch, handle it based on mismatch_alert property.
        else:
            ret = (Alert['error'] if Alert['error'] in checkset else
                   Alert['warning'])
            _, warner = self._mismatch_alert(*args, stacklevel=stacklevel + 1)
            warner("Non-matching overflow_alert behaviors %s.",
                   [alert.name for alert in checkset], stacklevel=stacklevel)
            warner("Using %r.", ret.name, stacklevel=stacklevel)

        return ret.name

    _oalert = overflow_alert

    def _mismatch_alert(self, *args: "FixedPoint",
                        stacklevel: int = 5) -> Tuple[str, Callable[..., None]]:
        """Resolve mismatch_alert properties between 2 FixedPoint objects.

        If they don't match, the most severe alarm between them is triggered. As
        long as the triggered alert is not an error, the priority is:
            1. warning
            2. ignore
        """
        if len(set(checklist := [obj._mismatch_alert for obj in args])) == 1:
            alert = args[0]._mismatch_alert
            warnerfunc = args[0]._mwarn
        else:
            # First make sure the mismatches don't trigger a warning
            warner = args[0]._mwarn
            for name in ('error', 'warning'):  # pragma: no branch
                for i, alert in enumerate(checklist):
                    if alert == Alert[name]:
                        warner = args[i]._mwarn
                        break
                else:
                    continue
                break

            # Prioritize for return value
            for name in ('warning', 'error'):  # pragma: no branch
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
        """Resolve mismatch_alert properties between 2 FixedPoint objects.

        If they don't match, the most severe alarm between them is triggered. As
        long as the triggered alert is not an error, the priority is:
            1. warning
            2. ignore
        """
        return self._mismatch_alert(*args, stacklevel=stacklevel + 1)[0]

    _malert = mismatch_alert

    def rounding(self, *args: "FixedPoint", stacklevel: int = 4) -> str:
        """Resolve rounding properties between 2 FixedPoint objects.

        If they don't match, then the priority is:
            1. convergent if either are signed, nearest otherwise
            2. nearest if either are signed, convergent otherwise
            3. down
            4. in
            5. out
            6. up
        A MismatchWarning is issued if they don't match.
        """
        if len(checkset := {obj._rounding for obj in args}) == 1:
            ret = checkset.pop()
        else:
            # If all values are unsigned, resolved rounding method is 'nearest'
            # if any argument has this attribute set.
            if any([x._signed for x in args]) or \
                    (ret := Rounding['nearest']) not in checkset:
                for rounding in Rounding:  # pragma: no branch
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
        """Resolve overflow properties between 2 FixedPoint objects.

        If they don't match, then the priority is:
            1. clamp
            2. wrap
        A MismatchWarning is issued if they don't match.
        """
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

    def all(self, *args: "FixedPoint", stacklevel: int = 4) -> ResolvedProps:
        """Resolve all properties."""
        ret: ResolvedProps
        if len(args) == 1:
            ret = {p: getattr(args[0], p) for p in PROPERTIES}
        else:
            kwargs = dict(stacklevel=stacklevel + 1)
            ret = dict(mismatch_alert=self._malert(*args, **kwargs))
            self.__ignore_mismatch = True
            try:
                ret["overflow"] = self.overflow(*args, **kwargs)
                ret["rounding"] = self.rounding(*args, **kwargs)
                ret["overflow_alert"] = self._oalert(*args, **kwargs)
                ret["implicit_cast_alert"] = self._ialert(*args, **kwargs)
                ret["str_base"] = self.str_base(*args)
            finally:
                self.__ignore_mismatch = False
        return ret
