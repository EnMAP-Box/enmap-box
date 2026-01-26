from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AffinityPropagation

clusterer = AffinityPropagation()
estimator = make_pipeline(StandardScaler(), clusterer)
