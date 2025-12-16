import os
import unittest

from enmapbox import initAll
from enmapbox.exampledata import enmap as pathEnMAP
from enmapbox.testing import EnMAPBoxTestCase, start_app
from imagecubeapp.imagecube import ImageCubeWidget
from qgis.core import QgsRasterLayer

start_app()
initAll()


class ImageCubeTestsMinimal(EnMAPBoxTestCase):

    @unittest.skipIf(os.environ.get('QT_QPA_PLATFORM') == 'offscreen', "missing OpenGL")
    def test_extent_mini(self):
        lyrCube = QgsRasterLayer(pathEnMAP)
        # self.assertTrue(lyrCube.isValid())
        W = ImageCubeWidget(

        )
        W.show()
        # self.showGui(W)

        # del lyrCube
        return


if __name__ == "__main__":
    unittest.main(buffer=False)
