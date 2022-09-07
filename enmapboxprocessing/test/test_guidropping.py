import pathlib
from os.path import exists
from warnings import warn

from enmapbox import EnMAPBox
from enmapbox.gui.dataviews.docks import MapDock
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtCore import QMimeData, QUrl, QPoint, Qt
from qgis.PyQt.QtGui import QDropEvent
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsProject, QgsRasterLayer


class TestGuiDropping(EnMAPBoxTestCase):

    def setUp(self):

        super().setUp()
        box = EnMAPBox.instance()
        if isinstance(box, EnMAPBox):
            box.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def tearDown(self):
        super().tearDown()
        box = EnMAPBox.instance()
        if isinstance(box, EnMAPBox):
            box.close()
        QApplication.processEvents()
        QgsProject.instance().removeAllMapLayers()

    def file2DropEvent(self, path) -> QDropEvent:
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        md = QMimeData()
        md.setUrls([QUrl.fromLocalFile(path.as_posix())])
        print('Drop {}'.format(path.name))
        self._mdref = md
        return QDropEvent(QPoint(0, 0), Qt.CopyAction, md, Qt.LeftButton, Qt.NoModifier)

    def test_dropping_external_products_on_empty_dockarea(self):
        filenames = [
            r'D:\data\sensors\desis\DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210\DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210-METADATA.xml',
            r'D:\data\sensors\desis\DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210\DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210-METADATA.xml',
            r'D:\data\sensors\desis\DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210\DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210-METADATA.xml',
            r'D:\data\sensors\enmap\L1B_Arcachon_3\ENMAP01-____L1B-DT000400126_20170218T110119Z_003_V000204_20200508T124425Z-METADATA.XML',
            r'D:\data\sensors\enmap\L1C_Arcachon_3\ENMAP01-____L1C-DT000400126_20170218T110119Z_003_V000204_20200510T095443Z-METADATA.XML',
            r'D:\data\sensors\enmap\L2A_Arcachon_3_combined\ENMAP01-____L2A-DT000400126_20170218T110119Z_003_V000204_20200512T142942Z-METADATA.XML',
            r'D:\data\sensors\landsat\C1L2\LC080140322019033001T1-SC20190517105817\LC08_L1TP_014032_20190330_20190404_01_T1_MTL.txt',
            r'D:\data\sensors\prisma\PRS_L1_STD_OFFL_20201107101404_20201107101408_0001.he5',
            r'D:\data\sensors\prisma\PRS_L2D_STD_20201107101404_20201107101408_0001.he5',
            r'D:\data\sensors\sentinel2\S2A_MSIL2A_20200816T101031_N0214_R022_T32UQD_20200816T130108.SAFE\MTD_MSIL2A.xml'
        ]
        filenames2 = [

            r'D:/data/sensors/desis/DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210/DESIS-HSI-L1B-DT1203190212_025-20191203T021128-V0210-SPECTRAL_IMAGE.vrt',
            r'D:/data/sensors/desis/DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210/DESIS-HSI-L1C-DT1203190212_025-20191203T021128-V0210-SPECTRAL_IMAGE.vrt',
            r'D:/data/sensors/desis/DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210/DESIS-HSI-L2A-DT1203190212_025-20191203T021128-V0210-SPECTRAL_IMAGE.vrt',
            r'D:/data/sensors/enmap/L1B_Arcachon_3/ENMAP01-____L1B-DT000400126_20170218T110119Z_003_V000204_20200508T124425Z-SPECTRAL_IMAGE_SWIR.vrt',
            r'D:/data/sensors/enmap/L1C_Arcachon_3/ENMAP01-____L1C-DT000400126_20170218T110119Z_003_V000204_20200510T095443Z-SPECTRAL_IMAGE.vrt',
            r'D:/data/sensors/enmap/L2A_Arcachon_3_combined/ENMAP01-____L2A-DT000400126_20170218T110119Z_003_V000204_20200512T142942Z-SPECTRAL_IMAGE.vrt',
            r'D:/data/sensors/landsat/C1L2/LC080140322019033001T1-SC20190517105817/LC08_L1TP_014032_20190330_20190404_01_T1_SR.vrt',
            r'D:/data/sensors/prisma/PRS_L1_STD_OFFL_20201107101404_20201107101408_0001_SR.tif',
            r'D:/data/sensors/prisma/PRS_L2D_STD_20201107101404_20201107101408_0001_SR.tif',
            r'D:/data/sensors/sentinel2/S2A_MSIL2A_20200816T101031_N0214_R022_T32UQD_20200816T130108.SAFE\S2A_MSIL2A_20200816T101031_N0214_R022_T32UQD_20200816T130108.SAFE_SR.vrt'
        ]

        # drop on
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        dockManager = EB.dockManager()
        dockArea = dockManager.currentDockArea()
        for filename, filename2 in zip(filenames, filenames2):
            if not exists(filename):
                warn(f'skip: {filename}')
            dockManager.onDockAreaDragDropEvent(dockArea, self.file2DropEvent(filename))
            QApplication.processEvents()
            docks = dockManager.docks()
            self.assertEqual(1, len(docks))
            for d in dockManager.docks():
                self.assertIsInstance(d, MapDock)
                layers = d.mapCanvas().layers()

                if 'ENMAP01-____L1B' in filename:
                    self.assertEqual(2, len(layers))
                else:
                    self.assertEqual(1, len(layers))

                layer = layers[0]
                self.assertIsInstance(layer, QgsRasterLayer)
                self.assertEqual(filename2, layer.source())

                dockManager.removeDock(d)
            EB.dataSourceManager().removeDataSources(EB.dataSourceManager().dataSources())
            QApplication.processEvents()
            QgsProject.instance().removeAllMapLayers()
            QApplication.processEvents()
        EB.close()
