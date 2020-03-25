..  currentmodule:: fixedpoint

###############################################################################
Arithmetic
###############################################################################

..  _arithmetic_addition:

*******************************************************************************
Addition
*******************************************************************************

:class:`FixedPoint` addition using the ``+`` or ``+=`` operator is always
full-precision; that is, there is always bit growth.

..  table:: Addition Bit Growth Summary

    +---------------------+---------------------+-----------------------------------+
    | Augend              | Addend              | Sum                               |
    +=====================+=====================+===================================+
    | | :math:`UQm_1.n_1` | | :math:`UQm_2.n_2` | | :math:`UQx.y`, where            |
    | | (unsigned)        | | (unsigned)        | | :math:`x = 1 + max\{m_1, m_2\}` |
    |                     |                     | | :math:`y = max\{n_1, n_2\}`     |
    +---------------------+---------------------+-----------------------------------+
    | | :math:`Qm_1.n_1`  | | :math:`Qm_2.n_2`  |                                   |
    | | (signed)          | | (signed)          |                                   |
    |                     |                     |                                   |
    +---------------------+---------------------+                                   |
    | | :math:`Qm_1.n_1`  | | :math:`UQm_2.n_2` | | :math:`Qx.y`, where             |
    | | (signed)          | | (unsigned)        | | :math:`x = 1 + max\{m_1, m_2\}` |
    |                     |                     | | :math:`y = max\{n_1, n_2\}`     |
    +---------------------+---------------------+                                   |
    | | :math:`UQm_1.n_1` | | :math:`Qm_2.n_2`  |                                   |
    | | (unsigned)        | | (signed)          |                                   |
    |                     |                     |                                   |
    +---------------------+---------------------+-----------------------------------+

As indicated in the table, any combination of signed and unsigned numbers can
be added together. The sum is only unsigned when both augend and added are
unsigned.

Overflow is not possible using the addition operators.

Unsigned
===============================================================================

..  doctest:: unsigned addition

    >>> x = FixedPoint(14, signed=0, m=8, n=4)
    >>> y = FixedPoint(6, signed=0, m=3, n=5)
    >>> z = x + y
    >>> print(f'  {x:q}\n+ {y:q}\n-------\n  {z:q}')
      UQ8.4
    + UQ3.5
    -------
      UQ9.5

Signed
===============================================================================

..  doctest:: signed addition

    >>> x = FixedPoint(-4, signed=1, m=4, n=4)
    >>> y = FixedPoint(3, signed=1, m=3, n=5)
    >>> z = x + y
    >>> print(f'  {x:q}\n+ {y:q}\n------\n  {z:q}')
      Q4.4
    + Q3.5
    ------
      Q5.5

Mixed Signedness
===============================================================================

..  testsetup:: mixed signedness addition

    reset_sn()

..  doctest:: mixed signedness addition

    >>> s = FixedPoint(-4.375, signed=1, m=4, n=4)
    >>> u = FixedPoint(3 + 2**-5, signed=0, m=3, n=5)
    >>> z = s + u
    WARNING [SN1]: Non-matching rounding behaviors ['convergent', 'nearest'].
    WARNING [SN1]: Using 'convergent'.

    >>> print(f'   {s:q}\n+ {u:q}\n-------\n   {z:q}')
       Q4.4
    + UQ3.5
    -------
       Q5.5

Additional Examples
===============================================================================

This behavior guarantees that addition will never cause overflow. However, it
does mean that an accumulator may grow larger than intended.

For example, summing 64 **Q18.0** numbers will grow at maximum
:math:`log_2(64) = 6` bits, thus the accumulator should be sized to 24 integer
bits.

..  testcode:: addition example - accumulator

    from fixedpoint import FixedPoint

    accum = FixedPoint(0, 1, 24, 0, overflow_alert='error', str_base=2)
    max_neg = FixedPoint(-2**17, 1, 18, 0)
    assert max_neg.clamped

    for _ in range(64):
        accum += max_neg
        accum.clamp(24)

    print(f"{int(accum)} in {accum:q} is\n0b{accum:_b}")

Summing the maximum negative *Q18.0* number 64 times produces a *Q24.0* that is
clamped to the maximum negative value. Note that ``accum.overflow_alert`` was
set to ``'error'``, thus we would have been informed had overflow occurred.

..  testoutput:: addition example - accumulator

    -8388608 in Q24.0 is
    0b1000_0000_0000_0000_0000_0000

..  _arithmetic_subtraction:

*******************************************************************************
Subtraction
*******************************************************************************

:class:`FixedPoint` subtraction using the ``-`` or ``-=`` operator is always
full-precision; that is, there is always bit growth.

