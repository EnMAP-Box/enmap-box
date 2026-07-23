"""
Calculate Normalized Difference Vegetation Index (NDVI) for a Landsat 5 scene and cut the result to the German state Brandenburg.
"""

import tempfile
import os
import numpy
from _classic.hubdc.applier import Applier, ApplierOperator, ApplierInputRaster, ApplierInputVector, ApplierOutputRaster, ApplierInputRasterIndex, ApplierInputRasterGroup
from _classic.hubdc.testdata import LT51940232010189KIS01, BrandenburgDistricts

# Set up input and output filenames.
applier = Applier()
applier.controls.setProjection()
path194 = applier.inputRaster.setGroup('194', value=ApplierInputRasterGroup())
row023 = path194.setGroup(key='023', value=ApplierInputRasterGroup())
row024 = path194.setGroup(key='024', value=ApplierInputRasterGroup())

# add first dataset
scene = row023.setGroup(key='LC81940232015235LGN00', value=ApplierInputRasterGroup())
scene.setRaster(key='LC81940232015235LGN00_cfmask', value=ApplierInputRaster(filename=r'C:\Work\data\gms\landsat\194\023\LC81940232015235LGN00\LC81940232015235LGN00_cfmask.img'))

# ...

# add last dataset
scene = row024.setGroup(key='LT51940242010189KIS01', value=ApplierInputRasterGroup())
scene.setRaster(key='LT51940242010189KIS01_cfmask', value=ApplierInputRaster(filename=r'C:\Work\data\gms\landsat\194\024\LT51940242010189KIS01\LT51940242010189KIS01_cfmask.img'))

applier.inputRaster.setGroup(key='landsat', value=ApplierInputRasterGroup.fromFolder(folder=r'C:\Work\data\gms\landsat',
                                                                                     extensions=['.img'],
                                                                                     ufunc=lambda root, basename, extension: basename.endswith('cfmask')))

class Operator(ApplierOperator):
    def ufunc(operator):
        # access individual dataset
        cfmask = operator.inputRaster.group(key='194').group(key='023').group(key='LC81940232015235LGN00').raster(key='LC81940232015235LGN00_cfmask')
        array = cfmask.array()
        # ... or
        cfmask = operator.inputRaster.raster(key='194/023/LC81940232015235LGN00/LC81940232015235LGN00_cfmask')


        # iterate over all datasets
        for path in operator.inputRaster.groups():
            for row in path.groups():
                for scene in row.groups():
                    key = scene.findRaster(filteendswith='cfmask')
                    cfmask = scene.raster(key=key)
                    array = cfmask.array()

        # flat iterate over all datasets
        for cfmask in operator.inputRaster.flatRasters():
            array = cfmask.array()

applier.apply(operatorType=Operator)
