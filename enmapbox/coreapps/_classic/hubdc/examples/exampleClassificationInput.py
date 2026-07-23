from osgeo import gdal
from _classic.hubdc.applier import Applier
from _classic.hubdc.applier import ApplierOperator

def script():

    filename = r'C:\Work\data\gms\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_cfmask.img'

    applier = Applier()
    applier.controls.setResolution(xRes=10, yRes=10)
    applier.setInput('classification', filename=r'C:\Work\source\QGISPlugIns\enmap-box\enmapbox\testdata\HymapBerlinA\HymapBerlinA_truth.img')
    applier.setOutputRaster('probability10m', filename=r'c:\output\probability10m.img')
    applier.setOutputRaster('classification10m', filename=r'c:\output\classification10m.img')
    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):

    def ufunc(self):

        overlap = 10

        probability10m = self.getProbabilityArray('classification', overlap=overlap)
        self.setArray('probability10m', array=probability10m, overlap=overlap)

        classification10m = self.getClassificationArray('classification', overlap=overlap)
        self.setArray('classification10m', array=classification10m, overlap=overlap)

        classes, classNames, classLookup = self.getMetadataClassDefinition('classification')
        self.setMetadataClassDefinition('classificationResampled', classes=classes, classNames=classNames, classLookup=classLookup)


if __name__ == '__main__':
    script()
