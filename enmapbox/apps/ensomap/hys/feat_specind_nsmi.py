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

__bands__    = [1800, 2119]
__filename__ = "_MOISTURE_NSMI"
__gui__      = "Normalized Soil Moisture Index"
__info__     = "This parameter estimates the soil moisture content:\n\n" + \
    "        R_1800 - R_2119  \n" + \
    " ind = ------------------\n" + \
    "        R_1800 + R_2119  \n\n" + \
    "Haubrock, S.-N., Chabrillat, S., Lemmnitz, C., Kaufmann, H., 2008\n"+\
    "Surface soil moisture quantification models from reflectance data \n"+\
    "under field conditions. Int. J. Remote Sens. 29 (1), 3–29."

def check_bands(ubands, wvl):
    ind0 = int(ubands[0])
    ind1 = int(ubands[1])
    if ind0 == ind1:
        return False, "Identical band found!\n\t- Results will be 0"
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
            B1800 = cube[ind[0], ky, kx]
            B2119 = cube[ind[1], ky, kx]
            num = B1800 - B2119
            den  = B1800 + B2119
            res = np.nan
            if den != 0:
                res = num / den
            prod[ky, kx] = res
    return prod

