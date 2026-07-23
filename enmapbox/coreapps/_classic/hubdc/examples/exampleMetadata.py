"""
Reads the ENVI/wavelength metadata item from an input dataset and passes it to an output dataset.
"""

import tempfile
import os
import numpy
from _classic.hubdc.applier import Applier, ApplierOperator, ApplierInputRaster, ApplierOutputRaster
from _classic.hubdc.examples.testdata import LT51940232010189KIS01

applier = Applier()
applier.inputRaster.setRaster(key='image', value=ApplierInputRaster(filename=LT51940232010189KIS01.band3))
applier.outputRaster.setRaster(key='outimage', value=ApplierOutputRaster(filename=os.path.join(tempfile.gettempdir(), 'outimage.img')))

class CopyMetadataOperator(ApplierOperator):

    def ufunc(operator):

        # copy raster data
        array = operator.inputRaster.raster(key='image').array()
        operator.outputRaster.raster(key='outimage').setArray(array=array)

        # copy ENVI/wavelength metadata
        wavelength = operator.inputRaster.raster(key='image').getMetadataItem(key='wavelength', domain='ENVI')
        operator.outputRaster.raster(key='outimage').setMetadataItem(key='wavelength', value=wavelength, domain='ENVI')

applier.apply(operatorType=CopyMetadataOperator)
print(applier.outputRaster.raster(key='outimage').filename)
