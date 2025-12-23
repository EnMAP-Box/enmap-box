from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import KernelPCA

kernelPCA = KernelPCA(n_components=3, fit_inverse_transform=True)
estimator = make_pipeline(StandardScaler(), kernelPCA)
