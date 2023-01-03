"""
This is a template to create an EnMAP-Box test
"""
import pathlib
import unittest

from qgis.PyQt.QtWidgets import QApplication
from qgis._core import QgsWkbTypes, QgsVectorFileWriter, QgsProcessingFeedback, QgsCoordinateTransformContext, \
    QgsProject
from qgis.core import QgsApplication, QgsRasterLayer, QgsVectorLayer
from enmapbox.testing import EnMAPBoxTestCase, TestObjects
from enmapbox import EnMAPBox


class EnMAPBoxTestCaseIssue286(EnMAPBoxTestCase):

    def createMultiLayerGPKG(self, path):

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
                err, p2 = QgsVectorFileWriter.writeAsVectorFormatV2(lyr, path.as_posix(), context, options)

    def test_with_enmapbox(self):
        tmpDir = self.tempDir()

        pathGPKG = tmpDir / 'test.gpkg'
        if True or not pathGPKG.is_file():
            self.createMultiLayerGPKG(pathGPKG)

        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)
        enmapBox.addSource(pathGPKG)

        self.showGui(enmapBox.ui)


if __name__ == '__main__':
    unittest.main(buffer=False)
