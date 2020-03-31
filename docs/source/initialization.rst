..  currentmodule:: fixedpoint

###############################################################################
Initialization
###############################################################################

..  _init_float:

*******************************************************************************
Initializing from a float
*******************************************************************************

When initializing a :class:`FixedPoint` from a `float`, *signed*, *m*, and *n*
are all optional. Thus the following object instantiations are all valid:

..  testsetup:: initializing from a float
    :skipif: should_skip("initializing from a float")

    reset_sn()

..  doctest:: initializing from a float
    :skipif: should_skip("initializing from a float")

    >>> from fixedpoint import FixedPoint
    >>> from math import pi
    >>> a = FixedPoint(pi) # No signed, m, or n argument
    >>> float(a), a.qformat
    (3.141592653589793, 'UQ2.48')

    >>> b = FixedPoint(pi, True) # No m or n argument
    >>> float(b), b.qformat
    (3.141592653589793, 'Q3.48')

    >>> c = FixedPoint(2**-80, m=10, n=80) # No signed argument
    >>> float(c), c.qformat
    (8.271806125530277e-25, 'UQ10.80')

..  |float issues| replace:: :pytut:`Issues and Limitations of Floating Point Arithmetic <floatingpoint.html>`

..  warning::

    Python's `float` type is typically implemented with 64-bit doubles,
    specified by `IEEE 754`_. This means that there's only 53 significant
    binary bits in a `float` (you can verify this by examining
    `sys.float_info`), and thus precision and resolution may be compromised in
    certain circumstances. See The Python Tutorial on the |float issues|.

..  doctest:: initializing from a float
    :skipif: should_skip("initializing from a float")

    >>> print(format(pi, '.60f'))
    3.141592653589793115997963468544185161590576171875000000000000
    >>> a = FixedPoint(pi, n=60, str_base=2)
    >>> print(str(a))
    11001001000011111101101010100010001000010110100011000000000000

In the example above, :math:`\pi` is only representable by 52 floating point
mantissa bits. Thus extending the decimal representation out to 60 places, the
bits eventually stabilize to 0 (even though :math:`\pi` is irrational and never
stabilizes). While the `FixedPoint` representation of the *float* is accurate,
this method of representing :math:`\pi` suffers from inaccuracy.

..  _init_int:

*******************************************************************************
Initializing from an int
*******************************************************************************

When initializing a `FixedPoint` from an `int`, *signed*, *m*, and *n* are all
optional. When *n* is left unspecified, it is guaranteed to be 0 (since integers
never require fractional bits). When *m* is left unspecified,
:meth:`FixedPoint.min_m` is used to deduce the number of integer bits needed to
represent *init*, and after rounding occurs, :meth:`~.FixedPoint.trim` is used
to remove superfluous leading 0s or sign-extended 1s.

..  testsetup:: initializing from an int
    :skipif: should_skip("initializing from an int")

    reset_sn()

..  doctest:: initializing from an int
    :skipif: should_skip("initializing from an int")

    >>> a = FixedPoint(-2**1000, n=42) # No signed or m argument
    >>> a.qformat
    'Q1001.42'

    >>> b = FixedPoint(14, True, 10) # No n argument
    >>> b.qformat, float(b)
    ('Q10.0', 14.0)

    >>> c = FixedPoint(0, 0, 19, 88) # Signed, m, and n arguments are present
    >>> str(c)
    '000000000000000000000000000'

..  |unlimited precision| replace:: :pylib:`unlimited precision <stdtypes.html#typesnumeric>`,

..  tip::

    Python's `int` type has |unlimited precision| meaning it can be as large
    as you need it to be! In fact, the FixedPoint :attr:`~.FixedPoint.bits` are
    stored internally as an *int*.

..  _init_str:

*******************************************************************************
Initializing from a str
*******************************************************************************

When initializing a `FixedPoint` from a `str`, *signed*, *m*, and *n* are
required:

..  testsetup:: initializing from a str
    :skipif: should_skip("initializing from a str")

    reset_sn()

..  doctest:: initializing from a str
    :skipif: should_skip("initializing from a str")

    >>> a = FixedPoint('1') # no Q format
    Traceback (most recent call last):
        ...
    ValueError: String literal initialization Q format must be fully constrained.

The string is converted to an *int* and this value is stored internally as the
FixedPoint :attr:`~.FixedPoint.bits`. This means that leading 0s are ignored
and not included in the total number of bits:

..  doctest:: initializing from a str
    :skipif: should_skip("initializing from a str")

    >>> a = FixedPoint('0x00000000000000001', signed=0, m=1, n=0) # Leading 0s
    >>> a.bits
    1

Rounding and overflow handling are not performed. If the bits of the string
exceed the specified :ref:`Q format <Q_Format>`, a :exc:`ValueError` is raised.

..  doctest:: initializing from a str
    :skipif: should_skip("initializing from a str")

    >>> a = FixedPoint('0xFF', 0, 1, 1) # A whole bunch of extra bits
    Traceback (most recent call last):
       ...
    ValueError: Superfluous bits detected in string literal '0xFF' for UQ1.1 format.

``int(init, 0)`` is used to internally convert the *str* to *int*, thus the
``0b``, ``0o``, or ``0x`` radix is required for binary, octal, or hexadecimal
strings, respectively. If the radix is not present, it is considered a decimal
number. This means if you have an integer that represents some known/desired
:ref:`Q format <Q_Format>`, you can simply call :func:`bin`, :func:`oct`,
:class:`str` or :func:`hex` to convert it to a *str*, then to a
:class:`FixedPoint`. This method of initialization may be super useful in
generating random stimulus:

..  doctest:: initializing from a str
    :skipif: should_skip("initializing from a str")

    >>> import random
    >>> random.seed(42)
    >>> signed, m, n = 1, 12, 13
    >>> bits = random.getrandbits(m + n)
    >>> x = FixedPoint(hex(bits), signed, m, n)
    >>> float(x), x.qformat
    (-1476.9078369140625, 'Q12.13')

