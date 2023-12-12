from unittest import TestCase
from tempfile import gettempdir
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from tests import enmapboxtestdata
from _classic.hubdc.progressbar import CUIProgressBar
from _classic.hubflow.core import *
import _classic.hubflow.testdata

CUIProgressBar.SILENT = False
overwrite = not True
vector = _classic.hubflow.testdata.vector()
enmap = _classic.hubflow.testdata.enmap()

enmapClassification = _classic.hubflow.testdata.enmapClassification(overwrite=overwrite)
vectorClassification = _classic.hubflow.testdata.vectorClassification()
vectorRegression = _classic.hubflow.testdata.vectorRegression()
vectorMask = _classic.hubflow.testdata.vectorMask()
vectorPoints = _classic.hubflow.testdata.vectorPoints()
enmapFraction = _classic.hubflow.testdata.enmapFraction(overwrite=overwrite)
enmapRegression = _classic.hubflow.testdata.enmapRegression(overwrite=overwrite)
enmapMask = enmapClassification.asMask()
speclib = EnviSpectralLibrary(filename=enmapboxtestdata.library)
# speclib2 = EnviSpectralLibrary(filename=enmapboxtestdata.speclib2)


rasterMaps = [enmap, enmapClassification, enmapRegression, enmapFraction, enmapMask]
vectorsMaps = [vector, vectorClassification, vectorMask]
maps = rasterMaps + vectorsMaps

enmapSample = _classic.hubflow.testdata.enmapSample()
enmapClassificationSample = _classic.hubflow.testdata.enmapClassificationSample()
enmapRegressionSample = _classic.hubflow.testdata.enmapRegressionSample()
enmapFractionSample = _classic.hubflow.testdata.enmapFractionSample()

samples = [enmapSample, enmapClassificationSample, enmapRegressionSample, enmapFractionSample]

objects = maps + samples + [MapCollection([enmap, enmapMask]),
                            enmap.sensorDefinition().wavebandDefinition(index=0),
                            enmap.sensorDefinition(),
                            speclib,
                            # RasterStack([enmap, enmapMask]),
                            enmapClassification.classDefinition(),
                            Classifier(sklEstimator=RandomForestClassifier()),
                            ClassificationPerformance.fromRaster(prediction=enmapClassification,
                                reference=enmapClassification),
                            FractionPerformance.fromRaster(prediction=enmapFraction, reference=enmapClassification),
                            RegressionPerformance.fromRaster(prediction=enmapRegression, reference=enmapRegression),
                            ClusteringPerformance.fromRaster(prediction=enmapClassification,
                                reference=enmapClassification),
                            Color('red')]

outdir = join(gettempdir(), 'hubflow_test')
openHTML = not True


