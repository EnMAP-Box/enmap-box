from os.path import join

import numpy as np

from qgis.core import QgsVectorLayer, QgsRasterLayer

from enmapbox.qgispluginsupport.qps.speclib.core import SpectralLibrary
from _classic.classificationapp.script import classificationWorkflow
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.qgsvectorclassificationscheme import QgsVectorClassificationScheme
from _classic.hubdsm.processing.savelayerasclassification import saveLayerAsClassification
from _classic.hubflow.core import EnviSpectralLibrary, Classification, ClassificationSample, Classifier, Raster, ClassDefinition

def test_enviSpeclib():
    from sklearn.ensemble import RandomForestClassifier
    import enmapboxtestdata
    library = EnviSpectralLibrary(filename=enmapboxtestdata.library)
    labels = Classification.fromEnviSpectralLibrary(filename='/vsimem/synthmixRegressionEnsemble/labels.bsq',
        library=library, attribute='level_2')

    sample = ClassificationSample(raster=library.raster(), classification=labels)
    outdir = r'c:\outputs'
    classificationWorkflow(
        sample=sample,
        classifier=Classifier(sklEstimator=RandomForestClassifier()),
        raster=Raster(filename=enmapboxtestdata.enmap),
        mask=None,
        n=labels.classDefinition().classes() * [10],
        cv=10,
        saveSampledClassificationComplement=False,
        saveSampledClassification=False,
        saveModel=True,
        saveClassification=True,
        saveProbability=True,
        saveRGB=False,
        saveReport=True,
        filenameSampledClassification=join(outdir, 'sampled.bsq'),
        filenameSampledClassificationComplement=join(outdir, 'sampled_complement.bsq'),
        filenameModel=join(outdir, 'model.pkl'),
        filenameClassification=join(outdir, 'classification.bsq'),
        filenameProbability=join(outdir, 'probability.bsq'),
        filenameReport=join(outdir, 'report.html')
    )


def test_boxSpeclib():
    from sklearn.ensemble import RandomForestClassifier
    import enmapboxtestdata

    # make speclib
    lyrV = QgsVectorLayer(enmapboxtestdata.landcover_points)
    lyrR = QgsRasterLayer(enmapboxtestdata.enmap)
    slib = SpectralLibrary.readFromVector(lyrV, lyrR, copy_attributes=True)

    # set renderer and get classification scheme
    slib.loadNamedStyle(r'C:\source\enmap-box-testdata\enmapboxtestdata\landcover_berlin_point.qml')
    qgsVectorClassificationScheme = QgsVectorClassificationScheme.fromQgsVectorLayer(qgsVectorLayer=slib)

    [print(c) for c in qgsVectorClassificationScheme.categories.items()]

    # make pseudo raster
    X = list()
    y = list()
    fieldIndex = None
    for profile in slib:
        if fieldIndex is None:
            fieldIndex = profile.fieldNames().index('level_2_id')
        X.append(profile.values()['y'])
        y.append(profile.attribute(fieldIndex))
    X = np.array(X, dtype=np.float64)
    y = np.array(y)
    raster = Raster.fromArray(
        array=np.atleast_3d(X.T),
        filename='c:/vsimem/X.bsq'
    )
    classification = GdalRaster.createFromArray(
        array=np.atleast_3d(y),
        filename='c:/vsimem/y.bsq'
    )
    classification.setCategories(list(qgsVectorClassificationScheme.categories.values()))
    del classification
    classification = Classification('c:/vsimem/y.bsq')

    # run workflow
    sample = ClassificationSample(raster=raster, classification=classification)
    outdir = r'c:\outputs'
    classificationWorkflow(
        sample=sample,
        classifier=Classifier(sklEstimator=RandomForestClassifier()),
        raster=Raster(filename=enmapboxtestdata.enmap),
        mask=None,
        n=None, #classification.classDefinition().classes() * [10],
        cv=10,
        saveSampledClassificationComplement=False,
        saveSampledClassification=False,
        saveModel=True,
        saveClassification=True,
        saveProbability=True,
        saveRGB=False,
        saveReport=True,
        filenameSampledClassification=join(outdir, 'sampled.bsq'),
        filenameSampledClassificationComplement=join(outdir, 'sampled_complement.bsq'),
        filenameModel=join(outdir, 'model.pkl'),
        filenameClassification=join(outdir, 'classification.bsq'),
        filenameProbability=join(outdir, 'probability.bsq'),
        filenameReport=join(outdir, 'report.html')
    )


def test_raster():
    from sklearn.ensemble import RandomForestClassifier
    import enmapboxtestdata

    # make classification
    qgsVectorLayer = QgsVectorLayer(enmapboxtestdata.landcover_polygons)
    saveLayerAsClassification(
        qgsMapLayer=qgsVectorLayer,
        grid=GdalRaster.open(enmapboxtestdata.enmap).grid,
        filename='/vsimem/classification1.bsq'
    )

    # eval renderer and save as
    saveLayerAsClassification(
        qgsMapLayer=QgsRasterLayer('c:/vsimem/classification1.bsq'),
        filename='/vsimem/classification2.bsq'
    )

    raster = Raster(filename=enmapboxtestdata.enmap)
    classification = Classification(filename='/vsimem/classification2.bsq')

    # run workflow
    sample = ClassificationSample(raster=raster, classification=classification)
    outdir = r'c:\outputs'
    classificationWorkflow(
        sample=sample,
        classifier=Classifier(sklEstimator=RandomForestClassifier()),
        raster=Raster(filename=enmapboxtestdata.enmap),
        mask=None,
        n=None, #classification.classDefinition().classes() * [10],
        cv=10,
        saveSampledClassificationComplement=False,
        saveSampledClassification=False,
        saveModel=True,
        saveClassification=True,
        saveProbability=True,
        saveRGB=False,
        saveReport=False,
        filenameSampledClassification=join(outdir, 'sampled.bsq'),
        filenameSampledClassificationComplement=join(outdir, 'sampled_complement.bsq'),
        filenameModel=join(outdir, 'model.pkl'),
        filenameClassification=join(outdir, 'classification.bsq'),
        filenameProbability=join(outdir, 'probability.bsq'),
        filenameReport=join(outdir, 'report.html')
    )


if __name__ == '__main__':
    # test_enviSpeclib()
    # test_boxSpeclib()
    test_raster()

