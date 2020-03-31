"""FixedPoint class."""
import logging
from math import log2 as _log2, ceil as _ceil
import sys
import operator
from typing import (Any, Callable, cast, ClassVar, Dict, List, Literal,
                    Mapping, overload, Tuple, Type, TypeVar, Union)

from fixedpoint.properties import (StrBase, StrConv, Alert, Overflow, Rounding,
                                   ResolvedProps, PropertyResolver)
from fixedpoint.logging import WARNER, LOGGER
from fixedpoint.json import DEFAULT_ENCODER, DEFAULT_DECODER

__all__ = ('FixedPoint',)

FixedPointType = TypeVar("FixedPointType", bound="FixedPoint")
Numeric = Union[FixedPointType, int, float]
Integral = Union[FixedPointType, int, bool]
AttrReturn = Tuple[int, bool, int, int]
_MAXEXPONENT = max(abs(sys.float_info.max_exp), abs(sys.float_info.min_exp))


def _sn(__id: Mapping[str, object]) -> int:
    """Extract the serial number from the nested __id dict.

    https://stackoverflow.com/questions/54786574/mypy-error-on-dict-of-dict-value-of-type-object-is-not-indexable
    """
    return cast(Mapping[str, int], __id['extra'])['sn']


class FixedPointBits(int):
    """Allow for slicing and mapping into FixedPoint.bits."""
    s: bool
    m: int
    n: int

    def __new__(cls, bits: int, s: bool, m: int, n: int) -> "FixedPointBits":
        # https://github.com/python/typeshed/issues/2686
        ret: "FixedPointBits" = super().__new__(cls, bits)  # type: ignore
        ret.s, ret.m, ret.n = s, m, n
        return ret

    @overload
    def __getitem__(self, key: Union[Literal['M'], Literal['INT'],
                                     Literal['N'], Literal['FRAC'],
                                     Literal['S'], Literal['SIGN'],
                                     Literal['MSB'], Literal['LSB']]) -> str:
        ...  # pragma: no cover

    @overload
    def __getitem__(self, key: Union[int, slice,
                                     Literal['m'], Literal['int'],
                                     Literal['n'], Literal['frac'],
                                     Literal['s'], Literal['sign'],
                                     Literal['msb'], Literal['lsb']]) -> int:
        ...  # pragma: no cover

    def __getitem__(self, key: Union[int, slice, str]) -> Union[str, int]:
        """Random access to one or more bits.

        Access a single bit with an int key.
        Access multiple bits with a slice key.
        Access a common bit slice with a str key (uppercase to return binary
                bit str, lowercase to return int):
            * x['m'] or x['int'] gives the integer bits. A KeyError is raised
              if there are no integer bits.
            * x['n'] or x['frac'] gives the fractional bits. A KeyError is
              raised if there are no fractional bits
            * x['s'] or x['sign'] gives the sign bit for signed numbers. A
              KeyError is raised for unsigned numbers
            * x['msb'] gives the most significant bit
            * x['lsb'] gives the least significant bit
        """
        # Single bit; LSb is index 0
        if isinstance(key, int):
            if not -(L := self.m + self.n) <= key < L:
                raise IndexError(f"Bit {key} does not exist in "
                                 f"{'' if self.s else 'U'}Q{self.m}.{self.n} "
                                 "format.")
            return (self.real >> abs(key + (key < 0))) & 1

        # Get the binary string
        string = f"{self.real:0{self.m + self.n}b}"
        strret = False

        # Special bit masks
        if isinstance(key, str):
            if (lkey := key.lower()) in ['m', 'int'] and self.m:
                ret = string[:self.m]
            elif lkey in ['n', 'frac'] and self.n:
                ret = string[-self.n:]
            elif lkey == 'msb' or (self.s and lkey in ['s', 'sign']):
                ret = string[0]
            elif lkey == 'lsb':
                ret = string[-1]
            else:
                raise KeyError(f"Invalid bit specification {key!r} for "
                               f"{'' if self.s else 'U'}Q{self.m}.{self.n} "
                               "format.")
            strret = all(ord('A') <= ord(c) <= ord('Z') for c in key)

        elif isinstance(key, slice):
            # With a key of 1, -1, or None,
            # LSb is index 0 when start > stop
            # MSb is index 0 when start < stop
            if isinstance(key.start, int) and isinstance(key.stop, int) and \
                    key.start >= 0 and key.stop >= 0 and \
                    key.step in [-1, None, 1]:
                # Ascending range
                if key.start < key.stop or \
                        (key.start == key.stop and key.step == 1):
                    ret = string[key.start : key.stop + 1]
                # Descending range
                elif key.start > key.stop or \
                        (key.start == key.stop and key.step == -1):
                    ret = (string[::-1][key.stop:key.start + 1])[::-1]
                else:
                    raise IndexError(f"Step must be 1 or -1 for equivalent "
                                     f"start and stop bound {key.start}.")

            # With a key that's not 1 or -1, treat the bits as a binary string
            else:
                ret = string[key]
        else:
            raise TypeError(f"{type(key)} not supported.")

        # For (example) FixedPoint(-1,1,1,0), x[1:] is an empty string.
        if strret:
            return ret
        return int(ret, 2) if ret else 0


