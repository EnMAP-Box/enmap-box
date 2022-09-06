from os.path import join, dirname
from unittest import TestCase

from sklearn.ensemble import RandomForestClassifier
from qgis.core import QgsVectorLayer, QgsRasterLayer

from enmapbox.qgispluginsupport.qps.speclib.core import SpectralLibrary
from enmapbox.exampledata import enmap, landcover_points
from _classic.hubdsm.algorithm.estimatorpredict import estimatorPredict
from _classic.hubdsm.core.qgsvectorclassificationscheme import QgsVectorClassificationScheme
from _classic.hubdsm.core.raster import Raster


class TestEstimatorFit(TestCase):

    def test(self):
        qgsVectorLayer: QgsVectorLayer = QgsVectorLayer(landcover_points)
        qgsRasterLayer: QgsRasterLayer = QgsRasterLayer(enmap)
        assert qgsVectorLayer.loadNamedStyle(join(dirname(__file__), 'landcover_berlin_point_categorizedByL1Id.qml')) != 'False'
        spectralLibrary = SpectralLibrary.readFromVector(qgsVectorLayer, qgsRasterLayer, copy_attributes=True)

        scheme = QgsVectorClassificationScheme.fromQgsVectorLayer(qgsVectorLayer=qgsVectorLayer)
        print(scheme.classAttribute)
        print(spectralLibrary.fields().field('level_1_id').typeName())
        X = list()
        y = list()
        for profile in spectralLibrary:
            classValue = profile.attribute(scheme.classAttribute)
            if classValue in scheme.categories:
                X.append(profile.values()['y'])
                classId = scheme.categories[classValue].id
                y.append(classId)
            else:
                print('skipped:', classValue, 'wait for Issue #463')

        estimator = RandomForestClassifier()
        estimator.fit(X=X, y=y)

        raster = Raster.open(enmap)
        prediction = estimatorPredict(raster=raster, estimator=estimator, filename='classification.bsq')
        prediction.setCategories(categories=list(scheme.categories.values()))