class Test(TestCase):

    def test_AttributeDefinitionEditor(self):
        filename = splitext(enmapboxtestdata.landcover_polygons)[0] + '.json'
        print(filename)
        definitions = AttributeDefinitionEditor.readFromJson(filename=filename)
        print(definitions)
        print(AttributeDefinitionEditor.makeClassDefinition(definitions=definitions, attribute='level_2_id'))

    def test_ENVI(self):
        ENVI.readHeader(filenameHeader=ENVI.findHeader(filenameBinary=enmapboxtestdata.library))

    def test_WavebandDefinition(self):

        wavebandDefinition = WavebandDefinition.fromFWHM(center=600, fwhm=10)
        print(wavebandDefinition)
        wavebandDefinition.plot()
        wavebandDefinition.resamplingWeights(sensor=SensorDefinition.fromPredefined(name='sentinel2'))

    def test_SensorDefinition(self):

        print(SensorDefinition.predefinedSensorNames())
        print(SensorDefinition.fromPredefined(name='sentinel2'))

        # a) response function from ENVI Speclib

        sentinel2ResponseFunction = EnviSpectralLibrary(
            filename=r'C:\source\QGISPlugIns\enmap-box\hubflow\sensors\sentinel2.sli')
        sentinel2Sensor = SensorDefinition.fromEnviSpectralLibrary(library=sentinel2ResponseFunction,
            isResponseFunction=True)
        print(sentinel2Sensor)
        sentinel2Sensor.plot()

        # b) wl+fwhm from ENVI Speclib
        enmapSensor = SensorDefinition.fromEnviSpectralLibrary(library=EnviSpectralLibrary(filename=speclib.filename()),
            isResponseFunction=False)
        print(enmapSensor)
        enmapSensor.plot()

        # c) wl+fwhm from raster
        enmapSensor = SensorDefinition.fromRaster(raster=enmap)
        print(enmapSensor)
        enmapSensor.plot()

        # resample EnMAP into Sentinel 2
        outraster = sentinel2Sensor.resampleRaster(filename=join(outdir, 'sentinel2.bsq'), raster=enmap,
            resampleAlg=SensorDefinition.RESAMPLE_LINEAR)
        outraster = sentinel2Sensor.resampleRaster(filename=join(outdir, 'sentinel2.bsq'), raster=enmap,
            resampleAlg=SensorDefinition.RESAMPLE_RESPONSE)

        print(outraster)

        if 1:  # plot
            pixel = Pixel(10, 10)
            plotWidget = sentinel2Sensor.plot(yscale=2000, pen='g')
            enmap.dataset().plotZProfile(pixel, plotWidget=plotWidget, spectral=True, xscale=1000)
            outraster.dataset().plotZProfile(pixel, plotWidget=plotWidget, spectral=True, symbol='o', symbolPen='r')

    def test_SensorDefinitionResampleArray(self):

        sentinel2ResponseFunction = EnviSpectralLibrary(
            filename=r'C:\source\QGISPlugIns\enmap-box\hubflow\sensors\sentinel2.sli')
        sentinel2Sensor = SensorDefinition.fromEnviSpectralLibrary(library=sentinel2ResponseFunction,
            isResponseFunction=True)

        profiles = [enmap.dataset().zprofile(pixel=Pixel(10, 10)),
                    enmap.dataset().zprofile(pixel=Pixel(20, 20)),
                    enmap.dataset().zprofile(pixel=Pixel(30, 30))]
        wavelength = enmap.metadataWavelength()

        import time
        t0 = time.time()
        outprofiles = sentinel2Sensor.resampleProfiles(array=profiles, wavelength=wavelength,
            wavelengthUnits='nanometers')
        print(time.time() - t0)
        print(outprofiles)

    def test_StringParser(self):
        p = StringParser()
        self.assertIsNone(p.list(''))
        self.assertListEqual(p.list('[]'), [])
        self.assertListEqual(p.list('[1]'), [1])
        self.assertListEqual(p.list('1'), [1])
        self.assertListEqual(p.list('[1, 2, 3]'), [1, 2, 3])
        self.assertListEqual(p.list('{1, 2, 3}'), [1, 2, 3])
        self.assertListEqual(p.list('(1, 2, 3)'), [1, 2, 3])
        self.assertListEqual(p.list('1 2 3'), [1, 2, 3])
        self.assertListEqual(p.list('1, 2, 3'), [1, 2, 3])
        self.assertListEqual(p.list('a b c'), ['a', 'b', 'c'])
        self.assertListEqual(p.list('1 2-4 5'), [1, 2, 3, 4, 5])
        self.assertListEqual(p.list('-4--2'), [-4, -3, -2])
        # self.assertListEqual(p.list('\eval range(3)'), [0, 1, 2])

        self.assertListEqual(p.list('1-3 7-10', extendRanges=False), [(1, 3), (7, 10)])
        self.assertListEqual(p.list('1 5-10', extendRanges=False), [1, (5, 10)])

    def test_Color(self):
        color = Color('red')
        print(color)
        print(color.name())
        print(color.red())
        print(color.green())
        print(color.blue())
        print(color.colorNames())

    def test_Classification(self):

        c = Classification.fromClassification(filename='/vsimem/c.bsq',
            classification=vectorClassification, grid=enmap.grid())
        print(c.noDataValues())

        raster = Raster.fromArray(array=[[[0, 1, 2]]], filename='/vsimem/raster.bsq')
        print(Classification(filename=raster.filename()))

        raster = enmapClassificationSample.raster()
        classification = enmapClassificationSample.classification()

        # resampling
        print(enmapClassification)
        classification = Classification(filename=enmapClassification.filename(), minOverallCoverage=0.,
            minDominantCoverage=0.)
        print(classification.resample(filename=join(outdir, 'ClassificationResample.bsq'),
            grid=enmap.grid().atResolution(5), controls=ApplierControls()))  # .setBlockFullSize()))

        # from fraction
        print(Classification.fromClassification(filename=join(outdir, 'ClassificationFromFraction.bsq'),
            classification=enmapFraction, masks=[enmapMask]))

        print(Classification.fromFraction(filename=join(outdir, 'ClassificationFromFraction.bsq'),
            fraction=enmapFraction, masks=[enmapMask]))

        def ufunc(array, meta):
            return (array > 1000) + 1

        classDefinition = ClassDefinition(names=['land', 'water', 'shadow', 'snow', 'cloud'],
            colors=['orange', 'blue', 'grey', 'snow', 'white'])

        print(Classification.fromRasterAndFunction(filename=join(outdir, 'ClassificationFromRasterAndFunction.bsq'),
            raster=enmap,
            ufunc=ufunc, classDefinition=classDefinition))

        print(Classification.fromClassification(filename=join(outdir, 'hymapLandCover.bsq'),
            classification=vectorClassification, grid=enmap.grid()))

        print(enmapClassification.reclassify(filename=join(outdir, 'classificationReclassify.bsq'),
            classDefinition=ClassDefinition(names=['urban', 'rest']),
            mapping={1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2}))

    def test_DEBUG_RECLASSIFY(self):

        c1 = Classification.fromArray(array=np.array([[[1, 888]]]), filename='c:/vsimem/c.bsq')
        c2 = c1.reclassify(
                filename='c:/vsimem/c2.bsq',
                classDefinition=ClassDefinition(names=['c1', 'c2']),
                mapping={1: 1, 888: 2}
            )
        print(c2.dataset().readAsArray())

        c3 = Classification.fromArray(array=np.array([[[1, 2]]]), filename='c:/vsimem/c.bsq')
        c4 = c3.reclassify(
                filename='c:/vsimem/c2.bsq',
                classDefinition=ClassDefinition(names=['c1', 'c2']),
                mapping={1: 1, 2: 888}
            )
        print(c4.dataset().readAsArray())



    def test_ClassificationSample(self):

        # read from labeled library
        library = EnviSpectralLibrary(filename=enmapboxtestdata.library)
        classificationSample = ClassificationSample(raster=library.raster(),
            classification=Classification.fromEnviSpectralLibrary(
                filename='/vsimem/labels.bsq',
                library=library,
                attribute='level_2'))

        # syntmix

        for includeWithinclassMixtures in [True, False]:
            for includeEndmember in [True, False]:
                print(includeWithinclassMixtures, includeEndmember)
                fractionSample = enmapClassificationSample.synthMix(
                    filenameFeatures=join(outdir, 'ClassificationSampleSynthMix.features.bsq'),
                    filenameFractions=join(outdir, 'ClassificationSampleSynthMix.fractions.bsq'),
                    mixingComplexities={2: 0.7, 3: 0.3}, classProbabilities='equalized',
                    n=1000, target=2, includeWithinclassMixtures=includeWithinclassMixtures,
                    includeEndmember=includeEndmember)
        features, labels = fractionSample.extractAsArray()
        print(features.shape, labels.shape)

        print(enmapClassificationSample)
        features, labels = enmapClassificationSample.extractAsArray()
        print(features.shape, labels.shape)

    def test_ClassDefinition(self):

        classification = Classification.fromArray(array=[[[0, 1, 2]]], filename='/vsimem/c.bsq')
        newNames = ['Class X']
        mapping = {0: 0, 1: 1, 2: 1}
        newDef = ClassDefinition(names=newNames)
        newDef.setNoDataNameAndColor(name='Not specified', color=Color(128, 128, 128))
        print(classification.classDefinition())
        print(newDef)
        reclassified = classification.reclassify(
            filename='/vsimem/c2.bsq', classDefinition=newDef, mapping=mapping)

        print(reclassified.dataset().band(0).categoryNames())
        print(reclassified.dataset().band(0).categoryColors())

        # qml read / write
        print(ClassDefinition.fromQml(filename=enmapboxtestdata.landcover_polygons.replace('.shp', '.qml')))
        print(ClassDefinition.fromQml(filename=enmapboxtestdata.landcover_points.replace('.shp', '.qml')))

        print(ClassDefinition.fromENVIClassification(raster=enmapClassification))
        print(ClassDefinition.fromGDALMeta(raster=enmapClassification))
        print(ClassDefinition(colors=['orange', 'blue', 'grey', 'snow', 'white']))
        print(ClassDefinition(classes=3))
        classDefinition1 = ClassDefinition(classes=3)
        classDefinition2 = ClassDefinition(classes=3)
        self.assertTrue(classDefinition1.equal(classDefinition2, compareColors=False))
        self.assertFalse(classDefinition1.equal(classDefinition2, compareColors=True))
        classDefinition1.color(label=1)
        print(ClassDefinition(colors=['blue'], names=['Class 1']).colorByName(name='Class 1'))
        print(ClassDefinition(colors=['blue'], names=['Class 1']).labelByName(name='Class 1'))
        ClassDefinition(classes=3).labels()

    def test_Clusterer(self):
        kmeans = Clusterer(sklEstimator=KMeans())
        print(kmeans)
        kmeans.fit(sample=enmapClassificationSample)
        print(kmeans.predict(filename=join(outdir, 'kmeansClustering.bsq'), raster=enmap, mask=vector))
        kmeans.classDefinition()

    def test_ClusteringPerformance(self):
        clusteringPerformance = ClusteringPerformance.fromRaster(prediction=enmapClassification,
            reference=enmapClassification)
        print(clusteringPerformance)
        clusteringPerformance.report().saveHTML(filename=join(outdir, 'reportClusteringPerformance.html'),
            open=openHTML)

    def test_FlowObject(self):
        enmap.dataset().gdalDataset()
        enmapClassification.dataset().gdalDataset()
        vector.dataset().ogrLayer()
        enmapMask.dataset().gdalDataset()
        sample = ClassificationSample(raster=enmap, classification=enmapClassification, mask=vector)
        rfc = Classifier(RandomForestClassifier(oob_score=True)).fit(sample)
        # rfc.browse()

    def test_MapCollection(self):

        mapCollection = MapCollection(
            maps=[enmap, enmapClassification, enmapRegression, enmapFraction, vector, vectorClassification])
        filenames = [join(outdir, 'MapCollectionExtractAsRaster_{}.bsq'.format(type(map).__name__)) for map in
                     mapCollection.maps()]
        rasters = mapCollection.extractAsRaster(filenames=filenames, grid=enmap.grid(), masks=[vector],
            onTheFlyResampling=True)
        for raster in rasters:
            print(raster)

    def test_Mask(self):
        print(enmapClassification.asMask().resample(filename=join(outdir, 'MaskResample.bsq'), grid=enmap))

        print(Mask.fromVector(filename=join(outdir, 'maskFromVector.bsq'), vector=vector, grid=enmap))
        print(Mask.fromRaster(filename=join(outdir, 'maskFromRaster.bsq'), raster=enmapClassification,
            #                              trueRanges=[(1, 100)], trueValues=[1, 2, 3],
            true=[range(1, 100), 1, 2, 3],
            #                              falseRanges=[(-9999, 0)], falseValues=[-9999]))
            false=[range(-9999, 0), -9999]))

    def test_FractionPerformance(self):
        fractionPerformance = FractionPerformance.fromRaster(prediction=enmapFraction, reference=enmapClassification)
        print(fractionPerformance)
        fractionPerformance.report().saveHTML(filename=join(outdir, 'reportFractionPerformance.html'), open=openHTML)

    def test_FractionSample(self):

        print(enmapFractionSample)
        features, labels = enmapFractionSample.extractAsArray()
        print(features.shape, labels.shape)

        # init
        fractionSample = FractionSample(raster=enmap, fraction=enmapFraction, grid=enmap.grid())
        print(fractionSample)
        print(fractionSample.raster().dataset().shape())
        print(fractionSample.fraction().dataset().shape())

    def test_Sample(self):

        # init
        sample = Sample(raster=enmap, mask=vector)
        print(sample)
        sample.extractAsArray(onTheFlyResampling=True)
        sample.extractAsRaster(filenames=['/vsimem/raster.bsq'], onTheFlyResampling=True)

    def test_Transformer(self):
        pca = Transformer(sklEstimator=PCA())
        print(pca)
        pca.fit(sample=enmapSample)
        pcaTransformation = pca.transform(filename=join(outdir, 'pcaTransformation.bsq'), raster=enmap, mask=vector)
        print(pcaTransformation)
        pcaInverseTransform = pca.inverseTransform(filename=join(outdir, 'pcaInverseTransformation.bsq'),
            raster=pcaTransformation, mask=vector)
        print(pcaInverseTransform)

    def test_Vector(self):

        # vector = Vector(filename=r'C:\output\LandCov_BerlinUrbanGradient_WGS84.gpkg|layername=polygons')
        # Raster.fromVector(filename=r'c:\output\test.bsq', vector=vector, grid=enmap.grid())

        print(vector.uniqueValues(attribute='level_2_id'))
        print(vector.uniqueValues(attribute='level_2'))
        print(vector)
        print(Vector.fromRandomPointsFromMask(filename=join(outdir, 'vectorFromRandomPointsFromMask.gpkg.shp'),
            mask=enmapMask,
            n=10))
        n = [10] * enmapClassification.classDefinition().classes()
        print(
            Vector.fromRandomPointsFromClassification(
                filename=join(outdir, 'vectorFromRandomPointsFromClassification.gpkg'),
                classification=enmapClassification, n=n))
        Vector.fromVectorDataset(vectorDataset=vector.dataset())
        Vector.fromPoints(filename='/vsimem/vector.shp', points=[Point(0, 0, Projection.wgs84())])
        vector.metadataDict()
        vector.metadataItem(key='a', domain='')
        vector.extent()
        vector.projection()
        vector.grid(resolution=1)

    def test_VectorMask(self):
        print(VectorMask(filename=vector.filename(), invert=False))

    def test_VectorClassification(self):
        print(VectorClassification(filename=enmapboxtestdata.landcover_polygons, classAttribute='level_2_id'))
        print(VectorClassification(filename=enmapboxtestdata.landcover_points, classAttribute='level_2_id'))

    def test_VectorRegression(self):
        print(VectorRegression(filename=enmapboxtestdata.landcover_points, regressionAttribute='level_2_id'))

    def test_extractPixels(self):
        c = ApplierControls()
        extractPixels(inputs=[enmap, enmapFraction, enmapClassification, enmapRegression, vector, vectorClassification],
            masks=[enmapMask], grid=enmap.grid(), controls=c)

    def test_applierMultiprocessing(self):

        c = ApplierControls()
        c.setBlockSize(25)
        c.setNumThreads(2)

        rfc = Classifier(sklEstimator=RandomForestClassifier())
        print(rfc)
        rfc.fit(sample=enmapClassificationSample)
        print(rfc.predict(filename=join(outdir, 'rfcClassification.bsq'), raster=enmap, mask=vector, controls=c))

    def test_pickle(self):

        def printDataset(obj):
            if isinstance(obj, Raster):
                print(obj._rasterDataset)
            elif isinstance(obj, Vector):
                print(obj._vectorDataset)
            else:
                pass

        for obj in objects:
            print(type(obj))
            if isinstance(obj, Map):
                obj.dataset()
            filename = join(outdir, 'pickle.pkl')
            printDataset(obj)
            obj.pickle(filename=filename)
            obj2 = obj.unpickle(filename=filename)
            printDataset(obj2)
            print(obj2)

    def test_repr(self):
        for obj in objects:
            print(type(obj))
            print(obj)

    def test_map_array(self):

        for map in rasterMaps:
            print(type(map))
            print(map.array()[0, 30:40, 30:40])

    def test_ApplierOptions(self):
        print(ApplierOptions())

    def test_debug(self):
        import _classic.hubflow.core

        newNames = ['No Class', 'Class B']
        newColors = [QColor('black'), QColor('yellow')]

        # but this fails
        newDef = _classic.hubflow.core.ClassDefinition(names=newNames[1:], colors=newColors[1:])
        newDef.setNoDataNameAndColor(newNames[0], QColor('yellow'))
        print(newDef)

    def test_uniqueValueCounts(self):
        import numpy as np
        x = np.array([np.inf, np.nan, 1, 1, 1, 2, 2, 5.5])
        values = np.unique(x)
        for v in values:
            if np.isnan(v):
                print(v, np.sum(np.isnan(x)))
            else:
                print(v, np.sum(x == v))


