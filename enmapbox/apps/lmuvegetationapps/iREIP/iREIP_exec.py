# -*- coding: utf-8 -*-

from lmuvegetationapps.iREIP.iREIP_GUI_core import iREIP_core

core = iREIP_core(division_factor=10000, max_ndvi_pos=None, ndvi_spec=None, nodat_val=-999)
matrix = core.read_image("U:\ECST_III\CHIME\HBach/ang20180702t105516_rfl_v2q2/105516_Fields.bsq")
reip, d1, d2 = core.derivate_3d(matrix)
print(reip)