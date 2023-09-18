# -*- coding: utf-8 -*-
#
# Copyright © 2019 Stéphane Guillaso
# Licensed under the terms of 
# (see ../../LICENSE.md for details)

import numpy as np
import hys
import numba as nb

__bands__    = [460, 660]
__filename__ = "_water"


# def check_bands(ubands, wvl):
#     ind0 = int(ubands[0])
#     ind1 = int(ubands[1])
#     if ind0 == ind1:
#         return False, 'Identical band found!\n'
#     if (ind1-ind0) < 2:
#         return False, 'Not enough points to calculate crad!\n'
#     return True, "Has been calculated!\n"


@nb.jit(nopython=True)
def process(cube):
    ny = cube.shape[1]
    nx = cube.shape[2]
    prod = np.zeros((ny, nx), dtype = np.float32)
    mask = np.zeros((ny, nx), dtype = np.int32)
    lim1 = 0.0
    lim2 = 1.00001
    for ky in range(ny):
        for kx in range(nx):
            B0660 = cube[1, ky, kx]
            B0460 = cube[0, ky, kx]
            diff = B0660 - B0460
            sum  = B0660 + B0460
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
#     out = np.zeros((ny, nx), dtype=np.float32)
#     for ky in range(ny):
#         for kx in range(nx):
#             out[ky, kx] = hys.tools.get_crad(wvl, cube[:, ky, kx])
#     return out
