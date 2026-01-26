from _classic.hubdc import PixelGrid, Applier, ApplierOperator, ApplierOutput
from _classic.hubdc.gis.mgrs import getMGRSPixelGridsByNames

LANDSAT_ANCHOR = (15, 15)
SENTINEL_ANCHOR = (0, 0)

def script():

    applier = Applier(ufuncClass=RandomImage, nworker=2, nwriter=2, windowxsize=256, windowysize=256)

    for name, grid in getMGRSPixelGridsByNames(names=['32UPC', '32UQC', '33UTT', '33UUT'], res=30, anchor=LANDSAT_ANCHOR, buffer=300):

        print('Apply '+name)
        applier.setPixelGrid(grid)
        applier['out'] = ApplierOutput(r'c:\output\random{name}.img'.format(name=name), format='GTiff')
        applier.run()

    applier.close()

class RandomImage(ApplierOperator):

    def ufunc(self):
        import numpy
        ysize, xsize = self.grid.getDimensions()
        randomImage = numpy.random.random_integers(low=0, high=255, size=(1, ysize, xsize))
        self.setData('out', array=randomImage, dtype=numpy.uint8)

if __name__ == '__main__':
    script()

