#!/usr/bin/env python3
# Copyright (c) 2019-2020, Schweitzer Engineering Laboratories, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Schweitzer Engineering Laboratories, Inc. nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL SCHWEITZER ENGINEERING LABORATORIES, INC.
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
import sys as _sys
from os.path import abspath as _abspath, join as _join, dirname as _dirname
import logging as _logging


# This is the base logger for the FixedPoint class
LOGGER = _logging.getLogger("FP")
LOGGER.setLevel(_logging.CRITICAL)

# This is the default file handler to be used unless a different handler is
# specified when logging is enabled.
DEFAULT_FILE_HANDLER = _logging.FileHandler(
    mode='w',
    filename=_join(_abspath(_dirname(__file__)), 'fixedpoint.log'),
    delay=True,
)
DEFAULT_FILE_HANDLER.setLevel(_logging.DEBUG)

# This is the default file handler formatter unless a different formatter is
# specified
DEFAULT_FILE_HANDLER_FORMATTER = _logging.Formatter(
    datefmt="%d %b %Y @ %H:%M:%S",
    fmt='\n'.join(
        [
            '~' * 80,
            "%(levelname)s: %(name)s.%(sn)d.%(funcName)s LINE %(lineno)d (%(asctime)s.%(msecs)d)",
            "%(message)s",
        ]
    )
)

DEFAULT_FILE_HANDLER.setFormatter(DEFAULT_FILE_HANDLER_FORMATTER)
LOGGER.addHandler(DEFAULT_FILE_HANDLER)

# The FP.CONSOLE logger is the method to generate console messages,
# specifically warnings
_WARNER = _logging.getLogger("FP.CONSOLE")
_WARNER.setLevel(_logging.WARNING)
_WARNER_CONSOLE_HANDLER = _logging.StreamHandler(_sys.stdout)
_WARNER_CONSOLE_HANDLER.setLevel(_logging.DEBUG)
_WARNER_FORMATTER = _logging.Formatter("%(levelname)s [SN%(sn)d]: %(message)s")
_WARNER_CONSOLE_HANDLER.setFormatter(_WARNER_FORMATTER)
_WARNER.addHandler(_WARNER_CONSOLE_HANDLER)
