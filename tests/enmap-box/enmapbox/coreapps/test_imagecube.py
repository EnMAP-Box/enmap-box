import os
import unittest
import uuid

import numpy as np
from osgeo import gdal, gdal_array

from enmapbox import initAll
from enmapbox.exampledata import enmap as pathEnMAP
from enmapbox.exampledata import hires as pathHyMap
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects
from qgis.core import QgsRasterLayer, QgsProject, QgsRasterRenderer, QgsRectangle, QgsCoordinateReferenceSystem

start_app()
initAll()

HAS_OPENGL = False
try:
    from imagecubeapp.imagecube import samplingGrid, ImageCubeWidget, GLItem, ImageCubeRenderTask

    HAS_OPENGL = True
except ModuleNotFoundError as ex:
    if ex.name == 'OpenGL':
        raise unittest.SkipTest('Missing OpenGL module. Skip all imagecube tests')
    else:
        raise ex


# @unittest.skipIf(not HAS_OPENGL, 'Missing OpenGL module. Skip all imagecube tests')
class ImageCubeTests(EnMAPBoxTestCase):

    def createImageCube(self, nb=10, ns=20, nl=30, crs='EPSG:32633') -> QgsRasterLayer:

        path = f'/vsimem/imagecube{uuid.uuid4()}.tiff'

        array = np.fromfunction(lambda i, j, k: i + j + k, (nb, nl, ns), dtype=np.uint32)
        # array = array * 10
        drv = gdal.GetDriverByName('GTiff')
        eType = gdal_array.NumericTypeCodeToGDALTypeCode(array.dtype)
        ds = drv.Create(path, ns, nl, bands=nb, eType=eType)
        if isinstance(crs, str):
            c = QgsCoordinateReferenceSystem(crs)
            ds.SetProjection(c.toWkt())
        ds.SetGeoTransform([0, 1.0, 0,
                            0, 0, -1.0])

        for b in range(nb):
            band = ds.GetRasterBand(b + 1)
            band.WriteArray(array[b, :, :])

        ds.FlushCache()

        lyr = QgsRasterLayer(path, 'image_cube', 'gdal')
        if not lyr.isValid():
            raise RuntimeError(f'Failed to load raster layer: {path}')

        return lyr

    def test_extent_mini(self):
        QgsRasterLayer(pathEnMAP)
        # self.assertTrue(lyrCube.isValid())
        W = ImageCubeWidget(

        )
        W.show()
        # self.showGui(W)

        # del lyrCube
        return

    def test_samplingGrid(self):

        from enmapbox.exampledata import enmap as pathEnMAP
        lyr = QgsRasterLayer(pathEnMAP)

        ext1 = lyr.extent()
        ns, nl = lyr.width(), lyr.height()
        cache = 1024 ** 4
        nnl, nns = samplingGrid(lyr, ext1, ncb=3, max_size=cache)
        self.assertIsInstance(nnl, int)
        self.assertIsInstance(nns, int)
        self.assertTrue(nnl >= 0 and nns >= 0)
        self.assertTrue(nnl == nl and nns == ns)

        # reduce cache
        nnl, nns = samplingGrid(lyr, ext1, ncb=3, max_size=1024 * 2)
        self.assertTrue(nnl < nl and nns < ns)

        f1 = ext1.width() / ext1.height()
        f2 = nns / nnl
        self.assertAlmostEqual(f1, f2, 1)

    def test_widget2(self):

        project = QgsProject()

        W = ImageCubeWidget()
        W.setProject(project)
        W.show()

        lyrCube = self.createImageCube(ns=100, nl=200)
        layers = [lyrCube]
        pathes = [pathEnMAP, pathHyMap]
        for p in pathes:
            if os.path.isfile(p):
                layers.append(QgsRasterLayer(p, os.path.basename(p)))

        project.addMapLayers(layers)

        if True:
            lyr = layers[0]
            self.assertIsInstance(lyr, QgsRasterLayer)
            W.setRasterLayer(lyr)
            self.assertEqual(lyr, W.rasterLayer())

            x = int(lyr.width() * 0.5)
            y = int(lyr.height() * 0.5)
            z = int(lyr.bandCount() * 0.5)
            W.setX(x)
            W.setY(y)
            W.setZ(z)

            # W.setZSCale(2)
            # self.assertEqual(W.zScale(), 2)
            # W.setZSCale(2)
            self.assertEqual(W.x(), x)
            self.assertEqual(W.y(), y)
            self.assertEqual(W.z(), z)

            W.setZScale(1.8)
            self.assertEqual(1.8, W.zScale())
            W.setZScale(1.9)
            self.assertEqual(1.9, W.zScale())
            W.setZScale(2)
            self.assertEqual(2, W.zScale())
            W.setZScale(1)
            self.assertIsInstance(W.sliceRenderer(), QgsRasterRenderer)
            self.assertIsInstance(W.topPlaneRenderer(), QgsRasterRenderer)

            ext1 = lyr.extent()
            self.assertEqual(ext1, W.extent())
            self.assertEqual(lyr.crs(), W.crs())
            ext2 = QgsRectangle(ext1)
            ext2.setXMinimum(ext2.xMinimum() - 5)

            W.setExtent(ext2)
            self.assertEqual(W.extent(), ext2)

        if True:
            W.setRasterLayer(layers[0])
            W.startDataLoading()

        self.showGui(W)
        del W
        src = lyrCube.source()
        project.removeAllMapLayers()
        gdal.Unlink(src)

    def test_noLayers(self):

        w = ImageCubeWidget()
        self.showGui(w)
        del w
        QgsProject.instance().removeAllMapLayers()

    def test_rendertask(self):
        layer: QgsRasterLayer = TestObjects.createRasterLayer()

        task = ImageCubeRenderTask(GLItem.TopPlane, layer)
        self.assertTrue(task.run(), msg=f'Failed to run task: {task.mError}')
        self.assertIsInstance(task.mRGBA2D, np.ndarray)
        self.assertTrue(task.mRGBA3D is None)

        task = ImageCubeRenderTask(GLItem.Cube, layer)
        self.assertTrue(task.run(), msg=f'Failed to run task: {task.mError}')
        self.assertIsInstance(task.mRGBA3D, np.ndarray)
        self.assertTrue(task.mRGBA2D is None)

    def test_extent(self):

        project = QgsProject()

        W = ImageCubeWidget()
        W.setProject(project)
        W.show()

        from enmapbox.exampledata import enmap as pathEnMAP
        from enmapbox.exampledata import hires as pathHyMap

        lyrCube = self.createImageCube(nb=177, ns=200, nl=400)
        layers = [lyrCube]
        # layers = []
        for p in [pathEnMAP, pathHyMap]:
            if os.path.isfile(p):
                layers.append(QgsRasterLayer(p, os.path.basename(p)))

        project.addMapLayers(layers)

        W.cbShowCube.setChecked(False)
        W.cbShowSliceX.setChecked(False)
        W.cbShowSliceY.setChecked(True)
        W.cbShowSliceZ.setChecked(False)

        lyr = layers[0]
        self.assertIsInstance(lyr, QgsRasterLayer)
        W.setRasterLayer(lyr)
        self.assertEqual(lyr, W.rasterLayer())

        x = int(lyr.width() * 0.5)
        y = int(lyr.height() * 0.5)
        z = int(lyr.bandCount() * 0.5)
        W.setX(x)
        W.setY(y)
        W.setZ(z)
        W.cbShowTopPlane.setChecked(False)
        ext1 = lyr.extent()
        self.assertIsInstance(ext1, QgsRectangle)
        w = ext1.width()
        h = ext1.height()

        if True:
            cut = 0.1
            x0 = ext1.xMinimum() + w * cut
            x1 = ext1.xMaximum() - 2 * w * cut
            y0 = ext1.yMinimum() + h * cut
            y1 = ext1.yMaximum() - 2 * h * cut
            ext2 = QgsRectangle(x0, y0, x1, y1)
            W.setExtent(ext2)
        W.startDataLoading()

        self.showGui(W)

        src = lyrCube.source()
        del W
        QgsProject.instance().removeAllMapLayers()
        gdal.Unlink(src)


if __name__ == "__main__":
    unittest.main(buffer=False)
