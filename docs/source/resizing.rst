..  currentmodule:: fixedpoint

###############################################################################
Bit Resizing
###############################################################################

..  attention::

    The code examples on this page change betwee the *function* version and the
    *method* version of the resizing operation. For example, **y1**, and **y2**
    in the following example are equivalent, and **x** remains unchanged:

    ..  doctest:: function vs. method
        :skipif: should_skip("function vs. method")

        >>> (x := FixedPoint(-1.5)).qformat
        'Q2.1'
        >>> y1 = FixedPoint(x)
        >>> y1.resize(10, 10)

        >>> y2 = resize(x, 10, 10)

        >>> print(f'{x.qformat=}\n{y1.qformat=}\n{y2.qformat=}')
        x.qformat='Q2.1'
        y1.qformat='Q10.10'
        y2.qformat='Q10.10'

    The function will operate on a copy of the given object, so the original
    object is not modified.

..  _resize:

*******************************************************************************
resize
*******************************************************************************

Using :meth:`.FixedPoint.resize` or :func:`~.resize`, the fractional and integer
bit width can grow or shrink. The bit widths are modified based on the position
of the binary point, so as long as overflow or rounding does not occur, the
value does not change.

..  testsetup:: resize
    :skipif: should_skip("resize")

    reset_sn()

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> from fixedpoint import FixedPoint
    >>> def show(A):
    ...     print(f"{A: <+5.2f}  ", end="")       # float
    ...     print(f"{A:>5q}  ", end="")           # Q format
    ...     print(f"{A:0{A.m+(A.m-1)//4}_bm}." if A.m else ".", end="")
    ...     print(f"{A:0{A.n}_bn}" if A.n else "") # Show binary point

    >>> neg_signed   = FixedPoint(-2, 1, 4, 2)
    >>> pos_signed   = FixedPoint(+2, 1, 4, 2)
    >>> pos_unsigned = FixedPoint(+2, 0, 4, 2)

    >>> show(neg_signed)
    -2.00   Q4.2  1110.00

    >>> show(pos_signed)
    +2.00   Q4.2  0010.00

    >>> show(pos_unsigned)
    +2.00  UQ4.2  0010.00

Increasing the integer bit width of a negative :class:`FixedPoint` will
sign-extend:

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> x = resize(neg_signed, 7, 2)
    >>> show(x)
    -2.00   Q7.2  111_1110.00

Increasing the integer bit width of a positive :class:`FixedPoint` (sign or
unsigned) will pad with zeros:

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> x = resize(pos_signed, 7, 2)
    >>> show(x)
    +2.00   Q7.2  000_0010.00

    >>> y = resize(pos_unsigned, 7, 2)
    >>> show(y)
    +2.00  UQ7.2  000_0010.00

Since fractional bits always have a positive weight (by virtue of the fact that
the :ref:`Q format <Q_Format>` does not allow for a non-positive integer bit
width for signed numbers), increasing the fractional bit width of any (signed
or unsigned) :class:`FixedPoint` will pad with zeros:

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> show(resize(neg_signed, 4, 5))
    -2.00   Q4.5  1110.0_0000

    >>> show(resize(pos_signed, 4, 5))
    +2.00   Q4.5  0010.0_0000

    >>> show(resize(pos_unsigned, 4, 5))
    +2.00  UQ4.5  0010.0_0000

Decreasing the integer bit width below the minimum number of bits required to
represent it will result in overflow:

..  doctest:: resize
    :skipif: should_skip("resize")
    :hide:

    reset_sn()

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> neg_signed.resize(1, 5)
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN1] Overflow in format Q4.5.

Override the :attr:`~.FixedPoint.overflow_alert` property by setting the *alert*
argument to the desired alert level. Override the :attr:`~.FixedPoint.overflow`
property by setting the *overflow* argument. These overrides only take effect
inside the function/method; the original property setting is restored after
resizing.

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> show(resize(neg_signed, 1, 5, alert='warning', overflow='wrap'))
    WARNING [SN10]: Overflow in format Q4.5.
    WARNING [SN10]: Wrapped minimum.
    +0.00   Q1.5  0.0_0000

    >>> show(resize(pos_signed, 1, 2, alert='warning'))
    WARNING [SN11]: Overflow in format Q4.2.
    WARNING [SN11]: Clamped to maximum.
    +0.75   Q1.2  0.11

    >>> show(resize(pos_unsigned, 1, 0, alert='ignore'))
    +1.00  UQ1.0  1.

