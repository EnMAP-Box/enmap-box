from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import FastICA

fastICA = FastICA(n_components=3)
estimator = make_pipeline(StandardScaler(), fastICA)
