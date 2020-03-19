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
import logging as _logging
from math import log2 as _log2, ceil as _ceil
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)
import sys as _sys

from fixedpoint.properties import (
    PROPERTIES,
    StrBase,
    StrConv,
    Alert,
    Overflow,
    Rounding,
    PropertyResolver,
)
from fixedpoint.logging import (
    _WARNER,
    LOGGER as _LOGGER,
)
from fixedpoint.json import (
    DEFAULT_ENCODER as _ENCODER,
    DEFAULT_DECODER as _DECODER,
)

__all__ = [
    'FixedPoint',
]

FixedPointType = TypeVar("FixedPointType", bound="FixedPoint")
Numeric = Union[FixedPointType, int, float]
_MAXEXPONENT = max(abs(_sys.float_info.max_exp), abs(_sys.float_info.min_exp))

class FixedPoint:
    '''Fixed point object with several features:

    * Converts floating-point to fixed point.
    * Various ways of rounding and overflow handling.
    * Arithmetic with full precision.
    * Configurable alerts for overflow, implicit casting, and property
      mismatches.
    * Configurable logging capabilities.
    '''
    __slots__ = (
        # Bit width attributes
        '_signed', '_m', '_n', '_bits',
        # Logging **kwargs for unique identification
        '__id',
        # Support context management restoration
        '__cmstack', '__context',
        # A flag for miscellaneous use
        '__flag',
        # Remaining properties
    ) + tuple(f"_{prop}" for prop in PROPERTIES)

    def __new__(cls: Type[FixedPointType],
    # Positional and required arguments
    init: Union[Numeric, str],
    /, # Positional but keyword-able arguments
    signed: bool = None,
    m: int = None,
    n: int = None,
    *, # Keyword-only arguments
    # Numerical handling keywords
    overflow: str = 'clamp',
    rounding: str = 'auto',
    # Formatting keywords
    str_base: int = 16,
    # Alert keywords
    overflow_alert: str = 'error',
    implicit_cast_alert: str = 'warning',
    mismatch_alert: str = 'warning') -> FixedPointType:
        """Make sure there's only one copy of static variables.
        """
        try:
            cls._SERIAL_NUMBER += 1
        except AttributeError:
            cls._RESOLVE: PropertyResolver = PropertyResolver()
            cls._SERIAL_NUMBER: int = 1
        finally:
            inst: FixedPointType = super(FixedPoint, cls).__new__(cls)

        return inst

    def __getnewargs__(self) -> Tuple[str]:
        """Returns the positional arguments to __new__ as a tuple, which
        supports pickling
        """
        return hex(self._bits),

    ###########################################################################
    # Initialization methods
    ###########################################################################
    def __init__(self: FixedPointType,
    # Positional and required arguments
    init: Union[Numeric, str],
    /, # Positional but keyword-able arguments
    signed: bool = None,
    m: int = None,
    n: int = None,
    *, # Keyword-only arguments
    # Numerical handling keywords
    overflow: str = 'clamp',
    rounding: str = 'auto',
    # Formatting keywords
    str_base: int = 16,
    # Alert keywords
    overflow_alert: str = 'error',
    implicit_cast_alert: str = 'warning',
    mismatch_alert: str = 'warning') -> None:
        """Initialize a fixed point number.

        Args:
            init: Initialization value. An int or float is interpreted as number
                to cast to fixed point. A str is interpreted as bit literal,
                including sign, integer, and fractional bits. It must include
                the radix unless it is decimal. Providing another FixedPoint
                object generates a copy.
            signed (optional): Signedness; if left unspecified, init < 0 will
                produce a signed number, init >= 0 generates an unsigned number.
            m (optional): Number of integer bits; if left unspecified, the
                number of integer bits is deduced from the value of init.
            n (optional): Number of fractional bits; if left unspecified, the
                number of fractional bits is deduced from the value of init.
                That is, n will grow to make the value of the FixedPoint object
                equal to the input.

        See the properties module for details on properties.
        """
        self.__id: Mapping[str, Union[int, Mapping[str, int]]] = {
            'stacklevel': 2,
            'extra': {'sn': self.__class__._SERIAL_NUMBER},
        }

        # Type validation
        initialize: Callable[[Union[str, int, float]], None]
        if isinstance(init, str):
            initialize = self.from_string # type: ignore
            if any([x is None for x in [signed, m, n]]):
                raise ValueError("When initializing with a string literal, "
                    "Q format must be fully constrained.")
        elif isinstance(init, int):
            initialize = self.from_int # type: ignore
        elif not isinstance(init, FixedPoint):
            initialize = self.from_float # type: ignore
            try:
                init = float(init)
            except:
                raise TypeError(f"Unsupported type {type(init)}; cannot "
                    "convert to float.")

        # Internally used variables
        self.__cmstack: List[Any] = []
        self.__context: Dict[str, Union[bool, int, str]] = {}
        self.__flag: bool = False

        # Copy attributes into a new object
        if isinstance(init, FixedPoint):
            for attr in [x for x in init.__slots__ if '__' not in x]:
                setattr(self, attr, getattr(init, attr))
            self._log("Copied from SN %d", init.__id['extra']['sn']) # type: ignore
            return

        # Qualify Q format (bit widths and signedness)
        if signed is None:
            signed = init < 0 # type: ignore # init won't be a str

        # min_m will account for worst case rounding; So if bit widths were not
        # specified, trim excess bits off
        trim_n = n is None
        _n: int
        if trim_n:
            _n = self.__class__.min_n(init) # type: ignore # init won't be a str
            self._log('Deduced fractional length: %d', _n)
        elif n < 0: # type: ignore # init won't be a str
            raise ValueError("Number of fractional bits must be non-negative.")
        else:
            _n = n # type: ignore # n is not None

        trim_m = m is None
        _m: int
        if trim_m:
            _m = self.__class__.min_m(init, signed) # type: ignore # init won't be a str
            _m += (_m + _n) == 0
            self._log('Deduced integer length: %d', _m)
        elif m < bool(signed): # type: ignore # m is not None
            raise ValueError("Number of integer bits must be " +
                ("at least 1 for signed numbers." if signed else "non-negative."))
        else:
            _m = m # type: ignore # m is not None

        if _m + _n == 0:
            raise ValueError("Word size (integer and fractional) must be positive.")

        self._signed: bool = bool(signed)
        self._m: int = int(_m)
        self._n: int = int(_n)

        # Determine rounding method if not specified
        if rounding == 'auto':
            rounding = 'convergent' if signed else 'nearest'

        # Assign/validate properties
        self._str_base: StrBase = StrBase(str_base)
        self._mismatch_alert: Alert = Alert[mismatch_alert]
        self._overflow_alert: Alert = Alert[overflow_alert]
        self._implicit_cast_alert: Alert = Alert[implicit_cast_alert]
        self._overflow: Overflow = Overflow[overflow]
        self._rounding: Rounding = Rounding[rounding]

        self._log('%s\n'
            "Serial number: %d\n"
            "intended: %r\n"
            "Q format: %s\n"
            "overflow: %s\n"
            "rounding: %s\n"
            "overflow_alert: %s\n"
            "mismatch_alert: %s\n"
            "implicit_cast_alert: %s\n"
            "str_base: %d",
            '-' * 80,
            self.__id['extra']['sn'], # type: ignore
            init,
            self.qformat,
            self._overflow.name,
            self._rounding.name,
            self._overflow_alert.name,
            self._mismatch_alert.name,
            self._implicit_cast_alert.name,
            self._str_base.value,
        )

        initialize(init)
        self.trim(trim_m, trim_n)

    def from_string(self: FixedPointType, string: str, /) -> None:
        """Initializes a FixedPoint object from a string literal.

        Raises:
            ValueError: Bits in string literal exceed preset bit widths
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

        Overflow handling is employed. Rounding is not.
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
                bits = eval(extreme)

        self._bits = bits & self.bitmask

    def from_float(self: FixedPointType, val: float, /) -> None:
        """Initialize a FixedPoint object from a floating point value.

        Rounding and overflow handling is employed.
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
                getattr(self, f"round_{self._rounding.name}")(n)
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
        """Obtain the signedness of the number.
        """
        return self._signed

    @signed.setter
    def signed(self: FixedPointType, val: bool) -> None:
        """Change signedness. Bit widths remain the same.

        This does not invert the value, it merely changes the interpretation of
        the MSb of the number.

        For a signed number, the MSb is weighted negative. For an unsigned
        number, the same MSB is weighter positive. Overflow handling is employed
        for the following conditions:
            * Current value is signed and negative, and signedness is changing
              to unsigned. This is underflow.
            * Current value is unsigned, and signedness is changing to signed,
              and the MSb is 1 (in other words changing the signedness of the
              number changes the sign of the value). This is overflow.

        Overflow handling is implemented as specified by the overflow attribute.
        Exceptions/warnings are issued as specified by the overflow_alert
        attribute.
        """
        # If we're not actually changing sign, exit
        if (val := bool(val)) == bool(signed := self._signed):
            return

        # We must have an integer bit to change sign
        if self._m == 0 and val:
            from fixedpoint import FixedPointError
            raise FixedPointError("Cannot change sign with 0 integer bits.")

        # If the msb is 0, overflow won't happen.
        if self['msb'] == 0:
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

    #__________________________________________________________________________
    @property
    def m(self: FixedPointType) -> int:
        """Number of integer bits.
        """
        return self._m

    @m.setter
    def m(self: FixedPointType, nbits: int) -> None:
        """Change the number of integer bits.

        If nbits is less than the current number of integer bits, overflow
        handling occurs as specified by the object's overflow property.

        If nbits is greater than the current number of integer bits, sign
        extension occurs.
        """
        if not isinstance(nbits, int):
            raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")

        if nbits < int(self._signed):
            raise ValueError("Number of integer bits must be " +
                ("positive for signed numbers." if self._signed else "non-negative."))
        if nbits + self._n == 0:
            raise ValueError("Word size (integer and fractional) must be positive.")

        nintbits = nbits - self._m
        # Number of integer bits are growing, do sign extension.
        if nintbits > 0 and self._negweight():
            shift = self._m + self._n
            self._bits |= (2**nintbits - 1) << (self._m + self._n)

        # Number of integer bits are shrinking, handle overflow
        elif nintbits < 0:
            getattr(self, self._overflow.name)(nbits)
        self._m = int(nbits)

    #__________________________________________________________________________
    @property
    def n(self: FixedPointType) -> int:
        """Obtain the number of fractional bits.
        """
        return self._n

    @n.setter
    def n(self: FixedPointType, nbits: int) -> None:
        """Change the number of fractional bits.

        If nbits is less than the current number of fractional bits, rounding
        occurs as specified by the object's rounding property.
        """
        if not isinstance(nbits, int):
            raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")

        if nbits < 0:
            raise ValueError("Number of fractional bits must be non-negative.")
        if self._m + nbits == 0:
            raise ValueError("Word size (integer and fractional) must be positive.")

        # Number of fractional bits are growing, just shift in s'more bits
        if (nfracbits := nbits - self._n) > 0:
            self._bits <<= nfracbits

        # Fractional bits count is shrinking, round
        elif nfracbits < 0:
            self.round(nbits)

        self._n = int(nbits)

    #__________________________________________________________________________
    @property
    def str_base(self: FixedPointType) -> int:
        """Obtain the str_base setting.
        """
        return int(self._str_base.value)

    @str_base.setter
    def str_base(self: FixedPointType, base: int) -> None:
        """Change the str_base setting.
        """
        try:
            self._str_base = StrBase(base)
        except ValueError:
            raise ValueError(f"Invalid str_base setting: {base!r}.")

    #__________________________________________________________________________
    @property
    def overflow_alert(self: FixedPointType) -> str:
        """Obtain the overflow_alert setting.
        """
        return self._overflow_alert.name

    @overflow_alert.setter
    def overflow_alert(self: FixedPointType, level: str) -> None:
        """Change the overflow_alert behavior.
        """
        try:
            self._overflow_alert = Alert[level]
        except KeyError:
            raise ValueError(f"Invalid overflow_alert setting: {level!r}.")

    #__________________________________________________________________________
    @property
    def implicit_cast_alert(self: FixedPointType) -> str:
        """Obtain the implicit_cast_alert setting.
        """
        return self._implicit_cast_alert.name

    @implicit_cast_alert.setter
    def implicit_cast_alert(self: FixedPointType, level: str) -> None:
        """Change the implicit_cast_alert behavior.
        """
        try:
            self._implicit_cast_alert = Alert[level]
        except KeyError:
            raise ValueError(f"Invalid implicit_cast_alert setting: {level!r}.")

    #__________________________________________________________________________
    @property
    def mismatch_alert(self: FixedPointType) -> str:
        """Obtain the mismatch_alert setting.
        """
        return self._mismatch_alert.name

    @mismatch_alert.setter
    def mismatch_alert(self: FixedPointType, level: str) -> None:
        """Change the mismatch_alert behavior.
        """
        try:
            self._mismatch_alert = Alert[level]
        except KeyError:
            raise ValueError(f"Invalid mismatch_alert setting: {level!r}.")

    #__________________________________________________________________________
    @property
    def rounding(self: FixedPointType) -> str:
        """Obtain the current rounding scheme setting.
        """
        return self._rounding.name

    @rounding.setter
    def rounding(self: FixedPointType, scheme: str) -> None:
        """Set the rounding scheme setting.
        """
        try:
            self._rounding = Rounding[scheme]
        except KeyError:
            raise ValueError(f"Invalid rounding setting: {scheme!r}.")

    #__________________________________________________________________________
    @property
    def overflow(self: FixedPointType) -> str:
        """Obtain the current overflow handling setting.
        """
        return self._overflow.name

    @overflow.setter
    def overflow(self: FixedPointType, scheme: str) -> None:
        """Set the overflow handling setting.
        """
        try:
            self._overflow = Overflow[scheme]
        except KeyError:
            raise ValueError(f"Invalid overflow setting: {scheme!r}.")

    ###########################################################################
    # Public properties and built-in property methods
    ###########################################################################
    @property
    def clamped(self: FixedPointType) -> bool:
        """Indicate if the current value of this number is clamped

        Returns:
            bool: True if clamped, False if not
        """
        return self._bits in [abs(self._minimum), self._maximum]

    @property
    def qformat(self: FixedPointType) -> str:
        """Q format string

        UQm.n for unsigned
        Qm.n for signed

        m represents the number of integer bits
        n represents the number of fractional bits
        """
        return f"{'' if self._signed else 'U'}Q{self._m}.{self._n}"

    @property
    def bitmask(self: FixedPointType) -> int:
        '''Integer bitmask for all integer fractional bits
        '''
        return int(2**(self._m + self._n) - 1)

    @property
    def bits(self: FixedPointType) -> int:
        '''Raw bits of the fixed point number.
        '''
        return self._bits

    def __len__(self: FixedPointType) -> int:
        """Bit size of the object.
        """
        return self._m + self._n

    def __getitem__(self: FixedPointType, key: Union[int, slice, str]) -> int:
        """Allows square bracket access to a bit or a slice of bits. Depending
        on how it's sliced, the bits are treated as either a:

        * a std_logic_vector with descending range
        * a std_logic_vector with ascending range
        * a python binary string

        Specific parts of the bit representation are also mapped to keywords:

        * x['m'] or x['int'] gives the integer bits. A KeyError is raised
          if there are no integer bits.
        * x['n'] or x['frac'] gives the fractional bits. A KeyError is
          raised if there are no fractional bits
        * x['s'] or x['sign'] gives the sign bit for signed numbers. A
          KeyError is raised for unsigned numbers
        * x['msb'] gives the most significant bit
        * x['lsb'] gives the least significant bit

        Examples:
            >>> from fixedpoint import FixedPoint
            >>> x = FixedPoint('0b1111101', 0, 5, 2)
            >>> x.qformat, bin(x), float(x)
            ('UQ5.2', '0b1111101', 31.25)

            There are 3 ways to get the 4 LSbs:
            1) Treat x as a std_logic_vector(6 downto 0) - use high to low
            indexing and both high and low indices must be used.
            >>> x[3:0], bin(x[3:0])
            (13, '0b1101')

            2) Treat x as a std_logic_vector(0 to 6) - use low to high indexing
            >>> x[3:6], bin(x[3:6])
            (13, '0b1101')

            3) Treat it as a python string - using negative indices, or define
            a step in the slice
            >>> x[-4:], x[-4::1], bin(x[-4:])
            (13, 13, '0b1101')

            When a single index is used, the number is treated like a
            std_logic_vector with descending range.
            >>> x[1]
            0

            Get the most significant bit
            >>> x['msb']
            1

            Get the integer portion
            >>> x['m']
            31

            Because it is not signed, attempting to get the sign bit throws an
            exception
            >>> x['sign']
            Traceback (most recent call last):
                ...
            KeyError: ...

        """

        # Single bit; treat like a descending std_logic_vector with bit 0 being
        # the LSb.
        if isinstance(key, int):
            if not -(L := self._m + self._n) <= key < L:
                raise IndexError(f"Bit {key} does not exist in "
                    f"{self.qformat} format.")
            return (self._bits >> abs(key + (key < 0))) & 1

        # Get the binary string
        string = f"{self._bits:0{self._m + self._n}b}"

        # Special bit masks
        if isinstance(key, str):
            if (lkey := key.lower()) in ['m', 'int'] and self._m:
                ret = string[:self._m]
            elif lkey in ['n', 'frac'] and self._n:
                ret = string[-self._n:]
            elif lkey == 'msb' or (self._signed and lkey in ['s', 'sign']):
                ret = string[0]
            elif lkey == 'lsb':
                ret = string[-1]
            else:
                raise KeyError(f"Invalid bit specification {key!r} for {self.qformat}.")

        elif isinstance(key, slice):

            # Treat it as std_logic_vector when start and stop are present and
            # non-negative and step is not present
            if isinstance(key.start, int) and isinstance(key.stop, int) and \
            key.start >= 0 and key.stop >= 0 and key.step in [-1, None, 1]:
                # Ascending range
                if (key.start < key.stop or
                (key.start == key.stop and key.step == 1)):
                    ret = string[key.start:key.stop+1]
                # Descending range
                elif (key.start > key.stop or
                (key.start == key.stop and key.step == -1)):
                    ret = (string[::-1][key.stop:key.start+1])[::-1]
                else:
                    raise IndexError(f"Step must be 1 or -1 for equivalent start and stop bound {key.start}.")

            # Any other format, just deal with the raw binary string
            else:
                ret = string[key]
        else:
            raise TypeError(f"{type(key)} not supported.")

        retval: int
        if self.__flag:
            retval = ret # type: ignore
        else:
            # For (example) FixedPoint(-1,1,1,0), x[1:] is an empty string.
            retval = int(ret, 2) if ret else 0
        return retval

    def __iter__(self: FixedPointType) -> Iterable[int]:
        """Iterates from MSb to LSb, one bit at a time.
        """
        return iter((int(bit) for bit in f"{self:0{len(self)}b}"))

    def __reversed__(self: FixedPointType) -> Iterable[int]:
        """Iterates from LSb to MSb, one bit at a time.
        """
        return iter((int(bit) for bit in f"{self:0{len(self)}b}"[::-1]))

    ###########################################################################
    # Private properties
    ###########################################################################
    @property
    def _minimum(self: FixedPointType) -> int:
        """Determine the minimum representable bit value
        """
        return int(2**(self._m + self._n - 1) * -bool(self._signed))

    @property
    def _maximum(self: FixedPointType) -> int:
        """Determine the maximum representable bit value
        """
        return int(2**(self._m + self._n - bool(self._signed)) - 1)

    @property
    def _signedint(self: FixedPointType) -> int:
        """A signed version of the bits
        """
        return (self._bits & self._maximum) + self._negweight()

    @property
    def _maxfloat(self: FixedPointType) -> float:
        """Maximum floating point number that can be represented.

        Returns:
            float: Maximum floating point number that can be represented.
        """
        return float(self._maximum * 2**-self._n)

    @property
    def _minfloat(self: FixedPointType) -> float:
        """Minimum floating point number that can be represented.

        Returns:
            float: Minimum floating point number that can be represented.
        """
        return float(self._minimum * 2**-self._n)

    def _negweight(self: FixedPointType, bits: int = None, signed: bool = None,
    m: int = None, n: int = None) -> int:
        """Return the negative weight of the number. Uses self's attributes for
        arguments not provided.
        """
        bits = self._bits if bits is None else bits
        signed = bool(self._signed if signed is None else signed)
        m = self._m if m is None else m
        n = self._n if n is None else n
        ret = 2**(m + n - 1) & bits
        return int(ret * -signed)

    def _posweight(self: FixedPointType, bits: int = None, signed: bool = None,
    m: int = None, n: int = None) -> int:
        """Return the positive weight of the number. Uses self's attributes for
        arguments not provided.
        """
        bits = self._bits if bits is None else bits
        signed = bool(self._signed if signed is None else signed)
        m = self._m if m is None else m
        n = self._n if n is None else n
        mask = 2**(m + n - signed) - 1
        return int(mask & bits)

    ###########################################################################
    # Arithmetic (normal, augmented, and reflected) operators
    ###########################################################################
    # https://www.factmonster.com/math-science/mathematics/terms-used-in-equations
    def __add__(self: FixedPointType, other: Numeric) -> FixedPointType:
        """Addition. This is the "+" operator.

        A new FixedPoint object sum is generated. Neither self nor other are
        modified.

        Full integer precision is always retained; i.e., the following
        properties pertain to the return value:
        *  Qm.n +  Qa.b =  Qx.y
        *  Qm.n + UQa.b =  Qx.y
        * UQm.n + UQa.b = UQx.y
        where x = max(m, a) + 1 and y = max(n, b)

        """
        fother: FixedPointType
        if isinstance(other, FixedPoint):
            fother = other # type: ignore
        else:
            orig = other
            fother = self.__class__(other)

            # Ensure implicit cast is exact
            if isinstance(orig, float) and (error := abs(orig - float(fother))) != 0:
                self._iwarn("Casting %r to %s introduces an error of %e",
                    orig, fother.qformat, error)

            # Make properties the same to avoid mismatch alerts
            for prop in PROPERTIES:
                setattr(fother, f'_{prop}', getattr(self, f'_{prop}'))

        with self as augend, fother as addend: # type: FixedPoint, FixedPoint
            # Determine the Q format of the sum
            n = max(augend._n, addend._n)
            m = max(augend._m, addend._m) + 1
            signed = bool(self._signed or fother._signed)

            # Line up binary points (i.e., both terms should have same number of
            # fractional bits)
            augend.n = n
            addend.n = n

            # Sum some
            bits = augend._posweight() + addend._posweight() + \
                   augend._negweight() + addend._negweight()

        # Mask off superfluous bits
        bits &= 2**(m + n) - 1

        # Generate the return value
        if self.__flag:
            ret = bits, signed, m, n
        else:
            props = self.__class__._RESOLVE.all(self, fother)
            ret = self.__class__(hex(bits), signed, m, n, **props) # type: ignore

        return ret # type: ignore # tuple return type used internally

    def __radd__(self: FixedPointType, augend: Numeric) -> FixedPointType:
        """Reflected addition. Called with the augend is not a FixedPoint
        """
        return self.__add__(augend)

    def __iadd__(self: FixedPointType, addend: Numeric) -> FixedPointType:
        """Augmented addition. This is the "+=" operator.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits, self._signed, self._m, self._n = self + addend # type: ignore
        finally:
            self.__flag = old
        return self

    def __sub__(self: FixedPointType, other: Numeric) -> FixedPointType:
        """Subtraction. This is the "-" operator.

        Full integer precision is always retained; i.e., the following
        properties pertain to the return value:
            *  Qm.n -  Qa.b =  Qx.y
            *  Qm.n - UQa.b =  Qx.y
            * UQm.n -  Qa.b =  Qx.y
            * UQm.n - UQa.b = UQx.y
        where x = max(m, a) + 1 and y = max(n, b)

        For the final case (unsigned minus unsigned), overflow will occur if the
        subtrahend is greater than the minuend.
        """
        fother: FixedPointType
        if isinstance(other, FixedPoint):
            fother = other # type: ignore
        else:
            orig = other
            fother = self.__class__(other, signed=self._signed)

            # Ensure implicit cast is exact
            if isinstance(orig, float) and  (error := abs(orig - float(fother))) != 0:
                self._iwarn("Casting %r to %s introduces an error of %e",
                    orig, fother.qformat, error)

            # Make properties the same to avoid mismatch alerts
            for prop in PROPERTIES:
                setattr(fother, f'_{prop}', getattr(self, f'_{prop}'))

        with self as minuend, fother as subtrahend: # type: FixedPoint, FixedPoint
            # Determine the Q format of the difference
            signed = self._signed or fother._signed
            sign_mismatch = (self._signed ^ fother._signed) & 1
            m = 1 + max(minuend._m, subtrahend._m) + sign_mismatch
            n = max(minuend._n, subtrahend._n)

            # Line up binary points (i.e., both terms should have same number of
            # fractional bits)
            minuend.resize(m, n)
            subtrahend.resize(m, n)
            minuend._signed, subtrahend._signed = signed, signed

            # Subtract some
            bits = minuend._posweight() + minuend._negweight() \
                 - subtrahend._posweight() - subtrahend._negweight()

        # Check overflow condition
        if not signed and bits < 0:
            self._owarn("Unsigned subtraction causes overflow.")
            if clamp := (self._overflow.name == 'clamp'):
                bits = 0
            self._owarn("%s minimum.", "Clamped to" if clamp else "Wrapped")

        # Mask off superfluous bits
        bits &= 2**(m + n) - 1

        # Generate the return value
        if self.__flag:
            ret = bits, signed, int(m), int(n)
        else:
            props = self.__class__._RESOLVE.all(self, fother)
            ret = self.__class__(hex(bits), signed, m, n, **props) # type: ignore

        return ret # type: ignore # tuple return type used internally

    def __rsub__(self: FixedPointType, minuend: Numeric) -> FixedPointType:
        """Reflected subtraction. This is called when the minuend is not
        a FixedPoint object.
        """
        other = self.__class__(minuend, signed=self._signed)
        other._log("Implicit Cast:\n%r", other)

        # Ensure implicit cast is exact
        if isinstance(minuend, float) and (error := abs(minuend - float(other))) != 0:
            self._iwarn("Casting %r to %s introduces an error of %e",
                minuend, other.qformat, error)

        # Make properties the same to avoid mismatch alerts
        for prop in PROPERTIES:
            setattr(other, f'_{prop}', getattr(self, f'_{prop}'))

        return other - self

    def __isub__(self: FixedPointType, subtrahend: Numeric) -> FixedPointType:
        """Augmented subtraction. This is the "-=" operator.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits, self._signed, self._m, self._n = self - subtrahend # type: ignore
        finally:
            self.__flag = old
        return self

    def __mul__(self: FixedPointType, other: Numeric) -> FixedPointType:
        """Multiplication. This is the "*" operator.

        Full integer precision is always retained; i.e., the following
        properties pertain to the return value:
            *  Qm.n *  Qa.b =  Qx.y
            *  Qm.n * UQa.b =  Qx.y
            * UQm.n * UQa.b = UQx.y
        where x = m + a and y = n + b
        """
        fother: FixedPointType
        if isinstance(other, FixedPoint):
            fother = other # type: ignore
        else:
            orig = other
            fother = self.__class__(other)

            # Ensure implicit cast is exact
            if isinstance(orig, float) and (error := abs(orig - float(fother))) != 0:
                self._iwarn("Casting %r to %s introduces an error of %e.",
                    orig, fother.qformat, error)

            # Make properties the same to avoid mismatch alerts
            for prop in PROPERTIES:
                setattr(fother, f'_{prop}', getattr(self, f'_{prop}'))

        # Determine the Q format of the product
        m = self._m + fother._m
        n = self._n + fother._n
        signed = bool(self._signed or fother._signed)

        # Do the thing
        bits = self._signedint * fother._signedint
        bits &= 2**(m + n) - 1

        # Generate the return value
        if self.__flag:
            ret = bits, signed, int(m), int(n)
        else:
            # Generate properties for the return value
            props = self.__class__._RESOLVE.all(self, fother)
            ret = self.__class__(hex(bits), signed, m, n, **props) # type: ignore

        return ret # type: ignore # tuple return type used internally

    def __rmul__(self: FixedPointType, multiplicand: Numeric) -> FixedPointType:
        """Reflected multiplication. Called when the multiplicand is not a
        FixedPoint object.
        """
        return self * multiplicand

    def __imul__(self: FixedPointType, multiplier: Numeric) -> FixedPointType:
        """Augmented multiplication. This is the "*=" operator.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits, self._signed, self._m, self._n = self * multiplier # type: ignore
        finally:
            self.__flag = old
        return self

    def __matmul__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected matrix multiplication. Called when the FixedPoint object
        is on the right.
        """
        return NotImplemented

    def __rmatmul__(self: FixedPointType, other: Any) -> NotImplemented:
        """Matrix multiplication. This is the "@" operator.
        """
        return NotImplemented

    def __imatmul__(self: FixedPointType, other: Any) -> NotImplemented:
        """Augmented matrix multiplication. This is the "@=" operator.
        """
        return NotImplemented

    # For future reference, in case division is needed:
    # https://courses.cs.washington.edu/courses/cse467/08au/labs/l5/fp.pdf
    def __truediv__(self: FixedPointType, other: Any) -> NotImplemented:
        """Division. This is the "/" operator.
        """
        return NotImplemented

    def __rtruediv__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected division. Called when the dividend is not a FixedPoint
        object.
        """
        return NotImplemented

    def __itruediv__(self: FixedPointType, other: Any) -> NotImplemented:
        """Augmented division. This is the "/=" operator.
        """
        return NotImplemented

    def __floordiv__(self: FixedPointType, other: Any) -> NotImplemented:
        """Integer division. This is the "//" operator.
        """
        return NotImplemented

    def __rfloordiv__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected integer division. Called when the dividend is not a
        FixedPoint object.
        """
        return NotImplemented

    def __ifloordiv__(self: FixedPointType, other: Any) -> NotImplemented:
        """Augmented integer division. This is the "//=" operator.
        """
        return NotImplemented

    def __mod__(self: FixedPointType, other: Any) -> NotImplemented:
        """Modulus. This is the "%" operator.
        """
        return NotImplemented

    def __rmod__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected modulus. Called when the left term is not a FixedPoint.
        """
        return NotImplemented

    def __imod__(self: FixedPointType, other: Any) -> NotImplemented:
        """Augmented modulus. This is the "%=" operator.
        """
        return NotImplemented

    def __divmod__(self: FixedPointType, other: Any) -> NotImplemented:
        """Division and modulus built-in function divmod().
        """
        return NotImplemented

    def __rdivmod__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected division and modulus. Called when the left term is not a
        FixedPoint.
        """
        return NotImplemented

    def __pow__(self: FixedPointType, exponent: int) -> FixedPointType:
        """Exponentiation. This is the "**" operator. Only supports positive
        integer exponents.
        """
        if not (isinstance(exponent, int) and exponent > 0):
            raise TypeError("Only positive integers are supported for exponentiation.")

        # Determine the Q format of the result
        m = self._m * exponent
        n = self._n * exponent
        signed = self._signed

        # Do the thing
        bits = self._signedint**exponent
        bits &= 2**(m + n) - 1

        # Generate the return value
        if self.__flag:
            ret = bits, signed, m, n
        else:
            # Generate properties for the return value
            props = self.__class__._RESOLVE.all(self)
            ret = self.__class__(hex(bits), signed, m, n, **props) # type: ignore

        return ret # type: ignore

    def __ipow__(self: FixedPointType, exponent: int) -> FixedPointType:
        """Augmented exponentiation. This is the "**=" operator. Only
        supports positive integer exponents.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits, self._signed, self._m, self._n = self**exponent # type: ignore
        finally:
            self.__flag = old
        return self

    def __rpow__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected exponentiation. Called when the FixedPoint object
        is the exponent.
        """
        return NotImplemented

    def __lshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Literal left shift. This is the "<<" operator.
        """
        ret: FixedPointType
        if nbits < 0:
            ret = self.__rshift__(-nbits)
        else:
            if not isinstance(nbits, int):
                raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")
            ret = self.__class__(self)
            ret._bits = (self._signedint << nbits) & self.bitmask
        return ret

    def __ilshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Augmented literal left shift. This is the "<<=" operator.
        """
        if nbits < 0:
            self.__irshift__(-nbits)
        else:
            if not isinstance(nbits, int):
                raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")
            self._bits = (self._signedint << nbits) & self.bitmask
        return self

    def __rlshift__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected literal left shift. This is the <<" operator with a
        FixedPoint object on the right.
        """
        return NotImplemented

    def __rshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Literal right shift. This is the ">>" operator. If signed, shift
        occurs with sign extension.
        """
        if nbits < 0:
            ret = self.__lshift__(-nbits)
        else:
            if not isinstance(nbits, int):
                raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")
            ret = self.__class__(self)
            ret._bits = (self._signedint >> nbits) & self.bitmask
        return ret

    def __irshift__(self: FixedPointType, nbits: int) -> FixedPointType:
        """Augmented literal right shift. This is the ">>=" operator. If
        signed, shift occurs with sign extension.
        """
        if nbits < 0:
            self.__ilshift__(-nbits)
        else:
            if not isinstance(nbits, int):
                raise TypeError(f"Expected {type(1)}; got {type(nbits)}.")
            self._bits = (self._signedint >> nbits) & self.bitmask
        return self

    def __rrshift__(self: FixedPointType, other: Any) -> NotImplemented:
        """Reflected literal right shift. This is the ">>" operator with a
        FixedPoint object on the right.
        """
        return NotImplemented

    def __and__(self: FixedPointType, other: Union[FixedPointType, int]) -> FixedPointType:
        """Bitwise AND. This is the "&" operator.
        """
        mask: int
        if isinstance(other, FixedPoint):
            mask = other._bits
        elif isinstance(other, int):
            mask = other
        else:
            raise TypeError(f"Expected {type(1)} or {type(self)}; got {type(other)}.")

        bits = (self._bits & mask) & self.bitmask
        ret: FixedPointType
        if self.__flag:
            ret = bits # type: ignore
        else:
            ret = self.__class__(self)
            ret._bits = bits

        return ret

    def __rand__(self: FixedPointType, other: int) -> FixedPointType:
        """Reflected bitwise AND. Called when the left term is not a FixedPoint.
        """
        return self & other

    def __iand__(self: FixedPointType, other: Union[FixedPointType, int]) -> FixedPointType:
        """Augmented bitwise AND. This is the "&=" operator.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits = self & other # type: ignore
        finally:
            self.__flag = old
        return self

    def __or__(self: FixedPointType, other: Union[FixedPointType, int]) -> FixedPointType:
        """Bitwise OR. This is the "|" operator. Returns the FixedPoint object
        masked with the bits in other. The returned object has the same Q format
        as self.
        """
        mask: int
        if isinstance(other, FixedPoint):
            mask = other._bits
        elif isinstance(other, int):
            mask = other
        else:
            raise TypeError(f"Expected {type(1)} or {type(self)}; got {type(other)}.")

        bits = (self._bits | mask) & self.bitmask
        ret: FixedPointType
        if self.__flag:
            ret = bits # type: ignore
        else:
            ret = self.__class__(self)
            ret._bits = bits

        return ret

    def __ror__(self: FixedPointType, other: int) -> FixedPointType:
        """Reflected bitwise OR. Called when the left term is not a FixedPoint.
        """
        return self | other

    def __ior__(self: FixedPointType, other: Union[FixedPointType, int]) -> FixedPointType:
        """Augmented bitwise OR. This is the "|=" operator.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits = self | other # type: ignore
        finally:
            self.__flag = old
        return self

    def __xor__(self: FixedPointType, other: Union[FixedPointType, int]) -> FixedPointType:
        """Bitwise XOR. This is the "^" operator. Returns the FixedPoint object
        masked with the bits in other. The returned object has the same Q format
        as self.
        """
        mask: int
        if isinstance(other, FixedPoint):
            mask = other._bits
        elif isinstance(other, int):
            mask = other
        else:
            raise TypeError(f"Expected {type(1)} or {type(self)}; got {type(other)}.")

        bits = (self._bits ^ mask) & self.bitmask
        ret: FixedPointType
        if self.__flag:
            ret = bits # type: ignore
        else:
            ret = self.__class__(self)
            ret._bits = bits

        return ret

    def __rxor__(self: FixedPointType, other: int) -> FixedPointType:
        """Reflected bitwise XOR. Called when the left term is not a FixedPoint.
        """
        return self ^ other

    def __ixor__(self: FixedPointType, other: Union[FixedPointType, int]) -> FixedPointType:
        """Augmented bitwise XOR. This is the "^=" operator.
        """
        old, self.__flag = self.__flag, True
        try:
            self._bits = self ^ other # type: ignore
        finally:
            self.__flag = old
        return self

    ###########################################################################
    # Unary operators and functions
    ###########################################################################
    def __neg__(self: FixedPointType) -> FixedPointType:
        """Unary negation. This is the unary "-" operator.

        If overflow occurs and overflow_alert is not 'error', Q format will
        be modified to allow for negation.

        Unsigned numbers cannot be negated. This is done in hopes that user
        error is minimized. Use the signed property setter to change the
        object to a signed number, then negation can occur.
        """
        if not self._signed:
            from fixedpoint import FixedPointError
            raise FixedPointError("Unsigned numbers cannot be negated.")

        # Overflow only occurs if the number is at its max negative
        if overflow := (self._signedint == self._minimum):
            self._owarn("Negating %s%s (%s) causes overflow.",
                {16: '0x', 10: '', 8: '0o', 2: '0b'}[self._str_base.value],
                self, self.qformat)

            self._owarn("Adjusting Q format to Q%d.%d to allow negation.",
                self._m + 1, self._n)

        ret = self.__class__(0, True, self._m, self._n,
            **self.__class__._RESOLVE.all(self)) # type: ignore
        ret -= self
        if not overflow:
            ret.clamp(self._m, alert='error')

        return ret

    def __pos__(self: FixedPointType) -> FixedPointType:
        """Unary positive. This is the unary "+" operator.
        """
        return self.__class__(self)

    def __invert__(self: FixedPointType) -> FixedPointType:
        """Unary bitwise inversion. This is the unary "~" operator.
        """
        ret = self.__class__(self)
        ret._bits = ~self._bits & self.bitmask
        return ret

    ###########################################################################
    # Context management
    ###########################################################################
    def __call__(self: FixedPointType, *, safe_retain: bool = False,
    **props: Union[int, str]) -> FixedPointType:
        """Intended to be used with the context manager to assign properties
        temporarily. Any argument to the __init__ function can be used here
        except the initialization value.

        If `safe_retain` evaluates as True, the changes that occur inside the
        with statement context will be retained after the context ends only if
        there are no exceptions.
        >>> from fixedpoint import FixedPoint
        >>> x = FixedPoint(2)
        >>> float(x), x.qformat
        (2.0, 'UQ2.0')
        >>> with x(safe_retain=True, overflow_alert='error'):
        ...   x.clamp(1)
        ...
        Traceback (most recent call last):
            ...
        FixedPointOverflowError: ...
        >>> x.qformat
        'UQ2.0'
        >>> with x(safe_retain=True, overflow_alert='ignore'):
        ...   x.clamp(1)
        ...
        >>> float(x), x.qformat
        (1.0, 'UQ1.0')

        The order in which properties are specified matters. The following
        example shows how attempting to make an unsigned number signed with 0
        integer bits is illegal, and results in an exception.

        >>> from fixedpoint import FixedPoint
        >>> x = FixedPoint(0.25)
        >>> x.qformat
        'UQ0.2'
        >>> with x(signed=True, m=2):
        ...    bits = x.bits
        ...
        Traceback (most recent call last):
            ...
        FixedPointError: Cannot change sign with 0 integer bits

        However, if m is specified first in the list of key=value pairs, it
        will work.
        >>> from fixedpoint import FixedPoint
        >>> x = FixedPoint(0.25)
        >>> x.qformat
        'UQ0.2'
        >>> with x(m=2, signed=True):
        ...    bits = x.bits
        ...
        >>> bits
        1

        """
        try:
            self.__context['safe_retain'] = bool(safe_retain)
            for attr, value in props.items():
                # Only change valid attributes
                if f'_{attr}' not in self.__slots__:
                    raise AttributeError(f"Invalid FixedPoint attribute {attr!r}.")
                # Caller should not try to be accessing any "private" variables
                elif attr.startswith('_'):
                    raise PermissionError(f"Access to {attr!r} is prohibited.")
                self.__context[f'_{attr}'] = value
        except:
            self.__context = {}
        return self

    def __enter__(self: FixedPointType) -> FixedPointType:
        """Saves the current attributes of the FixedPoint object so it can be
        restored when the context manager exits.
        """
        # Push the current context onto the context manager stack
        self.__cmstack.append(_ENCODER.encode(self))
        # Push the safe_retain option to the context manager stack
        self.__cmstack.append(self.__context.pop('safe_retain', False))

        # Assign temporary context items from __call__ to the current object.

        try:
            # Note that __call__ is optional, so __context may be empty.
            for attr, value in self.__context.items():
                # To assign the value to the attribute, go through the property
                # setter function if it exists, which validates and normalizes the
                # value to the correct type (e.g., @signed.setter ensures it's a
                # bool). Filched from https://stackoverflow.com/questions/3681272/can-i-get-a-reference-to-a-python-property
                prop = self.__class__.__dict__.get(attr[1:], None)
                if isinstance(prop, property) and bool(prop.fset):
                    prop.fset(self, value) # type: ignore
                else:
                    raise PermissionError(f"{attr[1:]!r} is read-only.")
        finally:
            # Context has been adopted, or some exception was raised. Reset it
            # so it can be reused later.
            self.__context = {}

        return self

    def __exit__(self: FixedPointType, exc_type: Type[Exception], *args: Any) -> None:
        """Restores the attributes of the FixedPoint object as it was when
        the context manager was entered.
        """
        # If no exception occurred, and safe_retain is True, do not restore
        # context
        if self.__cmstack.pop() and exc_type is None:
            # Remove context from context manager stack.
            self.__cmstack.pop()
            return

        # See the FixedPointEncoder.default method in .\json.py for the
        # serialization order of FixedPoint object attributes.
        attributes = _DECODER.decode_attributes(self.__cmstack.pop())
        self._bits = attributes.pop() # type: ignore
        self._signed, self._m, self._n = attributes.pop() # type: ignore
        for attr, value in attributes.pop().items(): # type: ignore
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
            ret = self.__class__(self)
        return ret

    def __int__(self: FixedPointType) -> int:
        """Integer cast of the fixed point value. The behavior is NOT the same
        as casting a float (which rounds toward 0). Returns the integer bits
        of the fixed point number, with sign.

        >>> from fixedpoint import FixedPoint
        >>> int(1.5), int(FixedPoint(1.5))
        (1, 1)
        >>> int(-1.5), int(FixedPoint(-1.5))
        (-1, -2)

        """
        return self._signedint >> self._n

    def __float__(self: FixedPointType) -> float:
        """Floating point representation of the stored value.

        For large numbers, this may not be bit accurate! Python's float
        typically follows IEEE 754 format, which means there's 52 bits of
        accuracy in a float. You can see information about your machine's
        float format by inspecting sys.float_info.

        If an object cannot be represented by a float type (i.e., its magnitude
        is too large), then inf or -inf is returned.
        >>> from fixedpoint import FixedPoint
        >>> x = FixedPoint(2**4000, 0, 4001, 0)
        >>> int(x) == 2**4000
        True
        >>> float(x)
        inf

        """
        try:
            ret = float((ret := self._signedint) * 2**-self._n)
        except OverflowError:
            ret = float('-inf' if ret < 0 else 'inf')
        return ret

    def __bool__(self: FixedPointType) -> bool:
        """True if non-zero.
        """
        return bool(self._bits)

    def __index__(self: FixedPointType) -> int:
        """Used for bin(), oct(), and hex(). Returns the bit value.
        """
        return self._bits

    def __str__(self: FixedPointType) -> str:
        """String representation of the stored value w/out its radix.

        Use the str_base property to adjust which base to use for this function.

        For str_base of 2, 8, or 16, output will be 0-padded to the bit width
        of the object.
        """
        ret = StrConv[self._str_base.value](self._bits)

        # Zero padding
        if self._str_base.value == 10:
            return ret

        # Remove radix
        ret = ret[2:]
        bits_needed = self._m + self._n
        nzeros = _ceil(bits_needed / _log2(self._str_base.value))
        return ret.zfill(nzeros)

    def __format__(self: FixedPointType, spec: str) -> str:
        """Format the raw bits with integer specs or the float equivalent using
        float specs.

        Format specification can be found here:
        https://docs.python.org/3/library/string.html#string-formatting

        The only addition is the type format 'q', which generates the Q format
        string.

        Examples:
            >>> from fixedpoint import FixedPoint
            >>> x = FixedPoint(3.1415926535)
            >>> x.qformat, f"{x:q}"
            ('UQ2.49', 'UQ2.49')
            >>> f"{x:_^+21.5g}"
            '_______+3.1416_______'
            >>> "{:#032x}".format(x)
            '0x000000000000000006487ed51045d1'

        """
        # By default, format this as a decimal number.
        if spec == '' or spec[-1] in 'bdoxX' or spec is None:
            ret = format(self._bits, spec)

        # Use just the integer bits for 'm'
        elif spec[-1] in 'm':
            ret = format((self._bits >> self._n) & (2**self._m - 1), spec[:-1])

        # Use just the integer bits for 'n'
        elif spec[-1] in 'n':
            ret = format(self._bits & (2**self._n - 1), spec[:-1])

        # If the format spec is 's', use str, which keys off of str_base
        elif spec[-1] in 's':
            ret = format(str(self), spec)

        # For float formats, convert to float
        elif spec[-1] in 'eEfFgG%':
            ret = format(float(self), spec)

        # Also allow q format specs
        elif spec[-1] == 'q':
            ret = format(self.qformat, f"{spec[:-1]}s")

        # Any other spec is invalid
        else:
            raise ValueError(f"Unknown format code {spec!r}.")

        return ret

    def __repr__(self: FixedPointType) -> str:
        """Python-executable code string indicating how this object can be
        reproduced.
        """
        str_base = self._str_base.value
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
            f"{str_base=})"
        )

    ###########################################################################
    # Comparison magic methods
    ###########################################################################
    def __cmp__(self: FixedPointType, other: Numeric) -> int:
        '''Comparison operator. Generic for >, >=, <, <=, ==, !=.

        This is not a magic method in python 3, but accomplishes what we want
        generically, so it is used by the actual operator calls.

        Returns:
            int: negative if self < other, 0 if self == other, positive if
                self > other.
        '''
        fother: FixedPoint
        if isinstance(other, FixedPoint):
            fother = other
        else:
            fother = self.__class__(other)

        # Force a signed subtraction - grow by one bit temporarily to safely
        # convert to a signed number if needed
        with self(mismatch_alert='ignore', m=self._m+1, signed=1) as left:
            old, left.__flag = left.__flag, True
            try:
                args = left - fother
                ret = self._posweight(*args) + self._negweight(*args) # type: ignore
            finally:
                left.__flag = old

        self._log("SELF: %.60f %s %s\n"
            "OTHER: %.60f %s %s\n"
            "ARGS: %s\n"
            "POSWEIGHT: %d\n"
            "NEGWEIGHT: %d\n"
            "RETURN: %d",
            float(self), self.qformat, bin(self._bits),
            float(fother), fother.qformat, bin(fother._bits),
            str(args),
            self._posweight(*args), # type: ignore
            self._negweight(*args), # type: ignore
            ret,
        )

        return ret

    def __eq__(self: FixedPointType, other: Any) -> bool:
        '''Equality. This is the "==" operator.
        '''
        return self.__cmp__(other) == 0

    def __ne__(self: FixedPointType, other: Any) -> bool:
        '''Non-equality. This is the "!=" operator.
        '''
        return self.__cmp__(other) != 0

    def __lt__(self: FixedPointType, other: Any) -> bool:
        '''Less than. This is the "<" operator.
        '''
        return self.__cmp__(other) < 0

    def __le__(self: FixedPointType, other: Any) -> bool:
        '''Less than or equal to. This is the "<=" operator.
        '''
        return self.__cmp__(other) <= 0

    def __gt__(self: FixedPointType, other: Any) -> bool:
        '''Greater than. This is the ">" operator.
        '''
        return self.__cmp__(other) > 0

    def __ge__(self: FixedPointType, other: Any) -> bool:
        '''Greater than or equal to. This is the ">=" operator.
        '''
        return self.__cmp__(other) >= 0

    ###########################################################################
    # Bit resizing methods
    ###########################################################################
    def resize(self: FixedPointType, m: int, n: int, /,
    rounding: str = None, overflow: str = None, alert: str = None) -> None:
        """Resizes a number to a specific number of integer and fractional bits.
        The number of fractional bits remaining after rounding is n. The
        number of integer bits remaining after rounding is m.

        If n is less than the current number of fractional bits, rounding
        behavior is specified by on the rounding argument. If this is not
        specified, the current rounding property setting is used.

        If m is less than the current number of integer bits, overflow
        behavior is specified by the overflow argument. If this is not
        specified, the current overflow property setting is used.

        The overflow_alert setting can be changed temporarily using the `alert`
        argument. This is useful if you are expecting overflow but want to
        continue processing after overflow detection.

        The overflow, rounding, and alert arguments are local only to this
        function. They do not change the properties of the object.
        >>> from fixedpoint import FixedPoint
        >>> x = FixedPoint(2.5, overflow='clamp', overflow_alert='ignore')
        >>> x.qformat
        'UQ2.1'
        >>> x.resize(1, 1, overflow='wrap')
        >>> bin(x)
        '0b1'
        >>> x.qformat
        'UQ1.1'
        >>> x.overflow
        'clamp'

        Fractional bits are resized first, followed by integer bits.
        """
        old = self._overflow, self._rounding, self._overflow_alert
        try:
            with self(safe_retain=True,
            overflow=overflow or self._overflow.name,
            rounding=rounding or self._rounding.name,
            overflow_alert=alert or self._overflow_alert.name):

                self.n = n
                self.m = m

        except:
            raise
        else:
            self._overflow, self._rounding, self._overflow_alert = old

    def trim(self: FixedPointType, /, ints: bool = None, fracs: bool = None) -> None:
        """Trims off insignificant bits (i.e., truncates trailing 0s, leading
        0s, and leading 1s - leaving 1 for sign - for signed numbers). If
        integer and fractional bits can both be trimmed to 0 length, integer
        bits will remain at 1, unless it's already at 0.

        You can opt to trim only integer bits or fractional bits by setting
        fracs or ints to True. By default, both integer and fractional bits
        are trimmed.
        """
        if ints is None and fracs is None:
            ints, fracs = True, True

        s, m, n = bool(self._signed), self._m, self._n
        old, self.__flag = self.__flag, True
        try:
            # Trailing 0s on fractional bits can be stripped
            if fracs:
                n = len(self['n'].rstrip('0')) if n else 0 # type: ignore

            if ints:
                # Remove leading 1s for negative numbers, leave 1 though
                if self._signedint < 0:
                    m = 1 + len(self['m'].lstrip('1')) # type: ignore
                # Remove all leading 0s
                # For signed, minimum m is 1
                # For unsigned, m can be 0 iff n is non-zero
                elif self._m:
                    m = max(s or n == 0, s + len(self['m'].lstrip('0'))) # type: ignore
                else:
                    m = self._m
        finally:
            self.__flag = old

        self._log("INTS:  %s\n"
            "FRACS: %s\n"
            "Trimming %d fractional bits\n"
            "Trimming %d integer bits\n", ints, fracs, self._n - n, self._m - m)

        self._bits >>= (self._n - n)
        self._n = n
        self._m = int(m)
        self._bits &= self.bitmask

    #__________________________________________________________________________
    # Rounding methods
    def __round__(self: FixedPointType, nfrac: int, /) -> FixedPointType:
        """Fractional rounding. This is the "round()" function.

        The rounding method used by this function is specified by the
        rounding attribute of this object.
        """
        ret = self.__class__(self)
        ret.round(nfrac)
        return ret

    def __floor__(self: FixedPointType) -> FixedPointType:
        """Round to negative infinity, but leave the number of fractional bits
        unmodified This is the "math.floor()" function. Creates a new
        FixedPoint object.

        >>> import fixedpoint, math
        >>> a = fixedpoint.FixedPoint(3.1415926535)
        >>> a.qformat
        'UQ2.49'
        >>> b = math.floor(a)
        >>> float(b), b.qformat
        (3.0, 'UQ2.49')

        """
        # When binary bits are truncated, it rounds to negative infinity.
        ret = self.__class__(self)
        if self._n:
            ret._bits &= ~(2**self._n - 1) & self.bitmask
        return ret

    def __ceil__(self: FixedPointType) -> FixedPointType:
        """Round to positive infinity, leaving 0 fractional bits. This is the
        "math.ceil()" function. Creates a new FixedPoint object.
        """
        ret = self.__class__(self)
        ret.round_up(0)
        return ret

    def __trunc__(self: FixedPointType) -> FixedPointType:
        """Truncates all fractional bits. This is the "math.trunc()" function.
        Creates a new FixedPoint object.

        When the number of integer bits is 0 - which may be the case for
        unsigned numbers in the range [0, 1) - the result will be UQ1.0.

        >>> import fixedpoint, math
        >>> x = fixedpoint.FixedPoint(0.25)
        >>> x.qformat
        'UQ0.2'
        >>> y = math.trunc(x)
        >>> float(y), y.qformat
        (0.0, 'UQ1.0')

        Truncation is done with respect to binary bits, not decimal digits.

        >>> import fixedpoint, math
        >>> from math import trunc
        >>> x = -1.5
        >>> y = fixedpoint.FixedPoint(x)
        >>> math.trunc(x), float(math.trunc(y))
        (-1, -2.0)

        """
        ret = self.__class__(self)
        ret._bits >>= ret._n
        ret._n = 0
        # Signed numbers are guaranteed to have at least 1 integer bit. Unsigned
        # numbers are not
        ret._m = ret._m or 1
        return ret

    def round(self: FixedPointType, nfrac: int, /) -> None:
        """Use the rounding method specified by the rounding attribute. The
        number of fractional bits left after rounding is nfrac.
        """
        getattr(self, f"round_{self._rounding.name}")(nfrac)

    def convergent(self: FixedPointType, nfrac: int, /) -> None:
        """Convergent rounding. The number of fractional bits left after
        rounding is nfrac.
        """
        try:
            self._rounding_arg_check(nfrac)
        except:
            raise

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
        """Rounding toward 0. The number of fractional bits left after rounding
        is nfrac.
        """
        try:
            self._rounding_arg_check(nfrac)
        except:
            raise

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
        """Round to nearest value with ties rounding away from 0. The number of
        fractional bits left after rounding is nfrac.
        """
        try:
            self._rounding_arg_check(nfrac)
        except:
            raise

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
        """Rounding toward nearest value, with ties rounded to positive.
        infinity. The number of fractional bits left after rounding is nfrac.
        """
        try:
            self._rounding_arg_check(nfrac)
        except:
            raise

        m, n, bits = self._m, self._n, self._bits

        # Truncate bits
        num_bits_truncated = n - nfrac
        truncated_bits = bits & (2**num_bits_truncated - 1)
        tie_threshold = 1 << (num_bits_truncated-1)
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
        """Rounding toward infinity. The number of fractional bits left after
        rounding is nfrac.
        """
        try:
            self._rounding_arg_check(nfrac)
        except:
            raise

        m, n, bits = self._m, self._n, self._bits

        # Truncate bits
        num_bits_truncated = n - nfrac
        truncated_bits = bits & (2**num_bits_truncated - 1)
        tie_threshold = 1 << (num_bits_truncated-1)
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
        """Rounding toward negative infinity. The number of fractional bits left
        after rounding is nfrac.
        """
        try:
            self._rounding_arg_check(nfrac)
        except:
            raise

        self._bits >>= self._n - nfrac
        self._n = nfrac

    def keep_msbs(self: FixedPointType, m: int, n: int, /,
    rounding: str = None, overflow: str = None, alert: str = None) -> None:
        """Round off LSbs, and reformat to the given number of bits. The number
        of bits left after rounding is m + n. Uses the indicated rounding and
        overflow scheme if specified, otherwise uses the current property
        setting. The overflow_alert property can be modified too if needed.
        Specifying a rounding, overflow, or overflow_alert property is local
        to this method; it will not change the object's properties permanently.
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
        overflow=overflow or self._overflow.name,
        overflow_alert=alert or self._overflow_alert.name):
            # Move the binary point but keep the same bits
            self._m, self._n = m, self._m + self._n - m
            # Now round off unwanted bits
            func = getattr(self, f'round_{rounding or self._rounding.name}')
            func(n)
            # If execution gets here, rounding did not cause an exception.
            # Revert the local overflow and overflow_alert properties back.
            self._overflow, self._overflow_alert = old

    #__________________________________________________________________________
    # Overflow methods
    def clamp(self: FixedPointType, nint: int, /, alert: str = None) -> None:
        """Removes integer bits and clamps if necessary. The number of integer
        bits left after clamping is nint. For signed numbers, nint does not
        include the sign bit. You can locally change the overflow alert level
        by specifying alert, otherwise the current overflow_alert setting is
        used.
        """
        if not isinstance(nint, int):
            raise TypeError(f"Expected {type(1)}; got {type(nint)}.")

        signed, m, n, bits = self._signed, self._m, self._n, self._bits

        # Validate arguments
        if not int (n == 0 or signed) <= nint < m:
            raise ValueError(f"{self:q} can only clamp between "
                f"[{int(n == 0 or signed)}, {m}) integer bits.")

        # Truncate and see if the values still match
        nbits = nint + n
        signedint = bits & (2**(nbits - signed) - 1)
        signedint -= bits & (signed * 2**(nbits-1))

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
        """Removes integer bits. The number of integer bits left afterwards is
        nint. For signed numbers, nint includes the sign bit. You can locally
        change the overflow alert level by specifying alert, otherwise the
        current overflow_alert setting is used.

        Examples:
            >>> from fixedpoint import FixedPoint
            >>> a = FixedPoint('0b10101', 1, 3, 2)
            >>> a.qformat, bin(a), float(a)
            ('Q3.2', '0b10101', -2.75)
            >>> a.wrap(1, 'ignore')
            >>> a.qformat, bin(a), float(a)
            ('Q1.2', '0b101', -0.75)

        """
        if not isinstance(nint, int):
            raise TypeError(f"Expected {type(1)}; got {type(nint)}.")

        signed, m, n, bits = bool(self._signed), self._m, self._n, self._bits

        # Validate arguments
        if not int (n == 0 or signed) <= nint < m:
            raise ValueError(f"{self:q} can only wrap between "
                f"[{int(n == 0 or signed)}, {m}) integer bits.")

        # Detect a change in value
        nbits = nint + n
        signedint = bits & (2**(nbits - signed) - 1)
        signedint -= bits & (signed * 2**(nbits-1))

        # Warn on overflows
        if signedint != (tmp := self._signedint):

            # Change local alert setting
            olvl = self._overflow_alert.name
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

    def keep_lsbs(self: FixedPointType, m: int, n: int, /,
    overflow: str = None, alert: str = None) -> None:
        """Remove MSbs, and reformat to the given number of bits. The number
        of bits left after removing MSbs is m + n. Uses the indicated overflow
        scheme if specified, otherwise uses the current property setting. The
        overflow_alert property can be modified too if needed. Specifying a
        overflow or overflow_alert property is local to this method; it will
        not change the object's properties permanently.
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
        signedint -= bits & (signed * 2**(length-1))

        # Change local alert setting
        olvl = self._overflow_alert.name
        self._overflow_alert = Alert[alert or olvl]

        # Warn on overflows
        if signedint != (tmp := self._signedint):

            # Warn on overflows
            try:
                self._owarn("Overflow in format %s.", self.qformat)
                clamp = (overflow or self._overflow.name) == 'clamp'
                self._owarn("%s %s.", 'Clamped to' if clamp else 'Wrapped',
                    'minimum' if tmp < 0 else 'maximum')

            # Revert back to original alert level
            except:
                self._overflow_alert = Alert[olvl]
                raise

        # Move the binary point but keep the same bits
        self._m, self._n = self._m + self._n - n, n
        # Now use the preferred method to remove unwanted bits
        func = getattr(self, overflow or self._overflow.name)
        # The alert has already been issued if needed, handle overflow silently.
        func(m, 'ignore')
        # Revert back to the original alert level
        self._overflow_alert = Alert[olvl]

    ###########################################################################
    # Error handling
    ###########################################################################
    def _format_exception_msg(self: FixedPointType, msg: str, args: Tuple[Any, ...]) -> None:
        return f"[SN{self.__id['extra']['sn']}] {msg}" % args # type: ignore

    def _mwarn(self: FixedPointType, msg: str, *args: Any, **kwargs: int) -> None:
        """Mismatch warning method. Use as you would a logger function. The
        level is set by virtue of the mismatch_alert property.
        """
        keywords = {**self.__id, **kwargs}
        if self._mismatch_alert == Alert['error']:
            from fixedpoint import MismatchError
            _LOGGER.error(msg, *args, **keywords, stack_info=1) # type: ignore
            raise MismatchError(self._format_exception_msg(msg, args))
        _WARNER.log(self._mismatch_alert.value, msg, *args, **keywords) # type: ignore

    def _owarn(self: FixedPointType, msg: str, *args: Any, **kwargs: int) -> None:
        """Overflow warning method. Use as you would a logger function. The
        level is set by virtue of the overflow_alert property.
        """
        keywords = {**self.__id, **kwargs}
        if self._overflow_alert == Alert['error']:
            from fixedpoint import FixedPointOverflowError
            _LOGGER.error(msg, *args, **keywords, stack_info=1) # type: ignore
            raise FixedPointOverflowError(self._format_exception_msg(msg, args))
        _WARNER.log(self._overflow_alert.value, msg, *args, **keywords) # type: ignore

    def _iwarn(self: FixedPointType, msg: str, *args: Any, **kwargs: int) -> None:
        """Implicit Cast warning method. Use as you would a logger function. The
        level is set by virtue of the implicit_cast_alert property.
        """
        keywords = {**self.__id, **kwargs}
        if self._implicit_cast_alert == Alert['error']:
            from fixedpoint import ImplicitCastError
            _LOGGER.error(msg, *args, **keywords, stack_info=1) # type: ignore
            raise ImplicitCastError(self._format_exception_msg(msg, args))
        _WARNER.log(self._implicit_cast_alert.value, msg, *args, **keywords) # type: ignore

    def _log(self: FixedPointType, msg: str, *args: Any, **kwargs: int) -> None:
        """Default logger.
        """
        keywords = {**self.__id, **kwargs}
        _LOGGER.debug(msg, *args, **keywords) # type: ignore

    def _rounding_arg_check(self: FixedPointType, nfrac: int) -> None:
        """Ensures nfrac is in the range [0, self._n) and that there is at least
        1 integer or fractional bit after rounding.
        """
        if not isinstance(nfrac, int):
            raise TypeError(f"Expected {type(1)}; got {type(nfrac)}.")

        if self._m + nfrac == 0 or (self._m == 0) == self._n:
            raise ValueError("Word size (integer and fractional) must be positive.")

        if not (self._m == 0) <= nfrac < self._n:
            raise ValueError("Number of fractional bits remaining after round "
                f"must be in the range [{int(self._m == 0)}, {self._n}).")

    @staticmethod
    def enable_logging() -> None:
        '''Enables the FixedPoint logger.
        '''
        _LOGGER.setLevel(_logging.DEBUG)

    @staticmethod
    def disable_logging() -> None:
        '''Disables the FixedPoint logger.
        '''
        _LOGGER.setLevel(_logging.CRITICAL)

    @classmethod
    def sign(cls: Type[FixedPointType], fp: Numeric, /) -> int:
        """Determine the sign of a numerical object. This is quicker than
        comparing to 0.

        Returns:
            int: -1 if val < 0, 1 if val > 0, 0 otherwise
        """
        signed: Union[int, float]
        if isinstance(fp, cls):
            signed = fp._signedint
        else:
            signed = fp
        return (signed > 0) - (signed < 0)

    @classmethod
    def min_m(cls: Type[FixedPointType], val: Union[float, int], /, signed: bool = None) -> int:
        """Calculate the minimum number of fixed point integer bits required to
        represent a number. Includes the sign bit if negative.

        This assumes worst case rounding. E.g. 3.25 can be represented with 2
        integer bits, 2 fractional bits, and no sign. However, the following
        example would generate an FixedPointOverflowError, because 3.25 would
        round up to 4, which needs 3 integer bits to represent.

        >>> from fixedpoint import FixedPoint
        >>> FixedPoint(3.25, 0, 2, 0, rounding='up')
        Traceback (most recent call last):
            ...
        FixedPointOverflowError: ...

        """
        # Start with an educated guess; round the value away from 0 and calculate
        # bit width from there, since that would be worst-case rounding
        wcround = cls.sign(val) * _ceil(abs(val))
        ret = _ceil(_log2(abs(wcround))) if val else 1

        # A signed number ranges from [-2**(m-1), 2**(m-1)-1]
        if signed or val < 0:
            while not -(boundary := 2**(ret-1)) <= wcround < boundary:
                ret += 1

        # An unsigned number ranges from [0, 2**m-1]
        else:
            ret += wcround >= 2**ret

        return int(ret)

    @classmethod
    def min_n(cls: Type[FixedPointType], val: Union[int, float], /, *,
    lo: int = 0, hi: int = _MAXEXPONENT) -> int:
        """Calculate the number of fixed point fractional bits required to
        represent a float with no error.

        Keyword arguments lo and hi are for the internally-used recursive binary
        search and shouldn't be used.

        >>> from fixedpoint import FixedPoint
        >>> FixedPoint.min_n(2**-15)
        15
        >>> FixedPoint.min_n(42)
        0

        >>> # The minimum representable floating point number requires at least
        >>> # the maximum negative exponent bit width available
        >>> import sys
        >>> FixedPoint.min_n(sys.float_info.min) >= abs(sys.float_info.min_exp)
        True

        """
        # Recursive binary search; fast but overflow-prone
        try:
            if lo + 1 == hi:
                ret = hi if (val * 2**lo) % 1.0 else lo

            elif (val * 2**(n := _ceil((lo + hi) / 2))) % 1.0:
                ret = cls.min_n(val, lo=n, hi=hi)

            else:
                ret = cls.min_n(val, lo=lo, hi=n)

        # Bubble search; slow but overflow-safe. Use as a last resort
        except OverflowError:
            ret = lo
            while val % 1.0: # pragma: no cover
                ret += 1
                val *= 2.0

        return ret

