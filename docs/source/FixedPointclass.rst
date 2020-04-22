..  module:: fixedpoint

###############################################################################
The **FixedPoint** Class
###############################################################################

..  admonition:: Examples are just a click away
    :class: example

    Boxes like this link to example code.

..  rubric:: Jump to Section

* :ref:`Initialization Methods <FixedPoint_initialization>`
* :ref:`FixedPoint Properties <FixedPoint_properties_rw>`

  * :ref:`Read/Write Properties <FixedPoint_properties_rw>`
  * :ref:`Read Only Properties <FixedPoint_properties_r>`

* :ref:`Operators <FixedPoint_arithmeticoperators>`

  * :ref:`Binary Operators <FixedPoint_arithmeticoperators>`
  * :ref:`Comparison Operators <FixedPoint_comparisonoperators>`
  * :ref:`Bitwise Operators <FixedPoint_bitwiseoperators>`
  * :ref:`Unary Operators <FixedPoint_unaryoperators>`

* :ref:`Built-in Function Support <FixedPoint_builtinfunctions>`
* :ref:`Bit Resizing Methods <FixedPoint_bitresizing>`

  * :ref:`Rounding Methods <FixedPoint_roundingmethods>`
  * :ref:`Overflow Handling Methods <FixedPoint_overflowhandling>`

* :ref:`Context Management <FixedPoint_contextmanagement>`
* :ref:`Logging <FixedPoint_logging>`
* :ref:`Utility Functions <FixedPoint_utils>`
* :ref:`Property Resolution <property_resolution_order>`
* :ref:`Bit Random Access <FixedPoint_slicingandmapping>`

..  _FixedPoint_initialization:

