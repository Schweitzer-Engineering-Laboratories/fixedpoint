###############################################################################
Fixed Point Basics
###############################################################################

A :class:`~fixedpoint.FixedPoint` object consists of:

* A distinct number of bits
* A distinct binary point position within those bits

  * to the left of the binary point are integer bits
  * to the right of the binary point are fractional bits

* Properties that govern interactions with other built-in and
  :class:`~fixedpoint.FixedPoint` objects

  * :attr:`~fixedpoint.FixedPoint.overflow`
  * :attr:`~fixedpoint.FixedPoint.rounding`
  * :attr:`~fixedpoint.FixedPoint.overflow_alert`
  * :attr:`~fixedpoint.FixedPoint.mismatch_alert`
  * :attr:`~fixedpoint.FixedPoint.implicit_cast_alert`

..  _Q_Format:

*******************************************************************************
Q Format
*******************************************************************************

..  warning::
    It is important to understand the Q format utilized by :mod:`fixedpoint`
    because there are various formats in use throughout the industry.

The :mod:`fixedpoint` module utilizes the "Q-format" notation specified by
ARM in :download:`DUI 0066G <_static/DUI0066G.pdf>` (see §4.7.9). That is:

* **Qm.n** represents a signed fixed point number with m integer bits and n
  fractional bits (that is, m + n total bits). The most significant bit has
  a negative weight.
* **UQm.n** represents an unsigned fixed point number with m integer bits and n
  fractional bits (that is, m + n total bits). The most significant bit has
  a positive weight.

..  note::

    DUI 0066G specifies the Q format as *Qn.m* with *n* being the integer bit
    width and *m* being the fractional bit width. However, the
    :mod:`fixedpoint` module reverses these symbols as indicated above.

Furthermore:

* Negative **m** or **n** is not allowed.
* Total word length (**m** + **n**) must be positive.
* Signed numbers must have **m** greater than 0, while unsigned numbers can
  have **m** equal to 0, as long as total word length is positive.
* **n** can be 0 as long as total word length is positive.

Any deviation from the above specifications constitutes an invalid Q format.

..  _range:

*******************************************************************************
Representable Range
*******************************************************************************

The :ref:`Q format <Q_Format>` specifies the range and resolution of values that
a fixed point number can represent.

..  table::
    :widths: auto

    +-----------+-----------------------------+----------------+
    | Q format  | Range                       | Resolution     |
    +===========+=============================+================+
    | **Qm.n**  | :math:`[-2^{m-1}, 2^{m-1})` |                |
    +-----------+-----------------------------+ :math:`2^{-n}` |
    | **UQm.n** | :math:`[0, 2^m)`            |                |
    +-----------+-----------------------------+----------------+