class TestClassificationPerformance(TestCase):
    def test_fromRaster(self):
        obj = ClassificationPerformance.fromRaster(prediction=enmapClassification, reference=enmapClassification)
        print(obj)
        obj.report().saveHTML(filename=join(outdir, 'ClassificationPerformanceFromRaster.html'), open=openHTML)


class TestClassifier(TestCase):

    def test_Classifier(self):
        enmap = Raster(filename=enmapboxtestdata.enmap)
        classification = Classification.fromClassification(classification=vectorClassification,
            grid=enmap.grid(),
            filename='/vsimem/classification.bsq')
        sample = ClassificationSample(raster=enmap, classification=classification)
        rfc = Classifier(sklEstimator=RandomForestClassifier())
        rfc.fit(sample=sample)
        rfc.predict(raster=enmap, filename='/vsimem/rfcClassification.bsq')
        rfc.crossValidation().report().saveHTML(filename=join(outdir, 'report.html'), open=False)

        rfc = Classifier(sklEstimator=RandomForestClassifier())
        print(rfc)
        rfc.fit(sample=enmapClassificationSample)
        enmapClassificationSample.raster().dataset()
        enmapClassificationSample.classification().dataset()

        rfc.pickle(filename=join(outdir, 'classifier.pkl'))
        print(rfc.predict(filename=join(outdir, 'rfcClassification.bsq'), raster=enmap, mask=vector))
        print(rfc.predictProbability(filename=join(outdir, 'rfcProbability.bsq'), raster=enmap, mask=vector))

    def test_performance(self):
        rfc = Classifier(sklEstimator=RandomForestClassifier())
        rfc.fit(sample=enmapClassificationSample)
        rfc.performanceCrossValidation(nfold=10).report().saveHTML(
            filename=join(outdir, 'ClassifierPerformanceCrossValidation.html'))
        rfc.performanceTraining().report().saveHTML(filename=join(outdir, 'ClassifierPerformanceTraining.html'))


