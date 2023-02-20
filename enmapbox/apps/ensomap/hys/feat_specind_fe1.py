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

__bands__    = [477, 556, 693]
__filename__ = "_IRON_RI"
__gui__      = "Iron Oxyde Content Redness Index"
__info__     = "This parameter estimates the Hematite content:\n\n" + \
    "           R_693^2       \n" + \
    " ind = ------------------\n" + \
    "        R_447 . R_556^3  \n\n" + \
    "Madeira, J., Bedidi, A., Cervelle, B., Pouget, M. and Flay, N. (1997)\n"+\
    "Visible spectrometric indices of hematite (Hm) and goethite (Gt)\n"+\
    "content in lateritic soils: the application of a Thematic Mapper (TM)\n"+\
    "image for soil-mapping in Brasilia, Brazil. Int. J. Remote Sens., \n"+\
    "18(13):2835-2852"

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
            B0477 = cube[ind[0], ky, kx]
            B0556 = cube[ind[1], ky, kx]
            B0693 = cube[ind[2], ky, kx]
            den = B0477 * B0556 * B0556 * B0556
            num = B0693 * B0693
            res = np.nan
            if den != 0:
                res = num / den
            prod[ky, kx] = res
    return prod
