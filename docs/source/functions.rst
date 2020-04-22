..  currentmodule:: fixedpoint

###############################################################################
Functions
###############################################################################

The :mod:`fixedpoint` module functions provide the same functionality as the
:class:`FixedPoint` methods of the same name, but make a copy of the
:class:`FixedPoint` object and operate on it, instead of modifying the object
itself.

..  admonition:: Examples are just a click away
    :class: example

    Boxes like this link to example code.

..  function:: resize(fp, m, n, /, rounding=None, overflow=None, alert=None)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int m:
            Number of integer bits to resize to.

        :param int n:
            Number of fractional bits to resize to

        :param str rounding:
            Temporary :attr:`~.FixedPoint.rounding` scheme to use.
            Can be keyworded.

        :param str overflow:
            Temporary :attr:`~.FixedPoint.overflow` scheme to use.
            Can be keyworded.

        :param str alert:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to
            use. Can be keyworded.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if resizing causes overflow (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not
            specified - is ``'error'``).

        Refer to :meth:`.FixedPoint.resize` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Resize <resize>`

..  function:: trim(fp, /, ints=None, fracs=None)

        :param FixedPoint fp:
            Object to copy and operate on

        :param bool ints:
            Set to *True* to trim off superfluous integer bits

        :param bool fracs:
            Set to *True* to trim off superfluous fractional bits

        :rtype:
            FixedPoint

        Refer to :meth:`.FixedPoint.trim` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Trim <trim>`

..  function:: convergent(fp, n, /)
               round_convergent(fp, n, /)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int n:
            Number of fractional bits remaining after rounding

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Refer to :meth:`.FixedPoint.convergent` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <convergent>`
            * :ref:`rounding_induced_overflow`

..  function:: round_nearest(fp, n, /)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int n:
            Number of fractional bits remaining after rounding

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Refer to :meth:`.FixedPoint.round_nearest` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <nearest>`
            * :ref:`rounding_induced_overflow`

..  function:: round_in(fp, n, /)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int n:
            Number of fractional bits remaining after rounding

        :rtype:
            FixedPoint

        Refer to :meth:`.FixedPoint.round_in` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <in>`
            * :ref:`overflow_safe_rounding`

..  function:: round_out(fp, n, /)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int n:
            Number of fractional bits remaining after rounding

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Refer to :meth:`.FixedPoint.round_out` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <out>`
            * :ref:`rounding_induced_overflow`

..  function:: round_up(fp, n, /)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int n:
            Number of fractional bits remaining after rounding

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if
            :attr:`~.FixedPoint.overflow_alert` is ``'error'``)

        Refer to :meth:`.FixedPoint.round_up` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <up>`
            * :ref:`rounding_induced_overflow`

..  function:: round_down(fp, n, /)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int n:
            Number of fractional bits remaining after rounding

        :rtype:
            FixedPoint

        Refer to :meth:`.FixedPoint.round_down` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <down>`
            * :ref:`overflow_safe_rounding`

..  function:: keep_msbs(fp, m, n, /, rounding=None, overflow=None, alert=None)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int m:
            Number of integer bits in the result

        :param int n:
            Number of fractional bits in the result

        :param str rounding:
            Temporary :attr:`~.FixedPoint.rounding` scheme to use.
            Can be keyworded.

        :param str overflow:
            Temporary :attr:`~.FixedPoint.overflow` scheme to use.
            Can be keyworded.

        :param str alert:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to\
            use. Can be keyworded.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if rounding causes overflow (raised only if *alert* - or
            :attr:`~.FixedPoint.overflow_alert` if *alert* is not
            specified - is ``'error'``)

        Refer to :meth:`.FixedPoint.keep_msbs` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`keep_msbs`

..  function:: clamp(fp, m, /, alert=None)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int m:
            Number of integer bits remaining after clamping

        :param str alart:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to
            use. Can be keyworded.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if reducing integer bit width causes overflow (raised only if
            *alert* - or :attr:`~.FixedPoint.overflow_alert` if
            *alert* is not specified - is ``'error'``)

        Refer to :meth:`.FixedPoint.clamp` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <clamp>`

..  function:: wrap(fp, m, /, alert=None)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int m:
            Number of integer bits remaining after wrapping

        :param str alart:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to
            use. Can be keyworded.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if reducing integer bit width causes overflow (raised only if
            *alert* - or :attr:`~.FixedPoint.overflow_alert` if
            *alert* is not specified - is ``'error'``)

        Refer to :meth:`.FixedPoint.wrap` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`Numerical examples from initialization <wrap>`

..  function:: keep_lsbs(fp, m, n, /, overflow=None, alert=None)

        :param FixedPoint fp:
            Object to copy and operate on

        :param int m:
            Number of integer bits in the result

        :param int n:
            Number of fractional bits in the result

        :param str overflow:
            Temporary :attr:`~.FixedPoint.overflow` scheme to use.
            Can be keyworded.

        :param str alert:
            Temporary :attr:`~.FixedPoint.overflow_alert` scheme to
            use. Can be keyworded.

        :rtype:
            FixedPoint

        :raises FixedPointOverflowError:
            if reducing integer bit width causes overflow (raised only if
            *alert* - or :attr:`~.FixedPoint.overflow_alert` if
            *alert* is not specified - is ``'error'``)

        Refer to :meth:`.FixedPoint.keep_lsbs` for more details.

        ..  admonition:: Jump to Examples
            :class: example

            * :ref:`keep_lsbs`
