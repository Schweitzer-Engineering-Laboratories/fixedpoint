..  module:: fixedpoint.properties

###############################################################################
The **PropertyResolver** Class
###############################################################################

..  admonition:: Examples are just a click away
    :class: example

    Boxes like this link to example code.

..  class:: PropertyResolver()

    Resolves properties between two :class:`~.fixedpoint.FixedPoint`\ s.

    This is used internally by the :class:`~.fixedpoint.FixedPoint` class for
    property resolution. You should not need to instantiate this class, but it
    is documented here to show how properties are resolved.

    ..  method:: mismatch_alert(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose |mismatch_alert|
            properties are to be resolved.

        :return:
            Resolved |mismatch_alert| property.

        :rtype:
            str

        :raises MismatchError:
            if |mismatch_alert| properties of all *args* do not match, and
            any *args*' |mismatch_alert| property setting is ``'error'``.

        When all *args* have equivalent |mismatch_alert| properties, that value
        is returned. Otherwise, the priority of resolution order is:

            #. ``'warning'``
            #. ``'error'``
            #. ``'ignore'``

        If there are mismatches in the |mismatch_alert| properties, then an
        alert is issued according to the highest priority :meth:`mismatch_alert`
        setting in *args*.

    ..  method:: overflow(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose |overflow|
            properties are to be resolved.

        :return:
            Resolved |overflow| property.

        :rtype:
            str

        :raises MismatchError:
            if |overflow| or |mismatch_alert| properties of all *args* do not
            match, and any *args*' |mismatch_alert| property setting is
            ``'error'``.

        When all *args* have equivalent |overflow| properties, that value is
        returned. Otherwise, the priority of resolution order is:

            #. ``'clamp'``
            #. ``'wrap'``

        If there are mismatches in the |mismatch_alert| properties, then an
        alert is issued according to the highest priority :meth:`mismatch_alert`
        setting in *args*.

    ..  method:: rounding(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose |rounding|
            properties are to be resolved.

        :return:
            Resolved |rounding| property.

        :rtype:
            str

        :raises MismatchError:
            if |rounding| or |mismatch_alert| properties of all *args* do not
            match, and any *args*' |mismatch_alert| property setting is
            ``'error'``.

        When all *args* have equivalent |rounding| properties, that value is
        returned. Otherwise, the priority of resolution order is:

            #. ``'convergent'`` (for if any *args* are signed, otherwise
               ``'nearest'``)
            #. ``'nearest'`` (if no *args* are signed, otherwise
               ``'convergent'``)
            #. ``'down'``
            #. ``'in'``
            #. ``'out'``
            #. ``'up'``

        If there are mismatches in the |mismatch_alert| properties, then an
        alert is issued according to the highest priority :meth:`mismatch_alert`
        setting in *args*.

    ..  method:: overflow_alert(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose |overflow_alert|
            properties are to be resolved.

        :return:
            Resolved |overflow_alert| property.

        :rtype:
            str

        :raises MismatchError:
            if |mismatch_alert| or |overflow_alert| properties of all *args* do
            not match.

        When all *args* have equivalent |overflow_alert| properties, that value
        is returned. Otherwise, the priority of resolution order is:

            #. ``'error'``
            #. ``'warning'``
            #. ``'ignore'``

        If there are mismatches in the |overflow_alert| properties, then an
        alert is issued according to the highest priority :meth:`mismatch_alert`
        setting in *args*.

    ..  method:: implicit_cast_alert(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose
            |implicit_cast_alert| properties are to be resolved.

        :return:
            Resolved |implicit_cast_alert| property.

        :rtype:
            str

        :raises MismatchError:
            if |mismatch_alert| or |implicit_cast_alert| properties of all
            *args* do not match.

        When all *args* have equivalent |implicit_cast_alert| properties, that
        value is returned. Otherwise, the priority of resolution order is:

            #. ``'warning'``
            #. ``'error'``
            #. ``'ignore'``

        If there are mismatches in the |implicit_cast_alert|
        properties, then an alert is issued according to the highest priority
        :meth:`mismatch_alert` setting in *args*.

    ..  method:: str_base(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose
            |str_base| properties are to be resolved.

        :return:
            Resolved |str_base| property.

        :rtype:
            int

        When all *args* have equivalent |str_base| properties, that |str_base|
        is returned. Otherwise the resolution is 16.

        ..  note::

            |str_base| mismatches do not raise
            :exc:`~fixedpoint.MismatchError`\ s.

    ..  method:: all(*args)

        :param FixedPoint args:
            An variable number of :class:`~.fixedpoint.FixedPoint`\ s whose property settings
            are to be resolved.

        :return:
            `dict` of resolved properties.

        :rtype:
            dict[str, str]

        :raises MismatchError:
            if any properties are not equivalent for all *args* and any *args*'
            |mismatch_alert| property setting is ``'error'``.

        Resolves all properties for each :class:`~.fixedpoint.FixedPoint` in *args*.

        Return value is a `dict`, with the format
        ``'property name': 'property setting'``. This can be used directly in
        the :class:`~fixedpoint.FixedPoint` constructor as its property keyword
        arguments.

        A mismatch alert is issued for each property mismatch.

        ..  _property_resolution_order:

        ..  rubric:: Property Resolution Order

        The order in which properties are resolved (and thus the order in which
        alerts may be issued) is:

            #. :meth:`.mismatch_alert`
            #. :meth:`.overflow`
            #. :meth:`.rounding`
            #. :meth:`.overflow_alert`
            #. :meth:`.implicit_cast_alert`
            #. :meth:`.str_base`



..  |str_base| replace:: `~fixedpoint.FixedPoint.str_base`
..  |overflow| replace:: `~fixedpoint.FixedPoint.overflow`
..  |rounding| replace:: `~fixedpoint.FixedPoint.rounding`
..  |overflow_alert| replace:: `~fixedpoint.FixedPoint.overflow_alert`
..  |mismatch_alert| replace:: `~fixedpoint.FixedPoint.mismatch_alert`
..  |implicit_cast_alert| replace:: `~fixedpoint.FixedPoint.implicit_cast_alert`
