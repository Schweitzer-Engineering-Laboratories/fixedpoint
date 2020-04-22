"""FixedPoint logging facilities."""
import sys
import pathlib
import logging

__all__ = ('LOGGER', 'DEFAULT_FILE_HANDLER', 'DEFAULT_FILE_HANDLER_FORMATTER',
           'WARNER', 'WARNER_CONSOLE_HANDLER', 'WARNER_FORMATTER')

# This is the base logger for the FixedPoint class
LOGGER = logging.getLogger("FP")
LOGGER.setLevel(logging.CRITICAL)

# This is the default file handler to be used unless a different handler is
# specified when logging is enabled.
logfile = pathlib.Path(__file__).parent / 'fixedpoint.log'
DEFAULT_FILE_HANDLER = logging.FileHandler(logfile, 'w', None, True)
DEFAULT_FILE_HANDLER.setLevel(logging.DEBUG)

# This is the default file handler formatter unless a different formatter is
# specified
fmt = """\
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
%(levelname)s: %(name)s.%(sn)d.%(funcName)s \
LINE %(lineno)d (%(asctime)s.%(msecs)d
%(message)s"""
DEFAULT_FILE_HANDLER_FORMATTER = logging.Formatter(fmt, "%d %b %Y @ %H:%M:%S")
DEFAULT_FILE_HANDLER.setFormatter(DEFAULT_FILE_HANDLER_FORMATTER)
LOGGER.addHandler(DEFAULT_FILE_HANDLER)

# The FP.CONSOLE logger is the method to generate console messages,
# specifically warnings
WARNER = logging.getLogger("FP.CONSOLE")
WARNER.setLevel(logging.WARNING)
WARNER_CONSOLE_HANDLER = logging.StreamHandler(sys.stderr)
WARNER_CONSOLE_HANDLER.setLevel(logging.DEBUG)
WARNER_FORMATTER = logging.Formatter("%(levelname)s [SN%(sn)d]: %(message)s")
WARNER_CONSOLE_HANDLER.setFormatter(WARNER_FORMATTER)
WARNER.addHandler(WARNER_CONSOLE_HANDLER)
