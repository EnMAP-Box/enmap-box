import tempfile
import unittest
from pathlib import Path

from qgis.core import QgsMultiBandColorRenderer, QgsProject, QgsRasterLayer
from qgis.gui import QgsMapCanvas
from enmapbox.gui.datasources.manager import DataSourceManagerTreeView
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.qgispluginsupport.qps.qgsrasterlayerproperties import QgsRasterLayerSpectralProperties
from enmapbox.testing import EnMAPBoxTestCase, start_app, TestObjects
from qgis.PyQt.QtWidgets import QTreeView

start_app()


class TestIssue478(EnMAPBoxTestCase):

    def test_issue478(self):
        # https://bitbucket.org/hu-geomatics/enmap-box/issues/478/visualization-of-single-band-fails
        # test if sources can be opened in a new map
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        from enmapbox.exampledata import enmap

        EB.addSource(enmap)
        wms = TestObjects.uriWMS()
        EB.addSource(wms)
        tv = EB.dataSourceManagerTreeView()
        self.assertIsInstance(tv, DataSourceManagerTreeView)
        for src in EB.dataSourceManager().dataSources('RASTER'):
            self.assertIsInstance(tv, QTreeView)
            tv.openInMap(src, rgb=[0])

        self.showGui(EB.ui)
        EB.close()
        QgsProject.instance().removeAllMapLayers()

    def test_issue1088(self):
        with tempfile.TemporaryDirectory() as tdir:
            path = Path(tdir) / 'example.bsq'
            ds = TestObjects.createRasterDataset(2, 2, nb=5, drv='ENVI', path=path, add_wl=False)
            self.assertEqual(ds.GetDriver().ShortName, 'ENVI')
            # set B,G,R,NIR,SWIR bands, but no wavelength unit
            ds.SetMetadataItem('wavelength', '{450,550,650,800,1600}', 'ENVI')
            del ds

            props = QgsRasterLayerSpectralProperties.fromRasterLayer(path)
            assert props.wavelengthUnits()[0] == 'nm'

            lyr1 = QgsRasterLayer(path.as_posix())
            dtv = DataSourceManagerTreeView()
            canvas = QgsMapCanvas()
            lyr2 = dtv.openInMap(lyr1, target=canvas, rgb='R,G,B')

            self.assertEqual(lyr1, lyr2)
            renderer: QgsMultiBandColorRenderer = lyr2.renderer()
            self.assertEqual(renderer.usesBands(), [3, 2, 1])
            del lyr1, lyr2, renderer


if __name__ == '__main__':
    unittest.main(buffer=False)
