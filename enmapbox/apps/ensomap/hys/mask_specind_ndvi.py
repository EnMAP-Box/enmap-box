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

__bands__    = [660, 800]
__filename__ = "_ndvi"



@nb.jit(nopython=True)
def process(cube):
    ny = cube.shape[1]
    nx = cube.shape[2]
    prod = np.zeros((ny, nx), dtype = np.float32)
    mask = np.zeros((ny, nx), dtype = np.int32)
    lim1 = -1.0
    lim2 = 0.3
    for ky in range(ny):
        for kx in range(nx):
            B0800 = cube[1, ky, kx]
            B0660 = cube[0, ky, kx]
            diff = B0800 - B0660
            sum  = B0800 + B0660
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
