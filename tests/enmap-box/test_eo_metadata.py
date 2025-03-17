import tempfile
import unittest
from pathlib import Path
from typing import Tuple

import numpy as np
from osgeo import gdal, gdal_array
from osgeo.osr import SpatialReference
from qgis._core import QgsRasterLayer

from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from enmapbox.testing import TestCase, start_app
from enmapboxprocessing.rasterreader import RasterReader

start_app()


class EOMetadataReadingTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mTestDir = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.mTestDir.cleanup()

    def createTestImage(self, basename: str, format: str = 'GTiff') -> Tuple[gdal.Dataset, Path]:
        gt = [0, 0.25, 0,
              0, 0, -0.25]
        sref = SpatialReference()
        sref.ImportFromEPSG(4326)
        sref.Validate()
        shape = (2, 2, 5)
        array = np.arange(np.prod(shape)).reshape(shape)

        path = Path(self.mTestDir.name) / f'{basename}'
        self.assertFalse(path.exists(), msg=f'File {path} already exists')
        ds: gdal.Dataset = gdal_array.SaveArray(array, path.as_posix(), format=format)
        self.assertIsInstance(ds, gdal.Dataset)

        ds.SetGeoTransform(gt)
        ds.SetSpatialRef(sref)

        return ds, path

    @staticmethod
    def wrapEnviList(values: list):
        values = ','.join([str(v) for v in values])
        return f'{{{values}}}'

    def test_no_metadata(self):
        ds, path = self.createTestImage('no_metadata.tif')
        del ds

        layer = QgsRasterLayer(path.as_posix())
        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertIsInstance(prop, QgsRasterLayerSpectralProperties)
        self.assertEqual(prop.bandCount(), layer.bandCount())
        self.assertEqual(prop.wavelengths(), [None, None])
        self.assertEqual(prop.wavelengthUnits(), [None, None])
        self.assertEqual(prop.fwhm(), [None, None])
        self.assertEqual(prop.badBands(), [None, None])
        self.assertEqual(prop.badBands(default=1), [1, 1])

        # RasterReader tests
        reader = RasterReader(layer)
        self.assertEqual(reader.bandCount(), ds.RasterCount)
        for b in range(1, reader.bandCount() + 1):
            self.assertEqual(reader.wavelength(b), None)
            self.assertEqual(reader.fwhm(b), None)
            self.assertEqual(reader.wavelengthUnits(b), None)
            self.assertEqual(reader.badBandMultiplier(b), 1)  # todo: None = undefined or 1 as default if undefined?

        self.assertEqual(True, False)  # add assertion here

    def test_layer_custom_properties_only(self):

        ds, path = self.createTestImage('no_metadata2.tif')
        del ds

        wavelengths = [400, 500]
        fwhm = [0.1, 0.2]
        bbl = [1, 0]

        layer = QgsRasterLayer(path.as_posix())
        layer.setCustomProperty('enmapbox/wavelength', wavelengths)
        layer.setCustomProperty('enmapbox/fwhm', fwhm)
        layer.setCustomProperty('enmapbox/bbl', bbl)

        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertEqual(prop.wavelengths(), wavelengths)
        self.assertEqual(prop.wavelengthUnits(), ['nm', 'nm'])
        self.assertEqual(prop.fwhm(), fwhm)
        self.assertEqual(prop.badBands(), bbl)

        # define metadata as dictionary
        wl = [400, 0.5]
        wlu = ['μm', 'nm']

        # use dictionaries to define band-specific values instead lists
        # numeric keys represent band numbers
        wl_dict = {b + 1: v for b, v in enumerate(wl)}
        wl_dict['foo'] = 'bar'

        wlu_dict = {b + 1: v for b, v in enumerate(wlu)}
        wlu_dict['sna'] = 'fu'

        layer.setCustomProperty('enmapbox/wavelength', wl_dict)
        layer.setCustomProperty('enmapbox/wavelength_unit', wlu_dict)

        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertEqual(prop.wavelengths(), wl)
        self.assertEqual(prop.wavelengthUnits(), wlu)

        reader = RasterReader(layer)
        for b in range(layer.bandCount()):
            pass
            # todo: raster reader tests
            # self.assertEqual(reader.wavelength(b + 1), wl[b])
            # self.assertEqual(reader.wavelengthUnits(b + 1), wlu[b])

    def test_wl_um_gdal_imagery_domain(self):
        #
        # wavelength according to GDAL metadata mode
        # see https://gdal.org/en/stable/user/raster_data_model.html#imagery-domain-remote-sensing
        ds, path = self.createTestImage('no_metadata.tif')

        wavelengths = [0.2, 0.4]
        fwhm = [0.0003, 0.0009]
        for b, (wl, fw) in enumerate(zip(wavelengths, fwhm), start=1):
            band: gdal.Band = ds.GetRasterBand(b)
            band.SetMetadataItem('CENTRAL_WAVELENGTH_UM', str(wl), 'IMAGERY')
            band.SetMetadataItem('FWHM_UM', str(fw), 'IMAGERY')
        del ds

        layer = QgsRasterLayer(path.as_posix())

        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertIsInstance(prop, QgsRasterLayerSpectralProperties)
        self.assertEqual(prop.bandCount(), layer.bandCount())
        self.assertEqual(prop.wavelengths(), wavelengths)
        self.assertEqual(prop.wavelengthUnits(), ['μm', 'μm'])
        self.assertEqual(prop.fwhm(), fwhm)

        for b in range(1, layer.bandCount() + 1):
            # todo: raster reader tests
            pass


if __name__ == '__main__':
    unittest.main()
