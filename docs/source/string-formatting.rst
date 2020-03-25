###############################################################################
String Conversion and Formatting
###############################################################################

..  currentmodule:: fixedpoint

When you need to generate a string representation of a :class:`FixedPoint`
number (such as stimulus generation for a test), you can use standard string
conversion (via ``str()``) or a more advanced string formatting using a
:pylib:`standard format specifier <string.html#format-specification-mini-language>`
with :meth:`str.format`, :func:`format`, or
:pyref:`f-strings <lexical_analysis.html#f-strings>`. These methods are
described below.

..  _str_conversion:

*******************************************************************************
String Conversion
*******************************************************************************

Calling ``str()`` on a :class:`FixedPoint` generates a decimal, binary, octal,
or hexadecimal string based on the :attr:`.FixedPoint.bits`. The latter 3 of
which are 0-padded (if necessary) to the bit length of the :class:`FixedPoint`
number. No radix is included.

..  doctest:: str conversion

    >>> init = '0b11001'
    >>> b = FixedPoint(init, 1, 3, 2, str_base=2)
    >>> str(b)
    '11001'
    >>> o = FixedPoint(init, 1, 3, 2, str_base=8)
    >>> str(o)
    '31'
    >>> d = FixedPoint(init, 1, 3, 2, str_base=10)
    >>> str(d)
    '25'
    >>> h = FixedPoint(init, 1, 3, 2, str_base=16)
    >>> str(h)
    '19'

..  _string_formatting:

*******************************************************************************
String Formatting
*******************************************************************************

..  include:: fixedpoint.rst
    :start-after: STRING FORMATTING INCLUDE START
    :end-before: STRING FORMATTING INCLUDE END

str() Output
===============================================================================

As described :ref:`above <str_conversion>`, ``str()`` generates a :class:`str`
from the :attr:`.FixedPoint.bits` in the base specified by
:attr:`.FixedPoint.str_base`. This can be further formatted with the
:pylib:`format specification mini language
<string.html#format-specification-mini-language>` using the ``format_spec``
``type`` ``'s'``.

The example below uses a :pyref:`formatted string literal (or f-string)
<lexical_analysis.html#f-strings>` to further format the output of ``str()``.

..  doctest:: format "s"

    >>> x = FixedPoint(0b1010_0101_1111, str_base=2)
    >>> str(x) # This is the str() output
    '101001011111'

    >>> f"{x:_^16s}" # Center str(x) in a field of underscores 16 characters wide
    '__101001011111__'

    >>> x.str_base = 16
    >>> f"{x:_^16s}" # Same thing but uses hex instead of binary due to str_base
    '______a5f_______'

The same thing can be done using :meth:`str.format`:

..  doctest:: format "s"

    >>> x.str_base = 8 # octal
    >>> '{:-^16s}'.format(x)
    '------5137------'

or :func:`format`:

.. doctest:: format "s"

    >>> x.str_base = 10
    >>> format(x, '~>6s')
    '~~2655'

The remaining examples will be done using :pyref:`f-strings
<lexical_analysis.html#f-strings>`, but the same syntax applies to
:meth:`str.format` and :func:`format`.

Q Format
===============================================================================

Using the ``format_spec`` ``type`` ``'q'`` allows you to format the
:attr:`.FixedPoint.qformat` output as a string.

..  doctest:: format "q"

    >>> a = FixedPoint(-12345.678)
    >>> f"{a:q}"
    'Q15.36'

    >>> f"{a: ^10q}"
    '  Q15.36  '

FixedPoint.bits
===============================================================================

Using the ``format_spec`` ``type`` ``'b'``, ``'o'``, ``'d'``,
``'x'``, or ``'X'`` allow you to format the :attr:`.FixedPoint.bits` as an
:class:`int`.

..  doctest:: format bits

    >>> a = FixedPoint(0b1111_0000_1011, m=14)
    >>> f"{a:#0{2 + len(a) // 4 + len(a)}_b}" # add 2 for radix, // 4 for seperators
    '0b00_1111_0000_1011'

    >>> f"{a:010,d}"
    '00,003,851'

    >>> f"{a:=^+#10X}"
    '==+0XF0B=='

Integer and Fractional Bits
===============================================================================

Using the ``format_spec`` ``type`` ``'m'`` or ``'n'`` allows you
to format the integer and fractional bits as an :class:`int`. Precede these
``type``\ s with other standard types like ``'b'``, ``'o'``, ``'d'``,
``'n'``, ``'x'``, or ``'X'``.

..  doctest:: format integer and fractional

    >>> a = FixedPoint('0b11001100', signed=0, m=4, n=5)
    >>> f"{a:#0{a.m+2}bm}.{a:0{a.n}bn}" # Show the binary point
    '0b0110.01100'

Float Equivalent
===============================================================================

Using the ``format_spec`` ``type`` ``'e'``, ``'E'``, ``'f'``,
``'F'``, ``'g'``, ``'G'``, or ``'%'`` allow you to format the
:class:`FixedPoint` as a :class:`float`.

..  doctest:: format float

    >>> a = FixedPoint(1.125, rounding='up')
    >>> f"{a:#0{2+a.m}bm}.{a:0{a.n}bn} ==> {a:.3f}"
    '0b1.001 ==> 1.125'

    >>> f"{a:.2f}" # Show 2 decimal points
    '1.12'

..  attention::

    Convergent rounding is used for rounding :class:`float`\ s in the example
    above, which is the default rounding method specified by `IEEE 754`_. This
    will be the case regardless of the :attr:`.FixedPoint.rounding` property
    specified.

..  doctest:: format float

    >>> f"{a:.3%}"
    '112.500%'

    >>> f"{a - 1:.2%}"
    '12.50%'

    >>> import sys
    >>> b = FixedPoint(2**sys.float_info.min_exp)
    >>> f"{b:+e}"
    '+4.450148e-308'