Decreasing the fractional bit width below the minimum number of bits required
to represent it will result in rounding. Override the
:attr:`~.FixedPoint.rounding` property by setting the *rounding* argument.
This override only takes effect inside the function/method; the original
property setting is restored after resizing.

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> neg_signed.rounding
    'convergent'
    >>> show(resize(neg_signed | 0b11, 3, 1))
    -1.00   Q3.1  111.0

    >>> show(resize(pos_signed | 0b11, 4, 1, rounding='down'))
    +2.50   Q4.1  0010.1
    >>> pos_signed.rounding
    'convergent'

    >>> show(resize(pos_unsigned | 0b11, 2, 0, 'out'))
    +3.00  UQ2.0  11.
    >>> pos_unsigned.rounding
    'nearest'

Rounding can potentially cause overflow if the integer portion of the
:class:`FixedPoint` is already at its maximum. Only
:ref:`certain rounding schemes <overflow_causes>` can cause this.

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> signed_maxed = FixedPoint('0xF', 1, 3, 2) # convergent rounding
    >>> show(signed_maxed)
    +3.75   Q3.2  011.11

    >>> show(resize(signed_maxed, 3, 0, alert='warning', overflow='wrap'))
    WARNING [SN20]: Convergent round to Q3.0 causes overflow.
    WARNING [SN20]: Wrapped maximum.
    -4.00   Q3.0  100.

When resizing, fractional bits are resized first, followed by integer bits. This
could cause issues if (for example) the number being resized originally has
0 integer bits, and you are resizing to 0 fractional bits:

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> orig = FixedPoint(0.25, rounding='up')
    >>> show(orig)
    +0.25  UQ0.2  .01

    >>> orig.resize(4, 0) # resize to Q4.0
    Traceback (most recent call last):
        ...
    ValueError: Word size (integer and fractional) must be positive.

In this case, you'll need to manually resize the integer bit width first, then
the fractional:

..  doctest:: resize
    :skipif: should_skip("resize")

    >>> orig.m = 4
    >>> orig.n = 0
    >>> show(orig)
    +1.00  UQ4.0  0001.

..  _trim:

*******************************************************************************
trim
*******************************************************************************

Using :meth:`.FixedPoint.trim` or :func:`.trim` will remove superfluous/\
insignificant bits.

..  testsetup:: trim
    :skipif: should_skip("trim")

    reset_sn()
    def show(A):
        print(f"{A: <+5.2f}  ", end="")       # float
        print(f"{A:>5q}  ", end="")           # Q format
        print(f"{A:0{A.m+(A.m-1)//4}_bm}." if A.m else ".", end="")
        print(f"{A:0{A.n}_bn}" if A.n else "") # Show binary point

..  doctest:: trim
    :skipif: should_skip("trim")

    >>> neg_signed   = FixedPoint(-2, 1, 4, 2)
    >>> pos_signed   = FixedPoint(+2, 1, 4, 2)
    >>> pos_unsigned = FixedPoint(+2, 0, 4, 2)

    >>> show(neg_signed)
    -2.00   Q4.2  1110.00
    >>> show(trim(neg_signed))
    -2.00   Q2.0  10.

    >>> show(pos_signed)
    +2.00   Q4.2  0010.00
    >>> show(trim(pos_signed))
    +2.00   Q3.0  010.

    >>> show(pos_unsigned)
    +2.00  UQ4.2  0010.00
    >>> show(trim(pos_unsigned))
    +2.00  UQ2.0  10.

You can opt to trim off only fractional or integer bits by setting *fracs* or
*int*, respectively, to *True*.

..  doctest:: trim
    :skipif: should_skip("trim")

    >>> neg_signed.trim(ints=True)
    >>> show(neg_signed)
    -2.00   Q2.2  10.00

    >>> pos_signed.trim(fracs=True)
    >>> show(pos_signed)
    +2.00   Q4.0  0010.

    >>> pos_unsigned.trim(True, True) # same as pos_unsigned.trim()
    >>> show(pos_unsigned)
    +2.00  UQ2.0  10.

