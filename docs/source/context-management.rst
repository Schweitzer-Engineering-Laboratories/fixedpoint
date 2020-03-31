..  currentmodule:: fixedpoint

###############################################################################
Context Management
###############################################################################

The :class:`.FixedPoint` class offers richly-featured context management (see
:pep:`343`) that allows for some unique approaches to programatic arithmetic.
Three functions are utilized:

* :meth:`.FixedPoint.__call__`
* :meth:`.FixedPoint.__enter__`
* :meth:`.FixedPoint.__exit__`

:meth:`.FixedPoint.__call__` allows properties to be assigned in the
:pyref:`with statement <compound_stmts.html#with>` at the start of the context;
this is called context initialization.

:meth:`.FixedPoint.__enter__` save off the current state of the
:class:`.FixedPoint` and assigns the properties specified by
:meth:`~.FixedPoint.__call__` in the new context.

:meth:`.FixedPoint.__exit__` restores the original context unless the
``safe_retain`` keyword was specified in :meth:`~.FixedPoint.__call__`.

*******************************************************************************
Basic Usage
*******************************************************************************

Use the :pyref:`with statement <compound_stmts.html#with>` to generate a scope
in which changes to the original object can be undone:

..  doctest:: context manager - basic
    :skipif: should_skip("context manager - basic")

    >>> from fixedpoint import FixedPoint
    >>> x = FixedPoint(1/9, signed=1)
    >>> x.qformat
    'Q1.54'

    >>> with x: # save off the current state of x
    ...    x.signed = 0
    ...    x.m = 42
    ...    x.qformat # show the changes that were made within the context
    'UQ42.54'

    >>> x.qformat # outisde of the with context, original x is restored
    'Q1.54'

Any property or attribute of the original `FixedPoint` can be changed within
the context. All changes made to `FixedPoint` properties are restored at
context exit. These properties include:

* :attr:`~.FixedPoint.signed`
* :attr:`~.FixedPoint.m`
* :attr:`~.FixedPoint.n`
* :attr:`~.FixedPoint.overflow`
* :attr:`~.FixedPoint.rounding`
* :attr:`~.FixedPoint.overflow_alert`
* :attr:`~.FixedPoint.mismatch_alert`
* :attr:`~.FixedPoint.implicit_cast_alert`
* :attr:`~.FixedPoint.str_base`

Even the value can be changed with :doc:`arithmetic` or :ref:`initializers`.

..  doctest:: context manager - basic
    :skipif: should_skip("context manager - basic")

    >>> float(x)
    0.1111111111111111

    >>> with x:
    ...    x.from_string("0x7FFFFFAAAA5555")
    ...    float(x)
    -7.947407237862691e-08

    >>> float(x)
    0.1111111111111111

New `FixedPoint`\ s generated inside the context manager are valid and available
outside of the context. This is useful for temporarily overriding properties.
You can also rename a variable if desired.

..  testsetup:: context manager - basic
    :skipif: should_skip("context manager - basic")

    reset_sn()

..  doctest:: context manager - basic
    :skipif: should_skip("context manager - basic")

    >>> x = FixedPoint(0.2)
    >>> y = FixedPoint(0.7)
    >>> x.qformat, y.qformat
    ('UQ0.54', 'UQ0.52')

    >>> z = x - y
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN3] Unsigned subtraction causes overflow.

    >>> with x as xtmp, y as ytmp:
    ...    xtmp.m, ytmp.m = 1, 1
    ...    xtmp.signed, ytmp.signed = 1, 1
    ...    z = x - y
    ...    xtmp.qformat, ytmp.qformat, z.qformat
    ('Q1.54', 'Q1.52', 'Q2.54')

    >>> x.qformat, y.qformat, z.qformat, float(round(z, 1))
    ('UQ0.54', 'UQ0.52', 'Q2.54', -0.5)

Context managers can be nested:

..  doctest:: context manager - basic
    :skipif: should_skip("context manager - basic")

    >>> def nest(x):
    ...     print(f'0) {x.rounding=}')
    ...     with x as y:
    ...         print(f'1) {x.rounding=}')
    ...         x.rounding = 'in'
    ...         print(f'2) {x.rounding=}')
    ...         with y as z:
    ...             print(f'3) {x.rounding=}')
    ...             z.rounding = 'convergent'
    ...             print(f'4) {x.rounding=}')
    ...         print(f'5) {x.rounding=}')
    ...     print(f'6) {x.rounding=}')

    >>> nest(FixedPoint(31))
    0) x.rounding='nearest'
    1) x.rounding='nearest'
    2) x.rounding='in'
    3) x.rounding='in'
    4) x.rounding='convergent'
    5) x.rounding='in'
    6) x.rounding='nearest'

*******************************************************************************
Context Initialization
*******************************************************************************

In addition to saving off the current context of `FixedPoint` objects, the
:pyref:`with statement <compound_stmts.html#with>` can also initialize the new
context for you. Given ``x``, ``y``, and ``z`` below,

..  testsetup:: context manager - initialization
    :skipif: should_skip("context manager - initialization")

    reset_sn()

..  doctest:: context manager - initialization
    :skipif: should_skip("context manager - initialization")

    >>> x = FixedPoint(-1)
    >>> y = FixedPoint(1, mismatch_alert='error')
    >>> z = x + y
    Traceback (most recent call last):
        ...
    fixedpoint.MismatchError: [SN2] Non-matching mismatch_alert behaviors ['warning', 'error'].

the following two code blocks accomplish the same goal:

.. doctest:: context manager - initialization
    :skipif: should_skip("context manager - initialization")

    >>> with x, y:
    ...     x.rounding = 'nearest'
    ...     x.mismatch_alert = 'error'
    ...     z = x + y
    >>> float(z)
    0.0

.. doctest:: context manager - initialization
    :skipif: should_skip("context manager - initialization")

    >>> with x(rounding='nearest', mismatch_alert='error'):
    ...     z = x + y
    >>> float(z)
    0.0

Any keywordable argument from the :class:`FixedPoint` constructor can be used in
the context manager. All initilization arguments must be keyworded. The
:meth:`~.FixedPoint.__call__` keywords can be specified in a :class:`dict` if
preferred.

..  doctest:: context manager - initialization
    :skipif: should_skip("context manager - initialization")

    >>> xprop = {'rounding': 'nearest', 'mismatch_alert': 'warning'}
    >>> yprop = {'mismatch_alert': 'warning'}
    >>> with x(**xprop), y(**yprop):
    ...     z = x + y

    >>> x.rounding, x.mismatch_alert, y.rounding, y.mismatch_alert
    ('convergent', 'warning', 'nearest', 'error')

*******************************************************************************
Retaining the Context
*******************************************************************************

Context initialization also supports a ``safe_retain`` keyword that, when
``True``, will not restore the original :class:`FixedPoint` context as long as
no exceptions occur.

..  testsetup:: context manager - safe_retain
    :skipif: should_skip("context manager - safe_retain")

    reset_sn()

..  doctest:: context manager - safe_retain
    :skipif: should_skip("context manager - safe_retain")

    >>> x = FixedPoint(3, str_base=10)
    >>> x.qformat
    'UQ2.0'

    >>> with x(safe_retain=True):
    ...     x.signed = True
    Traceback (most recent call last):
        ...
    fixedpoint.FixedPointOverflowError: [SN1] Changing signedness on 3 causes overflow.

    >>> x.signed, x.qformat # Changes were not retained because of exception
    (False, 'UQ2.0')

    >>> with x(m=3, safe_retain=True):
    ...     x.signed = True

    >>> x.signed, x.qformat # Changes were retained
    (True, 'Q3.0')

This is useful when several properties/attributes might change, and if all
changes are made successfully, the properties should be retained. In fact,
this is exactly how :meth:`.FixedPoint.resize` is implemented:

..  _resize_implementation:

..  literalinclude:: fixedpoint
    :language: python
    :start-at: def resize
    :end-before: def

The magic here is that if ``self.m = m`` raises an exception, then the
assignment on the line just before it is undone by the context manager. However,
if no exception occurs, then the assignments to the ``m`` and  ``n`` attributes
are kept and the number is resized.