..  warning::

    Converting a negative integer to a string is not allowed; the bits of
    interest should be masked before converting to a string.

..  doctest:: initializing from a str
    :skipif: should_skip("initializing from a str")

    >>> x = FixedPoint('-1', signed=1, m=2, n=0)
    Traceback (most recent call last):
       ...
    ValueError: Superfluous bits detected in string literal '-1' for Q2.0 format.

    >>> m, n = 2, 0
    >>> mask = 2**(m + n) - 1
    >>> x = FixedPoint(str(-1 & mask), 1, m, n)
    >>> float(x), x.qformat
    (-1.0, 'Q2.0')

..  _init_fixedpoint:

*******************************************************************************
Initializing from another FixedPoint
*******************************************************************************

When initializing a `FixedPoint` from another `FixedPoint`, only *init* is
required; all other arguments are ignored.

..  testsetup:: initializing from a FixedPoint
    :skipif: should_skip("initializing from a FixedPoint")

    reset_sn()

..  doctest:: initializing from a FixedPoint
    :skipif: should_skip("initializing from a FixedPoint")

    >>> x = FixedPoint(2**-5)
    >>> x.qformat
    'UQ0.5'

    >>> y = FixedPoint(x, n=492) # n is ignored
    >>> y.qformat
    'UQ0.5'

..  _initialize_from_other_types:

*******************************************************************************
Initializing from other types
*******************************************************************************

When *init* is not a(n) `float`, `int`, `str`, or `FixedPoint`, the object
is cast to a *float*.

..  testsetup:: initializing from other types
    :skipif: should_skip("initializing from other types")

    reset_sn()

..  doctest:: initializing from other types
    :skipif: should_skip("initializing from other types")

    >>> from decimal import Decimal
    >>> x = Decimal(1) / Decimal(10)
    >>> y = FixedPoint(x)
    >>> z = FixedPoint(0.1)
    >>> y == z
    True

If this fails, a :exc:`TypeError` is raised.

..  doctest:: initializing from other types
    :skipif: should_skip("initializing from other types")

    >>> file = open('some_file', 'a')
    >>> FixedPoint(file)
    Traceback (most recent call last):
        ...
    TypeError: Unsupported type <class '_io.TextIOWrapper'>; cannot convert to float.

..  _initializers:

*******************************************************************************
Initializers
*******************************************************************************

When the :ref:`Q format <Q_Format>` of a `FixedPoint` should stay the same, but
a different value is needed, it is quicker to use one of the following
*initializers* than generating a new `FixedPoint` object:

* :meth:`~.FixedPoint.from_float`
* :meth:`~.FixedPoint.from_int`
* :meth:`~.FixedPoint.from_string`

It's quicker because the :ref:`Q format <Q_Format>` and properties need not be
validated.

..  This test example is checked for syntax but the output is not verified
    because it will differ between each call.

..  testsetup:: constructor vs initializer
    :skipif: should_skip("constructor vs initializer")

    reset_sn()
    oldprint = print
    def print(*args, **kwargs):
        pass

..  testcode:: constructor vs initializer
    :skipif: should_skip("constructor vs initializer")

    from timeit import timeit

    test_constructor = {
        'stmt': 'FixedPoint(hex(random.getrandbits(100)), 1, 42, 58)',
        'setup': 'from fixedpoint import FixedPoint; import random',
        'number': 100000,
    }

    test_initializer = {
        'stmt': 'x.from_string(hex(random.getrandbits(100)))',
        'setup': 'import fixedpoint, random; x = fixedpoint.FixedPoint(0, 1, 42, 58)',
        'number': 100000,
    }

    print("Constructor:", timeit(**test_constructor))
    print("Initializer:", timeit(**test_initializer))

The code block above tests the difference between creating 100,000 `FixedPoint`
instances and 100,000 initializer calls. There is a significant time improvement
by using the initializer :meth:`~.FixedPoint.from_string` instead of the
:class:`FixedPoint` constructor:

..  testoutput:: constructor vs initializer
    :skipif: True

    Constructor: 1.6910291
    Initializer: 0.18432009999999988

The results are similar with :meth:`~.FixedPoint.from_int`:

..  testoutput:: constructor vs initializer
    :skipif: True

    Constructor: 1.8801342
    Initializer: 0.4326542

and :meth:`~.FixedPoint.from_float` (using :func:`random.random` with 50
fractional bits):

..  testoutput:: constructor vs initializer
    :skipif: True

    Constructor: 2.4381994
    Initializer: 0.7997059000000002

..  testcleanup:: constructor vs initializer
    :skipif: should_skip("constructor vs initializer")

    print = oldprint

One example is when stimulus is being created that uses a single `FixedPoint`
at a time, or when the processing of that `FixedPoint` does not change its
properties. Create a single instance, and then just use the initializer in
each loop iteration:

..  testcode:: using an initializer in a loop
    :skipif: should_skip("using an initializer in a loop")

    from fixedpoint import FixedPoint
    import random

    # Q1.24
    qformat = {'signed': True, 'm': 1, 'n': 24}

    # A single instance
    x = FixedPoint(0, **qformat)

    for i in range(10000):
        x.from_string(hex(random.getrandbits(25)))

        # Do stuff with x that doesn't change the Q format. If the Q format
        # is changed, you could use the context manager to restore the original
        # values once the processing in this iteration is done.

..  _overflow:

*******************************************************************************
``overflow``
*******************************************************************************

Overflow occurs when a number is greater than the minimum or maximum value that
the fixed point number can :ref:`represent <range>` (underflow is also
generalized here to *overflow*). This is determined by the
:ref:`Q format <Q_Format>`.

The FixedPoint class offers two forms of overflow handling:

* ``'clamp'`` (default if not specified)
* ``'wrap'``

..  _clamp:

``'clamp'``
===============================================================================

Clamping limits the number to the most maximum or minimum value
:ref:`representable <range>` by the available :ref:`Q format <Q_Format>`. The
:attr:`~.FixedPoint.overflow_alert` property may need to be changed from the
default ``'error'`` to allow processing to continue.