..  class:: FixedPoint(init, \
        /, \
        signed=None, \
        m=None, \
        n=None, \
        *, \
        overflow='clamp', \
        rounding='auto', \
        overflow_alert='error', \
        implicit_cast_alert='warning', \
        mismatch_alert='warning', \
        str_base=16)

    :param init:
        Initial value. This argument is required and positional, meaning it
        cannot be keyworded and must come first in the list of arguments.

    :type init:
        float or int or str or FixedPoint

    :param bool signed:
        Signedness, part of the :ref:`Q format <Q_Format>` specification. When
        left unspecified, :meth:`sign` is used to deduce signedness. This
        argument can be keyworded.

    :param int m:
        Number of integer bits, part of the :ref:`Q format <Q_Format>`
        specification. When left unspecified, :meth:`min_m` is used to
        deduce initial integer bit width, after which :meth:`~.FixedPoint.trim`
        is used after rounding to minimize integer bits. This argument can be
        keyworded.

    :param int n:
        Number of fractional bits, part of the :ref:`Q format <Q_Format>`
        specification. When left unspecified, :meth:`min_n` is used to deduce
        fractional bit width. This argument can be keyworded.

    :keyword str overflow:
        Specifies what shall happen when the value :ref:`overflows <overflow>`
        its integer bit width. Valid options are:

            * ``'clamp'`` (default when left unspecified)
            * ``'wrap'``

    :keyword str rounding:
        Specifies how superfluous fractional bits are :ref:`rounded <rounding>`
        away. Valid options are:

            * ``'convergent'`` (default for signed when left unspecified)
            * ``'nearest'`` (default for unsigned when left unspecified)
            * ``'in'``
            * ``'out'``
            * ``'up'``
            * ``'down'``

    :keyword str overflow_alert:
        Specifies the :ref:`notification scheme when overflow occurs
        <overflow_alert>`. Valid options are:

            * ``'error'`` (default when left unspecified)
            * ``'warning'``
            * ``'ignore'``

    :keyword str mismatch_alert:
        Specifies the :ref:`notification scheme when 2 FixedPoints with
        non-matching properties undergo arithmetic <mismatch_alert>`. Valid
        options are:

            * ``'error'``
            * ``'warning'`` (default when left unspecified)
            * ``'ignore'``

    :keyword str implicit_cast_alert:
        Specifies the :ref:`notification scheme when implicit casting is
        performed <implicit_cast_alert>` and the resultant *FixedPoint* is not
        valued the same as the original number. Valid options are:

            * ``'error'``
            * ``'warning'`` (default when left unspecified)
            * ``'ignore'``

    :keyword int str_base:
        Casting a *FixedPoint* to a *str* generates a bit string in the
        base specified by *str_base*. Valid options are:

            * ``16`` (default when left unspecified)
            * ``10``
            * ``8``
            * ``2``

    :raises ValueError:
        * if *init* is a *str* and any of *signed*, *m*, or *n* are not
          specified.
        * if more than *m* + *n* bits are present in *init* (when *init* is a
          *str*).
        * if an :ref:`invalid Q format <Q_Format>` is specified.

    :raises TypeError:
        if *init* is not an *int*, *float*, *str*, or *FixedPoint* and
        cannot be cast to a *float*.

    :raises FixedPointOverflowError:
        if *overflow_alert* is ``'error'`` and *m* is too small to
        represent *init*.

    ..  admonition:: Jump to Examples
        :class: example

        * :ref:`init_float`
        * :ref:`init_int`
        * :ref:`init_str`
        * :ref:`init_fixedpoint`
        * :ref:`initialize_from_other_types`

    ..  method:: from_int(val)

        :param int val:
            Value to set the :class:`FixedPoint` to.

        Set the value of the :class:`FixedPoint` from an integer value. Affects
        only integer bits (since integer require no fractional bits). Must fit
        into the :ref:`Q format <Q_Format>` already designated by the object,
        otherwise :ref:`overflow` will occur.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`initializers`

    ..  method:: from_float(val)

        :param float val:
            Value to set the :class:`FixedPoint` to.

        Set the value of the :class:`FixedPoint`. Must fit into the
        :ref:`Q format <Q_Format>` already designated by the object, otherwise
        :ref:`rounding` and/or :ref:`overflow` will occur.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`initializers`

    ..  method:: from_string(val)
                 from_str(val)

        :param str val:
            Value to set the :class:`FixedPoint` bits to.

        Directly set the bits of the :class:`FixedPoint`, using the
        :ref:`Q format <Q_Format>` already designated by the object. May be
        a decimal, binary, octal, or hexadecimal string, the latter three of
        which require a ``'0b'``, ``'0o'``, or ``'0x'`` radix, respectively.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`initializers`

    ..  _FixedPoint_properties_rw:

    ..  rubric:: FixedPoint Properties

    ..  attribute:: signed

        :type:
            |bool|_

        :getter:
            *True* for signed, *False* for unsigned.

        :setter:
            Set signedness.

        :raises FixedPointOverflowError:
            Fixed point value changes from negative to positive or positive to
            negative (raised only when `overflow_alert` is ``'error'``).

        :raises FixedPointError:
            Changing to *True* with 0 integer bits.

        Change signedness of number. Note that if the MSb is 0, the value of the
        number will not change. Overflow occurs if the MSb is 1.

    ..  attribute:: m

        :type:
            |int|_

        :getter:
            Number of integer bits in the :class:`FixedPoint` number.

        :setter:
            Set the number of integer bits in the :class:`FixedPoint` number.

        :raises FixedPointOverflowError:
            New value for *m* is smaller than needed to represent the current
            :class:`FixedPoint` value (raised only when
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``).

        :raises ValueError:
            Invalid :ref:`Q format <Q_Format>`

        When the number of integer bits increases, sign extension occurs for
        signed numbers, and 0-padding occurs for unsigned numbers. When then
        number of integer bits decreases, overflow handling may occur (per the
        :attr:`~.FixedPoint.overflow` property) if the :class:`FixedPoint`
        value is too large for the new integer bit width.

    ..  attribute:: n

        :type:
            |int|_

        :getter:
            Number of fractional bits in the :class:`FixedPoint` number.

        :setter:
            Set the number of fractional bits in the :class:`FixedPoint` number.

        :raises FixedPointOverflowError:
            Number of fractional bits causes rounding (per the
            :attr:`~.FixedPoint.rounding` property) which induces overflow
            (raised only when :attr:`~.FixedPoint.overflow_alert` is
            ``'error'``).

        :raises ValueError:
            :ref:`Invalid Q format <Q_Format>`

        When the number of fractional bits increases, 0s are appended to the
        fixed point number. When the number of fractional bits decreases,
        rounding may occur (per the :attr:`~.FixedPoint.rounding` property),
        which in turn may cause overflow (per the :attr:`~.FixedPoint.overflow`
        property) if the integer portion of the rounded result is too large to
        fit within the current integer bit width.

    ..  attribute:: str_base

        :type:
            |int|_

        :getter:
            Base of the string generated by :class:`str`.

        :setter:
            Set the base of the string generated by :class:`str`.

        Using the builtin python :class:`str` function on a :class:`FixedPoint`
        casts the object to a string. The string is the bits of the
        :class:`FixedPoint` number in the base specified by
        :attr:`~.FixedPoint.str_base`, but without the radix. Must be one of:

        * 16
        * 10
        * 8
        * 2

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`str_base`

    ..  attribute:: overflow

        :type:
            |str|_

        :getter:
            The current :attr:`~.FixedPoint.overflow` scheme.

        :setter:
            Set the :attr:`~.FixedPoint.overflow` scheme.

        Overflow occurs when the number of bits required to represent
        a value exceeds the number of integer bits available
        (:attr:`~.FixedPoint.m`). The :attr:`~.FixedPoint.overflow` property of
        a :class:`FixedPoint` specifies how to handle overflow. Must be one of:

        * ``'clamp'``
        * ``'wrap'``

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`overflow`

    ..  attribute:: rounding

        :type:
            |str|_

        :getter:
            The current :attr:`~.FixedPoint.rounding` scheme.

        :setter:
            Set the :attr:`~.FixedPoint.rounding` scheme.

        Rounding occurs when fractional bits must be removed from the object.
        Some rounding schemes can cause overflow in certain circumstances. Must
        be one of:

        * ``'convergent'``
        * ``'nearest'``
        * ``'in'``
        * ``'out'``
        * ``'up'``
        * ``'down'``

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`rounding`

    ..  attribute:: overflow_alert

        :type:
            |str|_

        :getter:
            The current :attr:`~.FixedPoint.overflow_alert` scheme.

        :setter:
            Set the :attr:`~.FixedPoint.overflow_alert` scheme.

        When overflow occurs, the :attr:`~.FixedPoint.overflow_alert` property
        indicates how you are notified. Must be one of:

        * ``'error'``
        * ``'warning'``
        * ``'ignore'``

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`overflow_alert`

    ..  attribute:: mismatch_alert

        :type:
            |str|_

        :getter:
            The current :attr:`~.FixedPoint.mismatch_alert` scheme.

        :setter:
            Set the :attr:`~.FixedPoint.mismatch_alert` scheme.

        When 2 :class:`FixedPoint`\ s interact to create another
        :class:`FixedPoint`, the properties assigned to the new object must be
        resolved from the 2 original objects. Whenever properties between these
        2 objects do not match, the :attr:`~.FixedPoint.mismatch_alert` property
        indicates how you are notified. Must be one of:

        * ``'warning'``
        * ``'error'``
        * ``'ignore'``

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`mismatch_alert`

    ..  attribute:: implicit_cast_alert

        :type:
            |str|_

        :getter:
            The current :attr:`~.FixedPoint.implicit_cast_alert` scheme.

        :setter:
            Set the :attr:`~.FixedPoint.implicit_cast_alert` scheme.

        Some operations allow a :class:`FixedPoint` to interact with another
        object that is not a :class:`FixedPoint`. Typically, the other object
        will need to be cast to a :class:`FixedPoint`, and is done so
        internally in the class method. If error exists after the cast to
        :class:`FixedPoint`, the :attr:`~.FixedPoint.implicit_cast_alert`
        property indicates how you are notified. Must be one of:

        * ``'warning'``
        * ``'error'``
        * ``'ignore'``

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`implicit_cast_alert`

    ..  |FixedPointBitsType| replace:: *FixedPointBits*
    ..  _FixedPointBitsType: :ref:`FixedPointBits <FixedPoint_slicingandmapping>`

    ..  _FixedPoint_properties_r:

    ..  attribute:: bits

        :type:
            |FixedPointBitsType|_

        :getter:
            Bits of the fixed point number.

        This is the read-only bits of the :class:`FixedPoint`, stored as an
        integer.

        Indexing, slicing, and mapping is available with the
        :class:`FixedPointBits` class.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`single_bit_slice`
            * :ref:`multi_bit_slice`
            * :ref:`bit_mapping`

    ..  attribute:: bitmask

        :type:
            |int|_

        :getter:
            Bitmask of the :class:`FixedPoint` number.

        Integer bitmask, equivalent to :math:`2^{m + n} - 1`.

    ..  attribute:: clamped

        :type:
            |bool|_

        :getter:
            *True* if the value of the :class:`FixedPoint` number is
            equal to it minimum or maximum value. *False* otherwise.

    ..  attribute:: qformat

        :type:
            |str|_

        :getter:
            :ref:`Q format <Q_Format>` of the :class:`FixedPoint` number.

        The string takes the form **UQm.n**, where:

        * **U** is only present for unsigned numbers
        * **m** is the number of integer bits
        * **n** is the number of fractional bits

    ..  _FixedPoint_arithmeticoperators:

    ..  rubric:: Arithmetic Operators

    ..  method:: __add__(augend)
                 __iadd__(augned)
                 __radd__(addend)

        ..  note::

            These are the ``+`` and ``+=`` operators.

        :param addend:
            addition term

        :type addend:
            FixedPoint or int or float

        :param augend:
            addition term

        :type augend:
            FixedPoint or int or float

        :return:
            *Sum* of *addend* and *augend*

        :rtype:
            FixedPoint

        :raises ImplicitCastError:
            if the *addend* or *augend* argument cannot be cast to a
            :class:`FixedPoint` without error.

        :raises MismatchError:
            if any *addend* or *augend* properties do not match, and either
            of their :attr:`~.FixedPoint.mismatch_alert` properties is
            ``'error'``.

        ..  note::

            :math:`\it{sum} = \it{addend} + \it{augend}`

        Addition using the ``+`` and ``+=`` operators are
        :ref:`full precision <arithmetic_addition>`; bit growth will occur:

        If both *augend* or *addend* are unsigned, the result is unsigned,
        otherwise the result will be signed.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`arithmetic_addition`

    ..  method:: __sub__(subtrahend)
                 __isub__(subtrahend)
                 __rsub__(minuend)

        ..  note::

            These are the ``-`` and ``-=`` operators.

        :param minuend:
            subtraction term

        :type minuend:
            FixedPoint or int or float

        :param subtrahend:
            subtraction term

        :type subtrahend:
            FixedPoint or int or float

        :return:
            *Difference* of *minuend* and *subtrahend*

        :rtype:
            FixedPoint

        :raises ImplicitCastError:
            if the *minuend* or *subtrahend* argument cannot be cast to a
            :class:`FixedPoint` without error.

        :raises FixedPointOverflowError:
            *Subtrahend* > *minuend* and both terms are unsigned.

        :raises MismatchError:
            if any *minuend* or *subtrahend* properties do not match, and either
            of their :attr:`~.FixedPoint.mismatch_alert` properties is
            ``'error'``.

        ..  note::

            :math:`\it{difference} = \it{minuend} - \it{subtrahend}`

        Subtraction using the ``-`` and ``-=`` operators are
        :ref:`full precision <arithmetic_subtraction>`; bit growth will occur.

        If both *minuend* or *subtrahend* are unsigned, the result is unsigned,
        otherwise the result will be signed.

        Overflow can occur for unsigned subtraction.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`arithmetic_subtraction`

    ..  method:: __mul__(multiplier)
                 __imul__(multiplier)
                 __rmul__(multiplicand)

        ..  note::

            These are the ``*`` and ``*=`` operators.

        :param multiplier:
            multiplication term

        :type multiplier:
            FixedPoint or int or float

        :param multiplicand:
            multiplication term

        :type multiplicand:
            FixedPoint or int or float

        :return:
            *Product* of *multiplicand* and *multiplier*

        :rtype:
            FixedPoint

        :raises ImplicitCastError:
            if the *addend* or *augend* argument cannot be cast to a
            :class:`FixedPoint` without error.

        :raises MismatchError:
            if any *multiplicand* or *multiplier* properties do not match, and
            either of their :attr:`~.FixedPoint.mismatch_alert` properties is
            ``'error'``.

        ..  note::

            :math:`\it{product} = \it{multiplicand} \times \it{multiplier}`

        Multiplication using the ``*`` and ``*=`` operators are
        :ref:`full precision <arithmetic_multiplication>`; bit growth will
        occur.

        If both *multiplicand* or *multiplier* are unsigned, the result is
        unsigned, otherwise the result will be signed.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`arithmetic_multiplication`

    ..  method:: __pow__(exponent)
                 __ipow__(exponent)

        ..  note::

            These are the ``**`` and ``**=`` operators.

        :param int exponent:
            The exponent to the :class:`FixedPoint` base. Must be positive.

        :return:
            *Result* of the *base* raised to the *exponent* power.

        :rtype:
            FixedPoint

        ..  note::

            :math:`\it{result} = \it{base}^{\it{exponent}}`

        Exponentiation using the ``**`` and ``**=`` operators are
        :ref:`full precision <arithmetic_exponentiation>`; bit growth will
        occur.

        The *result* has the same signedness as the *base*.

        Only positive integers are supported as the *exponent*.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`arithmetic_exponentiation`

    ..  _FixedPoint_comparisonoperators:

    ..  rubric:: Comparison Operators

    ..  method:: __lt__(other)
                 __le__(other)
                 __gt__(other)
                 __ge__(other)
                 __eq__(other)
                 __ne__(other)

        ..  note::

            These are the ``<``, ``<=``, ``>``, ``>=``, ``==`` and ``!=``
            operators.

        :param other:
            Numeric object to compare to

        :type other:
            FixedPoint or int or float

        :returns:
            *True* if the comparison is true, *False* otherwise

        :rtype:
            bool

    ..  method:: __cmp__(other)

        :param other:
            Numeric object to compare to

        :type other:
            FixedPoint or int or float

        :returns:
            * a negative number if the object is < *other*
            * 0 if the object == *other*
            * a positive number if the object is > *other*

        :rtype:
            int

        Generic comparison object. Not used for comparisons in python 3 but
        used internally by all other comparisons.

    ..  _FixedPoint_bitwiseoperators:

    ..  rubric:: Bitwise Operators

    ..  method:: __lshift__(nbits)
                 __ilshift__(nbits)

        ..  note::

            These are the ``<<`` and ``<<=`` operators.

        :param int nbits:
            Number of bits to shift left.

        :rtype:
            FixedPoint

        Bit shifting does not change the :class:`FixedPoint`\ 's
        :ref:`Q format <Q_Format>`. The *nbits* leftmost bits are discarded.

        To keep bits after shifting, multiply the object by :math:`2^{nbits}`
        instead of using the ``<<`` or ``<<=`` operator.

        If *nbits* < 0, bits are shifted right using ``>>`` or ``>>=`` by
        ``abs(nbits)`` instead.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`left_shift`

    ..  method:: __rshift__(nbits)
                 __irshift__(nbits)

        ..  note::

            These are the ``>>`` and ``>>=`` operators.

        :param int nbits:
            Number of bits to shift right.

        :return:
            Original :class:`FixedPoint` with bits shifted right.

        :rtype:
            FixedPoint

        Bit shifting does not change the :class:`FixedPoint`\ 's
        :ref:`Q format <Q_Format>`. The *nbits* rightmost bits are discarded.

        To keep bits after shifting, multiply the object by :math:`2^{-nbits}`
        instead of using the ``>>`` or ``>>=`` operator.

        For signed numbers, sign extension occurs.

        If *nbits* < 0, bits are shifted right using ``<<`` or ``<<=`` by
        ``abs(nbits)`` instead.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`right_shift`

    ..  method:: __and__(other)
                 __iand__(other)
                 __rand__(other)

        ..  note::

            These are the ``&`` and ``&=`` operators.

        :param other:
            Object to bitwise AND with

        :type other:
            int or FixedPoint

        :return:
            Original object's bits bitwise ANDed with *other*'s bits.

        :rtype:
            FixedPoint

        When ANDing 2 :class:`FixedPoint`\ s, the binary point is not aligned.

        After ANDing, the result is masked with the leftmost
        :attr:`.FixedPoint.bitmask` and assigned to the :attr:`~.FixedPoint.bits`
        of the return value.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Bitwise ANDing <and_or_xor>`

    ..  method:: __or__(other)
                 __ior__(other)
                 __ror__(other)

        ..  note::

            These are the ``|`` and ``|=`` operators.

        :param other:
            Object to bitwise OR with

        :type other:
            int or FixedPoint

        :return:
            Original object's bits bitwise ORed with *other*'s bits.

        :rtype:
            FixedPoint

        When ORing 2 :class:`FixedPoint`\ s, the binary point is not aligned.

        After ORing, the result is masked with the leftmost
        :attr:`.FixedPoint.bitmask` and assigned to the :attr:`~.FixedPoint.bits`
        of the return value.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Bitwise ORing <and_or_xor>`

    ..  method:: __xor__(other)
                 __ixor__(other)
                 __rxor__(other)

        ..  note::

            These are the ``^`` and ``^=`` operators.

        :param other:
            Object to bitwise XOR with

        :type other:
            int or FixedPoint

        :return:
            Original object's bits bitwise XORed with *other*'s bits.

        :rtype:
            FixedPoint

        When XORing 2 :class:`FixedPoint`\ s, the binary point is not aligned.

        After XORing, the result is masked with the leftmost
        :attr:`.FixedPoint.bitmask` and assigned to the :attr:`~.FixedPoint.bits`
        of the return value.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Bitwise XORing <and_or_xor>`

    ..  _FixedPoint_unaryoperators:

    ..  rubric:: Unary Operators

    ..  method:: __invert__()

        ..  note::

            This is the unary ``~`` operator.

        :return:
            Copy of original object with bits inverted.

        :rtype:
            FixedPoint

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Bitwise Inversion <inversion>`

    ..  method:: __pos__()

        ..  note::

            This is the unary ``+`` operator.

        :return:
            Copy of original object.

        :rtype:
            FixedPoint

    ..  method:: __neg__()

        ..  note::

            This is the unary ``-`` operator.

        :return:
            Negated copy of original object negated.

        :rtype:
            FixedPoint

        :raises FixedPointError:
            if unsigned number is negated.

        :raises FixedPointOverflowError:
            if the negative value is larger than the :ref:`Q format <Q_Format>`
            allows (raised only if :attr:`~.FixedPoint.overflow_alert` is
            ``'error'``).

        In an attempt to minimize user error, unsigned numbers cannot be
        negated. The idea is that you should be doing this very intentionally.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Negation <negation_abs>`

    ..  _FixedPoint_builtinfunctions:

    ..  rubric:: Built-in Function Support

    ..  method:: __abs__()

        ..  note::

            This is the built-in :func:`abs` function.

        :return:
            Absolute value.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if the absolute value of a negative-valued number is larger than the
            :ref:`Q format <Q_Format>` allows (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``).

        Signedness does not change.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Absolute Value <negation_abs>`

    ..  method:: __int__()

        ..  note::

            This is the built-in :class:`int` function.

        :return:
            Only the integer bits of the :class:`FixedPoint` number.

        :rtype:
            int

        Fractional bits are ignored, which is the same as rounding down.

    ..  method:: __float__()

        ..  note::

            This is the built-in :class:`float` function.

        :return:
            Floating point cast of the :class:`FixedPoint` number.

        :rtype:
            float

        When casting to a *float* would result in an :exc:`OverflowError`,
        ``float('inf')`` or ``float('-inf')`` is returned instead.

        ..  warning::

            A typical Python :class:`float` follows `IEEE 754`_ double-precision
            format, which means there's 52 mantissa bits and a sign bit (you
            can verify this by examining `sys.float_info`). Thus for
            :class:`FixedPoint` word lengths beyond 52 bits, the :class:`float`
            cast may lose precision or resolution.

    ..  method:: __bool__()

        ..  note::

            This is the built-in :class:`bool` function.

        :return:
            *False* if :attr:`.FixedPoint.bits` are non-zero,
            *True* otherwise.

        :rtype:
            bool

    ..  method:: __index__()

        ..  note::

            This is the built-in :func:`hex`, :func:`oct`, and :func:`bin`
            functions.

        :return:
            Bits of the :class:`FixedPoint` number.

        :rtype:
            int

        Calling :func:`hex`, :func:`oct`, or :func:`bin` on a
        :class:`FixedPoint` generates a :class:`str` with the
        :attr:`.FixedPoint.bits` represented as a hexadecimal, octal, or binary
        string. The radix prepends the :attr:`~.FixedPoint.bits`, which do not
        contain any left-padded zeros.

    ..  method:: __str__()

        ..  note::

            This is the built-in :class:`str` function.

        :return:
            Bits of the :class:`FixedPoint` number, left padded to the number of
            bits in the number, in the base specified by the
            :attr:`~.FixedPoint.str_base` property.

        :rtype:
            str

        Calling ``str()`` will generate a hexadecimal, octal, or binary string
        (according to the :attr:`~.FixedPoint.str_base` property setting)
        without the radix, and 0-padded to the actual bit width of the
        :class:`FixedPoint` number. Decimal strings are not 0-padded.

        This string represents the bits of the number, thus will always be
        non-negative.

        Signedness does not change.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`str_conversion`

    ..  method:: __format__()

        ..  note::

            This is the built-in :meth:`str.format` and :func:`format` function,
            and also applies to
            :pyref:`f-strings <lexical_analysis.html#f-strings>`.

        :return:
            Formatted string, various formats available.

        :rtype:
            str

        ..  STRING FORMATTING INCLUDE START

        A :class:`FixedPoint` can be formatted as a :class:`str`,
        :class:`float`, or :class:`int` would, depending on the
        :pylib:`format string syntax <string.html#format-string-syntax>`.

        ..  table:: Standard Format Specifier Parsing Summary

            +-------------------+----------------+-------------------------------------+
            | | ``format_spec`` | Formatted Type | | Formatted Value                   |
            | | ``type``        |                | | (given ``x = FixedPoint(...)``\ ) |
            +===================+================+=====================================+
            | ``'s'``           | :class:`str`   | | ``str(x)``                        |
            |                   |                | | (depends on ``x.str_base``)       |
            +-------------------+                +-------------------------------------+
            | ``'q'``           |                | ``x.qformat``                       |
            +-------------------+----------------+-------------------------------------+
            | | ``'b'``         | :class:`int`   | ``x.bits``                          |
            | | (binary)        |                |                                     |
            +-------------------+                |                                     |
            | | ``'d'``         |                |                                     |
            | | (decimal)       |                |                                     |
            +-------------------+                |                                     |
            | | ``'o'``         |                |                                     |
            | | (octal)         |                |                                     |
            +-------------------+                |                                     |
            | | ``'x'``         |                |                                     |
            | | (lowercase      |                |                                     |
            | | hexadecimal)    |                |                                     |
            +-------------------+                |                                     |
            | | ``'X'``         |                |                                     |
            | | (uppercase      |                |                                     |
            | | hexadecimal)    |                |                                     |
            +-------------------+                +-------------------------------------+
            | ``'...m'``        |                | | ``x.bits['int']``                 |
            | :sup:`1`          |                | | (integer bits only)               |
            +-------------------+                +-------------------------------------+
            | ``'...n'``        |                | | ``x.bits['frac']``                |
            | :sup:`1`          |                | | (fractional bits only)            |
            +-------------------+----------------+-------------------------------------+
            | ``'e'``           | :class:`float` | ``float(x)``                        |
            +-------------------+                |                                     |
            | ``'E'``           |                |                                     |
            +-------------------+                |                                     |
            | ``'f'``           |                |                                     |
            +-------------------+                |                                     |
            | ``'F'``           |                |                                     |
            +-------------------+                |                                     |
            | ``'g'``           |                |                                     |
            +-------------------+                |                                     |
            | ``'G'``           |                |                                     |
            +-------------------+                |                                     |
            | ``'%'``           |                |                                     |
            +-------------------+----------------+-------------------------------------+

        :sup:`1` Append to the specifier of another formatted  :class:`int`.
        E.g., ``'bn'`` would format the fractional bits of ``x`` in binary.

        ..  STRING FORMATTING INCLUDE END

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`string_formatting`

    ..  method:: __len__()

        ..  note::

            This is the built-in :func:`len` function..

        :return:
            Number of bits in the :class:`FixedPoint`.

        :rtype:
            int

    ..  method:: __repr__()

        ..  note::

            This is the built-in :func:`repr` function, which is also the output
            shown when a :class:`FixedPoint` is not assigned to a
            variable.

        :return:
            Python executable code; a :class:`str` representation of the object.

        :rtype:
            str

        This generates a code string that will exactly reproduce the
        :class:`FixedPoint`\ 's value and properties.

    ..  _FixedPoint_bitresizing:

    ..  rubric:: Bit Resizing Methods

    ..  method:: resize(m, n, /, rounding=None, overflow=None, alert=None)

        :param int m:
            Number of integer bits to resize to.

        :param int n:
            Number of fractional bits to resize to

        :param str rounding:
            Temporary :attr:`~.FixedPoint.rounding` scheme to use. Can be
            keyworded.

        :param str overflow:
            Temporary :attr:`~.FixedPoint.overflow` scheme to use. Can be
            keyworded.

        :param str alert:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to use. Can be
            keyworded.

        :raises FixedPointOverflowError:
            if resizing causes overflow (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not specified -
            is ``'error'``).

        Fractional bits are resized first, them integer bits. Bit sizes can grow
        or shrink from their current value.

        Rounding, overflow handling, and overflow alert notification severity
        can be temporarily modified within the scope of this method. I.e.,
        specifying the *rounding*, *overflow*, or *alert* arguments will only
        take effect within this method; it will not permanently change the
        property settings of the object. If left unspecified, the current
        property setting is used.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Resize <resize>`
            * :ref:`Resize uses the context manager <resize_implementation>`

    ..  method:: trim(ints=None, fracs=None)

        :param bool ints:
            Set to *True* to trim off superfluous integer bits

        :param bool fracs:
            Set to *True* to trim off superfluous fractional bits

        Trims off excess bits, including:

        * up to :attr:`~.FixedPoint.n` trailing 0s
        * for unsigned numbers:

          * up to :attr:`~.FixedPoint.m` leading 0s

        * for signed numbers:

          * up to :attr:`~.FixedPoint.m` - 1 leading 0s for positive numbers,
            leaving one leading 0 in front of the first 1 encountered
          * up to :attr:`~.FixedPoint.m` - 1 leading 1s, for negative numbers,
            leaving one leading 1 in front of the first 0 encountered

        Resultant :ref:`Q format <Q_Format>` is always valid. For the
        :class:`FixedPoint` value of 0, resulting Q format is *[U]Q1.0*.

        Opt to trim off only fractional bits or only integer bits by setting
        *fracs* or *ints*, respectively, to *True*. When left unspecified,
        both integer and fractional bits are trimmed.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Trim <trim>`

    ..  _FixedPoint_roundingmethods:

    ..  rubric:: Rounding Methods

    ..  method:: __round__(n)

        ..  note::

            This is the built-in :func:`round` function.

        :param int n:
            Number of bits remaining after round

        :return:
            A copy of the :class:`FixedPoint` rounded to *n* bits.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if the
            :attr:`~.FixedPoint.overflow_alert` property setting is
            ``'error'``).

        Rounds a copy of the :class:`FixedPoint` using the rounding scheme
        specified by the :attr:`~.FixedPoint.rounding` property setting.

        Refer to :meth:`.FixedPoint.resize` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Default Rounding <default_rounding>`

    ..  method:: __floor__()

        ..  note::

            This is the built-in :func:`math.floor` function. It does not
            modify the object given to it, but creates a copy and operates on
            it instead.

        :rtype:
            FixedPoint

        Rounds to the integer closest to :math:`-\infty`, but does not modify
        the fractional bit width.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`math.floor <floor>`

    ..  method:: __ceil__()

        ..  note::

            This is the built-in :func:`math.ceil` function. It does not
            modify the object given to it, but creates a copy and operates on
            it instead.

        :rtype:
            FixedPoint

        :raisesFixedPointOverflowError:
            if the integer value of the :class:`FixedPoint` is already at its
            maximum possible value (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Rounds to the integer closest to :math:`+\infty`, leaving 0 fractional
        bits. For values other than 0, this requires :attr:`~.FixedPoint.m` to
        be non-zero.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`math.ceil <ceil>`

    ..  method:: __trunc__()

        ..  note::

            This is the built-in :func:`math.trunc` function. It does not
            modify the object given to it, but creates a copy and operates on
            it instead.

        :rtype:
            FixedPoint

        Rounds to the integer closest to :math:`-\infty`, leaving 0
        fractional bits. If :attr:`~.FixedPoint.m` is 0, it is changed to 1,
        otherwise :attr:`~.FixedPoint.m` is not modified.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`math.trunc <trunc>`

    ..  method:: round(n)

        :param int n:
            Number of fractional bits remaining after rounding

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Rounds the :class:`FixedPoint` using the rounding scheme specified by
        the :attr:`~.FixedPoint.rounding` property setting.

    ..  method:: convergent(n)
                 round_convergent(n)

        :param int n:
            Number of fractional bits remaining after rounding

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Rounds to *n* fractional bits, biased toward the nearest value with
        ties rounding to the nearest even value.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <convergent>`
            * :ref:`rounding_induced_overflow`

    ..  method:: round_nearest(n)

        :param int n:
            Number of fractional bits remaining after rounding

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Rounds the :class:`FixedPoint` to *n* fractional bits, biased toward the
        nearest value with ties rounding to :math:`+\infty`.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <nearest>`
            * :ref:`rounding_induced_overflow`

    ..  method:: round_in(n)

        :param int n:
            Number of fractional bits remaining after rounding

        Rounds the :class:`FixedPoint` to *n* fractional bits toward 0.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <in>`
            * :ref:`overflow_safe_rounding`

    ..  method:: round_out(n)

        :param int n:
            Number of fractional bits remaining after rounding

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Rounds the :class:`FixedPoint` to *n* fractional bits, biased toward the
        nearest value with ties rounding away from 0.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <out>`
            * :ref:`rounding_induced_overflow`

    ..  method:: round_down(n)

        :param int n:
            Number of fractional bits remaining after rounding

        Rounds the :class:`FixedPoint` to *n* fractional bits toward
        :math:`-\infty`.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <down>`
            * :ref:`overflow_safe_rounding`

    ..  method:: round_up(n)

        :param int n:
            Number of fractional bits remaining after rounding

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Rounds the :class:`FixedPoint` to *n* fractional bits toward
        :math:`+\infty`.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <up>`
            * :ref:`rounding_induced_overflow`

    ..  method:: keep_msbs(m, n, /, rounding=None, overflow=None, alert=None)

        :param int m:
            Number of integer bits in the result

        :param int n:
            Number of fractional bits in the result

        :param str rounding:
            Temporary :attr:`~.FixedPoint.rounding` scheme to use. Can be
            keyworded.

        :param str overflow:
            Temporary :attr:`~.FixedPoint.overflow` scheme to use. Can be
            keyworded.

        :param str alert:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to use. Can be
            keyworded.

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not specified -
            is ``'error'``)

        Rounds away LSb(s), leaving *m* + *n* bit(s), using the *rounding*
        scheme specified, then interprets the result with *m* integer bits
        and *n* fractional bits.

        The rounding, overflow handling, and overflow alert notification schemes
        can be temporarily modified within the scope of this method. I.e.,
        specifying the *rounding*, *overflow*, or *alert* arguments will only
        take effect within this method; it will not permanently change the
        property settings of the object. The current property setting for any
        of these unspecified arguments is used.

        While other rounding functions cannot round beyond the fractional bits
        in a :class:`FixedPoint`, :meth:`~.FixedPoint.keep_msbs` will keep an
        arbitrary number of the :class:`FixedPoint`\ 's most significant bits,
        regardless of its current :ref:`Q format <Q_Format>`. The resulting
        :ref:`Q format <Q_Format>` must be valid.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`keep_msbs`

    ..  _FixedPoint_overflowhandling:

    ..  rubric:: Overflow Handling

    ..  method:: clamp(m, /, alert=None)

        :param int m:
            Number of integer bits remaining after clamping

        :param str alart:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to use. Can be
            keyworded.

        :raises FixedPointOverflowError:
            if new integer bit width is too small to represent the
            :class:`FixedPoint` object value (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not specified -
            is ``'error'``)

        Reduces the number of integer bits in the :class:`FixedPoint` to *m*,
        clamping to the minimum or maximum value on overflow.

        The overflow alert notification scheme can be temporarily modified
        within the scope of the method by using the *alert* argument. When
        left unspecified, the :attr:`~.FixedPoint.overflow_alert` property
        setting is used.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <clamp>`

    ..  method:: wrap(m, /, alert=None)

        :param int m:
            Number of integer bits remaining after wrapping

        :param str alart:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to use. Can be
            keyworded.

        :raises FixedPointOverflowError:
            if new integer bit width is too small to represent the
            :class:`FixedPoint` object value (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not specified -
            is ``'error'``)

        Reduces the number of integer bits in the :class:`FixedPoint` to *m*,
        masking away the removed integer bits.

        The overflow alert notification scheme can be temporarily modified
        within the scope of the method by using the *alert* argument. When
        left unspecified, the :attr:`~.FixedPoint.overflow_alert` property
        setting is used.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <wrap>`

    ..  method:: keep_lsbs(m, n, /, overflow=None, alert=None)

        :param int m:
            Number of integer bits in the result

        :param int n:
            Number of fractional bits in the result

        :param str overflow:
            Temporary :attr:`~.FixedPoint.overflow` scheme to use. Can be
            keyworded.

        :param str alert:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to use. Can be
            keyworded.

        :raises FixedPointOverflowError:
            if new *m* + *n* bits is too small to represent the
            :class:`FixedPoint` value (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not specified -
            is ``'error'``)

        Removes MSb(s), leaving *m* + *n* bit(s), using the *overflow*
        scheme specified, then interprets the result with *m* integer bits
        and *n* fractional bits.

        The overflow handling and overflow alert notification schemes can be
        temporarily modified within the scope of this method. I.e., specifying
        the *overflow* or *alert* arguments will only take effect within this
        method; it will not permanently change the property settings of the
        object. The current property setting for any of these unspecified
        arguments is used.

        While other overflow handling functions cannot remove MSbs beyond their
        integer bits in a :class:`FixedPoint`, :meth:`~.FixedPoint.keep_lsbs`
        will keep an arbitrary number of the :class:`FixedPoint`\ 's least
        significant bits, regardless of  its current :ref:`Q format <Q_Format>`.
        The resulting :ref:`Q format <Q_Format>` must be valid.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`keep_lsbs`

    ..  _FixedPoint_contextmanagement:

    ..  rubric:: Context Management

    ..  method:: __enter__()
                 __exit__(exc_type, *args)
                 __call__(*, safe_retain=False, **props)

        .. note::

            This is the built-in :pyref:`with statement <compound_stmts.html#with>`
            in conjunction with the ``()`` operator.

        :keyword bool safe_retain:
            Set to *True* to retain the changes made within the context as
            long as no exceptions were raised. Set to *False* (or leave
            unspecified) if the the changes made within the context are to be
            undone when the context exits.

        :keyword props:
            Any keyword-able argument from the :class:`FixedPoint` constructor,
            including:

            * signed (*bool*)
            * m (*int*)
            * n (*int*)
            * overflow (*str*)
            * rounding (*str*)
            * overflow_alert (*str*)
            * mismatch_alert (*str*)
            * implicit_cast_alert (*str*)
            * str_base (*int*)

        :raises AttributeError:
            if invalid keyword is specified

        :raises PermissionError:
            if a private or read-only :class:`FixedPoint` property/attribute is
            specified

        While the ``__call__`` method is not typically associated with the
        context manager, the :class:`FixedPoint` class uses this method to
        assign attributes temporarily (or permanently, with appropriate use of
        the *safe_retain* keyword) to the :class:`FixedPoint` called, within the
        context of the :pyref:`with statement <compound_stmts.html#with>`.

        Using the ``__call__`` method is optional when *safe_retain* does not
        need to be *True*.

        ..  admonition:: Jump to Examples
            :class: example

            * :doc:`context-management`

    ..  _FixedPoint_logging:

    ..  staticmethod:: enable_logging()

        Enables logging to *fixedpoint.log*, located in the root directory of
        the :mod:`fixedpoint` module.

        On initial import, logging is disabled.

        Any time this method is called, *fixedpoint.log* is erased.

    ..  staticmethod:: disable_logging()

        Disables logging to *fixedpoint.log*.

    ..  _FixedPoint_utils:

    ..  classmethod:: sign(val)

        :param val:
            Value from which to discern the sign.

        :type val:
            FixedPoint or int or float

        :return:
            * -1 if *val* < 0
            * +1 if *val* > 0
            * 0 if *val* == 0

        :rtype:
            int

        Determine the sign of a number.

    ..  classmethod:: min_m(val, /, signed=None)

        :param val:
            Value to analyze

        :type val:
            int or float

        :param bool signed:
            *True* if signed, *False* if unsigned

        :return:
            Minimum value for :attr:`.FixedPoint.m` for which *val* can be
            represented without overflow.

        :rtype:
            int

        Calculate the minimum value for :attr:`.FixedPoint.m` for which *va*
        can be represented without overflow. If *signed* is not specified, it is
        deduced from the value of *val*. When *val* < 0, *signed* is ignored.

        Worst case rounding is assumed (e.g., ``min_m(3.25)`` returns 3, in case
        3.25 needs to be rounded up to 4).

    ..  classmethod:: min_n(val)

        :param val:
            Value to analyze

        :type val:
            float

        :return:
            Minimum value for :attr:`.FixedPoint.n` for which *val* can be
            represented exactly.

        :rtype:
            int

        ..  Implemented as a recursive binary search,
            which is super fast and cool!
            But you don't get to know that :/
