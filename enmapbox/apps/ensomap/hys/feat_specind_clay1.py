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

__bands__    = [2133, 2209, 2225]
__filename__ = "_Clay_SWIRFI"
__gui__      = "Clay Content SWIR Fine particle Index"
__info__     = "This parameter estimates the clay mineral content:\n\n" + \
    "           B2133^2       \n" + \
    " ind = ------------------\n" + \
    "        B2225 . B2209^3  \n\n" + \
    "Levin, N., Kidron, G.J., Ben-Dor, E., (2007)\n"+\
    "Surface properties of stabilizing coastal dunes: combining spectral\n"+\
    "field analyses. Sedimentology 54, 771–788."

def check_bands(ubands, wvl):
    ind1 = int(ubands[0])
    ind2 = int(ubands[1])
    ind3 = int(ubands[2])
    if ind1 == ind2 or ind1 == ind3 or ind2 == ind3:
        return True, "Identical band found!\n\t- Results might be corrupted!\n"
    return True, "Has been calculated!\n"


@nb.jit(nb.float32[:,:](nb.float32[:,:,:], nb.float32[:], nb.int32[:], nb.int32[:,:]), nopython=True, fastmath=True)
def process(cube, wvl, ind, mask):
    ny = cube.shape[1]
    nx = cube.shape[2]
    prod = np.zeros((ny, nx), dtype = np.float32)
    for ky in range(ny):
        for kx in range(nx):
            if mask is not None:
                if mask[ky, kx] == 0:
                    prod[ky, kx] = np.nan
                    continue
            B2133 = cube[ind[0], ky, kx]
            B2209 = cube[ind[1], ky, kx]
            B2225 = cube[ind[2], ky, kx]
            den = B2225 * B2209 * B2209 * B2209
            num = B2133 * B2133
            res = np.nan
            if den != 0:
                res = num / den
            prod[ky, kx] = res
    return prod
