from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

clusterer = KMeans(n_init=10)
estimator = make_pipeline(StandardScaler(), clusterer)