..  table:: Subtraction Bit Growth Summary

    +---------------------+---------------------+-----------------------------------+
    | Minuend             | Subtrahend          | Difference                        |
    +=====================+=====================+===================================+
    | | :math:`UQm_1.n_1` | | :math:`UQm_2.n_2` | | :math:`UQx.y`, where            |
    | | (unsigned)        | | (unsigned)        | | :math:`x = 1 + max\{m_1, m_2\}` |
    |                     |                     | | :math:`y = max\{n_1, n_2\}`     |
    |                     |                     | | Overflow occurs if              |
    |                     |                     |   subtrahend > minuend.           |
    +---------------------+---------------------+-----------------------------------+
    | | :math:`Qm_1.n_1`  | | :math:`Qm_2.n_2`  | | :math:`Qx.y`, where             |
    | | (signed)          | | (signed)          | | :math:`x = 1 + max\{m_1, m_2\}` |
    |                     |                     | | :math:`y = max\{n_1, n_2\}`     |
    +---------------------+---------------------+-----------------------------------+
    | | :math:`Qm_1.n_1`  | | :math:`UQm_2.n_2` |                                   |
    | | (signed)          | | (unsigned)        |                                   |
    |                     |                     | | :math:`Qx.y`, where             |
    +---------------------+---------------------+ | :math:`x = 2 + max\{m_1, m_2\}` |
    | | :math:`UQm_1.n_1` | | :math:`Qm_2.n_2`  | | :math:`y = max\{n_1, n_2\}`     |
    | | (unsigned)        | | (signed)          |                                   |
    |                     |                     |                                   |
    +---------------------+---------------------+-----------------------------------+

As indicated in the table, any combination of signed and unsigned numbers can
be subtracted from each other. The difference is only unsigned when both augend
and added are unsigned.

When signedness between minuend and subtrahend does not match, an extra integer
bit is added to the unsigned term so it can be signed without overflowing.

Unsigned
===============================================================================

..  testsetup:: unsigned subtraction

    reset_sn()

..  doctest:: unsigned subtraction

    >>> x = FixedPoint(14, signed=0, m=8, n=4)
    >>> y = FixedPoint(6, signed=0, m=3, n=5)
    >>> z = x - y
    >>> print(f'  {x:q}\n- {y:q}\n-------\n  {z:q}')
      UQ8.4
    - UQ3.5
    -------
      UQ9.5
    >>> float(z)
    8.0

Overflow occurs when subtrahend > minuend.

..  doctest:: unsigned subtraction

    >>> q_presub = y.qformat
    >>> y.overflow_alert = 'warning'
    >>> y -= x
    WARNING [SN2]: Unsigned subtraction causes overflow.
    WARNING [SN2]: Clamped to minimum.

    >>> print(f'  {q_presub}\n- {x:q}\n-------\n  {y:q}')
      UQ3.5
    - UQ8.4
    -------
      UQ9.5

    >>> float(y)
    0.0

Signed
===============================================================================

..  doctest:: signed subtraction

    >>> x = FixedPoint(250 + 2**-6, signed=1)
    >>> y = FixedPoint(-13 - 2**-8, signed=1)
    >>> a = x - y
    >>> print(f'  {x:q}\n- {y:q}\n------\n {a:q}')
      Q9.6
    - Q5.8
    ------
     Q10.8

    >>> float(a)
    263.01953125

..  doctest:: signed subtraction

    >>> b = y - x
    >>> print(f'  {y:q}\n- {x:q}\n------\n {b:q}')
      Q5.8
    - Q9.6
    ------
     Q10.8

    >>> float(b)
    -263.01953125
    >>> a == -b
    True

Overflow is not possible with signed subtraction.

Mixed Signedness
===============================================================================

..  testsetup:: mixed signedness subtraction

    reset_sn()

..  doctest:: mixed signedness subtraction

    >>> s = FixedPoint(1, 1, 2)
    >>> u = FixedPoint(1, 0, 2)
    >>> x = u - s
    WARNING [SN2]: Non-matching rounding behaviors ['convergent', 'nearest'].
    WARNING [SN2]: Using 'convergent'.

    >>> print(f' {u:q}\n- {s:q}\n------\n  {x:q}')
     UQ2.0
    - Q2.0
    ------
      Q4.0

    >>> float(x)
    0.0

Note that even though *u* and *s* can be represented without overflow in both
*UQ2.0* and *Q2.0* formats (their difference can too), 2 bits are still added
to the maximum integer bit width for the result. This makes for deterministic
bit growth. Use :meth:`~.FixedPoint.clamp` or :meth:`~.FixedPoint.wrap` to
revert back to the original Q format if needed.

