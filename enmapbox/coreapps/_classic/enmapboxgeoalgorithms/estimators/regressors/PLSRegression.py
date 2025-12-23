from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.cross_decomposition import PLSRegression

plsr = PLSRegression(scale=True)
max_components = 3
param_grid = {'n_components': [i+1 for i in range(max_components)]}
estimator = GridSearchCV(cv=3, estimator=plsr, scoring='neg_mean_absolute_error', param_grid=param_grid)
