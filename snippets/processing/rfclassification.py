from enmapbox.testing import start_app
from enmapboxprocessing.algorithm.fitclassifieralgorithmbase import FitClassifierAlgorithmBase
from enmapboxprocessing.algorithm.predictclassificationalgorithm import PredictClassificationAlgorithm
from enmapboxprocessing.algorithm.prepareclassificationdatasetfromcategorizedvectoralgorithm import \
    PrepareClassificationDatasetFromCategorizedVectorAlgorithm
from enmapbox.exampledata import enmap, landcover_polygon
from processing.core.Processing import Processing

qgsApp = start_app()

# prepare dataset
alg = PrepareClassificationDatasetFromCategorizedVectorAlgorithm()
parameters = {
    alg.P_FEATURE_RASTER: enmap,
    alg.P_CATEGORIZED_VECTOR: landcover_polygon,
    alg.P_OUTPUT_DATASET: 'c:/test/dataset.pkl'
}
Processing.runAlgorithm(alg, parameters)


# fit RFC
class MyRFC(FitClassifierAlgorithmBase):

    def displayName(self) -> str:
        return ''

    def shortDescription(self) -> str:
        return ''

    def helpParameterCode(self) -> str:
        return ''

    def code(self):
        from sklearn.ensemble import RandomForestClassifier
        classifier = RandomForestClassifier(n_estimators=10, oob_score=True, random_state=42)
        return classifier


alg = MyRFC()
parameters = {
    alg.P_DATASET: 'c:/test/dataset.pkl',
    alg.P_CLASSIFIER: str(alg.defaultCodeAsString()),
    alg.P_OUTPUT_CLASSIFIER: 'c:/test/classifier.pkl',
}
Processing.runAlgorithm(alg, parameters)

# predict RFC
alg = PredictClassificationAlgorithm()
alg.initAlgorithm()
parameters = {
    alg.P_RASTER: enmap,
    alg.P_CLASSIFIER: 'c:/test/classifier.pkl',
    alg.P_OUTPUT_CLASSIFICATION: 'c:/test/classification.tif'
}
Processing.runAlgorithm(alg, parameters)
