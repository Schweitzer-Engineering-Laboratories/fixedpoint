The fixedpoint package offers several features that are widely used in
DSP applications:

* Generate fixed point numbers from
  :ref:`string literals <init_str>`,
  :ref:`integers <init_int>`, or
  :ref:`floating point numbers <init_float>`.
* Specify bit widths and signedness, or allow it to be deduced
* Various :ref:`rounding <rounding>` methods
* Various :ref:`overflow <overflow>` handling methods
* Configurable alerts for
  :ref:`overflow <overflow_alert>`,
  :ref:`property mismatches <mismatch_alert>`, and
  :ref:`implicit casting errors <implicit_cast_alert>`
* Arithmetic operations such as
  :ref:`addition <arithmetic_addition>`,
  :ref:`subtraction <arithmetic_subtraction>`,
  :ref:`multiplication <arithmetic_multiplication>`,
  :ref:`exponentiation <arithmetic_exponentiation>`
* Bitwise operations :ref:`AND, OR, XOR <and_or_xor>`, and
  :ref:`inversion <inversion>`.
* Type casting to :class:`int`, :class:`float`, :class:`bool`, :class:`str`
* Built-in string formatting
  (:pyref:`f-strings <lexical_analysis.html#f-strings>` or :meth:`str.format`)
* Comparisons with other :class:`~fixedpoint.FixedPoint`, :class:`int`, or
  :class:`float` objects

The fixedpoint package is unit-tested against MATLAB stimulus (with the fixed
point toolbox), making the :mod:`fixedpoint` package a viable, accurate, and
cost-free alternative to MATLAB.
