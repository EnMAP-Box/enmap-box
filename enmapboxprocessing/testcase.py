from os.path import join
from typing import Union

import numpy as np
from qgis.core import QgsCoordinateReferenceSystem, QgsRectangle

import enmapbox.testing
from enmapbox.typeguard import typechecked
from enmapboxprocessing.driver import Driver
from enmapboxprocessing.rasterwriter import RasterWriter
from enmapboxprocessing.typing import Array2d, Array3d, Number

enmapbox.testing.start_app()


@typechecked
class TestCase(enmapbox.testing.TestCase):

    def assertArrayEqual(self, array1: Union[Number, Array2d, Array3d], array2: Union[Array2d, Array3d]):
        array1 = np.array(array1)
        array2 = np.array(array2)
        self.assertTrue(np.all(array1 == array2))

    def createTestOutputFolder(self):
        return str(self.createTestOutputDirectory())

    def filename(self, basename: str):
        return join(self.createTestOutputFolder(), basename)

    def rasterFromArray(
            self, array, basename: str = None, extent: QgsRectangle = None, crs: QgsCoordinateReferenceSystem = None
    ) -> RasterWriter:
        if basename is None:
            basename = f'temp/{np.random.randint(0, 999999999)}.tif'

        filename = self.filename(basename)
        writer = Driver(filename).createFromArray(np.array(array), extent, crs)
        return writer

    def rasterFromRange(
            self, shape, basename: str = None, extent: QgsRectangle = None, crs: QgsCoordinateReferenceSystem = None
    ) -> RasterWriter:
        array = np.reshape(range(np.prod(shape)), shape)
        return self.rasterFromArray(array, basename, extent, crs)

    def rasterFromValue(
            self, shape, value, basename: str = None, extent: QgsRectangle = None,
            crs: QgsCoordinateReferenceSystem = None
    ) -> RasterWriter:
        array = np.full(shape, value)
        return self.rasterFromArray(array, basename, extent, crs)