class TestEnviSpectralLibrary(TestCase):

    def test(self):

        # init
        speclib = EnviSpectralLibrary(filename=enmapboxtestdata.library)
        print(speclib)
        print(speclib.profiles())
        print(speclib.raster().dataset().metadataDict())

        print(speclib.attributeNames())
        print(speclib.attributeDefinitions())
        print(speclib.attributeTable())

        # speclib from raster
        speclib = EnviSpectralLibrary.fromRaster(filename=join(outdir, 'EnviSpectralLibraryFromRaster.sli'),
            raster=enmap)
        print(speclib)
        print(speclib.raster().dataset().shape())

        raster = speclib.raster(transpose=False)
        print(raster.dataset().shape())
        raster.dataset().plotXProfile(row=Row(y=0, z=0))

        raster = speclib.raster(transpose=True)
        print(raster.dataset().shape())
        raster.dataset().plotZProfile(pixel=Pixel(x=0, y=0), spectral=True)

    def test_fromClassificationSample(self):
        classification = Classification.fromClassification(classification=vectorPoints, grid=enmap.grid(),
            filename='/vsimem/classification.bsq')
        sample = ClassificationSample(raster=enmap, classification=classification)
        outdir = r'c:\test'
        speclib = EnviSpectralLibrary.fromSample(sample=sample, filename=join(outdir, 'speclib.sli'))
        print(speclib)
        classification2 = Classification.fromEnviSpectralLibrary(filename='/vsimem/classification.bsq', library=speclib,
            attribute='id')
        assert classification.classDefinition().equal(classification2.classDefinition())

    def test_plot(self):
        speclib = EnviSpectralLibrary(filename=enmapboxtestdata.library)

        import pyqtgraph as pg
        import pyqtgraph.exporters
        plot = pg.plot()
        for y in range(speclib.raster().dataset().ysize()):
            speclib.raster().dataset().plotZProfile(pixel=Pixel(x=0, y=y), spectral=True, plotWidget=plot)
        exporter = pyqtgraph.exporters.ImageExporter(plot.plotItem)
        # workaround a bug with float conversion to int
        exporter.params.param('width').setValue(600, blockSignal=exporter.widthChanged)
        exporter.params.param('height').setValue(400, blockSignal=exporter.heightChanged)
        exporter.export(join(outdir, 'plot.png'))

    def test_debug(self):
        pass


