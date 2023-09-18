# -*- coding: utf-8 -*-
#
# Copyright © 2019 Stéphane Guillaso
# Licensed under the terms of 
# (see ../../LICENSE.md for details)

import numpy as np
import hys
import os # <-- to be removed
# import importlib
import numba as nb
from hys.tools import get_crad

__bands__    = [760, 1050]
__filename__ = "_IRON_CRAD_760_1050"
__gui__      = "Iron CRAD: 760 -> 1050"
__info__     = "Perform a continuum removal absorption depth\n" + \
    "between 760 nm and 1050 nm."

def check_bands(ubands, wvl):
    ind0 = int(ubands[0])
    ind1 = int(ubands[1])
    if ind0 == ind1:
        return False, 'Identical band found!\n'
    if (ind1-ind0) < 2:
        return False, 'Not enough points to calculate crad!\n'
    return True, "Has been calculated!\n"


@nb.jit(nb.float32[:,:](nb.float32[:,:,:], nb.float32[:], nb.int32[:], nb.int32[:,:]), nopython=True, fastmath=True)
def process(cube, wvl, ind, mask):
    ny = cube.shape[1]
    nx = cube.shape[2]
    nc = ind[1] - ind[0]
    out = np.zeros((ny, nx), dtype=np.float32)
    x = np.zeros((nc), dtype=np.float32)
    y = np.zeros((nc), dtype=np.float32)
    for kc in range(nc):
        x[kc] = wvl[kc + ind[0]]
    for ky in range(ny):
        for kx in range(nx):
            if mask is not None:
                if mask[ky, kx] == 0:
                    out[ky, kx] = np.nan
                    continue
            for kc in range(nc):
                y[kc] = cube[kc+ind[0], ky, kx]
            out[ky, kx] = get_crad(x, y)
    return out