..  testsetup:: clamp
    :skipif: should_skip("clamp")

    reset_sn()

..  doctest:: clamp
    :skipif: should_skip("clamp")

    >>> x = FixedPoint(999, 0, 4, 1, overflow='clamp')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN1] Integer 999 overflows in UQ4.1 format.

    >>> try:
    ...     x
    ... except NameError:
    ...     print('x was not assigned because of the FixedPointOverflowError')
    x was not assigned because of the FixedPointOverflowError

    >>> x = FixedPoint(999, 0, 4, 1, overflow='clamp', overflow_alert='ignore')
    >>> x.clamped, x.qformat, bin(x), float(x)
    (True, 'UQ4.1', '0b11111', 15.5)

    >>> x = FixedPoint(999, 1, 4, 1, overflow='clamp', overflow_alert='warning')
    WARNING [SN3]: Integer 999 overflows in Q4.1 format.
    WARNING [SN3]: Clamped to maximum.
    >>> x.qformat, hex(x), float(x)
    ('Q4.1', '0xf', 7.5)

    >>> x = FixedPoint(-999, 0, 4, 1, overflow='clamp', overflow_alert='warning')
    WARNING [SN4]: Integer -999 overflows in UQ4.1 format.
    WARNING [SN4]: Clamped to minimum.
    >>> x.qformat, hex(x), float(x)
    ('UQ4.1', '0x0', 0.0)

    >>> x = FixedPoint(-999, 1, 4, 1, overflow='clamp', overflow_alert='ignore')
    >>> x.qformat, bin(x), float(x)
    ('Q4.1', '0b10000', -8.0)

..  _wrap:

``'wrap'``
===============================================================================

Wrapping will compute the full-length value and then mask away unspecified MSbs.
This is also called 2's complement overflow. The
:attr:`~.FixedPoint.overflow_alert` property may need to be changed from the
default ``'error'`` to allow processing to continue.

..  testsetup:: wrap
    :skipif: should_skip("wrap")

    reset_sn()

..  doctest:: wrap
    :skipif: should_skip("wrap")

    >>> big = 0b11000 # Needs 5 (unsigned) integer bits to represent
    >>> big
    24
    >>> x = FixedPoint(big, 0, 4, 1, overflow='wrap')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN1] Integer 24 overflows in UQ4.1 format.

    >>> try:
    ...     x
    ... except NameError:
    ...     print('x was not assigned because of the FixedPointOverflowError')
    x was not assigned because of the FixedPointOverflowError

    >>> x = FixedPoint(big, 0, 4, 1, overflow='wrap', overflow_alert='ignore')
    >>> x.clamped, x.qformat, bin(x), float(x)
    (False, 'UQ4.1', '0b10000', 8.0)

    >>> x = FixedPoint(big, 1, 4, 1, overflow='wrap', overflow_alert='warning')
    WARNING [SN3]: Integer 24 overflows in Q4.1 format.
    WARNING [SN3]: Wrapped maximum.
    >>> x.qformat, hex(x), float(x)
    ('Q4.1', '0x10', -8.0)

    >>> x = FixedPoint(-1, 0, 4, 1, overflow='wrap', overflow_alert='warning')
    WARNING [SN4]: Integer -1 overflows in UQ4.1 format.
    WARNING [SN4]: Wrapped minimum.
    >>> x.qformat, bin(x), 15.0
    ('UQ4.1', '0b11110', 15.0)

    >>> -big & 0b11111
    8
    >>> x = FixedPoint(-big, 1, 4, 1, overflow='wrap', overflow_alert='ignore')
    >>> x.qformat, bin(x), float(x)
    ('Q4.1', '0b10000', -8.0)

..  _rounding:

*******************************************************************************
``rounding``
*******************************************************************************

Rounding occurs when non-zero fractional bits must be removed from the number.
The :class:`FixedPoint` class offers several forms of rounding:

* ``'convergent'`` (default for signed numbers if not specified)
* ``'nearest'`` (default for unsigned numbers if not specified)
* ``'out'``
* ``'in'``
* ``'up'``
* ``'down'``

The table below summarizes the behavior of all supported rounding schemes.
When the number in the first column is rounded to 0 fractional bits using the
rounding scheme in the first row, the result is shown.

..  This testcode generates the table below it. Turn off the skipif option to
    regenerate the table.

..  testcode:: rounding comparison table generation
    :hide:
    :skipif: True

    from fixedpoint.properties import Rounding
    schemes = tuple(x.name for x in Rounding)
    N = len(schemes)
    W = len(max(schemes, key=len))
    divider = f"+{'+'.join(['-' * (W+2) for _ in range(N+1)])}+"

    # Header row
    print(divider)
    print('| ', ' ' * W, end='')
    for i, scheme in enumerate(schemes, 1):
        print('|', format(scheme, f' ^{W}'), '', end='|\n' * bool(i == N))
    print(divider.replace('-', '='))

    x = FixedPoint(0, signed=1, m=5, n=0, rounding=scheme)
    for sign in (-1, +1):
        for mag in (3.49, 3.5, 3.51):
            val = mag * sign
            for i, scheme in enumerate(schemes, 1):
                if i == 1:
                    print(f'| {val: ^+{W}.2f} ', end='')
                x.rounding = scheme
                x.from_float(val)
                print(f'| {x: ^+{W}.0f} ', end='|\n' * bool(i == N))
            print(divider)

