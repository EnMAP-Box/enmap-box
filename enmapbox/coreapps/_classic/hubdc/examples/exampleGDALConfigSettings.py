from _classic.hubdc import PixelGrid, Applier, ApplierOperator
import _classic.hubdc.applier.Applier

def script():

    #filename = r'H:\EuropeanDataCube\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_sr_band1.img'
    filename = r'C:\Work\data\gms\LC81940242015235LGN00_sr_band1.img'

    grid = PixelGrid(projection='EPSG:3035', xRes=100, yRes=100, xMin=4400000, xMax=4440000, yMin=3150000, yMax=3200000)
    applier = Applier()
    applier.controls.setGDALCacheMax(bytes=1000*2**20)
    applier.controls.setGDALSwathSize(bytes=1000*2**20)
    applier.controls.setGDALDisableReadDirOnOpen(disable=True)
    applier.controls.setGDALMaxDatasetPoolSize(nfiles=1000)
    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):

    def ufunc(self):
        self.setData('out', array=self.getArray('in'))

if __name__ == '__main__':
    script()
