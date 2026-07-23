from osgeo import gdal
import numpy
from _classic.hubdc.applier import Applier
from _classic.hubdc.applier import ApplierOperator


def script():

    #filename = r'H:\EuropeanDataCube\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_sr_band1.img'
    filename = r'C:\Work\data\gms\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_cfmask.img'

    applier = Applier()
    applier.controls.setResolution(xRes=1000, yRes=1000)
    applier.setInput('cfmask', filename=filename, resampleAlg=gdal.GRA_Average)
    applier.setOutputRaster('cloudFraction', filename=r'c:\output\out.img', format='ENVI')
    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):
    def ufunc(self):

        def cloudFraction(cfmask):
            return numpy.float32(cfmask==4)

        overlap = 10
        array = self.getDerivedArray('cfmask', ufunc=cloudFraction, overlap=overlap)
        self.setArray('cloudFraction', array=array, overlap=overlap)

if __name__ == '__main__':
    script()