Zero is always trimmed to 1 integer bit and 0 fractional bits.

..  doctest:: trim
    :skipif: should_skip("trim")

    >>> signed = FixedPoint(0, 1, 4, 4)
    >>> signed_no_frac = FixedPoint(0, 1, 4, 0)
    >>> unsigned_no_int = FixedPoint(0, 0, 0, 4)

    >>> show(signed)
    +0.00   Q4.4  0000.0000
    >>> show(trim(signed))
    +0.00   Q1.0  0.

    >>> show(signed_no_frac)
    +0.00   Q4.0  0000.
    >>> show(trim(signed_no_frac))
    +0.00   Q1.0  0.

    >>> show(unsigned_no_int)
    +0.00  UQ0.4  .0000
    >>> show(trim(unsigned_no_int))
    +0.00  UQ1.0  0.

*******************************************************************************
Rounding
*******************************************************************************

See the :ref:`Initialization <rounding>` page for numerical examples on various
rounding schemes. The items described here warrant more information than what
those examples show.

..  _default_rounding:

Default rounding
===============================================================================

When a :class:`.FixedPoint` is instantiated, a rounding scheme (whether
:ref:`defaulted <rounding>` or explicitly specified) is determined.

The :meth:`.FixedPoint.round` method and built-in :func:`round` function use
the inherent rounding scheme.

..  testsetup:: default rounding
    :skipif: should_skip("default rounding")

    reset_sn()
    def show(A):
        print(f"{A: <+5.2f}  ", end="")       # float
        print(f"{A:>5q}  ", end="")           # Q format
        print(f"{A:0{A.m+(A.m-1)//4}_bm}." if A.m else ".", end="")
        print(f"{A:0{A.n+(A.n-1)//4}_bn}" if A.n else "") # Show binary point

..  doctest:: default rounding
    :skipif: should_skip("default rounding")

    >>> x = FixedPoint(1/3, n=24)
    >>> x.rounding
    'nearest'
    >>> show(x)
    +0.33  UQ0.24  .0101_0101_0101_0101_0101_0101

    >>> show(round(x, 4))
    +0.31  UQ0.4  .0101

    >>> x.rounding = 'up'
    >>> x.round(7)
    >>> show(x)
    +0.34  UQ0.7  .010_1011

Additionally, when shrinking the fractional bit width (via
:attr:`.FixedPoint.n`), the default rounding scheme is used.

..  doctest:: default rounding
    :skipif: should_skip("default rounding")

    >>> x.rounding = 'in'
    >>> x.n = 3
    >>> show(x)
    +0.25  UQ0.3  .010

..  _floor:

:func:`math.floor`
===============================================================================

When given a :class:`float`, :func:`math.floor` will round towards
:math:`-\infty` and return an :class:`int` type.

..  testsetup:: resize math.floor
    :skipif: should_skip("resize math.floor")

    reset_sn()
    def show(A):
        print(f"{A: <+5.2f}  ", end="")       # float
        print(f"{A:>5q}  ", end="")           # Q format
        print(f"{A:0{A.m+(A.m-1)//4}_bm}." if A.m else ".", end="")
        print(f"{A:0{A.n+(A.n-1)//4}_bn}" if A.n else "") # Show binary point

..  doctest:: resize math.floor
    :skipif: should_skip("resize math.floor")

    >>> import math
    >>> x = math.floor(1/3)
    >>> x, type(x)
    (0, <class 'int'>)

    >>> y = math.floor(-1/2)
    >>> y, type(y)
    (-1, <class 'int'>)

Using :func:`math.floor` on a :class:`FixedPoint` will produce the same result,
but will not modify the fractional bit width. It simply sets all fractional
bits to 0.

..  doctest:: resize math.floor
    :skipif: should_skip("resize math.floor")

    >>> x = FixedPoint(-2**-5)
    >>> y = math.floor(x)
    >>> show(x); show(y)
    -0.03   Q1.5  1.1_1111
    -1.00   Q1.5  1.0_0000

The :meth:`.FixedPoint.round_down` method is similar to :func:`math.floor`, but
instead will change the fractional bit width. A bit mask can accomplish
the same thing as :func:`math.floor` if importing :mod:`math` is not desired.

