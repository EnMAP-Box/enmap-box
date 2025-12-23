import tempfile
import os
from scipy.ndimage import uniform_filter

from _classic.hubdc.applier import Applier, ApplierOperator, ApplierInputRaster, ApplierOutputRaster
from _classic.hubdc.examples.testdata import LT51940232010189KIS01

applier = Applier()
applier.inputRaster.setRaster(key='image', value=ApplierInputRaster(filename=LT51940232010189KIS01.band3))
applier.outputRaster.setRaster(key='outimage', value=ApplierOutputRaster(filename=os.path.join(tempfile.gettempdir(), 'smoothed.img')))

class SmoothOperator(ApplierOperator):
    def ufunc(operator):

        # does a spatial 11x11 uniform filter.
        # Note: for a 3x3 the overlap is 1, 5x5 overlap is 2, ..., 11x11 overlap is 5, etc
        overlap = 5
        array = operator.inputRaster.raster(key='image').array(overlap=overlap)
        arraySmoothed = uniform_filter(array, size=11, mode='constant')
        operator.outputRaster.raster(key='outimage').setArray(array=arraySmoothed, overlap=overlap)

applier.apply(operatorType=SmoothOperator)
print(applier.outputRaster.raster(key='outimage').filename)
