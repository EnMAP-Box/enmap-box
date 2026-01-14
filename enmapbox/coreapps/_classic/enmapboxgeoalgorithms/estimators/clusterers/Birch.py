from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import Birch

clusterer = Birch()
estimator = make_pipeline(StandardScaler(), clusterer)
