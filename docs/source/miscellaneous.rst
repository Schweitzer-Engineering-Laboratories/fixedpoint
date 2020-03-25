###############################################################################
Miscellaneous
###############################################################################

..  module:: fixedpoint.logging

*******************************************************************************
Logging Integration
*******************************************************************************

The :mod:`fixedpoint` package uses standard logging constructs to generate
warnings and debug logs. The following specifications allow you to customize
the logging schemes, handlers, formats, etc. to your liking.

Warnings
===============================================================================

:mod:`fixedpoint` warnings are generated using the :mod:`logging` package.

..  data:: WARNER_CONSOLE_HANDLER

    :type:
        logging.StreamHandler

    :value:
        * *stream* is set to `sys.stderr`
        * *level* is set to *logging.DEBUG*.

..  data:: WARNER

    :type:
        logging.Logger

    :value:
        * *name* is *FP.CONSOLE*
        * *level* defaults to *logging.WARNING*

    You can retrieve this logger with ``logging.getLogger("FP.CONSOLE")``.

The :data:`WARNER_CONSOLE_HANDLER` is added to :data:`WARNER`.

Additionally, each :class:`~.fixedpoint.FixedPoint` object has a unique
serial number associated with it that is available in the
:class:`~logging.LogRecord` instance as the key **sn**. This is described in
more detail :pylib:`here <logging.html#logging.Logger.debug>` as the *extra*
keyword.

Debug Logging
===============================================================================

Logging is also used for debug purposes.

..  data:: LOGGER

    :type:
        logging.Logger

    :value:
        * *name* is *FP*
        * *level* defaults to *logging.CRITICAL*

..  data:: DEFAULT_FILE_HANDLER

    :type:
        logging.FileHandler

    :value:
        * *filename* is set to *fixedpoint.log* located in the same directory
          as the source code
        * *mode* is set to *'w'*
        * *delay* is set to *True*, thus no file is generated (or overwritten)
          until logging is enabled with
          :meth:`fixedpoint.FixedPoint.enable_logging`
        * *level* defaults to *logging.DEBUG*

The :data:`DEFAULT_FILE_HANDLER` is added to the :data:`LOGGER`.

On initial import, :data:`LOGGER`\ 's level is set to *logging.CRITICAL*. Since
no critical level logs are made within :mod:`fixedpoint`, it essentially
disables debug logging.

..  currentmodule:: fixedpoint

When :meth:`.FixedPoint.enable_logging` is called,
:data:`~fixedpoint.logging.LOGGER`\ 's level is set to *logging.DEBUG*.

When :meth:`.FixedPoint.disable_logging` is called,
:data:`~fixedpoint.logging.LOGGER`\ 's level is set back to *logging.CRITICAL*.

*******************************************************************************
Typing
*******************************************************************************

The :mod:`fixedpoint` package is typed (see :pep:`484`) and supported by
`mypy <https://mypy.readthedocs.io/en/stable/>`_,
`PyCharm <https://www.jetbrains.com/pycharm/>`_, etc.

Subclassing :class:`.FixedPoint` is also supported.

*******************************************************************************
Numpy Integration
*******************************************************************************

..  |numpy| replace:: ``numpy``
..  _numpy: https://numpy.org/
..  |convolve| replace:: ``numpy.convolve``
..  _convolve: https://docs.scipy.org/doc/numpy/reference/generated/numpy.convolve.html

While not specifically tested, integration with |numpy|_ should be possible as
long as unsupported operators (like ``@``, ``/``, ``//``, ``%``, etc.) are not
used.

Examples taken from the |convolve|_ documentation:

..  doctest:: numpy.convolve

    >>> import numpy as np
    >>> a = [FixedPoint(1), FixedPoint(2), FixedPoint(3)]
    >>> b = [FixedPoint(0), FixedPoint(1), FixedPoint(0.5)]
    >>> x = np.convolve(a, b)
    >>> [float(fp) for fp in x]
    [0.0, 1.0, 2.5, 4.0, 1.5]

    >>> y = np.convolve(a, b, 'same')
    >>> [float(fp) for fp in y]
    [1.0, 2.5, 4.0]

    >>> z = np.convolve(a, b, 'valid')
    >>> [float(fp) for fp in z]
    [2.5]

*******************************************************************************
Serialization
*******************************************************************************

JSON
===============================================================================

..  class:: fixedpoint.json.JSONEncoder

..  class:: fixedpoint.json.JSONDecoder

..  doctest:: json serialization

    >>> from fixedpoint.json import FixedPointEncoder, FixedPointDecoder
    >>> import random, json
    >>> L = 52
    >>> signed = random.randrange(2)
    >>> m = random.randrange(L)
    >>> n = L - m
    >>> original = FixedPoint(hex(random.getrandbits(L)), signed, m, n)
    >>> serialized = json.dumps(original, cls=FixedPointEncoder)
    >>> deserialized = json.loads(serialized, cls=FixedPointDecoder)
    >>> original == deserialized
    True

Pickle
===============================================================================

The :mod:`pickle` scheme works out of the box:

..  doctest:: pickle

    >>> import random, pickle
    >>> L = 52
    >>> signed = random.randrange(2)
    >>> m = random.randrange(L)
    >>> n = L - m
    >>> original = FixedPoint(hex(random.getrandbits(L)), signed, m, n)
    >>> pickled = pickle.dumps(original)
    >>> unpickled = pickle.loads(pickled)
    >>> original == unpickled
    True