..  table:: Rounding Scheme Summary
    :widths: grid
    :align: center

    +-------+------------+---------+------+----+-----+----+
    |       | convergent | nearest | down | in | out | up |
    +=======+============+=========+======+====+=====+====+
    | -3.49 |     -3     |    -3   |  -4  | -3 |  -3 | -3 |
    +-------+------------+---------+------+----+-----+----+
    | -3.50 |     -4     |    -3   |  -4  | -3 |  -4 | -3 |
    +-------+------------+---------+------+----+-----+----+
    | -3.51 |     -4     |    -4   |  -4  | -3 |  -4 | -3 |
    +-------+------------+---------+------+----+-----+----+
    | +3.49 |     +3     |    +3   |  +3  | +3 |  +3 | +4 |
    +-------+------------+---------+------+----+-----+----+
    | +3.50 |     +4     |    +4   |  +3  | +3 |  +4 | +4 |
    +-------+------------+---------+------+----+-----+----+
    | +3.51 |     +4     |    +4   |  +3  | +3 |  +4 | +4 |
    +-------+------------+---------+------+----+-----+----+

..  _convergent:

``'convergent'``
===============================================================================

Rounds toward the nearest even value in the case of a tie, otherwise rounds to
the nearest value. :wikirounding:`Wikipedia <Round_half_to_even>` outlines the
pros and cons of convergent rounding.

..  testsetup:: convergent round
    :skipif: should_skip("convergent round")

    reset_sn()

..  doctest:: convergent round
    :skipif: should_skip("convergent round")

    >>> x = FixedPoint(0, signed=1, m=4, n=0, rounding='convergent')
    >>> for sign in [+1, -1]:
    ...     for mag in [3.49, 3.5, 3.51, 4.49, 4.5, 4.51]:
    ...         x.from_float(init := mag * sign)
    ...         print(f"{init: .2f} rounds to {x: .0f}")
     3.49 rounds to  3
     3.50 rounds to  4
     3.51 rounds to  4
     4.49 rounds to  4
     4.50 rounds to  4
     4.51 rounds to  5
    -3.49 rounds to -3
    -3.50 rounds to -4
    -3.51 rounds to -4
    -4.49 rounds to -4
    -4.50 rounds to -4
    -4.51 rounds to -5

The example above shows easy-to-understand values and rounding off fractional
bits completely. However, the same principal applies to round to a non-zero
number of fractional bits:

..  doctest:: convergent round
    :skipif: should_skip("convergent round")

    >>> x = FixedPoint('0b100110', 1, 2, 4, rounding='convergent')
    >>> float(x), x.qformat
    (-1.625, 'Q2.4')

    >>> y = FixedPoint(float(x), n=2, rounding='convergent') # round to 2 frac bits
    >>> float(y), bin(y)
    (-1.5, '0b1010')

Because convergent rounding can cause the value of the number to increase, it
can cause overflow.

..  testsetup:: convergent round with overflow
    :skipif: should_skip("convergent round with overflow")

    reset_sn()

..  doctest:: convergent round with overflow
    :skipif: should_skip("convergent round with overflow")

    >>> x = FixedPoint(3.5)
    >>> x.qformat # Can be represented with 2 integer bits
    'UQ2.1'
    >>> y = FixedPoint(3.5, m=2, n=0, rounding='convergent')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN2] 3.500000e+00 overflows in UQ2.0 format.

    >>> z = FixedPoint(3.5, n=0, rounding='convergent') # Requires 4 integer bits
    >>> float(z), z.qformat
    (4.0, 'UQ3.0')

..  _nearest:

``'nearest'``
===============================================================================

Rounds toward :math:`+\infty` in the case of a tie, otherwise rounds to the
nearest value. :wikirounding:`Wikipedia <Round_half_up>` describes this widely
used rounding method.

..  testsetup:: round nearest
    :skipif: should_skip("round nearest")

    reset_sn()

..  doctest:: round nearest
    :skipif: should_skip("round nearest")

    >>> x = FixedPoint(0, signed=1, m=4, n=0, rounding='nearest')
    >>> for sign in [+1, -1]:
    ...     for mag in [3.49, 3.5, 3.51, 4.49, 4.5, 4.51]:
    ...         x.from_float(init := mag * sign)
    ...         print(f"{init: .2f} rounds to {x: .0f}")
     3.49 rounds to  3
     3.50 rounds to  4
     3.51 rounds to  4
     4.49 rounds to  4
     4.50 rounds to  5
     4.51 rounds to  5
    -3.49 rounds to -3
    -3.50 rounds to -3
    -3.51 rounds to -4
    -4.49 rounds to -4
    -4.50 rounds to -4
    -4.51 rounds to -5

The example above shows easy-to-understand values and rounding off fractional
bits completely. However, the same principal applies to round to a non-zero
number of fractional bits:

..  doctest:: round nearest
    :skipif: should_skip("round nearest")

    >>> x = FixedPoint('0b100110', 1, 2, 4, rounding='nearest')
    >>> x.qformat, float(x)
    ('Q2.4', -1.625)

    >>> y = FixedPoint(float(x), n=2, rounding='nearest') # round to 2 frac bits
    >>> bin(y), float(y)
    ('0b1010', -1.5)

Because rounding to nearest can cause the value of the number to increase, it
can cause overflow.

..  testsetup:: round nearest with overflow
    :skipif: should_skip("round nearest with overflow")

    reset_sn()

..  doctest:: round nearest with overflow
    :skipif: should_skip("round nearest with overflow")

    >>> FixedPoint(15.5).qformat # Can be represented with 4 integer bits
    'UQ4.1'
    >>> x = FixedPoint(15.5, m=4, n=0, rounding='nearest')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN2] 1.550000e+01 overflows in UQ4.0 format.

    >>> z = FixedPoint(15.5, n=0, rounding='nearest') # Requires 5 integer bits
    >>> float(z), z.qformat
    (16.0, 'UQ5.0')

..  _out:

``'out'``
===============================================================================

Rounds away from 0 in the case of a tie, otherwise rounds to the nearest value.
:wikirounding:`Wikipedia <Round_half_away_from_zero>` outlines the pros and
cons of rounding away from 0.

