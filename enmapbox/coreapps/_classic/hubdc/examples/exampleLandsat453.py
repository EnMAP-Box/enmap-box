"""
Create a Landsat 4-5-3 band stack.
"""

import tempfile
import os
import numpy
from _classic.hubdc.applier import Applier, ApplierOperator, ApplierInputRaster, ApplierInputVector, ApplierOutputRaster
from _classic.hubdc.testdata import LT51940232010189KIS01, BrandenburgDistricts

applier = Applier()
applier.inputRaster.setRaster(key='b3', value=ApplierInputRaster(filename=LT51940232010189KIS01.band3))
applier.inputRaster.setRaster(key='b4', value=ApplierInputRaster(filename=LT51940232010189KIS01.band4))
applier.inputRaster.setRaster(key='b5', value=ApplierInputRaster(filename=LT51940232010189KIS01.band5))
applier.outputRaster.setRaster(key='stack453', value=ApplierOutputRaster(filename=os.path.join(tempfile.gettempdir(), 'landsat453.img')))

class Landsat453Operator(ApplierOperator):
    def ufunc(operator):
        array = numpy.vstack([operator.inputRaster.raster(key='b4').array(),
                              operator.inputRaster.raster(key='b5').array(),
                              operator.inputRaster.raster(key='b3').array()])
        operator.outputRaster.raster(key='stack453').setArray(array=array)

applier.apply(operatorType=Landsat453Operator)
print(applier.outputRaster.raster(key='stack453').filename)
