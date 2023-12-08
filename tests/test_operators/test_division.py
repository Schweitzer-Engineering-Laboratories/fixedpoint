#!/usr/bin/env python3
# This test was not written by the original authors of the fixedpoint library and does not conform
# to its quality standards.

import pathlib
import sys
sys.path.insert(1, str(pathlib.Path('./../..').resolve()));
import fixedpoint as uut

from random import *
import math

# fuzz test divide
for i in range(1000):
    x = uut.FixedPoint(0, m=int(random() * 100)+1, n=int(random() * 100)+1, signed=1)
    y = uut.FixedPoint(0, m=int(random() * 100)+1, n=int(random() * 100)+1, signed=1)

    # because we are choosing only numbers that are precisely representable in fixed-point,
    # no error is introduced at these steps.
    x._bits = getrandbits(x._m + x._n + int(x._signed))
    y._bits = getrandbits(y._m + y._n + int(y._signed))
    if (y._bits == 0): y._bits = 1
    d = x / y

    xf = float(x)
    yf = float(y)
    df = xf / yf

    # TODO: establish actual error bounds
    MANTISSABITS = 52
    exp = math.frexp(df)[1]
    tol = (2**(exp - MANTISSABITS))
    err = df - float(d)
    if (math.fabs(err) > tol):
        print(f"division of {x.qformat} / {y.qformat} has error {err}")
        print(f"d = {float(d)}, df = {xf / yf}, tol = {tol}")
        print()
