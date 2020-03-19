#!/usr/bin/env python3
# Copyright 2020, Schweitzer Engineering Laboratories, Inc
# SEL Confidential
"""
Initialization methods for unit tests
"""
import sys
import logging
import pathlib
import random

import nose

from . import tools
# sys.path.insert(1, str(pathlib.Path('./../..').resolve()));
import fixedpoint as uut

# Configure logger
UTLOG = logging.getLogger("FP.UNITTESTS")
LOGID = dict(extra=dict(sn=-1))
uut.FixedPoint.enable_logging()

# Generate random seed
seed = random.getrandbits(31)
random.seed(seed)
UTLOG.info("RANDOM SEED: %d", seed, **LOGID)

def setup_logging():
    logger = logging.getLogger("FP")
    # Remove all handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    # Generate custom rotating file handler with formatter
    handler = tools.TestCaseRotatingFileHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        datefmt="%d %b %Y @ %H:%M:%S",
        fmt='\n'.join(
            [
                '~' * 80,
                "%(levelname)s: %(name)s.%(sn)d.%(funcName)s LINE %(lineno)d (%(asctime)s.%(msecs)d)",
                "%(message)s",
            ]
        )
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
setup_logging()