class TestLogger(TestCase):

    def test_setAndLogSklEstimators(self):
        from sklearn.linear_model import LinearRegression
        estimator = Regressor(sklEstimator=LinearRegression()).fit(sample=enmapRegressionSample)
        LoggerFlowObject(filename=r'c:\test\logLinearRegression.txt').setSklEstimatorItems(
            estimator=estimator.sklEstimator()).logItems()

        from sklearn.ensemble import RandomForestRegressor
        estimator = Regressor(sklEstimator=RandomForestRegressor(oob_score=True)).fit(sample=enmapRegressionSample)
        LoggerFlowObject(filename=r'c:\test\logRandomForestRegressor.txt').setSklEstimatorItems(
            estimator=estimator.sklEstimator()).logItems()

        from sklearn.cross_decomposition import PLSRegression
        estimator = Regressor(sklEstimator=PLSRegression(n_components=3, scale=True)).fit(sample=enmapRegressionSample)
        LoggerFlowObject(filename=r'c:\test\logPLSRegression.txt').setSklEstimatorItems(
            estimator=estimator.sklEstimator()).logItems()

        from sklearn.ensemble import RandomForestClassifier
        estimator = Classifier(sklEstimator=RandomForestClassifier(oob_score=True)).fit(
            sample=enmapClassificationSample)
        LoggerFlowObject(filename=r'c:\test\logRandomForestClassifier.txt').setSklEstimatorItems(
            estimator=estimator.sklEstimator()).logItems()


