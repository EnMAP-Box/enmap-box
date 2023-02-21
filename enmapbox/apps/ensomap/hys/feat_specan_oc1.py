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
from hys.tools import get_continuum_line

__bands__    = [400, 700]
__filename__ = "_OC_SUM_400_700"
__gui__      = "SOC Index: 1/sum 400 - 700"
__info__     = "Organic matter content: \n"+\
    "Calculate the inverse of the sum of the total reflectance \n"+\
    "minus the continuum removed function:\n\n"+\
    "ind = 1/sum(R_400 to R_700)\n\n"+\
    "Bartholomeus, H., Epema, G., Schaepman, M., 2007.\n"+\
    "Determining iron content in Mediterranean soils in partly vegetated\n"+\
    "regions, using spectral reflectance and imaging spectroscopy.\n"+\
    "Int. J. Appl. Earth Observ. Geoinform. 9, 194–203."
    
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
    h = np.zeros((nc), dtype=np.float32)
    for kc in range(nc):
        x[kc] = wvl[kc + ind[0]]
    for ky in range(ny):
        for kx in range(nx):
            if mask is not None:
                if mask[ky, kx] == 0:
                    out[ky, kx] = np.nan
                    continue
            for kc in range(nc):
                y[kc] = cube[kc + ind[0], ky, kx]
            get_continuum_line(x, y, h, 0, nc-1)
            sum = np.float32(0.0)
            for kc in range(nc):
                if h[kc] != 0: sum += h[kc] - y[kc]
            if sum != 0: out[ky, kx] =  1. / sum
            else:        out[ky, kx] = np.nan
    return out