..  doctest:: mixed signedness subtraction

    >>> y = s - u
    WARNING [SN1]: Non-matching rounding behaviors ['convergent', 'nearest'].
    WARNING [SN1]: Using 'convergent'.

    >>> print(f'   {s:q}\n- {u:q}\n-------\n   {y:q}')
       Q2.0
    - UQ2.0
    -------
       Q4.0

    >>> float(y), clamp(y, s.m).qformat
    (0.0, 'Q2.0')

Overflow is not possible with mixed signedness subtraction.

..  _arithmetic_multiplication:

*******************************************************************************
Multiplication
*******************************************************************************

:class:`FixedPoint` multiplication using the ``*`` or ``*=`` operator is always
full-precision; that is, there is always bit growth.

..  table:: Multiplication Bit Growth Summary

    +---------------------+---------------------+-------------------------+
    | Multiplicand        | Multiplier          | Product                 |
    +=====================+=====================+=========================+
    | | :math:`UQm_1.n_1` | | :math:`UQm_2.n_2` | | :math:`UQx.y`, where  |
    | | (unsigned)        | | (unsigned)        | | :math:`x = m_1 + m_2` |
    |                     |                     | | :math:`y = n_1 + n_2` |
    +---------------------+---------------------+-------------------------+
    | | :math:`Qm_1.n_1`  | | :math:`Qm_2.n_2`  |                         |
    | | (signed)          | | (signed)          |                         |
    |                     |                     |                         |
    +---------------------+---------------------+                         |
    | | :math:`Qm_1.n_1`  | | :math:`UQm_2.n_2` | | :math:`Qx.y`, where   |
    | | (signed)          | | (unsigned)        | | :math:`x = m_1 + m_2` |
    |                     |                     | | :math:`y = n_1 + n_2` |
    +---------------------+---------------------+                         |
    | | :math:`UQm_1.n_1` | | :math:`Qm_2.n_2`  |                         |
    | | (unsigned)        | | (signed)          |                         |
    |                     |                     |                         |
    +---------------------+---------------------+-------------------------+

Overflow is not possible using the multiplication operator.

Unsigned
===============================================================================

..  doctest:: unsigned multiplication

    >>> x = FixedPoint(10, n=2)
    >>> y = FixedPoint(29, n=7)
    >>> z = x * y
    >>> print(f'  {x:q}\n* {y:q}\n-------\n  {z:q}')
      UQ4.2
    * UQ5.7
    -------
      UQ9.9

Signed
===============================================================================

..  doctest:: signed multiplication

    >>> x = FixedPoint(-4, signed=1, n=8)
    >>> y = FixedPoint(2.5, signed=1)
    >>> q = y.qformat
    >>> y *= x
    >>> print(f'  {q}\n* {x:q}\n------\n  {y:q}')
      Q3.1
    * Q3.8
    ------
      Q6.9

    >>> float(y)
    -10.0

Mixed Signedness
===============================================================================

..  doctest:: mixed signedness multiplication

    >>> s = FixedPoint("0b1000", signed=1, m=3, n=1, rounding='nearest')
    >>> u = FixedPoint("0b11", signed=0, m=2, n=0)
    >>> z = u * s
    >>> print(f"{u:.1f} * {s:.1f} = {z:.1f}")
    3.0 * -4.0 = -12.0

    >>> print(f' {u:q}\n* {s:q}\n------\n  {z:q}')
     UQ2.0
    * Q3.1
    ------
      Q5.1

..  _arithmetic_exponentiation:

*******************************************************************************
Exponentiation
*******************************************************************************

`FixedPoint` exponentiation using the ``**`` or ``**=`` operator is always
full-precision; that is, there is always bit growth. Only positive integer
exponents are supported.

..  |Z+| replace:: :math:`p \in \mathbb{Z}^+`

..  table:: Exponentiation Bit Growth Summary

    +-----------------+---------------+--------------------------------------------+
    | Base            | Exponent      | Result                                     |
    +=================+===============+=================+==========================+
    | | :math:`UQm.n` | | |Z+|        | :math:`UQx.y`   | | where                  |
    | | (unsigned)    | | (`int` > 0) |                 | | :math:`x = p \times m` |
    +-----------------+               +-----------------+ | :math:`y = p \times n` |
    | | :math:`Qm.n`  |               | :math:`Qx.y`    |                          |
    | | (signed)      |               |                 |                          |
    +-----------------+---------------+-----------------+--------------------------+