class TestRaster(TestCase):

    def test_Raster(self):
        # from array
        raster = Raster.fromArray(array=[[[-1, 1, 2, np.inf, np.nan]]], filename='/vsimem/raster.bsq',
            noDataValues=[-9], descriptions=['band 1'])
        print(raster.asMask(noDataValues=[-1]).array())

        raster.dataset().setNoDataValue(-1)
        statistics = raster.statistics(calcMean=True, calcStd=True, calcPercentiles=True, percentiles=[0, 50, 100],
            calcHistogram=True, histogramRanges=[(1, 3)], histogramBins=[2])
        print(statistics)
        assert statistics[0].min == 1
        assert statistics[0].max == 2
        assert statistics[0].nvalid == 2
        assert statistics[0].ninvalid == 3
        print(raster)

        # apply mask
        enmapMaskInv = Mask(filename=enmapMask.filename(), invert=not True)
        enmapMaskInv = VectorMask(filename=vectorClassification.filename(), invert=True)

        print(enmapClassification.applyMask(filename=join(outdir, 'ClassificationApplyMask.bsq'), mask=enmapMaskInv))
        cl = Classification(filename=join(outdir, 'ClassificationApplyMask.bsq'))
        # cl.dataset().plotCategoryBand()

        # convolution
        from astropy.convolution import Gaussian2DKernel, Kernel1D
        # 2d
        kernel = Gaussian2DKernel(x_stddev=1)
        print(enmapRegression.convolve(filename=join(outdir, 'RasterConvolveSpatial.bsq'), kernel=kernel))

        # 1d
        from scipy.signal import savgol_coeffs
        kernel = Kernel1D(array=savgol_coeffs(window_length=11, polyorder=3, deriv=1))
        print(enmap.convolve(filename=join(outdir, 'RasterConvolveSpectral.bsq'), kernel=kernel))

        print(enmapClassification.uniqueValues(index=0))

        print(Raster.fromVector(filename=join(outdir, 'RasterFromVector.bsq'), vector=vectorClassification,
            grid=enmap.grid(),
            overwrite=overwrite))
        print(enmap.statistics(bandIndicies=None, mask=vector, grid=enmap))

        bandIndicies = 0, 1

        statistics = enmap.statistics(bandIndicies=bandIndicies, calcPercentiles=True, calcHistogram=True,
            calcMean=True,
            calcStd=True, mask=enmapMask)
        statistics = enmap.statistics(mask=vector)

        H, xedges, yedges = enmap.scatterMatrix(raster2=enmap, bandIndex1=bandIndicies[0], bandIndex2=bandIndicies[1],
            range1=(statistics[0].min, statistics[0].max),
            range2=(statistics[1].min, statistics[1].max),
            bins=10, mask=vector)
        print(H)

        H, xedges, yedges = enmap.scatterMatrix(raster2=enmap, bandIndex1=bandIndicies[0], bandIndex2=bandIndicies[1],
            stratification=enmapClassification,
            range1=(statistics[0].min, statistics[0].max),
            range2=(statistics[1].min, statistics[1].max),
            bins=10, mask=vector)
        print(H)

    def test_fromEnviSpectralLibrary(self):
        print(Raster.fromEnviSpectralLibrary(filename=join(outdir, 'RasterFromEnviSpectralLibrary.bsq'),
            library=speclib))

    def test_fromAsdTxt(self):
        import tests.enmapboxtestdata.asd
        print(Raster.fromAsdTxt(filename=join(outdir, 'RasterFromAsdTxt__.tif'),
                                asdFilenames=enmapboxtestdata.asd.filenames_ascii))

    def test_saveAs(self):
        raster = Raster(enmapboxtestdata.enmap)
        copy = raster.saveAs(filename='/vsimem/raster.tif', driver=None)

    def test_convolve(self):
        raster = Raster(enmapboxtestdata.hires)
        from astropy.convolution import Gaussian2DKernel
        kernel = Gaussian2DKernel(x_stddev=3, y_stddev=3)
        convolved = raster.convolve(filename='/vsimem/raster.bsq', kernel=kernel)
        # MapViewer().addLayer(convolved.dataset().mapLayer()).show()

    def test_subsetBands(self):
        # subset bands
        raster = enmap.subsetBands(indices=[1, -1], invert=False, filename=join(outdir, 'sub1.bsq'))
        raster = enmap.subsetBands(indices=[1, -1], invert=True, filename=join(outdir, 'sub2.bsq'))
        print(raster)

    def test_subsetWavebands(self):
        # subset bands
        hires = Raster(filename=enmapboxtestdata.hires)
        raster = enmap.subsetWavebands(wavelength=hires.metadataWavelength(),
            filename=join(outdir, 'Raster.subsetWavebands.raster.bsq'))
        print(raster)
        print(raster.metadataWavelength())

    def test_applySpatial(self):
        # apply spatial function
        print(enmap.applySpatial(filename=join(outdir, 'RasterApplySpatial.bsq'),
            function=lambda a: a > 1000))

    def test_calculate(self):
        def myFunc(a):
            result = a > 500
            return result

        # apply spatial function
        print(enmap.calculate(filename=join(outdir, 'RasterCalculate.bsq'),
            function=myFunc))

    def test_resample(self):
        print(enmap.resample(filename=join(outdir, 'RasterResample.bsq'), grid=enmap.grid().atResolution(10),
            resampleAlg=gdal.GRA_Average))

    def test_resampleAllResampleAlgs(self):
        print(enmap.resample(filename=join(outdir, 'RasterResample.bsq'), grid=enmap.grid().atResolution(10),
            resampleAlg=gdal.GRA_Average))


