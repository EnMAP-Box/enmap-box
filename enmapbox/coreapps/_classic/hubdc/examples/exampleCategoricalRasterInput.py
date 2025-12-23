from osgeo import gdal
import numpy
from _classic.hubdc.applier import Applier
from _classic.hubdc.applier import ApplierOperator

def script():

    filename = r'C:\Work\data\gms\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_cfmask.img'

    applier = Applier()
    applier.controls.setResolution(xRes=1000, yRes=1000)
    applier.setInput('cfmask30m', filename=filename)
    applier.setOutputRaster('cfmask1000m', filename=r'c:\output\cfmask1000m.img')
    applier.setOutputRaster('cfmaskFractions1000m', filename=r'c:\output\cfmaskFractions1000m.img')

    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):

    def ufunc(self):

        overlap = 10

        cfmask1000m = self.getCategoricalArray('cfmask30m', ids=[0, 1, 2, 4], noData=255, minCoverage=0.9, overlap=overlap)
        self.setArray('cfmask1000m', array=cfmask1000m, overlap=overlap)

        cfmaskFractions1000m = self.getCategoricalFractionArray('cfmask30m', ids=[0, 1, 2, 4], overlap=overlap)
        self.setArray('cfmaskFractions1000m', array=cfmaskFractions1000m, overlap=overlap)


if __name__ == '__main__':
    script()

