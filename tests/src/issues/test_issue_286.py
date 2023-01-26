"""
This is a template to create an EnMAP-Box test
"""
import pathlib
import unittest

from qgis.core import QgsWkbTypes, QgsVectorFileWriter, QgsProcessingFeedback, QgsCoordinateTransformContext, \
    QgsProject

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from qgis.core import QgsVectorLayer


class EnMAPBoxTestCaseIssue286(EnMAPBoxTestCase):

    def createMultiLayerGPKG(self, path) -> pathlib.Path:

        path = pathlib.Path(path)
        lyr1 = TestObjects.createVectorLayer(QgsWkbTypes.Point)

        lyr2 = TestObjects.createVectorLayer(QgsWkbTypes.Polygon)

        lyr1.setName('Points')
        lyr2.setName('Polygons')
        feedback = QgsProcessingFeedback()

        for lyr in [lyr1, lyr2]:
            lyr: QgsVectorLayer
            ogrDataSourceOptions = []
            ogrLayerOptions = [
                f'IDENTIFIER={lyr.name()}',
                f'DESCRIPTION={lyr.name()}']

            context = QgsProject.instance().transformContext()
            options = QgsVectorFileWriter.SaveVectorOptions()
            if path.is_file():
                options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
            options.layerName = lyr.name()

            options.feedback = feedback
            options.datasourceOptions = ogrDataSourceOptions
            options.layerOptions = ogrLayerOptions
            options.fileEncoding = 'UTF-8'
            options.skipAttributeCreation = False
            options.driverName = 'GPKG'

            transformationContext = QgsCoordinateTransformContext()

            if False:

                writer: QgsVectorFileWriter = QgsVectorFileWriter.create(path.as_posix(),
                                                                         lyr.fields(),
                                                                         lyr.wkbType(),
                                                                         lyr.crs(),
                                                                         transformationContext,
                                                                         options)
                if writer.hasError() != QgsVectorFileWriter.NoError:
                    raise Exception(f'Error when creating {path}: {writer.errorMessage()}')

                if not writer.addFeatures(list(lyr.getFeatures())):
                    if writer.errorCode() != QgsVectorFileWriter.NoError:
                        raise Exception(f'Error when creating feature: {writer.errorMessage()}')

                # QgsVectorFileWriter.writeAsVectorFormatV2(lyr, path.as_posix(), )
                del writer
            else:
                err, msg, p, geom = QgsVectorFileWriter.writeAsVectorFormatV3(lyr, path.as_posix(), context, options)
                assert err == QgsVectorFileWriter.WriterError.NoError
                s = ""

    @unittest.skipIf(TestObjects.repoDirGDAL() is None, 'Test requires GDAL repo testdata')
    @unittest.skipIf(EnMAPBoxTestCase.runsInCI(), 'Blocking dialog to select sublayer')
    def test_with_enmapbox(self):
        dir_gdal = TestObjects.repoDirGDAL()
        path_grps = dir_gdal / 'autotest/gdrivers/data/hdf5/groups.h5'

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        enmapBox.addSource(path_grps)

        self.showGui(enmapBox.ui)


if __name__ == '__main__':
    unittest.main(buffer=False)