class FixedPoint:
    """Fixed point number."""

    __slots__ = ('_bits', '_signed', '_m', '_n', '_str_base', '_overflow',
                 '_rounding', '_overflow_alert', '_implicit_cast_alert',
                 '_mismatch_alert', '__id', '__cmstack', '__context')
    _RESOLVE: ClassVar[PropertyResolver]  # Resolves properties for new objects
    _SERIAL_NUMBER: ClassVar[int]  # Logging aid
    _bits: int  # Raw bits of the fixed point number
    _signed: bool  # Signed or unsigned
    _m: int  # Integer bit width
    _n: int  # Fractional bit width
    _str_base: StrBase  # Base of str() conversion
    _overflow: Overflow  # Overflow scheme
    _rounding: Rounding  # Rounding scheme
    _overflow_alert: Alert  # Overflow notification scheme
    _implicit_cast_alert: Alert  # Implicit cast notification scheme
    _mismatch_alert: Alert  # Property mismatch notification scheme
    __id: Mapping[str, Union[int, Mapping[str, int]]]  # Logging aid
    __cmstack: List[Any]  # Context manager stack
    __context: Dict[str, Union[bool, int, str]]  # Context manager initial vals

    def __new__(cls: Type[FixedPointType], init: Union[Numeric, str], /,
                signed: bool = None, m: int = None, n: int = None, *,
                overflow: str = 'clamp', rounding: str = 'auto',
                str_base: int = 16, overflow_alert: str = 'error',
                implicit_cast_alert: str = 'warning',
                mismatch_alert: str = 'warning') -> FixedPointType:
        """Initialize class variables and generate instance."""
        try:
            cls._SERIAL_NUMBER += 1
            cls._RESOLVE
        except AttributeError:
            cls._RESOLVE = PropertyResolver()
            cls._SERIAL_NUMBER = 1
        finally:
            inst: FixedPointType = super().__new__(cls)

        return inst

    @classmethod
    def __new(cls: Type[FixedPointType], bits: int, signed: bool, m: int,
              n: int, overflow: str, rounding: str, str_base: int,
              overflow_alert: str, implicit_cast_alert: str,
              mismatch_alert: str) -> FixedPointType:
        """Quick initialization for internal computations."""
        self: FixedPointType = super().__new__(cls)
        cls._SERIAL_NUMBER += 1
        self._bits = bits
        self._signed = signed
        self._m = m
        self._n = n
        self._overflow = Overflow[overflow]
        self._rounding = Rounding[rounding]
        self._str_base = StrBase(str_base)
        self._overflow_alert = Alert[overflow_alert]
        self._mismatch_alert = Alert[mismatch_alert]
        self._implicit_cast_alert = Alert[implicit_cast_alert]
        self.__cmstack = []
        self.__context = {}
        self.__id = {'stacklevel': 2, 'extra': {'sn': cls._SERIAL_NUMBER}}
        return self

    def __getnewargs__(self: FixedPointType) -> Tuple[str]:
        """Support pickling with positional-only arguments."""
        return (hex(self._bits),)

    ###########################################################################
    # Initialization methods
    ###########################################################################
    def __init__(self: FixedPointType,
                 init: Union[Numeric, str],
                 /,
                 signed: bool = None,
                 m: int = None,
                 n: int = None,
                 *,
                 overflow: str = 'clamp',
                 rounding: str = 'auto',
                 str_base: int = 16,
                 overflow_alert: str = 'error',
                 implicit_cast_alert: str = 'warning',
                 mismatch_alert: str = 'warning') -> None:
        """Initialize FixedPoint attributes and properties."""
        self.__id = {'stacklevel': 2,
                     'extra': {'sn': self.__class__._SERIAL_NUMBER}}

        # Type validation
        initialize: Callable[..., None]
        if isinstance(init, str):
            initialize = self.from_string
            if signed is None or m is None or n is None:
                raise ValueError("String literal initialization "
                                 "Q format must be fully constrained.")
        elif isinstance(init, int):
            initialize = self.from_int
        elif not isinstance(init, FixedPoint):
            initialize = self.from_float
            try:
                init = float(init)
            except Exception:
                raise TypeError(f"Unsupported type {type(init)}; cannot "
                                "convert to float.")

        # Internally used variables
        self.__cmstack = []
        self.__context = {}

        # Copy attributes into a new object
        if isinstance(init, FixedPoint):
            for attr in [x for x in init.__slots__ if '__' not in x]:
                setattr(self, attr, getattr(init, attr))
            self._log("Copied from SN %d", _sn(init.__id))
            return

        # Change typing for subsequent processing
        numeric: Union[int, float] = init  # type: ignore

        # Qualify Q format (bit widths and signedness)
        if signed is None:
            signed = numeric < 0

        # min_m will account for worst case rounding; So if bit widths were not
        # specified, trim excess bits off
        trim_n = n is None
        if trim_n:
            _n = self.__class__.min_n(numeric)
            self._log('Deduced fractional length: %d', _n)
        else:
            if (_n := cast(int, n)) < 0:
                raise ValueError("Number of fractional bits "
                                 "must be non-negative.")

        trim_m = m is None
        _m: int
        if trim_m:
            _m = self.__class__.min_m(numeric, signed)
            _m += (_m + _n) == 0
            self._log('Deduced integer length: %d', _m)
        else:
            if (_m := cast(int, m)) < bool(signed):
                raise ValueError("Number of integer bits must be " +
                                 ("at least 1 for signed numbers." if signed
                                  else "non-negative."))

        if _m + _n == 0:
            raise ValueError("Word size (integer and fractional) "
                             "must be positive.")

        self._signed = bool(signed)
        self._m = int(_m)
        self._n = int(_n)

        # Determine rounding method if not specified
        if rounding == 'auto':
            rounding = 'convergent' if signed else 'nearest'

        # Assign/validate properties
        self._str_base = StrBase(str_base)
        self._mismatch_alert = Alert[mismatch_alert]
        self._overflow_alert = Alert[overflow_alert]
        self._implicit_cast_alert = Alert[implicit_cast_alert]
        self._overflow = Overflow[overflow]
        self._rounding = Rounding[rounding]

        self._log('%s\n'
                  "intended: %r\n"
                  "Q format: %s\n"
                  "overflow: %s\n"
                  "rounding: %s\n"
                  "overflow_alert: %s\n"
                  "mismatch_alert: %s\n"
                  "implicit_cast_alert: %s\n"
                  "str_base: %d",
                  '-' * 80,
                  init,
                  self.qformat,
                  self.overflow,
                  self.rounding,
                  self.overflow_alert,
                  self.mismatch_alert,
                  self.implicit_cast_alert,
                  self.str_base)

        initialize(init)
        self.trim(trim_m, trim_n)

    def from_string(self: FixedPointType, string: str, /) -> None:
        """Initialize a FixedPoint object from a string literal.

        No rounding or overflow handling occurs.
        No more than Len(self) set bits are allowed.
        """
        if not isinstance(string, str):
            raise TypeError(f"Expected {type('')}; got {type(string)}.")

        val = int(string, 0)
        bits = val & self.bitmask
        if bits != val:
            raise ValueError("Superfluous bits detected in string literal "
                             f"{string!r} for {self.qformat} format.")
        self._bits = bits

    from_str = from_string

    def from_int(self: FixedPointType, integer: int, /) -> None:
        """Initialize a FixedPoint object from an integer value.

        Overflow handling occurs. Rounding does not.
        """
        if not isinstance(integer, int):
            raise TypeError(f"Expected {type(1)}; got {type(integer)}.")

        bits = integer << self._n

        self._log("MIN: % d\nINT: % d\nMAX: % d",
                  minimum := self._minimum, bits, maximum := self._maximum)

        if not minimum <= bits <= maximum:
            self._owarn("Integer %d overflows in %s format.", integer,
                        self.qformat)
            clamp = self._overflow == Overflow['clamp']
            self._owarn("%s %s.", 'Clamped to' if clamp else 'Wrapped',
                        extreme := ('minimum' if integer < 0 else 'maximum'))

            # Handle overflow
            if clamp:
                bits = getattr(self, f"_{extreme}")

        self._bits = bits & self.bitmask

    def from_float(self: FixedPointType, val: float, /) -> None:
        """Initialize a FixedPoint object from a floating point value.

        Rounding and overflow handling occurs.
        """
        if not isinstance(val, float):
            raise TypeError(f"Expected {type(1.0)}; got {type(val)}.")

        # Shift fractional bits to the left of the binary point
        bits = int(val * 2**self._n)

        # Round if no need for clamping
        if self._minfloat <= val <= self._maxfloat:
            bits &= self.bitmask
            # Fake an extra 2 bits so we can use class methods for rounding
            n = self._n
            if frac := abs(val * 2**n) % 1.0:
                self._n = n + 2
                bits <<= 2
                if val < 0.0:
                    bits -= 0b100
                    bitmask = 0b11 if frac < 0.5 else 0b01
                else:
                    bitmask = 0b01 if frac < 0.5 else 0b11
                if frac == 0.5:
                    bitmask = 0b10
                self._bits = bits | bitmask
                getattr(self, f"round_{self.rounding}")(n)
            else:
                self._bits = bits

        # We must clamp
        else:
            self._owarn("%e overflows in %s format.", val, self.qformat)
            clamp = self._overflow == Overflow['clamp']
            self._owarn("%s %s.", 'Clamped to' if clamp else 'Wrapped',
                        extreme := ('minimum' if val < 0 else 'maximum'))

            if clamp:
                bits = getattr(self, f'_{extreme}')

            self._bits = bits & self.bitmask

    ###########################################################################
    # Property accessors and mutators
    ###########################################################################
    @property
    def signed(self: FixedPointType) -> bool:
        """Retrieve signedness."""
        return self._signed

    @signed.setter
    def signed(self: FixedPointType, val: bool) -> None:
        """Change signedness. Bit widths remain the same.

        Overflow handling occurs.
        """
        # If we're not actually changing sign, exit
        if (val := bool(val)) == bool(signed := self._signed):
            return

        # We must have an integer bit to change sign
        if self._m == 0 and val:
            from fixedpoint import FixedPointError
            raise FixedPointError("Cannot change sign with 0 integer bits.")

        # If the msb is 0, overflow won't happen.
        if self.bits['msb'] == 0:
            self._signed = val
            return

        # If we're currently signed, we underflow, otherwise we overflow.
        extreme = 'minimum' if signed else 'maximum'
        clamp = self._overflow == Overflow['clamp']

        # Generate warning
        self._owarn("Changing signedness on %s causes overflow.", self)
        self._owarn("%s %s.", 'Clamped to' if clamp else 'Wrapped', extreme)

        # Handle overflow
        self._signed = val
        if clamp:
            self._bits = self.bitmask & getattr(self, f"_{extreme}")

    # _________________________________________________________________________
    @property
    def m(self: FixedPointType) -> int:
        """Retrieve the integer bit width."""
        return self._m

    @m.setter
    def m(self: FixedPointType, nbits: int) -> None:
        """Set the integer bit width.

        Overflow handling or sign-extension occurs.
        """
        if not isinstance(nbits, int):
            raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")

        if nbits < int(self._signed):
            raise ValueError("Number of integer bits must be " +
                             ("positive for signed numbers."
                              if self._signed else "non-negative."))
        if nbits + self._n == 0:
            raise ValueError("Word size (integer and fractional) "
                             "must be positive.")

        # Number of integer bits are growing, do sign extension.
        if (nintbits := nbits - self._m) > 0 and self._negweight():
            shift = self._m + self._n
            self._bits |= (2**nintbits - 1) << (self._m + self._n)

        # Number of integer bits are shrinking, handle overflow
        elif nintbits < 0:
            getattr(self, self.overflow)(nbits)
        self._m = int(nbits)

    # _________________________________________________________________________
    @property
    def n(self: FixedPointType) -> int:
        """Retrieve the fractional bit width."""
        return self._n

    @n.setter
    def n(self: FixedPointType, nbits: int) -> None:
        """Set the fractional bit width. Rounding occurs."""
        if not isinstance(nbits, int):
            raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")

        if nbits < 0:
            raise ValueError("Number of fractional bits must be non-negative.")
        if self._m + nbits == 0:
            raise ValueError("Word size (integer and fractional) "
                             "must be positive.")

        # Number of fractional bits are growing, just shift in s'more bits
        if (nfracbits := nbits - self._n) >= 0:
            self._bits <<= nfracbits

        # Fractional bits count is shrinking, round
        else:
            self.round(nbits)

        self._n = int(nbits)

    # _________________________________________________________________________
    @property
    def str_base(self: FixedPointType) -> int:
        """Retrieve the str_base property setting."""
        return int(self._str_base.value)

    @str_base.setter
    def str_base(self: FixedPointType, base: int) -> None:
        """Set the str_base property setting."""
        try:
            self._str_base = StrBase(base)
        except ValueError:
            raise ValueError(f"Invalid str_base setting: {base!r}.")

    # _________________________________________________________________________
    @property
    def overflow_alert(self: FixedPointType) -> str:
        """Retrieve the overflow_alert property setting."""
        return self._overflow_alert.name

    @overflow_alert.setter
    def overflow_alert(self: FixedPointType, level: str) -> None:
        """Set overflow alert notification behavior."""
        try:
            self._overflow_alert = Alert[level]
        except KeyError:
            raise ValueError(f"Invalid overflow_alert setting: {level!r}.")

    # _________________________________________________________________________
    @property
    def implicit_cast_alert(self: FixedPointType) -> str:
        """Retrieve the implicit_cast_alert property setting."""
        return self._implicit_cast_alert.name

    @implicit_cast_alert.setter
    def implicit_cast_alert(self: FixedPointType, level: str) -> None:
        """Set implicit cast alert notification behavior."""
        try:
            self._implicit_cast_alert = Alert[level]
        except KeyError:
            raise ValueError(f"Invalid implicit_cast_alert setting: {level!r}.")

    # _________________________________________________________________________
    @property
    def mismatch_alert(self: FixedPointType) -> str:
        """Retrieve the mismatch_alert property setting."""
        return self._mismatch_alert.name

    @mismatch_alert.setter
    def mismatch_alert(self: FixedPointType, level: str) -> None:
        """Set the property mismatch alert notification behavior."""
        try:
            self._mismatch_alert = Alert[level]
        except KeyError:
            raise ValueError(f"Invalid mismatch_alert setting: {level!r}.")

    # _________________________________________________________________________
    @property
    def rounding(self: FixedPointType) -> str:
        """Retrieve the rounding scheme property setting."""
        return self._rounding.name

    @rounding.setter
    def rounding(self: FixedPointType, scheme: str) -> None:
        """Set the rounding scheme property setting."""
        try:
            self._rounding = Rounding[scheme]
        except KeyError:
            raise ValueError(f"Invalid rounding setting: {scheme!r}.")

    # _________________________________________________________________________
    @property
    def overflow(self: FixedPointType) -> str:
        """Retrieve the overflow handling property setting."""
        return self._overflow.name

    @overflow.setter
    def overflow(self: FixedPointType, scheme: str) -> None:
        """Set the overflow handling property setting."""
        try:
            self._overflow = Overflow[scheme]
        except KeyError:
            raise ValueError(f"Invalid overflow setting: {scheme!r}.")

    ###########################################################################
    # Public properties and built-in property methods
    ###########################################################################
    @property
    def clamped(self: FixedPointType) -> bool:
        """Indicate saturation to minimum or maximum value."""
        return self._bits in [abs(self._minimum), self._maximum]

    @property
    def qformat(self: FixedPointType) -> str:
        """Q format indicating signedness, and integer/fractional bit width."""
        return f"{'' if self._signed else 'U'}Q{self._m}.{self._n}"

    @property
    def bitmask(self: FixedPointType) -> int:
        """Bitmask for the current Q format."""
        return int(2**(self._m + self._n) - 1)

    @property
    def bits(self: FixedPointType) -> FixedPointBits:
        """Raw FixedPoint bits."""
        return FixedPointBits(self._bits, self._signed, self._m, self._n)

    def __len__(self: FixedPointType) -> int:
        """Sum of integer and fractional bit widths."""
        return self._m + self._n

    ###########################################################################
    # Private properties
    ###########################################################################
    @property
    def _minimum(self: FixedPointType) -> int:
        """Minimum representable bit value."""
        return int(2**(self._m + self._n - 1) * -bool(self._signed))

    @property
    def _maximum(self: FixedPointType) -> int:
        """Maximum representable bit value."""
        return int(2**(self._m + self._n - bool(self._signed)) - 1)

    @property
    def _signedint(self: FixedPointType) -> int:
        """Signed version of _bits."""
        return (self._bits & self._maximum) + self._negweight()

    @property
    def _maxfloat(self: FixedPointType) -> float:
        """Maximum representable floating point number."""
        return float(self._maximum * 2**-self._n)

    @property
    def _minfloat(self: FixedPointType) -> float:
        """Minimum representable floating point number."""
        return float(self._minimum * 2**-self._n)

    def _negweight(self: FixedPointType, bits: int = None,
                   signed: bool = None, m: int = None, n: int = None) -> int:
        """Only the negative weight. Uses self's attributes for the Nones."""
        bits = self._bits if bits is None else bits
        signed = bool(self._signed if signed is None else signed)
        m = self._m if m is None else m
        n = self._n if n is None else n
        ret = 2**(m + n - 1) & bits
        return int(ret * -signed)

    def _posweight(self: FixedPointType, bits: int = None,
                   signed: bool = None, m: int = None, n: int = None) -> int:
        """Only the positive weight. Uses self's attributes for the Nones."""
        bits = self._bits if bits is None else bits
        signed = bool(self._signed if signed is None else signed)
        m = self._m if m is None else m
        n = self._n if n is None else n
        mask = 2**(m + n - signed) - 1
        return int(mask & bits)

    ###########################################################################
    # Operators
    # https://www.factmonster.com/math-science/mathematics/terms-used-in-equations
    ###########################################################################
    # _________________________________________________________________________
    # Arithmetic (normal, augmented, and reflected) operators
    def __unsupported(*args: Any, **kwargs: Any) -> NotImplemented:
        """Unsupported FixedPoint method."""
        return NotImplemented

    # For future reference, in case division is needed:
    # https://courses.cs.washington.edu/courses/cse467/08au/labs/l5/fp.pdf
    __floordiv__ = __rfloordiv__ = __ifloordiv__ = __unsupported
    __truediv__ = __rtruediv__ = __itruediv__ = __unsupported
    __matmul__ = __rmatmul__ = __imatmul__ = __unsupported
    __mod__ = __rmod__ = __imod__ = __unsupported
    __rlshift__ = __rrshift__ = __unsupported
    __divmod__ = __rdivmod__ = __unsupported
    __rpow__ = __unsupported

    def __to_FixedPoint(self: FixedPointType, num: Numeric,
                        signed: bool = None) -> FixedPointType:
        """Return a FixedPoint version of num."""
        ret: FixedPointType
        if isinstance(num, self.__class__):
            ret = num  # Note that signed does not take affect here
        else:
            ret = self.__class__(num, signed)
            if isinstance(num, float) and (error := abs(num - float(ret))):
                self._iwarn("Casting %r to %s introduces an error of %e",
                            num, ret.qformat, error, stacklevel=3)
        return ret

    def __to_FixedPoint_resolved(self: FixedPointType, num: Numeric,
                                 signed: bool = None) -> Tuple[FixedPointType,
                                                               ResolvedProps]:
        """Return a FixedPoint version of num, with resolved properties."""
        props: ResolvedProps = (self.__class__._RESOLVE.all(self, num)
                                if isinstance(num, self.__class__) else
                                self.__class__._RESOLVE.all(self))
        return self.__to_FixedPoint(num, signed), props

    def __add(augend: FixedPointType, addend: FixedPointType) -> AttrReturn:
        """Perform addition and return attributes of the result."""
        with augend, addend:
            # Determine the Q format of the sum
            n: int = max(augend._n, addend._n)
            m: int = max(augend._m, addend._m) + 1
            signed: bool = bool(augend._signed or addend._signed)

            # Align binary points
            augend.n, addend.n = n, n

            # Sum some
            bits: int = (2**(m + n) - 1) & \
                (augend._posweight() + addend._posweight() +
                 augend._negweight() + addend._negweight())

        return bits, signed, m, n

    def __add__(self: FixedPointType, other: Numeric) -> FixedPointType:
        """Full precision addition operator."""
        fother, props = self.__to_FixedPoint_resolved(other)
        return self.__class__.__new(*self.__add(fother), **props)

    def __iadd__(self: FixedPointType, addend: Numeric) -> FixedPointType:
        """Full precision augmented addition operator."""
        other = self.__to_FixedPoint(addend)
        self._bits, self._signed, self._m, self._n = self.__add(other)
        return self

    def __sub(minuend: FixedPointType, subtrahend: FixedPointType,
              overflow: str, owarner: Callable[..., None]) -> AttrReturn:
        """Perform subtraction and return attributes of the result."""
        with minuend, subtrahend:
            # Determine the Q format of the difference
            signed: bool = minuend._signed or subtrahend._signed
            sign_mismatch: bool = minuend._signed ^ subtrahend._signed
            m: int = 1 + max(minuend._m, subtrahend._m) + sign_mismatch
            n: int = max(minuend._n, subtrahend._n)

            # Align binary points and properties
            minuend.resize(m, n)
            subtrahend.resize(m, n)
            minuend._signed, subtrahend._signed = signed, signed

            # Subtract some
            bits: int = minuend._posweight() + minuend._negweight() \
                - subtrahend._posweight() - subtrahend._negweight()

        # Check overflow condition
        if not signed and bits < 0:
            owarner("Unsigned subtraction causes overflow.")
            if clamp := (overflow == 'clamp'):
                bits = 0
            owarner("%s minimum.", "Clamped to" if clamp else "Wrapped")

        return bits & (2**(m + n) - 1), signed, m, n

    def __sub__(self: FixedPointType, other: Numeric) -> FixedPointType:
        """Full precision subtraction operator."""
        subtrahend, props = self.__to_FixedPoint_resolved(other, self._signed)

        # Because overflow may occur, make sure the object with the highest
        # priority overflow_alert is used for the warning.
        warner = self._owarn if props['overflow_alert'] == self.overflow \
            else subtrahend._owarn
        return self.__class__.__new(*self.__sub(subtrahend,
                                                cast(str, props['overflow']),
                                                warner), **props)

    def __rsub__(self: FixedPointType, minuend: Numeric) -> FixedPointType:
        """Full precision reflected subtraction."""
        other = self.__to_FixedPoint(minuend, self._signed)
        return self.__class__.__new(*other.__sub(self, self.overflow,
                                                 self._owarn),
                                    self.overflow, self.rounding, self.str_base,
                                    self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __isub__(self: FixedPointType, subtrahend: Numeric) -> FixedPointType:
        """Full precision augmented subtraction operator."""
        other = self.__to_FixedPoint(subtrahend, self._signed)
        self._bits, self._signed, self._m, self._n = \
            self.__sub(other, self.overflow, self._owarn)
        return self

    def __mul(multiplicand: FixedPointType,
              multiplier: FixedPointType) -> AttrReturn:
        """Perform multiplication and return attributes of the result."""
        m: int = multiplicand._m + multiplier._m
        n: int = multiplicand._n + multiplier._n
        signed: bool = bool(multiplicand._signed or multiplier._signed)
        bits = multiplicand._signedint * multiplier._signedint
        return bits & (2**(m + n) - 1), signed, m, n

    def __mul__(self: FixedPointType, other: Numeric) -> FixedPointType:
        """Full precision multiplication operator."""
        multiplier, props = self.__to_FixedPoint_resolved(other)
        return self.__class__.__new(*self.__mul(multiplier), **props)

    def __imul__(self: FixedPointType, multiplier: Numeric) -> FixedPointType:
        """Full precision augmented multiplication operator."""
        other = self.__to_FixedPoint(multiplier)
        self._bits, self._signed, self._m, self._n = self.__mul(other)
        return self

    def __pow(self: FixedPointType, exponent: int) -> AttrReturn:
        """Perform exponentiation and return attributes of the result."""
        if not (isinstance(exponent, int) and exponent > 0):
            raise TypeError("Only positive integers are supported "
                            "for exponentiation.")
        m: int = self._m * exponent
        n: int = self._n * exponent
        signed: bool = self._signed
        return self._signedint**exponent & (2**(m + n) - 1), signed, m, n

    def __pow__(self: FixedPointType, exponent: int) -> FixedPointType:
        """Full precision exponentiation operator."""
        return self.__class__.__new(*self.__pow(exponent), self.overflow,
                                    self.rounding, self.str_base,
                                    self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __ipow__(self: FixedPointType, exponent: int) -> FixedPointType:
        """Full precision augmented exponentiation operator."""
        self._bits, self._signed, self._m, self._n = self.__pow(exponent)
        return self

    def __bitshift(self: FixedPointType, nbits: int) -> int:
        """Perform bit shifting and return the new bits."""
        if not isinstance(nbits, int):
            raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")
        shift = operator.lshift if nbits < 0 else operator.rshift
        return cast(int, shift(self._signedint, abs(nbits)) & self.bitmask)

    def __lshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Literal left shift."""
        return self.__class__.__new(self.__bitshift(-nbits), self._signed,
                                    self._m, self._n, self.overflow,
                                    self.rounding, self.str_base,
                                    self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __ilshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Augmented literal left shift."""
        self._bits = self.__bitshift(-nbits)
        return self

    def __rshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Literal right shift."""
        return self.__class__.__new(self.__bitshift(+nbits), self._signed,
                                    self._m, self._n, self.overflow,
                                    self.rounding, self.str_base,
                                    self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __irshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Augmented literal right shift."""
        self._bits = self.__bitshift(+nbits)
        return self

    @classmethod
    def __getbits(cls: Type[FixedPointType], obj: Integral) -> int:
        """Retrieve bits of integer or FixedPoint types."""
        ret: int
        if isinstance(obj, cls):
            ret = obj._bits
        elif isinstance(obj, int):
            ret = obj
        else:
            raise TypeError(f"Expected {type(1)} or {cls}; got {type(obj)}.")
        return ret

    def __bitwise(self: FixedPointType, operand: Integral,
                  operate: Callable[[int, int], int]) -> int:
        """Bitwise operator on integer or FixedPoint types."""
        return operate(self._bits,
                       self.__class__.__getbits(operand)) & self.bitmask

    def __and__(self: FixedPointType, other: Integral) -> FixedPointType:
        """Bitwise AND."""
        return self.__class__.__new(self.__bitwise(other, operator.__and__),
                                    self._signed, self._m, self._n,
                                    self.overflow, self.rounding,
                                    self.str_base, self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __iand__(self: FixedPointType, other: Integral) -> FixedPointType:
        """Augmented bitwise AND."""
        self._bits = self.__bitwise(other, operator.__and__)
        return self

    def __or__(self: FixedPointType, other: Integral) -> FixedPointType:
        """Bitwise OR."""
        return self.__class__.__new(self.__bitwise(other, operator.__or__),
                                    self._signed, self._m, self._n,
                                    self.overflow, self.rounding,
                                    self.str_base, self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __ior__(self: FixedPointType, other: Integral) -> FixedPointType:
        """Augmented bitwise OR."""
        self._bits = self.__bitwise(other, operator.__or__)
        return self

    def __xor__(self: FixedPointType, other: Integral) -> FixedPointType:
        """Bitwise XOR."""
        return self.__class__.__new(self.__bitwise(other, operator.__xor__),
                                    self._signed, self._m, self._n,
                                    self.overflow, self.rounding,
                                    self.str_base, self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __ixor__(self: FixedPointType, other: Integral) -> FixedPointType:
        """Augmented bitwise XOR."""
        self._bits = self.__bitwise(other, operator.__xor__)
        return self

    # Commutative operations
    __radd__ = __add__
    __rmul__ = __mul__
    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__

    # _________________________________________________________________________
    # Unary operators
    def __neg__(self: FixedPointType) -> FixedPointType:
        """Unary negation. Overflow handling occurs for max negative."""
        if not self._signed:
            from fixedpoint import FixedPointError
            raise FixedPointError("Unsigned numbers cannot be negated.")

        # Overflow only occurs if the number is at its max negative
        if overflow := (self._signedint == self._minimum):
            self._owarn("Negating %s%s (%s) causes overflow.",
                        self._str_base.name.strip(), self, self.qformat)

            self._owarn("Adjusting Q format to Q%d.%d to allow negation.",
                        self._m + 1, self._n)

        ret = self.__class__.__new(0, True, self._m, self._n, self.overflow,
                                   self.rounding, self.str_base,
                                   self.overflow_alert,
                                   self.implicit_cast_alert,
                                   self.mismatch_alert)
        ret._bits, ret._signed, ret._m, ret._n = \
            ret.__sub(self, 'clamp', ret._owarn)
        if not overflow:
            ret.clamp(self._m, alert='error')

        return ret

    def __pos__(self: FixedPointType) -> FixedPointType:
        """Unary positive."""
        return self.__class__.__new(self._bits, self._signed, self._m,
                                    self._n, self.overflow,
                                    self.rounding, self.str_base,
                                    self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    def __invert__(self: FixedPointType) -> FixedPointType:
        """Unary bitwise inversion."""
        return self.__class__.__new(self.bitmask & ~self._bits, self._signed,
                                    self._m, self._n, self.overflow,
                                    self.rounding, self.str_base,
                                    self.overflow_alert,
                                    self.implicit_cast_alert,
                                    self.mismatch_alert)

    # _________________________________________________________________________
    # Comparison operators
    def __cmp__(self: FixedPointType, other: Numeric) -> int:
        """Python 2 style comparison operator."""
        fother: FixedPointType = self.__to_FixedPoint(other)

        # Force a signed subtraction - grow by one bit temporarily to safely
        # convert to a signed number if needed
        with self(mismatch_alert='ignore', m=self._m + 1, signed=1) as left:
            args = left.__sub(fother, '', self._owarn)
        return self._posweight(*args) + self._negweight(*args)

    def __eq__(self: FixedPointType, other: Any) -> bool:
        """Equality comparison operator."""
        return self.__cmp__(other) == 0

    def __ne__(self: FixedPointType, other: Any) -> bool:
        """Non-equality comparison operator."""
        return self.__cmp__(other) != 0

    def __lt__(self: FixedPointType, other: Any) -> bool:
        """Less than comparison operator."""
        return self.__cmp__(other) < 0

    def __le__(self: FixedPointType, other: Any) -> bool:
        """Less than or equal to comparison operator."""
        return self.__cmp__(other) <= 0

    def __gt__(self: FixedPointType, other: Any) -> bool:
        """Greater than comparison operator."""
        return self.__cmp__(other) > 0

    def __ge__(self: FixedPointType, other: Any) -> bool:
        """Greater than or equal to comparison operator."""
        return self.__cmp__(other) >= 0

    ###########################################################################
    # Context management
    ###########################################################################
    def __call__(self: FixedPointType, *, safe_retain: bool = False,
                 **props: Union[int, bool, str]) -> FixedPointType:
        """Context initialization.

        Assign properties temporarily. Any argument to the __init__ function can
        be used here except the initialization value.

        If `safe_retain` evaluates as True, the changes that occur inside the
        with statement context will be retained after the context ends only if
        there are no exceptions.

        The order in which properties are specified is honored.
        """
        try:
            self.__context['safe_retain'] = bool(safe_retain)
            for attr, value in props.items():
                # Only change valid attributes
                if f'_{attr}' not in self.__slots__:
                    raise AttributeError(f"Invalid FixedPoint attribute "
                                         f"{attr!r}.")
                # Caller should not try to be accessing any "private" variables
                if attr.startswith('_'):
                    raise PermissionError(f"Access to {attr!r} is prohibited.")
                self.__context[f'_{attr}'] = value
        except Exception:
            self.__context = {}
            raise
        return self

    def __enter__(self: FixedPointType) -> FixedPointType:
        """Save the current attributes for later restoration."""
        # Push the current context onto the context manager stack
        self.__cmstack.append(DEFAULT_ENCODER.encode(self))
        # Push the safe_retain option to the context manager stack
        self.__cmstack.append(self.__context.pop('safe_retain', False))

        # Assign temporary context items from __call__ to the current object.
        try:
            # Note that __call__ is optional, so __context may be empty.
            for attr, value in self.__context.items():
                # To assign the value to the attribute, go through the property
                # setter function if it exists, which validates and normalizes
                # the value to the correct type (e.g., @signed.setter ensures
                # it's a bool). Filched from
                # https://stackoverflow.com/questions/3681272/can-i-get-a-reference-to-a-python-property
                prop = self.__class__.__dict__.get(attr[1:], None)
                if isinstance(prop, property) and bool(prop.fset):
                    prop.fset(self, value)  # type: ignore
                else:
                    raise PermissionError(f"{attr[1:]!r} is read-only.")
        finally:
            # Context has been adopted, or some exception was raised. Reset it
            # so it can be reused later.
            self.__context = {}

        return self

    def __exit__(self: FixedPointType, exc_type: Type[Exception],
                 *args: Any) -> None:
        """Conditionally restores/retains FixedPoint attributes.

        Context manager saved the context of the FixedPoint object. The context
        is restored unless `safe_retain` was True and there were no exception.
        """
        # If no exception occurred, and safe_retain is True, do not restore
        # context
        if self.__cmstack.pop() and exc_type is None:
            # Remove context from context manager stack.
            self.__cmstack.pop()
            return

        # See the FixedPointEncoder.default method in .\json.py for the
        # serialization order of FixedPoint object attributes.
        attributes = DEFAULT_DECODER.decode_attributes(self.__cmstack.pop())
        self._bits = attributes.pop()
        self._signed, self._m, self._n = attributes.pop()
        for attr, value in attributes.pop().items():
            self.__class__.__dict__[attr].fset(self, value)

    ###########################################################################
    # Built-in functions and type conversion
    ###########################################################################
    def __abs__(self: FixedPointType) -> FixedPointType:
        """Absolute value. This is the "abs()" function.

        Returns a copy of self is positive or a negated copy of self if
        negative. Signedness does not change.
        """
        if self._negweight():
            ret = -self
        else:
            ret = self.__class__.__new(self._bits, self._signed, self._m,
                                       self._n, self.overflow,
                                       self.rounding, self.str_base,
                                       self.overflow_alert,
                                       self.implicit_cast_alert,
                                       self.mismatch_alert)
        return ret

    def __int__(self: FixedPointType) -> int:
        """Integer cast of the fixed point value. Integer bits only."""
        return self._signedint >> self._n

    def __float__(self: FixedPointType) -> float:
        """Floating point representation of the stored value."""
        try:
            ret = float((ret := self._signedint) * 2**-self._n)
        except OverflowError:
            ret = float('-inf' if ret < 0 else 'inf')
        return ret

    def __bool__(self: FixedPointType) -> bool: # noqa: D401
        """True if non-zero."""
        return bool(self._bits)

    def __index__(self: FixedPointType) -> int:
        """Bits of the FixedPoint number."""
        return self._bits

    def __str__(self: FixedPointType) -> str: # noqa: D401
        """String representation of the stored value w/out its radix.

        Use the str_base property to adjust which base to use for this function.
        For str_base of 2, 8, or 16, output is 0-padded to the bit width.
        """
        ret = StrConv[self.str_base](self._bits)
        # Zero padding
        if self.str_base == 10:
            return ret

        # Remove radix
        ret = ret[2:]
        bits_needed = self._m + self._n
        nzeros = _ceil(bits_needed / _log2(self.str_base))
        return ret.zfill(nzeros)

    def __format__(self: FixedPointType, spec: str) -> str:
        """Format as a string."""
        # All bits
        if spec == '' or spec[-1] in 'bdoxX' or spec is None:
            ret = format(self._bits, spec)

        # Integer bits
        elif spec[-1] in 'm':
            ret = format((self._bits >> self._n) & (2**self._m - 1), spec[:-1])

        # Fractional bits
        elif spec[-1] in 'n':
            ret = format(self._bits & (2**self._n - 1), spec[:-1])

        # str()
        elif spec[-1] in 's':
            ret = format(str(self), spec)

        # float()
        elif spec[-1] in 'eEfFgG%':
            ret = format(float(self), spec)

        # qformat
        elif spec[-1] == 'q':
            ret = format(self.qformat, f"{spec[:-1]}s")

        else:
            raise ValueError(f"Unknown format code {spec!r}.")

        return ret

    def __repr__(self: FixedPointType) -> str:
        """Python-executable code string, allows for exact reproduction."""
        str_base = self.str_base
        return (
            f"FixedPoint({StrConv[str_base](self._bits)!r}, "
            f"signed={int(self._signed)}, "
            f"m={self._m}, "
            f"n={self._n}, "
            f"overflow={self.overflow!r}, "
            f"rounding={self.rounding!r}, "
            f"overflow_alert={self.overflow_alert!r}, "
            f"mismatch_alert={self.mismatch_alert!r}, "
            f"implicit_cast_alert={self.implicit_cast_alert!r}, "
            f"{str_base=})")

    ###########################################################################
    # Bit resizing methods
    ###########################################################################
    def resize(self: FixedPointType, m: int, n: int, /, rounding: str = None,
               overflow: str = None, alert: str = None) -> None:
        """Resize integer and fractional bit widths.

        Overflow handling, sign-extension, and rounding are employed.

        Override rounding, overflow, and overflow_alert settings for the
        scope of this method by specifying the appropriate arguments.
        """
        old = self._overflow, self._rounding, self._overflow_alert
        try:
            with self(safe_retain=True,
                      overflow=overflow or self.overflow,
                      rounding=rounding or self.rounding,
                      overflow_alert=alert or self.overflow_alert):
                self.n = n
                self.m = m
        except Exception:
            raise
        else:
            self._overflow, self._rounding, self._overflow_alert = old

    def trim(self: FixedPointType, /, ints: bool = None,
             fracs: bool = None) -> None:
        """Trims off insignificant bits.

        This includes trailing 0s, leading 0s, and leading 1s as appropriate.

        Trim only integer bits or fractional bits by setting `fracs` or `ints`
        to True. By default, both integer and fractional bits are trimmed.
        """
        if ints is None and fracs is None:
            ints, fracs = True, True

        s, m, n = bool(self._signed), self._m, self._n
        # Trailing 0s on fractional bits can be stripped
        if fracs:
            n = len(self.bits['N'].rstrip('0')) if n else 0

        if ints:
            # Remove leading 1s for negative numbers, leave 1 though
            if self._signedint < 0:
                m = 1 + len(self.bits['M'].lstrip('1'))
            # Remove all leading 0s
            # For signed, minimum m is 1
            # For unsigned, m can be 0 iff n is non-zero
            elif self._m:
                m = max(s or n == 0,
                        s + len(self.bits['M'].lstrip('0')))
            else:
                m = self._m

        self._log("INTS:  %s\n"
                  "FRACS: %s\n"
                  "Trimming %d fractional bits\n"
                  "Trimming %d integer bits\n",
                  ints, fracs, self._n - n, self._m - m)

        self._bits >>= (self._n - n)
        self._n = n
        self._m = int(m or n == 0)
        self._bits &= self.bitmask

    # _________________________________________________________________________
    # Rounding methods
    def __rounding_arg_check(self: FixedPointType, nfrac: int) -> None:
        """Validate rounding arguments."""
        if not isinstance(nfrac, int):
            raise TypeError(f"Expected {type(1)}; got {type(nfrac)}.")

        if self._m + nfrac == 0 or (self._m == 0) == self._n:
            raise ValueError("Word size (integer and fractional) "
                             "must be positive.")

        if not (self._m == 0) <= nfrac < self._n:
            raise ValueError("Number of fractional bits remaining after round "
                             "must be in the range "
                             f"[{int(self._m == 0)}, {self._n}).")

    def __round__(self: FixedPointType, nfrac: int, /) -> FixedPointType:
        """Fractional rounding. This is the "round()" function.

        The rounding method used by this function is specified by the
        rounding attribute of this object.
        """
        ret: FixedPointType = self.__class__.__new(self._bits, self._signed,
                                                   self._m, self._n,
                                                   self.overflow,
                                                   self.rounding, self.str_base,
                                                   self.overflow_alert,
                                                   self.implicit_cast_alert,
                                                   self.mismatch_alert)
        ret.round(nfrac)
        return ret

    def __floor__(self: FixedPointType) -> FixedPointType:
        """Round to negative infinity, leave fractional bit width unmodified."""
        # When binary bits are truncated, it rounds to negative infinity.
        ret = self.__class__.__new(self._bits, self._signed, self._m,
                                   self._n, self.overflow,
                                   self.rounding, self.str_base,
                                   self.overflow_alert,
                                   self.implicit_cast_alert,
                                   self.mismatch_alert)
        if self._n:
            ret._bits &= ~(2**self._n - 1) & self.bitmask
        return ret

    def __ceil__(self: FixedPointType) -> FixedPointType:
        """Round to positive infinity, leaving 0 fractional bits."""
        ret = self.__class__.__new(self._bits, self._signed, self._m,
                                   self._n, self.overflow,
                                   self.rounding, self.str_base,
                                   self.overflow_alert,
                                   self.implicit_cast_alert,
                                   self.mismatch_alert)
        ret.round_up(0)
        return ret

    def __trunc__(self: FixedPointType) -> FixedPointType:
        """Truncate all fractional bits. Adds an integer bit if needed."""
        ret = self.__class__.__new(self._bits, self._signed, self._m,
                                   self._n, self.overflow,
                                   self.rounding, self.str_base,
                                   self.overflow_alert,
                                   self.implicit_cast_alert,
                                   self.mismatch_alert)
        ret._bits >>= ret._n
        ret._n = 0
        # Signed numbers are guaranteed to have at least 1 integer bit. Unsigned
        # numbers are not
        ret._m = ret._m or 1
        return ret

    def round(self: FixedPointType, nfrac: int, /) -> None:
        """Round with the default setting."""
        getattr(self, f"round_{self.rounding}")(nfrac)

    def convergent(self: FixedPointType, nfrac: int, /) -> None:
        """Round half to even."""
        self.__rounding_arg_check(nfrac)

        m, n, bits = self._m, self._n, self._bits

        num_bits_truncated = n - nfrac
        # Determine if we need to round
        must_round = False
        # The most significant fractional bit
        msb_frac = 2**(num_bits_truncated - 1) & bits
        # Least significant integer bit
        lsb_int = 2**num_bits_truncated & bits

        # There are multiple fractional bits to be rounded off
        if num_bits_truncated > 1:
            # Least significant fractional bits
            lsb_fracs = (2**(n - nfrac - 1) - 1) & bits
            # If the most significant fractional bit is 1, round if the number
            # is odd or remaining fractional bits are non-zero
            must_round = msb_frac and (lsb_fracs or lsb_int)
        # This is only one fractional bit; round iff the number is odd and
        # fractional bit is '1'
        else:
            must_round = msb_frac and lsb_int

        # Get rid of the bits we don't want
        bits >>= n - nfrac
        n = nfrac
        maximum = 2**(m - bool(self._signed) + n) - 1

        # Check for overflow before rounding
        if must_round:
            if bits == maximum:
                self._owarn("Convergent round to %s.%d causes overflow.",
                            self.qformat.split('.')[0], n)
                clamp = self._overflow == Overflow['clamp']
                self._owarn("%s maximum.", 'Clamped to' if clamp else "Wrapped")

                # If we need to clamp, set the value to 1 less than the max,
                # we will add the rounding bit later
                if clamp:
                    bits = maximum - 1

            bits += 1

        self._n = n
        self._bits = bits & self.bitmask

    # Add a round_ prefix in front of rounding functions for generic rounding
    # attribute access
    round_convergent = convergent

    def round_in(self: FixedPointType, nfrac: int, /) -> None:
        """Round towards 0."""
        self.__rounding_arg_check(nfrac)

        n, bits = self._n, self._bits

        # For negative numbers add one to truncated result if truncated bits
        # are non-zero
        num_bits_truncated = n - nfrac
        truncated_bits = bits & (2**num_bits_truncated - 1)
        bits >>= num_bits_truncated
        bits += bool(self._signedint < 0) and bool(truncated_bits)
        self._n = nfrac
        self._bits = bits & self.bitmask

    def round_out(self: FixedPointType, nfrac: int) -> None:
        """Round half away from zero."""
        self.__rounding_arg_check(nfrac)

        m, n, bits = self._m, self._n, self._bits

        # Truncate bits
        num_bits_truncated = n - nfrac
        truncated_bits = bits & (2**num_bits_truncated - 1)
        tie_threshold = 1 << (num_bits_truncated - 1)
        if truncated_bits == tie_threshold:
            must_round = self._signedint > 0
        else:
            must_round = truncated_bits > tie_threshold

        bits >>= num_bits_truncated
        n = nfrac
        maximum = 2**(m - bool(self._signed) + n) - 1

        # Check for overflow before rounding
        if must_round:
            if bits == maximum:
                self._owarn("Rounding out to %s.%d causes overflow.",
                            self.qformat.split('.')[0], n)
                clamp = self._overflow == Overflow['clamp']
                self._owarn("%s maximum.", 'Clamped to' if clamp else "Wrapped")

                # If we need to clamp, set the value to 1 less than the max,
                # we will add the rounding bit later
                if clamp:
                    bits = maximum - 1

            bits += 1

        self._n = n
        self._bits = bits & self.bitmask

    def round_nearest(self: FixedPointType, nfrac: int, /) -> None:
        """Round half up."""
        self.__rounding_arg_check(nfrac)

        m, n, bits = self._m, self._n, self._bits

        # Truncate bits
        num_bits_truncated = n - nfrac
        truncated_bits = bits & (2**num_bits_truncated - 1)
        tie_threshold = 1 << (num_bits_truncated - 1)
        bits >>= num_bits_truncated
        n = nfrac
        maximum = 2**(m - bool(self._signed) + n) - 1

        # Ties or greater round up
        must_round = truncated_bits >= tie_threshold

        # Check for overflow before rounding
        if must_round:
            if bits == maximum:
                self._owarn("Rounding to nearest %s.%d causes overflow.",
                            self.qformat.split('.')[0], n)
                clamp = self._overflow == Overflow['clamp']
                self._owarn("%s maximum.", 'Clamped to' if clamp else "Wrapped")

                # If we need to clamp, set the value to 1 less than the max,
                # we will add the rounding bit later
                if clamp:
                    bits = maximum - 1

            bits += 1

        self._n = n
        self._bits = bits & self.bitmask

    def round_up(self: FixedPointType, nfrac: int, /) -> None:
        """Round towards infinity."""
        self.__rounding_arg_check(nfrac)

        m, n, bits = self._m, self._n, self._bits

        # Truncate bits
        num_bits_truncated = n - nfrac
        truncated_bits = bits & (2**num_bits_truncated - 1)
        bits >>= num_bits_truncated
        n = nfrac
        maximum = 2**(m - bool(self._signed) + n) - 1

        # Any non-zero truncated bits round up
        must_round = bool(truncated_bits)

        # Check for overflow before rounding
        if must_round:
            if bits == maximum:
                self._owarn("Rounding up to %s.%d causes overflow.",
                            self.qformat.split('.')[0], n)
                clamp = self._overflow == Overflow['clamp']
                self._owarn("%s maximum.", 'Clamped to' if clamp else "Wrapped")

                # If we need to clamp, set the value to 1 less than the max,
                # we will add the rounding bit later
                if clamp:
                    bits = maximum - 1

            bits += 1

        self._n = n
        self._bits = bits & self.bitmask

    def round_down(self: FixedPointType, nfrac: int, /) -> None:
        """Round towards negative infinity."""
        self.__rounding_arg_check(nfrac)

        self._bits >>= self._n - nfrac
        self._n = nfrac

    def keep_msbs(self: FixedPointType, m: int, n: int, /, rounding: str = None,
                  overflow: str = None, alert: str = None) -> None:
        """Round off MSbs, and reformat to the given number of bits.

        Override rounding, overflow, and overflow_alert settings for the
        scope of this method by specifying the appropriate arguments.
        """
        if n < 0 or m < 0:
            raise ValueError("Bit format specifications must be non-negative.")

        if self._signed and m == 0:
            raise ValueError("Signed number must have at least 1 integer bit.")

        if not 2 <= m + n < self._m + self._n:
            raise ValueError("Total number of bits must be in the range [2, "
                             f"{self._m + self._n}).")

        old = self._overflow, self._overflow_alert
        with self(safe_retain=True,
                  overflow=overflow or self.overflow,
                  overflow_alert=alert or self.overflow_alert):
            # Move the binary point but keep the same bits
            self._m, self._n = m, self._m + self._n - m
            # Now round off unwanted bits
            func = getattr(self, f'round_{rounding or self.rounding}')
            func(n)
            # If execution gets here, rounding did not cause an exception.
            # Revert the local overflow and overflow_alert properties back.
            self._overflow, self._overflow_alert = old

    # _________________________________________________________________________
    # Overflow methods
    def clamp(self: FixedPointType, nint: int, /, alert: str = None) -> None:
        """Remove integer bits and clamps if necessary.

        Override the overflow_alert setting for the scope of this method by
        specifying an alternative `alert`.
        """
        if not isinstance(nint, int):
            raise TypeError(f"Expected {type(1)}; got {type(nint)}.")

        signed, m, n, bits = self._signed, self._m, self._n, self._bits

        # Validate arguments
        if not int(n == 0 or signed) <= nint < m:
            raise ValueError(f"{self:q} can only clamp between "
                             f"[{int(n == 0 or signed)}, {m}) integer bits.")

        # Truncate and see if the values still match
        nbits = nint + n
        signedint = bits & (2**(nbits - signed) - 1)
        signedint -= bits & (signed * 2**(nbits - 1))

        # Truncation is not sufficient, must clamp
        if signedint != (tmp := self._signedint):
            bits = (1 << nbits) - (tmp >= 0)

            # Change local alert setting
            olvl = self._overflow_alert
            self._overflow_alert = Alert[alert or olvl.name]
            extreme = 'minimum' if tmp < 0 else 'maximum'
            # Warn on overflows
            try:
                self._owarn("Overflow in format %s.", self.qformat)
                self._owarn("Clamped to %s.", extreme)
            finally:
                # Revert back to original alert level
                self._overflow_alert = olvl

            bits = getattr(self, f"_{extreme}") >> (self._m - nint)

        # Truncation is sufficient!
        else:
            bits = signedint

        self._m = int(nint)
        self._bits = bits & self.bitmask

    def wrap(self: FixedPointType, nint: int, /, alert: str = None) -> None:
        """Remove integer bits by masking them away.

        Override the overflow_alert setting for the scope of this method by
        specifying an alternative `alert`.
        """
        if not isinstance(nint, int):
            raise TypeError(f"Expected {type(1)}; got {type(nint)}.")

        signed, m, n, bits = bool(self._signed), self._m, self._n, self._bits

        # Validate arguments
        if not int(n == 0 or signed) <= nint < m:
            raise ValueError(f"{self:q} can only wrap between "
                             f"[{int(n == 0 or signed)}, {m}) integer bits.")

        # Detect a change in value
        nbits = nint + n
        signedint = bits & (2**(nbits - signed) - 1)
        signedint -= bits & (signed * 2**(nbits - 1))

        # Warn on overflows
        if signedint != (tmp := self._signedint):

            # Change local alert setting
            olvl = self.overflow_alert
            self._overflow_alert = Alert[alert or olvl]

            # Warn on overflows
            try:
                self._owarn("Overflow in format %s.", self.qformat)
                self._owarn("Wrapped %s.", 'minimum' if tmp < 0 else 'maximum')
            finally:
                # Revert back to original alert level
                self._overflow_alert = Alert[olvl]

        self._m = int(nint)
        self._bits &= self.bitmask

    def keep_lsbs(self: FixedPointType, m: int, n: int, /, overflow: str = None,
                  alert: str = None) -> None:
        """Remove MSbs, and reformat to the given number of bits.

        Override the overflow and overflow_alert setting for the scope of this
        method by specifying the appropriate arguments.
        """
        if not isinstance(m, int):
            raise TypeError(f"Expected {type(1)}; got {type(m)}.")
        if not isinstance(n, int):
            raise TypeError(f"Expected {type(1)}; got {type(n)}.")

        if n < 0 or m < 0:
            raise ValueError("Bit format specifications must be non-negative.")

        if (signed := self._signed) and m == 0:
            raise ValueError("Signed number must have at least 1 integer bit.")

        if not 2 <= (length := m + n) < self._m + self._n:
            raise ValueError("Total number of bits must be in the range [2, "
                             f"{self._m + self._n}).")

        # Detect a change in value
        signedint = (bits := self._bits) & (2**(length - signed) - 1)
        signedint -= bits & (signed * 2**(length - 1))

        # Change local alert setting
        olvl = self.overflow_alert
        self._overflow_alert = Alert[alert or olvl]

        # Warn on overflows
        if signedint != (tmp := self._signedint):

            # Warn on overflows
            try:
                self._owarn("Overflow in format %s.", self.qformat)
                clamp = (overflow or self.overflow) == 'clamp'
                self._owarn("%s %s.", 'Clamped to' if clamp else 'Wrapped',
                            'minimum' if tmp < 0 else 'maximum')

            # Revert back to original alert level
            except Exception:
                self._overflow_alert = Alert[olvl]
                raise

        # Move the binary point but keep the same bits
        self._m, self._n = self._m + self._n - n, n
        # Now use the preferred method to remove unwanted bits
        func = getattr(self, overflow or self.overflow)
        # The alert has already been issued if needed, handle overflow silently.
        func(m, 'ignore')
        # Revert back to the original alert level
        self._overflow_alert = Alert[olvl]

    ###########################################################################
    # Alerts and error handling
    ###########################################################################
    def __format_exception_msg(self: FixedPointType, msg: str,
                               args: Tuple[Any, ...]) -> str:
        """Prepends the serial number to the message."""
        return f"[SN{_sn(self.__id)}] {msg}" % args

    def _mwarn(self: FixedPointType, msg: str, *args: Any,
               **kwargs: int) -> None:
        """Mismatch warning method configured by mismatch_alert."""
        keywords = {**self.__id, **kwargs}
        if self._mismatch_alert == Alert['error']:
            from fixedpoint import MismatchError
            LOGGER.error(msg, *args, **keywords, stack_info=1)  # type: ignore
            raise MismatchError(self.__format_exception_msg(msg, args))
        WARNER.log(self._mismatch_alert.value,
                   msg, *args, **keywords)  # type: ignore

    def _owarn(self: FixedPointType, msg: str, *args: Any,
               **kwargs: int) -> None:
        """Overflow warning method configured by overflow_alert."""
        keywords = {**self.__id, **kwargs}
        if self._overflow_alert == Alert['error']:
            from fixedpoint import FixedPointOverflowError
            LOGGER.error(msg, *args, **keywords, stack_info=1)  # type: ignore
            raise FixedPointOverflowError(self.__format_exception_msg(msg,
                                                                      args))
        WARNER.log(self._overflow_alert.value,
                   msg, *args, **keywords)  # type: ignore

    def _iwarn(self: FixedPointType, msg: str, *args: Any,
               **kwargs: int) -> None:
        """Implicit cast warning method configured by implicit_cast_alert."""
        keywords = {**self.__id, **kwargs}
        if self._implicit_cast_alert == Alert['error']:
            from fixedpoint import ImplicitCastError
            LOGGER.error(msg, *args, **keywords, stack_info=1)  # type: ignore
            raise ImplicitCastError(self.__format_exception_msg(msg, args))
        WARNER.log(self._implicit_cast_alert.value,
                   msg, *args, **keywords)  # type: ignore

    def _log(self: FixedPointType, msg: str, *args: Any, **kwargs: int) -> None:
        """Log to file."""
        keywords = {**self.__id, **kwargs}
        LOGGER.debug(msg, *args, **keywords)  # type: ignore

    @staticmethod
    def enable_logging() -> None:
        """Enable the FixedPoint logger."""
        LOGGER.setLevel(logging.DEBUG)

    @staticmethod
    def disable_logging() -> None:
        """Disable the FixedPoint logger."""
        LOGGER.setLevel(logging.CRITICAL)

    @classmethod
    def sign(cls: Type[FixedPointType], fp: Numeric, /) -> int:
        """Determine the sign of a numerical object.

        Returns -1 if val < 0, 1 if val > 0, 0 otherwise.
        """
        signed: Union[int, float]
        if isinstance(fp, cls):
            signed = fp._signedint
        else:
            signed = fp
        return (signed > 0) - (signed < 0)

    @classmethod
    def min_m(cls: Type[FixedPointType], val: Union[float, int], /,
              signed: bool = None) -> int:
        """Calculate the minimum integer bit width."""
        # Start with an educated guess; round the value away from 0 and
        # calculate bit width from there, since that would be worst-case
        # rounding
        wcround = cls.sign(val) * _ceil(abs(val))
        ret = _ceil(_log2(abs(wcround))) if val else 1

        # A signed number ranges from [-2**(m-1), 2**(m-1)-1]
        if signed or val < 0:
            while not -(boundary := 2**(ret - 1)) <= wcround < boundary:
                ret += 1

        # An unsigned number ranges from [0, 2**m-1]
        else:
            ret += wcround >= 2**ret

        return int(ret)

    @staticmethod
    def min_n(val: Union[int, float], /) -> int:
        """Calculate minimum fractional bit width."""
        def recursive(val: Union[int, float], lo: int, hi: int) -> int:
            # Recursive binary search; fast but overflow-prone
            try:
                if lo + 1 == hi:
                    ret = hi if (val * 2**lo) % 1.0 else lo

                elif (val * 2**(n := _ceil((lo + hi) / 2))) % 1.0:
                    ret = recursive(val, n, hi)

                else:
                    ret = recursive(val, lo, n)

            # Bubble search; slow but overflow-safe. Use as a last resort
            except OverflowError:
                ret = lo
                while val % 1.0:  # pragma: no cover
                    ret += 1
                    val *= 2.0

            return ret

        return recursive(val, 0, _MAXEXPONENT)