..  doctest:: resize math.floor
    :skipif: should_skip("resize math.floor")

    >>> show(x); show(x & ~(2**x.n - 1))
    -0.03   Q1.5  1.1_1111
    -1.00   Q1.5  1.0_0000

..  _ceil:

:func:`math.ceil`
===============================================================================

When given a :class:`float`, :func:`math.ceil` will round towards
:math:`+\infty` and return an :class:`int` type.

..  testsetup:: resize math.ceil
    :skipif: should_skip("resize math.ceil")

    reset_sn()
    def show(A):
        print(f"{A: <+5.2f}  ", end="")       # float
        print(f"{A:>5q}  ", end="")           # Q format
        print(f"{A:0{A.m+(A.m-1)//4}_bm}." if A.m else ".", end="")
        print(f"{A:0{A.n+(A.n-1)//4}_bn}" if A.n else "") # Show binary point

..  doctest:: resize math.ceil
    :skipif: should_skip("resize math.ceil")

    >>> import math
    >>> x = math.ceil(1/3)
    >>> x, type(x)
    (1, <class 'int'>)

    >>> y = math.ceil(-1/2)
    >>> y, type(y)
    (0, <class 'int'>)

Using :func:`math.ceil` on a :class:`FixedPoint` produces the same result.
Note that this can cause :ref:`overflow <overflow>`.

..  doctest:: resize math.ceil
    :skipif: should_skip("resize math.ceil")

    >>> x = FixedPoint(2**-5, signed=True, overflow_alert='warning')
    >>> y = math.ceil(x)
    WARNING [SN2]: Rounding up to Q1.0 causes overflow.
    WARNING [SN2]: Clamped to maximum.
    >>> show(x); show(y)
    +0.03   Q1.5  0.0_0001
    +0.00   Q1.0  0.

Because the fractional bit width is changed to 0, unsigned numbers with no
no integer bits will raise an exception.

..  doctest:: resize math.ceil
    :skipif: should_skip("resize math.ceil")

    >>> x = FixedPoint(2**-5)
    >>> show(x)
    +0.03  UQ0.5  .0_0001

    >>> math.ceil(x)
    Traceback (most recent call last):
        ...
    ValueError: Word size (integer and fractional) must be positive.

..  _trunc:

:func:`math.trunc`
===============================================================================

When given a :class:`float`, :func:`math.trunc` will round towards 0
(truncating decimal digits) and return an :class:`int` type.

..  testsetup:: resize math.trunc
    :skipif: should_skip("resize math.trunc")

    reset_sn()
    def show(A):
        print(f"{A: <+5.2f}  ", end="")       # float
        print(f"{A:>5q}  ", end="")           # Q format
        print(f"{A:0{A.m+(A.m-1)//4}_bm}." if A.m else ".", end="")
        print(f"{A:0{A.n+(A.n-1)//4}_bn}" if A.n else "") # Show binary point

..  doctest:: resize math.trunc
    :skipif: should_skip("resize math.trunc")

    >>> import math
    >>> x = math.trunc(0.333333333333333333)
    >>> x, type(x)
    (0, <class 'int'>)

    >>> y = math.trunc(-0.5)
    >>> y, type(y)
    (0, <class 'int'>)

The *truncation* that :func:`math.trunc` performs on :class:`float`\ s is the
truncation of **decimal** digits. For :class:`FixedPoint`\ s, **binary** digits
are truncated, effectively *flooring* the number. Thus the only difference
between :func:`math.floor` and :func:`math.trunc` is that the latter leaves no
fractional bits in the return value.

..  attention::

    ..  table:: Comparison of floor/truncation rounding on floats/FixedPoints

        +--------------------+---------------------+------------------+-----------------+
        | Function           | Argument Type       | Truncated Digits | Rounds Towards  |
        +====================+=====================+==================+=================+
        |                    | :class:`FixedPoint` | binary           | :math:`-\infty` |
        | :func:`math.floor` +---------------------+------------------+-----------------+
        |                    | :class:`float`      | decimal          | :math:`-\infty` |
        +--------------------+---------------------+------------------+-----------------+
        |                    | :class:`FixedPoint` | binary           | :math:`-\infty` |
        | :func:`math.trunc` +---------------------+------------------+-----------------+
        |                    | :class:`float`      | decimal          | 0               |
        +--------------------+---------------------+------------------+-----------------+

