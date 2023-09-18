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

__bands__    = [2138, 2209]
__filename__ = "_OC_SLOPE_2138_2209"
__gui__      = "SOC Index: 1/slope 2138 - 2209"
__info__     = "Indirect organic matter content: \n"+\
    "Calculate the inverse of the slope of a straight line defined\n"+\
    "between the reflectance value at the start of the absorption feature \n"+\
    "and the reflectance value at the centre of the absorption feature:\n\n"+\
    "ind = 1/slope(R_2138, R_2209)\n\n"+\
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
    out = np.zeros((ny, nx), dtype=np.float32)
    for ky in range(ny):
        for kx in range(nx):
            if mask is not None:
                if mask[ky, kx] == 0:
                    out[ky, kx] = np.nan
                    continue
            R2138 = cube[ind[0], ky, kx]
            R2209 = cube[ind[1], ky, kx]
            W2138 = wvl[ind[0]]
            W2209 = wvl[ind[1]]
            slope = (R2209 - R2138) / (W2209 - W2138)
            if slope != 0: out[ky, kx] = 1. / slope
            else:        out[ky, kx] = np.nan
    return out