class TestFraction(TestCase):

    def test_Fraction(self):
        print(enmapFraction)
        fraction = Fraction(filename=enmapFraction.filename(), minOverallCoverage=0, minDominantCoverage=0)
        print(fraction.resample(filename=join(outdir, 'FractionResample.bsq'),
            grid=enmapClassification.grid(), controls=ApplierControls()))  # .setBlockFullSize()))

        print(enmapFraction.asClassColorRGBRaster(filename=join(outdir, 'fractionAsClassColorRGBImage.bsq')))

        print(enmapFraction.subsetClassesByName(filename=join(outdir, 'fractionSubsetClassesByName.bsq'),
            names=enmapFraction.classDefinition().names()))

    def test_fromClassification(self):
        print(Fraction.fromClassification(filename=join(outdir, 'enmapFraction.bsq'),
            classification=vectorClassification, grid=enmap.grid()))


class TestRegression(TestCase):

    def test_Regression(self):
        r = Regression.fromVectorRegression(filename=join(outdir, 'RegressionFromRegression1.bsq'),
            vectorRegression=vectorRegression, grid=enmap.grid())
        print(enmapRegression.asMask())
        print(enmapRegression.resample(filename=join(outdir, 'RegressionResample.bsq'),
            grid=enmap.grid().atResolution(10)))

    def test_ordinationPfeilhauerEtAll2014(self):
        # todo prepare new testdata
        return

        from sklearn.ensemble import RandomForestRegressor

        # define inputs
        aisa = Raster(filename=r'C:\Work\data\hannes_feilhauer\aisaClean.bsq')
        # aisa = aisa.subsetBands(filename=r'c:\test\tmp.bsq', indices=range(0, aisa.dataset().zsize(), 10))

        plots = Vector(filename=r'C:\Work\data\hannes_feilhauer\plotsClean.gpkg')

        # extract data
        raster, species = plots.extractPixel(raster=aisa, filenameRaster='/vsimem/raster.bsq',
            filenameRegression='/vsimem/regression.bsq')

        # ordinate species abundances
        ordinations, vectorForPlotting, cumulativeExplainedVariance, stress = species.ordinationFeilhauerEtAl2014(
            filename=r'c:\test\feilhauer.bsq',
            filenameVector=r'c:\test\feilhauerVector.gpkg',
            n_components=3)

        print('stress:', stress)
        print('cumExpVar:', cumulativeExplainedVariance)

        # fit regressor
        sample = RegressionSample(raster=raster, regression=ordinations)
        rfr = Regressor(sklEstimator=RandomForestRegressor(n_estimators=100, n_jobs=-1)).fit(sample=sample)
        # rfr = Regressor(sklEstimator=PLSRegression(n_components=10, scale=True)).fit(sample=sample)

        # predict map
        rfr.predict(filename=r'c:\test\map.bsq', raster=aisa)

        # assess performance
        rfr.performanceCrossValidation(nfold=10).report().saveHTML(filename=r'c:\test\accassCrossVal.html')
        rfr.performanceTraining().report().saveHTML(filename=r'c:\test\accassTrain.html')


class TestRegressionPerformance(TestCase):
    def test_RegressionPerformance(self):
        print(enmapRegression.filename())
        print(enmapRegression)

        # mask = Vector.fromRandomPointsFromMask(filename=join(outdir, 'random.shp'), mask=enmapMask, n=10)
        # maskInverted = Vector(filename=mask.filename(), initValue=mask.burnValue(), burnValue=mask.initValue())

        rfr = Regressor(sklEstimator=RandomForestRegressor())
        rfr.fit(sample=enmapRegressionSample)
        reference = rfr.predict(filename='/vsimem/rfrRegression.bsq', raster=enmap)

        obj = RegressionPerformance.fromRaster(prediction=enmapRegression, reference=reference)
        print(obj)
        obj.report().saveHTML(filename=join(outdir, 'RegressionPerformance.html'), open=not openHTML)


