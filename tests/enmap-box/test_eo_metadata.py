import tempfile
import unittest
from pathlib import Path
from typing import Tuple

import numpy as np
from osgeo import gdal, gdal_array
from osgeo.osr import SpatialReference

from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from enmapbox.testing import start_app, TestCase
from enmapboxprocessing.rasterreader import RasterReader
from qgis.core import QgsRasterLayer

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
        self.assertEqual(reader.bandCount(), layer.bandCount())
        for b in range(1, reader.bandCount() + 1):
            self.assertEqual(reader.wavelength(b), None)
            self.assertEqual(reader.fwhm(b), None)
            self.assertEqual(reader.wavelengthUnits(b), None)
            self.assertEqual(reader.badBandMultiplier(b), 1)  # todo: None = undefined or 1 as default if undefined?

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
        ds, path = self.createTestImage('gdal_imagery.tif')

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

    def test_classic_envi_domain(self):
        ds, path = self.createTestImage('gdal_envi_dataset_domain.bsq', format='ENVI')

        wl = [400, 500]
        fwhm = [2.3, 3.4]
        wlu = ['nm', 'nm']

        ds.SetMetadataItem('wavelength', self.wrapEnviList(wl), 'ENVI')
        ds.SetMetadataItem('wavelength units', wlu[0], 'ENVI')
        ds.SetMetadataItem('fwhm', self.wrapEnviList(fwhm), 'ENVI')

        del ds

        layer = QgsRasterLayer(path.as_posix())
        prop = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertWavelengthsEqual(prop.wavelengths(), prop.wavelengthUnits(),
                                    wl, wlu)
        self.assertWavelengthsEqual(prop.fwhm(), prop.wavelengthUnits(),
                                    fwhm, wlu, precision=3)

        reader = RasterReader(layer)
        for b in range(layer.bandCount()):
            wl1 = reader.wavelength(b + 1, units=reader.wavelengthUnits(b + 1))
            wlu1 = reader.wavelengthUnits(b + 1)
            wl2 = wl[b]
            wlu2 = wlu[b]
            self.assertWavelengthsEqual(wl1, wlu1,
                                        wl2, wlu2, precision=3)

    def test_overwrite_by_custom_properties(self):

        ds, path = self.createTestImage('gdal_overwrite_custom_props.tif')

        wl = [0.2, 0.4]
        fwhm = [0.0003, 0.0009]
        for b, (_wl, _fwhm) in enumerate(zip(wl, fwhm), start=1):
            band: gdal.Band = ds.GetRasterBand(b)
            band.SetMetadataItem('CENTRAL_WAVELENGTH_UM', str(_wl), 'IMAGERY')
            band.SetMetadataItem('FWHM_UM', str(_fwhm), 'IMAGERY')
        del ds

        layer = QgsRasterLayer(path.as_posix())
        propsOriginal = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertEqual(propsOriginal.wavelengths(), wl)
        self.assertEqual(propsOriginal.fwhm(), fwhm)
        self.assertEqual(propsOriginal.wavelengthUnits(), ['μm', 'μm'])

        reader = RasterReader(layer)
        for b in range(1, layer.bandCount() + 1):
            # todo: Raster Reader support for GDAL metadata
            # self.assertEqual(reader.wavelength(b), wl[b - 1])
            # self.assertEqual(reader.fwhm(b), fwhm[b - 1])
            # self.assertTrue(reader.wavelengthUnits(b) in ['μm', 'Micrometers'])
            pass

        # overwrite properties via setCustomProperty
        wl2 = [400, 500]
        wlu2 = ['nm', 'nm']
        fwhm2 = [1, 2]

        layer.setCustomProperty('enmapbox/wavelengths', wl2)
        layer.setCustomProperty('enmapbox/wavelength_units', wlu2)
        layer.setCustomProperty('enmapbox/fwhm', fwhm2)

        propsChanged = QgsRasterLayerSpectralProperties.fromRasterLayer(layer)
        self.assertEqual(propsChanged.wavelengths(), wl2)
        self.assertEqual(propsChanged.fwhm(), fwhm2)
        self.assertEqual(propsChanged.wavelengthUnits(), wlu2)

        reader = RasterReader(layer)
        for b in range(1, layer.bandCount() + 1):
            # todo: raster reader test
            pass


if __name__ == '__main__':
    unittest.main()
