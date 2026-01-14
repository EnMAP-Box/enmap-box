from osgeo import gdal
from _classic.hubdc import PixelGrid, Applier, ApplierInput, ApplierOutput, ApplierOperator
from _classic.hubdc.landsat.LandsatArchiveParser import LandsatArchiveParser

def script():

    # define grid
    grid = PixelGrid(projection='EPSG:3035', xRes=100, yRes=100, xMin=4400000, xMax=4440000, yMin=3150000, yMax=3200000)

    # parse landsat archive for filenames
    cfmask, red, nir = LandsatArchiveParser.getFilenames(archive=r'C:\Work\data\gms\landsat',
                                                         footprints=['194024'], names=['cfmask', 'red', 'nir'])

    # setup and apply _applier
    applier = Applier(grid=grid, ufuncClass=NDVICompositor, nworker=1, nwriter=1, windowxsize=256, windowysize=256)
    applier['cfmask'] = ApplierInput(cfmask, resampleAlg=gdal.GRA_Mode, errorThreshold=0.)
    applier['red'] = ApplierInput(red, resampleAlg=gdal.GRA_Average, errorThreshold=0.)
    applier['nir'] = ApplierInput(nir, resampleAlg=gdal.GRA_Average, errorThreshold=0.)
    applier['ndvi'] = ApplierOutput(r'c:\output\ndvi.img', format='ENVI', creationOptions=[])
    applier.run()

class NDVICompositor(ApplierOperator):

    def ufunc(self):
        from numpy import float32, full, nan

        normalizedDifference = lambda a, b: (a-b)/(a+b)

        ysize, xsize = self.grid.getDimensions()
        ndvi = full((1, ysize, xsize), fill_value=nan, dtype=float32)

        for cfmask, red, nir in zip(self.getArrayIterator('cfmask'),
                                    self.getArrayIterator('red', dtype=float32),
                                    self.getArrayIterator('nir', dtype=float32)):
            valid = cfmask == 0
            ndvi[valid] = normalizedDifference(nir[valid], red[valid])

        self.setData('ndvi', array=ndvi)

    def umeta(self, *args, **kwargs):
        self.setMetadataItem('ndvi', 'my value', 42, 'ENVI')

if __name__ == '__main__':
    script()
