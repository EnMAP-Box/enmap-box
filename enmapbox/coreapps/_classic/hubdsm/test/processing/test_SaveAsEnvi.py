import numpy as np
from qgis.core import QgsRasterLayer

from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.processing.saveasenvi import SaveAsEnvi
from _classic.hubdsm.test.processing.testcase import TestCase


class TestSaveAsEnvi(TestCase):

    def test(self):
        filename = '/vsimem/r1.bsq'
        array = np.array([[[0]], [[1]], [[10]]])
        gdalRaster = GdalRaster.createFromArray(array=array, filename=filename)
        gdalRaster.setMetadataItem(key='wavelength', value=[1, 2, 3], domain='ENVI')
        gdalRaster.setMetadataItem(key='wavelength_units', value='nanometers', domain='ENVI')
        gdalRaster.setMetadataItem(key='myKey', value='hello', domain='ENVI')
        gdalRaster.setNoDataValue(value=-9999)
        categories = [
            Category(id=1, name='class 1', color=Color(255, 0, 0)),
            Category(id=10, name='class 10', color=Color(0, 255, 0))
        ]
        gdalRaster.setCategories(categories=categories)
        for gdalBand, name in zip(gdalRaster.bands, ['b1', 'b2', 'b3']):
            gdalBand.setDescription(name)
        del gdalRaster

        layer = QgsRasterLayer(filename)

        alg = SaveAsEnvi()
        io = {
            alg.P_RASTER: layer,
            alg.P_OUTRASTER: '/vsimem/r2.bsq',
        }
        result = self.runalg(alg=alg, io=io)

        gdalRaster2 = GdalRaster.open(result[alg.P_OUTRASTER])
        self.assertTrue(np.all(array == gdalRaster2.readAsArray()))
        self.assertListEqual([1, 2, 3], gdalRaster2.metadataItem(key='wavelength', domain='ENVI', dtype=int))
        self.assertEqual('nanometers', gdalRaster2.metadataItem(key='wavelength units', domain='ENVI'))
        self.assertEqual('hello', gdalRaster2.metadataItem(key='myKey', domain='ENVI'))
        self.assertEqual(-9999, gdalRaster2.band(1).noDataValue)
        self.assertListEqual(categories, gdalRaster2.categories)
