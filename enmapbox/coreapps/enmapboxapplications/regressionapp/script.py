from qgis.PyQt.QtWidgets import QApplication, QProgressBar

from _classic.hubdc.progressbar import CUIProgressBar
from _classic.hubflow.core import *


class ProgressBar(CUIProgressBar):

    def __init__(self, bar):
        assert isinstance(bar, QProgressBar)
        self.bar = bar
        self.bar.setMinimum(0)
        self.bar.setMaximum(100)

    def setText(self, text):
        pass

    def setPercentage(self, percentage):
        self.bar.setValue(int(percentage))
        QApplication.processEvents()


def regressionWorkflow(
        sample, regressor, raster, strata,
        n,
        cv,
        saveSampledRegression, saveSampledRegressionComplement,
        saveModel, saveRegression, saveReport,
        filenameSampledRegression, filenameSampledRegressionComplement,
        filenameModel, filenameRegression, filenameReport,
        ui=None
):
    assert isinstance(sample, RegressionSample)
    assert isinstance(regressor, Regressor)

    def setInfo(text):
        if ui is not None:
            ui.log(text)
        else:
            print(text)

    if ui is not None:
        progressBar = ProgressBar(ui.uiProgressBar_)
    else:
        progressBar = None

    setInfo('Step 1: draw random sample')
    if n is not None:
        assert isinstance(strata, Classification)
        points = Vector.fromRandomPointsFromClassification(
            filename='/vsimem/regression_workflow_random_points.gpkg',
            classification=strata, n=n,
            **ApplierOptions(progressBar=progressBar))
        sample = RegressionSample(raster=sample.raster(),
            regression=sample.regression(),
            mask=points)
    else:
        points = None

    if saveSampledRegression:
        sampledRegression = sample.regression().applyMask(filename=filenameSampledRegression, mask=points,
            **ApplierOptions(progressBar=progressBar))
    else:
        sampledRegression = None

    if saveSampledRegressionComplement:
        if sampledRegression is None:
            sampledRegression = sample.regression().applyMask(
                filename='/vsimem/classification_workflow/sampled.bsq', mask=points)
        sample.regression().applyMask(filename=filenameSampledRegressionComplement,
            mask=Mask(filename=sampledRegression.filename(), invert=True),
            **ApplierOptions(progressBar=progressBar))

    setInfo('Step 2: fit regressor')
    regressor.fit(sample)

    from enmapbox import EnMAPBox
    enmapBox: EnMAPBox = EnMAPBox.instance()

    if saveModel:
        regressor.pickle(filename=filenameModel)
        enmapBox.addSource(filenameModel)

    setInfo('Step 3: predict regression')
    if saveRegression:
        regressor.predict(filename=filenameRegression, raster=raster, progressBar=progressBar)
        enmapBox.addSource(filenameRegression)

    setInfo('Step 4: assess cross-validation performance')
    if saveReport:
        regressor.performanceCrossValidation(nfold=cv).report().saveHTML(filename=filenameReport)
        enmapBox.addSource(filenameReport)


def test():
    from sklearn.ensemble import RandomForestRegressor
    import enmapboxtestdata

    outdir = r'c:\outputs'

    raster = Raster(filename=r'C:\Work\data\sam_cooper\enmap_subset.bsq')
    regression = VectorRegression(filename=r'C:\Work\data\sam_cooper\biomass_training.shp',
        regressionAttribute='biomass_la')
    regression = Regression.fromVectorRegression(
        filename=join(outdir, 'rasterized_regression.bsq'), vectorRegression=regression, grid=raster.grid()
    )

    sample = RegressionSample(raster=raster, regression=regression)
    n = [76, 106, 84, 28, 4]
    bin_edges = [0., 100., 200., 300., 400., 500.]

    def doit(array, bin_edges):
        result = np.zeros_like(array, dtype=np.uint8)
        for i, v0 in enumerate(bin_edges[:-1], 1):
            result[array >= v0] = i
        result[array > bin_edges[-1]] = 0
        return result

    kwds = dict(bin_edges=bin_edges)
    strataFilename = join(outdir, 'strata.bsq')
    tmp = regression.applySpatial(filename=strataFilename, function=doit, kwds=kwds)
    del tmp
    strata = Classification(strataFilename, classDefinition=ClassDefinition(classes=len(n)))

    regressionWorkflow(sample=sample,
        regressor=Regressor(sklEstimator=RandomForestRegressor(n_estimators=10)),
        raster=raster,
        strata=strata,
        n=n,
        cv=10,
        saveSampledRegression=True,
        saveSampledRegressionComplement=True,
        saveModel=True,
        saveRegression=True,
        saveReport=True,
        filenameModel=join(outdir, 'model.pkl'),
        filenameRegression=join(outdir, 'regression.bsq'),
        filenameReport=join(outdir, 'report.html'),
        filenameSampledRegression=join(outdir, 'sample_regression.bsq'),
        filenameSampledRegressionComplement=join(outdir, 'sampleComplement_regression.bsq'),
    )


if __name__ == '__main__':
    CUIProgressBar.SILENT = False
    test()