..  doctest:: exponentiation

    >>> x = FixedPoint(1.5)
    >>> y = FixedPoint(-1.5)
    >>> x**y # not allowed
    Traceback (most recent call last):
        ...
    TypeError: Only positive integers are supported for exponentiation.

    >>> x **= -2 # not allowed
    Traceback (most recent call last):
        ...
    TypeError: Only positive integers are supported for exponentiation.

    >>> 2**x # not allowed
    Traceback (most recent call last):
        ...
    TypeError: unsupported operand type(s) for **: 'int' and 'FixedPoint'

    >>> a = x**4
    >>> x.qformat, float(a), a.qformat
    ('UQ1.1', 5.0625, 'UQ4.4')

    >>> b = y**3
    >>> y.qformat, float(b), b.qformat
    ('Q2.1', -3.375, 'Q6.3')

Overflow is not possible using the power operators.

..  _negation_abs:

*******************************************************************************
Negation & Absolute Value
*******************************************************************************

Negation is achieved using the unary negation operator ``-`` (see
:meth:`.FixedPoint.__neg__`). Absolute value (see :meth:`.FixedPoint.__abs__`)
is achieved using the negation operator on negative numbers, thus the same
behavior applies to unary negation and absolute value.

..  testsetup:: negation and absolute value

    reset_sn()

..  doctest:: negation and absolute value

    >>> x = FixedPoint(-4, m=10, overflow_alert='warning', str_base=2)
    >>> float(y := -x)
    4.0
    >>> float(abs(x))
    4.0

If the :ref:`Q format <Q_Format>` can be maintained without overflow it will,
(as in the example above) otherwise an :ref:`overflow alert <overflow_alert>` is
issued, and the Q format of the result has an integer bit width one more than
the original `FixedPoint` (as long as ``overflow_alert`` is not ``'error'``).

..  doctest:: negation and absolute value

    >>> y.qformat
    'Q10.0'
    >>> x.trim(ints=True) # remove unneeded leading bits
    >>> x.qformat, float(x)
    ('Q3.0', -4.0)

    >>> yy = -x
    WARNING [SN1]: Negating 0b100 (Q3.0) causes overflow.
    WARNING [SN1]: Adjusting Q format to Q4.0 to allow negation.

    >>> x.qformat, y.qformat, yy.qformat, float(yy)
    ('Q3.0', 'Q10.0', 'Q4.0', 4.0)

    >>> zz = abs(x)
    WARNING [SN1]: Negating 0b100 (Q3.0) causes overflow.
    WARNING [SN1]: Adjusting Q format to Q4.0 to allow negation.

    >>> x.qformat, y.qformat, zz.qformat, float(zz)
    ('Q3.0', 'Q10.0', 'Q4.0', 4.0)

Unsigned numbers cannot be negated; this behavior is intended to minimize user
error. Negating an unsigned number should be intentional. The preferred method
is by use of the context manager:

..  testsetup:: unsigned negation

    reset_sn()

..  doctest:: unsigned negation

    >>> x = FixedPoint(3, signed=0)
    >>> xx = abs(x)
    >>> float(xx)
    3.0
    >>> -x
    Traceback (most recent call last):
        ...
    FixedPointError: [SN1] Unsigned numbers can't be negated.

    >>> with x(m=x.m + 1, signed=1): # Increase integer bit width for sign
    ...     y = -x
    >>> x.qformat, y.qformat, float(y)
    ('UQ2.0', 'Q3.0', -3.0)

*******************************************************************************
Bitwise Operations
*******************************************************************************

Bitwise operations do not cause overflow, nor do they modify the
:ref:`Q format <Q_Format>`.

..  _left_shift:

Left Shift
===============================================================================

Shifting bits left will cause MSbs to be lost. 0s are shifted into the LSb.

..  doctest:: left shift

    >>> x = FixedPoint('0b111000', 0, 3, 3, str_base=2)
    >>> str(x << 2)
    '100000'

To shift bits left and *not* lose bits, instead multiply the number by
2\ :sup:`n`\ , where *n* is the number of bits to shift.

..  doctest:: left shift

    >>> float(x) * 2**4
    112.0
    >>> y = x << 4
    >>> float(y), y.qformat
    (0.0, 'UQ3.3')

    >>> z = x * 2**4
    >>> float(z), z.qformat
    (112.0, 'UQ8.3')

If the number of bits to shift is negative, a right shift is performed instead.
For signed numbers, the value of the bits shifted in is the MSb. For unsigned
numbers, 0s are shifted into the MSb.