class TestRegressionSample(TestCase):
    def test_RegressionSample(self):
        sample = RegressionSample(raster=enmap, regression=enmapFraction)

        print(enmapRegressionSample)
        features, labels = enmapRegressionSample.extractAsArray()
        print(features.shape, labels.shape)

        # init
        regressionSample = RegressionSample(raster=enmap, regression=enmapFraction, mask=vector)
        print(regressionSample)

    def test_fromArtmo(self):
        ''  # todo prepare new testdata
        return
        directional_reflectance = r'C:\Work\data\artmo\Directional_reflectance_PROSAIL1000_FVC.txt'
        directional_reflectance_meta = r'C:\Work\data\artmo\Directional_reflectance_PROSAIL1000_FVC_meta.txt'

        sample = RegressionSample.fromArtmo(filenameRaster=join(outdir, 'RegressionSample.fromArtmo.raster.bsq'),
            filenameRegression=join(outdir, 'RegressionSample.fromArtmo.regression.bsq'),
            filenameArtmo=directional_reflectance,
            filenameArtmoMeta=directional_reflectance_meta,
            scale=10000)

        resampled = enmap.sensorDefinition().resampleRaster(raster=sample.raster(),
            filename=join(outdir, 'RegressionSample.fromArtmo.enmap.bsq'),
            resampleAlg=SensorDefinition.RESAMPLE_LINEAR)

        sampleEnmap = RegressionSample(raster=resampled, regression=sample.regression())

        rfr = Regressor(sklEstimator=RandomForestRegressor()).fit(sample=sampleEnmap)

        prediction = rfr.predict(raster=enmap, filename=join(outdir, 'RegressionSample.fromArtmo.rfrPrediction.bsq'))
        print(resampled)
        print(prediction)


class TestRegressor(TestCase):

    def test_RegressorFitPredict(self):
        rfr = Regressor(sklEstimator=RandomForestRegressor())
        print(rfr)
        rfr.fit(sample=enmapRegressionSample)
        print(rfr.predict(filename=join(outdir, 'rfrRegression.bsq'), raster=enmap, mask=vector))

    def test_RegressorPredictOnSpectrallyHigherResolved(self):
        # subset bands
        hires30m = Raster(filename=enmapboxtestdata.hires).resample(filename='/vsimem/lowres.bsq', grid=enmap.grid())
        regressionSample = RegressionSample(raster=hires30m, regression=enmapRegression)
        rfr = Regressor(sklEstimator=RandomForestRegressor()).fit(sample=regressionSample)
        print(rfr.predict(filename=join(outdir, 'RegressorPredictOnSpectrallyHigherResolved.rfrRegression.bsq'),
            raster=enmap))

    def test_RegressorPerformance(self):
        rfr = Regressor(sklEstimator=RandomForestRegressor())
        rfr.fit(sample=enmapRegressionSample)
        report = rfr.performanceCrossValidation(nfold=3).report()
        report.saveHTML(filename=join(outdir, 'RegressorPerformanceCrossValidation.html'))
        report = rfr.performanceTraining().report()
        report.saveHTML(filename=join(outdir, 'RegressorPerformanceTraining.html'))

    def test_RegressorRefitOnFeatureSubset(self):
        rfr = Regressor(sklEstimator=RandomForestRegressor())
        rfr.fit(sample=enmapRegressionSample)
        rfr2 = rfr.refitOnFeatureSubset(indices=range(0, enmap.dataset().zsize(), 2),
            filenameRaster='/vsimem/raster.bsq',
            filenameRegression='/vsimem/regression.bsq')
        prediction = rfr2.predict(filename=join(outdir, 'RegressorRefitOnFeatureSubset.rfrPrediction.bsq'),
            raster=enmap)
        report = rfr2.performanceTraining().report()
        report.saveHTML(filename=join(outdir, 'RegressorPerformanceTraining.html'))
        print(rfr2.sample().raster().dataset().zsize())


class TestRecipe(TestCase):

    def test_mergeSamples(self):
        fractionSample1 = enmapClassificationSample.synthMix(
            filenameFeatures='/vsimem/features1.bsq',
            filenameFractions='/vsimem/fractions1.bsq',
            mixingComplexities={2: 0.5, 3: 0.5}, classProbabilities='equalized',
            n=10, target=1)

        fractionSample2 = enmapClassificationSample.synthMix(
            filenameFeatures='/vsimem/features2.bsq',
            filenameFractions='/vsimem/fractions2.bsq',
            mixingComplexities={2: 0.5, 3: 0.5}, classProbabilities='equalized',
            n=20, target=1)

        features1, labels1 = fractionSample1.extractAsArray()
        features2, labels2 = fractionSample2.extractAsArray()
        features = np.atleast_3d(np.concatenate([features1, features2], axis=1))
        labels = np.atleast_3d(np.concatenate([labels1, labels2], axis=1))

        raster = Raster.fromArray(array=features, filename='raster.bsq',
            noDataValues=fractionSample1.raster().noDataValues(),
            descriptions=[band.description() for band in
                          fractionSample1.raster().dataset().bands()])  # a bit ugly, need to introduce Raster.descriptions() to get all band names directly!!!
        fraction = Fraction.fromArray(array=labels, filename='classification.bsq',
            noDataValues=fractionSample1.fraction().noDataValues(),
            descriptions=[band.description() for band in
                          fractionSample1.fraction().dataset().bands()])  # a bit ugly, need to introduce Raster.descriptions() to get all band names directly!!!

        fractionSample = FractionSample(raster=raster, fraction=fraction)

        rfr = Regressor(sklEstimator=RandomForestRegressor()).fit(fractionSample)
        print(rfr)


if __name__ == '__main__':
    print('output directory: ' + outdir)
