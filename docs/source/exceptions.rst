..  currentmodule:: fixedpoint

###############################################################################
Exceptions
###############################################################################

..  exception:: FixedPointError

    Base class for other fixedpoint exceptions.

..  exception:: FixedPointOverflowError

    Signals that overflow has occurred. Raised only when
    :attr:`~.FixedPoint.overflow_alert` is ``'error'``.

    Inherits from `FixedPointError` and :exc:`OverflowError`.

..  exception:: MismatchError

    Signals that the properties of 2 :class:`FixedPoint`\ s do not
    match. Raised only when :attr:`~.FixedPoint.mismatch_alert` is
    ``'error'``.

    Inherits from `FixedPointError`.

..  exception:: ImplicitCastError

    Signals that an object required implicit casting to a
    :class:`FixedPoint`, and the cast was not exact. Raised only
    when :attr:`~.FixedPoint.implicit_cast_alert` is ``'error'``.

    Inherits from :exc:`FixedPointError` and :exc:`FloatingPointError`.