..  doctest:: left shift

    >>> str(x << -2) # unsigned shift
    '001110'
    >>> with x(overflow_alert='ignore', overflow='wrap', signed=1): # signed shift
    ...     str(x << -2)
    '111110'

..  _right_shift:

Right Shift
===============================================================================

Shifting bits right will cause LSbs to be lost. 0s are shifted into the MSb for
unsigned numbers. Sign bits are shifted into the MSb for signed numbers.

..  doctest:: right shift

    >>> notsigned = FixedPoint('0b111000', 0, 3, 3, str_base=2)
    >>> signedneg = FixedPoint('0b111000', 1, 3, 3, str_base=2)
    >>> signedpos = FixedPoint('0b011000', 1, 3, 3, str_base=2)
    >>> print(f"{notsigned >> 2!s}\n{signedpos >> 2!s}\n{signedneg >> 2!s}")
    001110
    000110
    111110

To shift bits left and *not* lose bits, instead multiply the number by
2\ :sup:`-n`\ , where *n* is the number of bits to shift.

If the number of bits to shift is negative, a left shift is performed instead.
0s are shifted into the LSb.

..  doctest:: right shift

    >>> print(f"{notsigned >> -2!s}\n{signedpos >> -2!s}\n{signedneg >> -2!s}")
    100000
    100000
    100000

..  doctest:: right shift

    >>> x = FixedPoint(1, m=3)
    >>> 2**-3 # Desired numerical value
    0.125

    >>> y = x >> 3
    >>> float(y), y.qformat
    (0.0, 'UQ3.0')

    >>> z = x * 2**-3
    >>> float(z), z.qformat
    (0.125, 'UQ3.3')

..  _and_or_xor:

AND, OR, XOR
===============================================================================

The ``&``, ``&=``, ``|``, ``|=``, ``^``, and ``^=`` operators perform bitwise
operations. A :class:`FixedPoint` is inter operable with an :obj:`int` or
another :class:`FixedPoint`. In the latter case, the operand on the left will
be the :ref:`Q format <Q_Format>` of the returned value.

..  doctest:: bitwise 2 FixedPoints

    >>> from operator import and_, or_, xor
    >>> def operate(left, op, right):
    ...     """Pretty display of using `op` with `left` and `right` operands"""
    ...     r = {'&': and_, '|': or_, '^': xor}[op](left, right)
    ...     l = max(len(left), len(right))
    ...     return (f"  {left:>{l}s} ({left:q})\n"
    ...             f"{op} {right:>{l}s} ({right:q})\n"
    ...             f"----------{'-' * l}\n"
    ...             f"  {r:>{l}s} ({r:q})")

    >>> L = FixedPoint('0b100011', 0, 3, 3, str_base=2)
    >>> R = FixedPoint(0b10, str_base=2)
    >>> print(f"  L & R\n{operate(L, '&', R)}")
      L & R
      100011 (UQ3.3)
    &     10 (UQ2.0)
    ----------------
      000010 (UQ3.3)

    >>> print(f"  R | L\n{operate(R, '|', L)}")
      R | L
          10 (UQ2.0)
    | 100011 (UQ3.3)
    ----------------
          11 (UQ2.0)

    >>> print(f"  L ^ R\n{operate(L, '^', R)}")
      L ^ R
      100011 (UQ3.3)
    ^     10 (UQ2.0)
    ----------------
      100001 (UQ3.3)

When using an :obj:`int` as an operand, the operation is performed on the
:attr:`.FixedPoint.bits` attribute, and not the numerical value.

..  doctest:: bitwise with int

    >>> x = FixedPoint('0b100011', 1, 3, 3, str_base=2)
    >>> str(a := 7 & x)
    '000011'

    >>> float(a)
    0.375

The order of  the operands is irrelevant.

..  doctest:: bitwise with int

    >>> str(b1 := x ^ 0b110000)
    '010011'

    >>> str(b2 := 0b110000 ^ x)
    '010011'

    >>> float(b1), float(b2)
    (2.375, 2.375)

The integer is masked to the the number of bits in the `FixedPoint` before
performing the operation.

..  doctest:: bitwise with int

    >>> b1 |= 0b11111111111111111111101100 # (only the left len(b1) bits are used)
    >>> str(b1), float(b1)
    ('111111', -0.125)

..  _inversion:

Inversion
===============================================================================

Use the unary inversion operator ``~`` (see :meth:`.FixedPoint.__invert__`) to
perform bitwise inversion.

..  doctest:: bitwise inversion

    >>> x = FixedPoint(0xAAAA)
    >>> hex(~x)
    '0x5555'

    >>> ~x == (x ^ x.bitmask)
    True
