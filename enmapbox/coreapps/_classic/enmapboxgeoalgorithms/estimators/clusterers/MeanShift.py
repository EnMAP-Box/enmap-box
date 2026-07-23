from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import MeanShift

clusterer = MeanShift()
estimator = make_pipeline(StandardScaler(), clusterer)