..  doctest:: round out
    :skipif: should_skip("round out")

    >>> x = FixedPoint(0, signed=1, m=4, n=0, rounding='out')
    >>> for sign in [+1, -1]:
    ...     for mag in [3.49, 3.5, 3.51, 4.49, 4.5, 4.51]:
    ...         x.from_float(init := mag * sign)
    ...         print(f"{init: .2f} rounds to {x: .0f}")
     3.49 rounds to  3
     3.50 rounds to  4
     3.51 rounds to  4
     4.49 rounds to  4
     4.50 rounds to  5
     4.51 rounds to  5
    -3.49 rounds to -3
    -3.50 rounds to -4
    -3.51 rounds to -4
    -4.49 rounds to -4
    -4.50 rounds to -5
    -4.51 rounds to -5

The example above shows easy-to-understand values and rounding off fractional
bits completely. However, the same principal applies to round to a non-zero
number of fractional bits:

..  doctest:: round out
    :skipif: should_skip("round out")

    >>> x = FixedPoint('0b100110', 1, 2, 4, rounding='out')
    >>> x.qformat, float(x)
    ('Q2.4', -1.625)

    >>> y = FixedPoint(float(x), n=2, rounding='out') # round to 2 fractional bits
    >>> bin(y), float(y)
    ('0b1001', -1.75)

Because rounding away from 0 causes the magnitude of the number to increase, it
can cause overflow.

..  testsetup:: round out with overflow
    :skipif: should_skip("round out with overflow")

    reset_sn()

..  doctest:: round out with overflow
    :skipif: should_skip("round out with overflow")

    >>> FixedPoint(15.5).qformat # Can be represented with 4 integer bits
    'UQ4.1'
    >>> x = FixedPoint(15.5, m=4, n=0, rounding='out')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN2] 1.550000e+01 overflows in UQ4.0 format.

    >>> z = FixedPoint(15.5, n=0, rounding='out') # Requires 5 integer bits
    >>> float(z), z.qformat
    (16.0, 'UQ5.0')

..  _in:

``'in'``
===============================================================================

Rounds unconditionally toward 0.

..  note::

    This has the same effect as truncating *decimal* digits.

..  warning::

    This is **not** the same as truncating *bits*; use the down_ rounding
    scheme for bit truncation.

..  doctest:: round in
    :skipif: should_skip("round in")

    >>> x = FixedPoint(0, signed=1, m=4, n=0, rounding='in')
    >>> for sign in [+1, -1]:
    ...     for mag in [3.49, 3.5, 3.51, 4.49, 4.5, 4.51]:
    ...         x.from_float(init := mag * sign)
    ...         print(f"{init: .2f} rounds to {x: .0f}")
     3.49 rounds to  3
     3.50 rounds to  3
     3.51 rounds to  3
     4.49 rounds to  4
     4.50 rounds to  4
     4.51 rounds to  4
    -3.49 rounds to -3
    -3.50 rounds to -3
    -3.51 rounds to -3
    -4.49 rounds to -4
    -4.50 rounds to -4
    -4.51 rounds to -4

The example above shows easy-to-understand values and rounding off fractional
bits completely. However, the same principal applies to round to a non-zero
number of fractional bits:

..  doctest:: round in
    :skipif: should_skip("round in")

    >>> x = FixedPoint('0b100110', 0, 2, 4, rounding='in')
    >>> x.qformat, float(x)
    ('UQ2.4', 2.375)

    >>> y = FixedPoint(float(x), n=2, rounding='in') # round to 2 fractional bits
    >>> bin(y), float(y)
    ('0b1001', 2.25)

Because rounding in will always decrease the number's magnitude, it cannot
cause overflow.

..  _up:

``'up'``
===============================================================================

Rounds unconditionally toward :math:`+\infty`.

..  doctest:: round up
    :skipif: should_skip("round up")

    >>> x = FixedPoint(0, signed=1, m=4, n=0, rounding='up')
    >>> for sign in [+1, -1]:
    ...     for mag in [3.49, 3.5, 3.51, 4.49, 4.5, 4.51]:
    ...         x.from_float(init := mag * sign)
    ...         print(f"{init: .2f} rounds to {x: .0f}")
     3.49 rounds to  4
     3.50 rounds to  4
     3.51 rounds to  4
     4.49 rounds to  5
     4.50 rounds to  5
     4.51 rounds to  5
    -3.49 rounds to -3
    -3.50 rounds to -3
    -3.51 rounds to -3
    -4.49 rounds to -4
    -4.50 rounds to -4
    -4.51 rounds to -4

The example above shows easy-to-understand values and rounding off fractional
bits completely. However, the same principal applies to round to a non-zero
number of fractional bits:

..  doctest:: round up
    :skipif: should_skip("round up")

    >>> x = FixedPoint('0b100110', 0, 2, 4, rounding='up')
    >>> x.qformat, float(x)
    ('UQ2.4', 2.375)

    >>> y = FixedPoint(float(x), n=2, rounding='up') # round to 2 fractional bits
    >>> bin(y), float(y)
    ('0b1010', 2.5)

Because rounding up can cause the number's magnitude to increase, it can cause
overflow.

..  testsetup:: round up with overflow
    :skipif: should_skip("round up with overflow")

    reset_sn()

..  doctest:: round up with overflow
    :skipif: should_skip("round up with overflow")

    >>> FixedPoint(15.5).qformat # Can be represented with 4 integer bits
    'UQ4.1'
    >>> x = FixedPoint(15.5, m=4, n=0, rounding='up')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN2] 1.550000e+01 overflows in UQ4.0 format.

    >>> z = FixedPoint(15.5, n=0, rounding='up') # Requires 5 integer bits
    >>> float(z), z.qformat
    (16.0, 'UQ5.0')

..  _down:

``'down'``
===============================================================================

Rounds unconditionally toward :math:`-\infty`.

.. note::

    This is the same as truncating bits, since fractional bits cannot have
    negative weight.

..  warning::

    This is **not** the same as truncating *decimal* digits; use the in_
    rounding scheme to achieve decimal digit truncation.

