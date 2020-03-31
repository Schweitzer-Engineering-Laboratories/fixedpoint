###############################################################################
Bit Slicing
###############################################################################

..  currentmodule:: fixedpoint

Sometimes you want to access only certain bits of a :class:`FixedPoint` number.
The :attr:`.FixedPoint.bits` attribute returns a :class:`FixedPointBits` object,
which is an :class:`int` that support square bracket access.

*******************************************************************************
Bit Random Access
*******************************************************************************

One or more contiguous bits in the :class:`FixedPointBits` can be accessed
with an :class:`int` or :class:`slice` key.

..  _single_bit_slice:

Single-Bit Random Access
===============================================================================

To access a single bit use an integer key. Bits are indexed with the MSb being
index ``m+n-1`` and the LSb being index 0.

..  doctest:: slice single bit
    :skipif: should_skip("slice single bit")

    >>> x = FixedPoint('0b001001', signed=0, m=3, n=3, str_base=2)
    >>> bin(x.bits), x.bits[3]
    ('0b1001', 1)

You can also access a single bit using a :class:`slice` when start and stop
values are equal. The slice step must be either

* **-1** (indicating a descending range with the MSb as index ``m+n-1`` and the
  LSb as index 0)
* **+1** (indicating an ascending range with the MSb as index 0 and the LSb as
  index ``m+n-1``)

..  doctest:: slice single bit
    :skipif: should_skip("slice single bit")

    >>> x = FixedPoint('0b001000', signed=0, m=3, n=3)
    >>> x.bits[3:3:-1] # the middle '1' with a descending range
    1
    >>> x.bits[2:2:1] # the middle '1' with an ascending range
    1

Attempting to access a single bit in this fashion (the slice start and stop
are equal) without specifying a step results in an error.

..  doctest:: slice single bit
    :skipif: should_skip("slice single bit")

    >>> x.bits[3:3]
    Traceback (most recent call last):
        ...
    IndexError: Step must be 1 or -1 for equivalent start and stop bound 3.

..  _multi_bit_slice:

Multi-Bit Random Access
===============================================================================

To access multiple bits at a time, :class:`slice`\ s are employed. Both
ascending and descending ranges are supported.

..  doctest:: multi-bit slicing
    :skipif: should_skip("multi-bit slicing")

    >>> x = FixedPoint(0b0001100, m=7)
    >>> x.bits[3:2] # Access the middle two 1s using a descending range
    3
    >>> x.bits[3:2:-1] # The step can be -1 for clarity but is unnecessary
    3
    >>> x.bits[3:4] # Access the middle two 1s using an ascending range
    3
    >>> x.bits[3:4:1] # The step can be +1 for clarity but is unnecessary
    3

When a step is used that is not 1 or -1, or when the start/stop index is
negative, the slice accesses the bits as if they were a :class:`str`.

..  doctest:: multi-bit slicing
    :skipif: should_skip("multi-bit slicing")

    >>> x = FixedPoint(0b100_100_100_100)
    >>> x.bits[::3] # Get every 3rd bit starting from the first
    15
    >>> bin(x.bits[:-6]) # Get the last 6 bits
    '0b100100'

..  _bit_mapping:

*******************************************************************************
Bit Mappings
*******************************************************************************

Common parts of the `FixedPoint` bit string are mapped to keys, specified as
strings (like a :obj:`dict`).

These include:

* integer bits (``'m'`` or ``'int'``)
* fractional bits (``'n'`` or ``'frac'``)
* sign bit (``'s'`` or ``'sign'``)
* most significant bit (``'msb'``)
* least significant bit (``'lsb'``)

If the portion of the `FixedPoint` bits does not exist (e.g., the sign bit of
an unsigned number), a :exc:`KeyError` is raised.

..  doctest:: mappings
    :skipif: should_skip("mappings")

    >>> intonly = signed = FixedPoint("0b1110", 1, 4, 0)
    >>> fraconly = unsigned = FixedPoint("0b0001", 0, 0, 4)
    >>> intonly.bits['m']
    14
    >>> fraconly.bits['int']
    Traceback (most recent call last):
        ...
    KeyError: "Invalid bit specification 'int' for UQ0.4 format."

    >>> intonly.bits['n']
    Traceback (most recent call last):
        ...
    KeyError: "Invalid bit specification 'n' for Q4.0 format."
    >>> signed.bits['sign']
    1
    >>> (-signed).bits['s']
    0
    >>> unsigned.bits['sign']
    Traceback (most recent call last):
        ...
    KeyError: "Invalid bit specification 'sign' for UQ0.4 format."

    >>> intonly.bits['msb'], intonly.bits['lsb']
    (1, 0)
    >>> fraconly.bits['msb'], fraconly.bits['lsb']
    (0, 1)

When the mappings are uppercased, a :class:`str` type is returned corresponding
to the binary bits.

..  doctest:: mappings
    :skipif: should_skip("mappings")

    >>> intonly = signed = FixedPoint("0b1110", 1, 4, 0)
    >>> fraconly = unsigned = FixedPoint("0b0001", 0, 0, 4)
    >>> intonly.bits['M']
    '1110'
    >>> fraconly.bits['INT']
    Traceback (most recent call last):
        ...
    KeyError: "Invalid bit specification 'INT' for UQ0.4 format."

    >>> intonly.bits['N']
    Traceback (most recent call last):
        ...
    KeyError: "Invalid bit specification 'N' for Q4.0 format."
    >>> signed.bits['SIGN']
    '1'
    >>> (-signed).bits['S']
    '0'
    >>> unsigned.bits['SIGN']
    Traceback (most recent call last):
        ...
    KeyError: "Invalid bit specification 'SIGN' for UQ0.4 format."

    >>> intonly.bits['MSB'], intonly.bits['LSB']
    ('1', '0')
    >>> fraconly.bits['MSB'], fraconly.bits['LSB']
    ('0', '1')
