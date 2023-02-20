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

__bands__    = [1690, 1750]
__filename__ = "_GYPSUM_NDGI"
__gui__      = "Normalized Differenced Gypsum Ratio"
__info__     = "This parameter estimates the gypsum feature:\n\n" + \
    "        R_1690 - R_1750  \n" + \
    " ind = ------------------\n" + \
    "        R_1690 + R_1750  \n\n" + \
    "R. Milewski, S. Chabrillat, M. Brell, A. M. Schleicher and L. Guanter\n" + \
    "Assessment of the 1.75 μm Absorption Feature for Gypsum Estimation Using Laboratory, Air- and Spaceborne Hyperspectral Sensors\n" + \
    "Remote Sensing, ???"

def check_bands(ubands, wvl):
    ind1 = int(ubands[0])
    ind2 = int(ubands[1])
    if ind1 == ind2:
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
            B1690 = cube[ind[0], ky, kx]
            B1750 = cube[ind[1], ky, kx]
            num = B1690 - B1750
            den  = B1690 + B1750
            res = np.nan
            if den != 0:
                res = num / den
            prod[ky, kx] = res
    return prod