..  doctest:: round down
    :skipif: should_skip("round down")

    >>> x = FixedPoint(0, signed=1, m=4, n=0, rounding='down')
    >>> for sign in [+1, -1]:
    ...     for mag in [3.49, 3.5, 3.51, 4.49, 4.5, 4.51]:
    ...         x.from_float(init := mag * sign)
    ...         print(f"{init: .2f} rounds to {x: .0f}")
     3.49 rounds to  3
     3.50 rounds to  3
     3.51 rounds to  3
     4.49 rounds to  4
     4.50 rounds to  4
     4.51 rounds to  4
    -3.49 rounds to -4
    -3.50 rounds to -4
    -3.51 rounds to -4
    -4.49 rounds to -5
    -4.50 rounds to -5
    -4.51 rounds to -5

The example above shows easy-to-understand values and rounding off fractional
bits completely. However, the same principal applies to round to a non-zero
number of fractional bits:

..  doctest:: round down
    :skipif: should_skip("round down")

    >>> x = FixedPoint('0b100110', 0, 2, 4, rounding='down')
    >>> x.qformat, float(x)
    ('UQ2.4', 2.375)

    >>> y = FixedPoint(float(x), n=2, rounding='down')
    >>> bin(y), float(y)
    ('0b1001', 2.25)

Because rounding down will always make the value of the number smaller in
magnitude, it cannot cause overflow.

..  _overflow_alert:

*******************************************************************************
``overflow_alert``
*******************************************************************************

The ``overflow_alert`` property indicates how you will be notified and if
operation should be halted when overflow occurs. You can choose from:

* ``'error'`` (default if not specified)
* ``'warning'``
* ``'ignore'``

..  _overflow_causes:

Overflow can occur in the following scenarios:

* initialization
* changing the :attr:`~.FixedPoint.signed` attribute
* negation (the unary :meth:`~.FixedPoint.__neg__` operator)
* reducing the number of integer bits

  * changing the :attr:`~.FixedPoint.m` attribute
  * :meth:`~.FixedPoint.resize`
  * :meth:`~.FixedPoint.clamp`
  * :meth:`~.FixedPoint.wrap`
  * :meth:`~.FixedPoint.keep_lsbs`

* unsigned subtraction (see :meth:`~.FixedPoint.__sub__`)
* rounding with the following schemes/methods

  * :ref:`convergent` (or using :meth:`~.FixedPoint.round_convergent`)
  * :ref:`nearest` (or using :meth:`~.FixedPoint.round_nearest`)
  * :ref:`out` (or using :meth:`~.FixedPoint.round_out`)
  * :ref:`up` (or using :meth:`~.FixedPoint.round_up`)

Some methods that can cause overflow have an *alert* argument which can
change the notification scheme for the scope of the method. This can be used if
overflow is expected.

``'error'``
===============================================================================

In this notification scheme, overflow causes execution to halt and a
:exc:`FixedPointOverflowError` is raised.

..  testsetup:: overflow_alert error
    :skipif: should_skip("overflow_alert error")

    reset_sn()

..  doctest:: overflow_alert error
    :skipif: should_skip("overflow_alert error")

    >>> x = FixedPoint(999, 0, 1, 0, overflow_alert='error')
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN1] Integer 999 overflows in UQ1.0 format.

    >>> x # Does not exist because of the exception!
    Traceback (most recent call last):
        ...
    NameError: name 'x' is not defined

``'warning'``
===============================================================================

In this notification scheme, overflow will emit two warnings, and execution will
continue. The first warning informs you of the overflow cause, the second
warning informs you of the action taken.

..  testsetup:: overflow_alert warning
    :skipif: should_skip("overflow_alert warning")

    reset_sn()

..  doctest:: overflow_alert warning
    :skipif: should_skip("overflow_alert warning")

    >>> x = FixedPoint(999, 0, 1, 0, overflow='clamp', overflow_alert='warning')
    WARNING [SN1]: Integer 999 overflows in UQ1.0 format.
    WARNING [SN1]: Clamped to maximum.
    >>> float(x), x.clamped
    (1.0, True)

    >>> y = FixedPoint(3, 1, 2, 0, overflow='wrap', overflow_alert='warning')
    WARNING [SN2]: Integer 3 overflows in Q2.0 format.
    WARNING [SN2]: Wrapped maximum.
    >>> float(y), y.clamped
    (-1.0, False)

``'ignore'``
===============================================================================

In this notification scheme, overflow is handled silently.

..  testsetup:: overflow_alert ignore
    :skipif: should_skip("overflow_alert ignore")

    reset_sn()

..  doctest:: overflow_alert ignore
    :skipif: should_skip("overflow_alert ignore")

    >>> x = FixedPoint(3.75, 0, 2, 1, overflow_alert='ignore')
    >>> float(x), x.clamped
    (3.5, True)

    >>> y = FixedPoint(-3, 1, 2, 10, overflow='wrap', overflow_alert='ignore')
    >>> float(y), bin(y)
    (1.0, '0b10000000000')

..  _mismatch_alert:

*******************************************************************************
``mismatch_alert``
*******************************************************************************

The ``mismatch_alert`` property indicates how you will be notified and if
operation should be halted when any property of 2 combining `FixedPoint`\ s do
not match. You can choose from:

* ``'error'``
* ``'warning'`` (default if not specified)
* ``'ignore'``

For instance, what are the properties of ``c`` below?

..  The PropertyResolver uses a set to check for mismatches, and sets are
    unordered. So we have to mess with the order of the warning output
    to make sure this doctest passes. Warnings are captured with a StringIO
    instance, and then the mismatching properties are printed to stdout in
    alphabetical order.

..  testsetup:: mismatch_alert example
    :skipif: should_skip("mismatch_alert example")

    reset_sn()

..  testcode:: mismatch_alert example
    :skipif: should_skip("mismatch_alert example")

    a = FixedPoint(1,
        overflow='wrap',
        rounding='in',
        overflow_alert='error',
        mismatch_alert='warning',
        implicit_cast_alert='ignore',
        str_base=8,
    )

    b = FixedPoint(3.12345,
        overflow='clamp',
        rounding='convergent',
        overflow_alert='warning',
        mismatch_alert='ignore',
        implicit_cast_alert='error',
        str_base=2,
    )

    c = a + b