..  doctest:: resize math.trunc
    :skipif: should_skip("resize math.trunc")

    >>> x = FixedPoint(-2**-5, signed=1)
    >>> y = math.trunc(x)
    >>> show(x); show(y)
    -0.03   Q1.5  1.1_1111
    -1.00   Q1.0  1.

Because the fractional bit width is changed to 0, unsigned numbers with no
no integer bits will have the integer bit width set to 1.

..  doctest:: resize math.trunc
    :skipif: should_skip("resize math.trunc")

    >>> x = FixedPoint(2**-5)
    >>> show(x)
    +0.03  UQ0.5  .0_0001

    >>> show(math.trunc(x))
    +0.00  UQ1.0  0.

..  _rounding_induced_overflow:

Rounding-induced overflow
===============================================================================

The following rounding schemes can cause overflow under the right circumstances:

* :ref:`convergent <convergent>`
* :ref:`nearest <nearest>`
* :ref:`out <out>`
* :ref:`up <up>`

This is because each of these schemes can increase the value of a number toward
:math:`+\infty` which can overflow into the integer bits. One possible
workaround (if clamping/wrapping is not desired) is to manually change the
integer bit width via :attr:`.FixedPoint.m` before rounding:

..  testsetup:: rounding-induced overflow
    :skipif: should_skip("rounding-induced overflow")

    reset_sn()

..  doctest:: rounding-induced overflow
    :skipif: should_skip("rounding-induced overflow")

    >>> x = FixedPoint("0b1111", 0, 2, 2)
    >>> x.round_out(1)
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN1] Rounding out to UQ2.1 causes overflow.

    >>> x.m += 1
    >>> x.round_out(1)
    >>> x.qformat, bin(x)
    ('UQ3.1', '0b1000')

..  _overflow_safe_rounding:

Overflow-safe rounding
===============================================================================

The following rounding schemes cannot possibly cause overflow:

* :ref:`in <in>`
* :ref:`down <down>`

..  _keep_msbs:

Rounding beyond the fractional bit width
===============================================================================

There may be times when you want to round away bits beyond the fractional bit
width (e.g., keep the most significant 18 bits of a Q24.18 number and round off
the rest). This can be done with :meth:`.FixedPoint.keep_msbs` or
:func:`.keep_msbs`.

..  doctest:: resizing with keep_msbs
    :skipif: should_skip("resizing with keep_msbs")

    >>> x = FixedPoint('0x15555555555', 1, 24, 18, rounding='up')
    >>> y = keep_msbs(x, 18, 0)
    >>> print(f'{x: <6q} {x:_b}\n{y: <6q} {y:_b}')
    Q24.18 1_0101_0101_0101_0101_0101_0101_0101_0101_0101_0101
    Q18.0  1_0101_0101_0101_0110

Bit widths are calculated with respect to the MSb. This is *not* the same as
``y = resize(x, 18, 0)`` where the bit widths are calculated with respect to
the current binary point position.

*******************************************************************************
Overflow Handling
*******************************************************************************

See the :ref:`Initialization <overflow>` page for numerical examples on various
overflow handling schemes. The items described here warrant more information
than what those examples show.

..  _keep_lsbs:

Clamping/wrapping below 0 integer bits
===============================================================================

There may be times when you want to remove MSbs and still perform clamping (
e.g. keep the least significant 18 bits of a Q18.24 number but clamp/wrap the
entire value). This can be done with the :meth:`.FixedPoint.keep_lsbs` or
:func:`.keep_lsbs`.

..  doctest:: resizing with keep_lsbs
    :skipif: should_skip("resizing with keep_lsbs")

    >>> x = FixedPoint('0x15555555555', 1, 18, 24)
    >>> y = keep_lsbs(x, 18, 0, overflow='clamp', alert='ignore')
    >>> print(f'{x: <6q} {x:_b}\n{y: <6q} {y:_b}')
    Q18.24 1_0101_0101_0101_0101_0101_0101_0101_0101_0101_0101
    Q18.0  1_1111_1111_1111_1111

Bit widths are calculated with respect to the LSb. This is *not* the same as
``y = resize(x, 18, 0)`` where the bit widths are calculated with respect to
the current binary point position.
