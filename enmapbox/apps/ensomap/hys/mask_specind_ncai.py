# -*- coding: utf-8 -*-
#
# Copyright © 2019 Stéphane Guillaso
# Licensed under the terms of 
# (see ../../LICENSE.md for details)

import numpy as np
import hys
import os # <-- to be removed
import importlib
import numba as nb

__bands__    = [2000, 2100, 2200]
__filename__ = "_ncai"


@nb.jit(nopython=True)
def process(cube):
    ny = cube.shape[1]
    nx = cube.shape[2]
    prod = np.zeros((ny, nx), dtype = np.float32)
    mask = np.zeros((ny, nx), dtype = np.int32)
    lim1 = -1.0
    lim2 = 0.03
    for ky in range(ny):
        for kx in range(nx):
            B2000 = cube[0, ky, kx]
            B2100 = cube[1, ky, kx]
            B2200 = cube[2, ky, kx]
            diff = 0.5 * (B2000 + B2200) - B2100
            sum  = 0.5 * (B2000 + B2200) + B2100
            res = float(0)
            msk = 0
            if sum != 0:
                res = diff / sum
                msk = 1
            if msk == 1 and res > lim1 and res < lim2:
                msk = 1
            else:
                msk = 0
            prod[ky, kx] = res
            mask[ky, kx] = msk
    return prod, mask