FixedPoint uses the :class:`~fixedpoint.properties.PropertyResolver` class to
resolve property mismatches for the following operations:

    * addition (see :meth:`.FixedPoint.__add__`)
    * subtraction (see :meth:`.FixedPoint.__sub__`)
    * multiplication (see :meth:`.FixedPoint.__mul__`)

(in case you're curious, the example above produces the following):

..  testoutput:: mismatch_alert example
    :skipif: should_skip("mismatch_alert example")

    WARNING [SN1]: Non-matching mismatch_alert behaviors ['ignore', 'warning'].
    WARNING [SN1]: Using 'warning'.
    WARNING [SN1]: Non-matching overflow behaviors ['clamp', 'wrap'].
    WARNING [SN1]: Using 'clamp'.
    WARNING [SN1]: Non-matching rounding behaviors ['convergent', 'in'].
    WARNING [SN1]: Using 'convergent'.
    WARNING [SN1]: Non-matching overflow_alert behaviors ['error', 'warning'].
    WARNING [SN1]: Using 'error'.
    WARNING [SN1]: Non-matching implicit_cast_alert behaviors ['error', 'ignore'].
    WARNING [SN1]: Using 'error'.

..  tip::

    You may consider starting out with :attr:`~.FixedPoint.mismatch_alert` set
    to ``'error'``, just to make sure you understand the nuances of the
    :class:`~.FixedPoint` class.

``'error'``
===============================================================================

In this notification scheme, the first property mismatch encountered will raise
a :exc:`MismatchError` exception.

..  testsetup:: mismatch_alert error
    :skipif: should_skip("mismatch_alert error")

    reset_sn()

..  doctest:: mismatch_alert error
    :skipif: should_skip("mismatch_alert error")

    >>> a = FixedPoint(-1, rounding='convergent', mismatch_alert='error')
    >>> b = FixedPoint(+1, rounding='nearest', mismatch_alert='error')
    >>> c = a + b  #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    fixedpoint.MismatchError: [SN1] Non-matching rounding behaviors ['convergent', 'nearest'].

    >>> c # Does not exist because of the exception!
    Traceback (most recent call last):
        ...
    NameError: name 'c' is not defined

If either `FixedPoint`\ 's :attr:`~.FixedPoint.mismatch_alert` is ``'error'``,
then an exception is thrown. This is even the case if one of the settings is
``'ignore'`` (see the example below). When there are multiple mismatched
properties the first mismatch encountered in the
:ref:`resolution order <property_resolution_order>` is the culprit.

..  doctest:: mismatch_alert error
    :skipif: should_skip("mismatch_alert error")

    >>> a.mismatch_alert = 'ignore' # Now mismatch_alert and rounding don't match
    >>> d = a + b #doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    MismatchError: Non-matching mismatch_alert behaviors ['error', 'ignore'].

    >>> d # Does not exist because of the exception!
    Traceback (most recent call last):
        ...
    NameError: name 'd' is not defined

``'warning'``
===============================================================================

In this notification scheme, two warnings are emitted for each mismatch, but
execution will continue. The first warning informs you of the non-matching
properties, the second informs you of the resolution.

..  testsetup:: mismatch_alert warning
    :skipif: should_skip("mismatch_alert warning")

    reset_sn()

..  doctest:: mismatch_alert warning
    :skipif: should_skip("mismatch_alert warning")

    >>> x = FixedPoint(1492)
    >>> y = FixedPoint(x)
    >>> y.rounding = 'down'
    >>> z = x - y
    WARNING [SN1]: Non-matching rounding behaviors ['down', 'nearest'].
    WARNING [SN1]: Using 'nearest'.

    >>> z.rounding
    'nearest'

Warnings are emitted in the
:ref:`property resolution order<property_resolution_order>`.

..  doctest:: mismatch_alert warning
    :skipif: should_skip("mismatch_alert warning")

    >>> y.overflow = 'wrap'
    >>> zz = x + y # Overflow is resolved before rounding
    WARNING [SN1]: Non-matching overflow behaviors ['clamp', 'wrap'].
    WARNING [SN1]: Using 'clamp'.
    WARNING [SN1]: Non-matching rounding behaviors ['down', 'nearest'].
    WARNING [SN1]: Using 'nearest'.

    >>> zz.rounding, zz.overflow
    ('nearest', 'clamp')

For augmented arithmetic operations (e.g. ``+=``), mismatches are ignored
because a new :class:`FixedPoint` is not being created.

..  This doctest shows that nothing is printed to stderr; its a farce...
    The doctest_global_setup in conf.py redirects the warning logger to stdout.
    So this is really just for show...

..  doctest:: mismatch_alert warning
    :skipif: should_skip("mismatch_alert warning")

    >>> import sys, io
    >>> sys.stderr = io.StringIO() # redirect stderr to a string buffer
    >>> x -= y
    >>> y *= x
    >>> sys.stderr.flush()
    >>> sys.stderr.getvalue() # Nothing written to stderr
    ''
    >>> sys.stderr = sys.__stderr__ # Restore stderr

``'ignore'``
===============================================================================

In this notification scheme, property mismatches are resolved silently.
The same examples from above are used.

..  doctest:: mismatch_alert ignore
    :skipif: should_skip("mismatch_alert ignore")

    >>> x = FixedPoint(1492, mismatch_alert='ignore')
    >>> y = FixedPoint(x)
    >>> y.rounding = 'down'
    >>> z = x - y
    >>> z.rounding
    'nearest'

    >>> y.overflow = 'wrap'
    >>> zz = x + y # Overflow is resolved before rounding
    >>> zz.rounding, zz.overflow
    ('nearest', 'clamp')

..  _implicit_cast_alert:

*******************************************************************************
``implicit_cast_alert``
*******************************************************************************

Arithmetic operations allow non-\ `FixedPoint`\ s as operands, and in such
cases, are cast to a `FixedPoint` (see the :ref:`initialize_from_other_types`
section) prior to operation. When a value is cast, its value is compared to the
previous object, and if it doesn't exactly match, `FixedPoint` emits an alert.
The ``implicit_cast_alert`` property indicates how you will be notified and if
operation should be halted when implicit casting introduces error. You can
choose from:

* ``'error'``
* ``'warning'`` (default if not specified)
* ``'ignore'``

..  |patcher| replace:: :pylib:`patcher <unittest.mock.html#the-patchers>`

..  note::

    Finding stimulus to actually cause this alert naturally has not been
    achieved. This notification scheme was unit tested using a |patcher|. The
    examples in this section employ the same technique to illustrate
    functionality.

Imiplicit cast alerts can conceivably be issued for the following operations:

    * addition (see :meth:`.FixedPoint.__add__`)
    * subtraction (see :meth:`.FixedPoint.__sub__`)
    * multiplication (see :meth:`.FixedPoint.__mul__`)

``'error'``
===============================================================================

In this notification scheme, numerical error introduced by implicit casting will
raise an :exc:`ImplicitCastError` exception and operation is halted.

..  testsetup:: implicit_cast_alert error
    :skipif: should_skip("implicit_cast_alert error")

    patch = patch_min_n(FixedPoint(0.2).n - 1)
    reset_sn()

..  doctest:: implicit_cast_alert error
    :skipif: should_skip("implicit_cast_alert error")

    >>> a = FixedPoint(3, implicit_cast_alert='error')
    >>> x = a + 0.2
    Traceback (most recent call last):
        ...
    fixedpoint.ImplicitCastError: [SN1] Casting 0.2 to UQ0.53 introduces an error of 5.551115e-17

    >>> x # Does not exist because of the exception!
    Traceback (most recent call last):
        ...
    NameError: name 'x' is not defined

..  testcleanup:: implicit_cast_alert error
    :skipif: should_skip("implicit_cast_alert error")

    unpatch(patch)

``'warning'``
===============================================================================

In this notification scheme, numerical error introduced by implicit casting will
emit a warning, but the operation is still carried out.

..  testsetup:: implicit_cast_alert warning
    :skipif: should_skip("implicit_cast_alert warning")

    patch = patch_min_n(FixedPoint(0.3).n - 1)
    reset_sn()

..  doctest:: implicit_cast_alert warning
    :skipif: should_skip("implicit_cast_alert warning")

    >>> a = FixedPoint(1969, implicit_cast_alert='warning')
    >>> a -= 0.3
    WARNING [SN1]: Casting 0.3 to UQ0.52 introduces an error of 5.551115e-17

    >>> print(f"{a:.60f}")
    1968.700000000000045474735088646411895751953125000000000000000000

..  testcleanup:: implicit_cast_alert warning
    :skipif: should_skip("implicit_cast_alert warning")

    unpatch(patch)

``'ignore'``
===============================================================================

In this notification scheme, numerical error introduced by implicit casting is
ignored.

..  doctest:: implicit_cast_alert ignore
    :skipif: should_skip("implicit_cast_alert ignore")

    >>> a = FixedPoint(-10.5, implicit_cast_alert='ignore')
    >>> x = 0.2 * a
    >>> print(f"{x:.60f}")
    -2.100000000000000088817841970012523233890533447265625000000000

..  _str_base:

*******************************************************************************
``str_base``
*******************************************************************************

When casting a :class:`FixedPoint` to a :class:`str`, the bits of the
`FixedPoint` are displayed. Since the :attr:`~.FixedPoint.bits` are stored
internally as an `int`, they are simply converted using :func:`bin`,
:func:`oct`, :class:`str`, or :func:`hex` from the :meth:`~.FixedPoint.__str__`
method. The ``str_base`` property indicates the base of the generated string.
You can choose from:


* ``16`` (default if not specified)
* ``10``
* ``8``
* ``2``

``16``
===============================================================================

Generates a hexadecimal string representative of :attr:`.FixedPoint.bits`. The
string is sign extended (or 0-padded) to the bit width of the object, and does
not include the radix.

..  doctest:: str_base 16
    :skipif: should_skip("str_base 16")

    >>> x = FixedPoint(0xdeadbeef, 1, 64, 8) # str_base=16 by default
    >>> str(x)
    '00000000deadbeef00'
    >>> str(-x)
    'ffffffff2152411100'

``10``
===============================================================================

Generates a decimal string representative of :attr:`.FixedPoint.bits`. The
string is not sign extended to the bit width of the object, and does not
include a radix. This is equivalent to ``str(FixedPoint(...).bits)``.

..  doctest:: str_base 10
    :skipif: should_skip("str_base 10")

    >>> x = FixedPoint(2, 1, 8, str_base=10)
    >>> str(x) # no zero-padding occurs
    '2'
    >>> x.n += 1 # Effectively multiplies the bits by 2
    >>> str(x)
    '4'
    >>> x.n = 0
    >>> str(-x) # Never negative
    '254'

``8``
===============================================================================

Generates an octal string representative of :attr:`.FixedPoint.bits`. The
string is sign extended (or 0-padded) to the bit width of the object, and does
not include the radix.

..  doctest:: str_base 8
    :skipif: should_skip("str_base 8")

    >>> x = FixedPoint(1/3, 1, 1, str_base=8)
    >>> x.qformat, str(x)
    ('Q1.54', '0252525252525252525')
    >>> str(-x)
    '1525252525252525253'

``2``
===============================================================================

Generates a binary string representative of :attr:`.FixedPoint.bits`. The
string is sign extended (or 0-padded) to the bit width of the object, and does
not include the radix.

..  doctest:: str_base 2
    :skipif: should_skip("str_base 2")

    >>> x = FixedPoint(-1 + 2**-40, str_base=2)
    >>> x.qformat, str(x)
    ('Q1.40', '10000000000000000000000000000000000000001')
    >>> str(-x)
    '01111111111111111111111111111111111111111'
