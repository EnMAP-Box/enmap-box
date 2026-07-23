from osgeo import gdal, ogr
from _classic.hubdc import Applier, ApplierOperator, ApplierInput, ApplierOutput
from _classic.hubdc.gis.mgrs import getMGRSPixelGridsByShape
from _classic.hubdc.gis.wrs2 import getWRS2NamesInsidePixelGrid
from _classic.hubdc.landsat.LandsatArchiveParser import LandsatArchiveParser

LANDSAT_ANCHOR = (15, 15)

def script():

    germany = getCountry('Germany')
    #germany = getCountry('Luxembourg')

    roi = getCountry('United States')

    applier = Applier(ufuncClass=RandomImage, nworker=1, nwriter=30, windowxsize=256, windowysize=256)

    for mgrsFootprint, grid in getMGRSPixelGridsByShape(shape=roi, res=30, anchor=LANDSAT_ANCHOR, buffer=30):

        wrs2Footprints = getWRS2NamesInsidePixelGrid(grid=grid)

        import os
        if os.path.exists(r'c:\output\random{mgrsFootprint}.img'.format(mgrsFootprint=mgrsFootprint)):
            continue

        print('Apply {mgrsFootprint} ({wrs2Footprints})'.format(mgrsFootprint=mgrsFootprint, wrs2Footprints=', '.join(wrs2Footprints)))
        applier.setPixelGrid(grid)
        applier['out'] = ApplierOutput(r'c:\output\random{mgrsFootprint}.img'.format(mgrsFootprint=mgrsFootprint), format='GTiff')
        applier.run()
        print('---')

    applier.close()

class RandomImage(ApplierOperator):

    def ufunc(self):
        import numpy
        ysize, xsize = self.grid.getDimensions()
        image = numpy.random.random_integers(low=0, high=255, size=(1, ysize, xsize))
        self.setData('out', array=image, dtype=numpy.uint8)


def getCountry(name):
    ds = ogr.Open(r'C:\Work\data\gms\gis\countries\countries.shp')
    layer = ds.GetLayer()
    for feature in layer:
        if feature.GetField('name') == name:
            geometry = feature.GetGeometryRef()
            geometry = geometry.Clone()
            break
    ds = None
    return geometry


if __name__ == '__main__':
    from timeit import default_timer
    t0 = default_timer()
    script()
    s = (default_timer() - t0)
    m = s / 60
    h = m / 60
    print('done in {s} sec | {m}  min | {h} hours'.format(s=int(s), m=round(m, 2), h=round(h, 2)))
