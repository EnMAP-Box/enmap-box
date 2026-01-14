from osgeo import gdal
from _classic.hubdc import PixelGrid, Applier, ApplierInput, ApplierOutput, ApplierOperator

def script():

    # use grid from input file, but enlarge the resolution to 300 meter
    grid = PixelGrid.fromFile(r'C:\Work\data\gms\LC81940242015235LGN00_sr.img')
    grid.xRes = grid.yRes = 3000
    applier = Applier(grid=grid, ufuncClass=MyOperator, nworker=1, nwriter=2, windowxsize=256, windowysize=256)
    applier['inList'] = ApplierInput(filename=[r'C:\Work\data\gms\LC81940242015235LGN00_sr.img',
                                               r'C:\Work\data\gms\LE71940242015275NSG00_sr.img'])

    applier['outList'] = ApplierOutput(filename=[r'c:\output\list_LC81940242015235LGN00_sr.img',
                                                 r'c:\output\list_LE71940242015275NSG00_sr.img'],
                                       format='ENVI', creationOptions=['INTERLEAVE=BSQ'])

    applier.run()

class MyOperator(ApplierOperator):

    def ufunc(self):

        for i, sr in enumerate(self.getArrayIterator('inList')):
            self.setData(('outList', i), array=sr)

    def umeta(self):
        self.setMetadataItem(('outList', 0), key='my value', value=41, domain='ENVI')
        self.setMetadataItem(('outList', 1), key='my value', value=42, domain='ENVI')

if __name__ == '__main__':
    script()
