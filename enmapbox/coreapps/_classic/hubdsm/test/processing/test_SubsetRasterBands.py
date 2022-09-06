import numpy as np
from qgis.core import QgsRasterLayer

from enmapbox.exampledata import enmap
from _classic.hubdsm.core.gdaldriver import MEM_DRIVER
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.processing.subsetrasterbands import SubsetRasterBands
from _classic.hubdsm.test.processing.testcase import TestCase


class TestSubsetRasterBands(TestCase):

    def test_parseNumbers(self):
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[0]], [[10]], [[20]]]))
        gdalRaster.setMetadataItem('wavelength', [100, 200, 300], domain='ENVI')

        # for empty text return all bands
        self.assertListEqual(SubsetRasterBands.parseNumbers(text='', gdalRaster=gdalRaster, excludeBadBands=False),
            [1, 2, 3])

        # single band
        self.assertListEqual(SubsetRasterBands.parseNumbers(text='2', gdalRaster=gdalRaster, excludeBadBands=False),
            [2])

        # two bands
        self.assertListEqual(SubsetRasterBands.parseNumbers(text='1, 3', gdalRaster=gdalRaster, excludeBadBands=False),
            [1, 3])

        # single waveband
        self.assertListEqual(SubsetRasterBands.parseNumbers(text='90.', gdalRaster=gdalRaster, excludeBadBands=False),
            [1])

        # band / waveband mix
        self.assertListEqual(
            SubsetRasterBands.parseNumbers(text='90., 2, 310.', gdalRaster=gdalRaster, excludeBadBands=False), [1, 2, 3]
        )

        # single number range
        self.assertListEqual(
            SubsetRasterBands.parseNumbers(text='2 3', gdalRaster=gdalRaster, excludeBadBands=False), [2, 3]
        )

        # single waveband range
        self.assertListEqual(
            SubsetRasterBands.parseNumbers(text='190. 310.', gdalRaster=gdalRaster, excludeBadBands=False), [2, 3]
        )

        # single number/waveband range mix
        self.assertListEqual(
            SubsetRasterBands.parseNumbers(text='2 310.', gdalRaster=gdalRaster, excludeBadBands=False), [2, 3]
        )

        # mix everything
        self.assertListEqual(
            SubsetRasterBands.parseNumbers(
                text='3, 200., 1, 1 3, 0. 500.',
                gdalRaster=gdalRaster,
                excludeBadBands=False),
            [3, 2, 1, 1, 2, 3, 1, 2, 3]
        )

        # out of range exception
        try:
            SubsetRasterBands.parseNumbers(text='0', gdalRaster=gdalRaster, excludeBadBands=False)
        except AssertionError as error:
            self.assertEqual(str(error), 'number out of range: 0')
        try:
            SubsetRasterBands.parseNumbers(text='4', gdalRaster=gdalRaster, excludeBadBands=False)
        except AssertionError as error:
            self.assertEqual(str(error), 'number out of range: 4')

        # error if wavelength not specified
        gdalRaster = MEM_DRIVER.createFromArray(array=np.array([[[0]], [[10]], [[20]]]))
        try:
            SubsetRasterBands.parseNumbers(text='0.', gdalRaster=gdalRaster, excludeBadBands=False)
        except ValueError as error:
            self.assertEqual(str(error), 'raster band center wavelength is undefined')

    def test(self):
        raster = Raster.open(enmap)
        alg = SubsetRasterBands()
        io = {
            alg.P_RASTER: QgsRasterLayer(enmap),
            alg.P_EXCLUDE_BAB_BANDS: False,
            alg.P_OUTPUT_RASTER: 'c:/vsimem/raster2.vrt'
        }

        # subset first band
        io[alg.P_NUMBERS] = '1'
        result = self.runalg(alg=alg, io=io)
        raster2 = Raster.open(result[alg.P_OUTPUT_RASTER])
        self.assertEqual(raster.band(1).wavelength, raster2.band(1).wavelength)
        self.assertEqual(raster.band(1).fwhm, raster2.band(1).fwhm)
        self.assertEqual(raster.band(1).isBadBand, raster2.band(1).isBadBand)
        gold = raster.band(1).metadataDomain()
        lead = raster2.band(1).metadataDomain()
        self.assertDictEqual(gold, lead)
