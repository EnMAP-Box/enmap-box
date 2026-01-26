from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.kernel_ridge import KernelRidge

krr = KernelRidge()
param_grid = {'kernel': ['rbf'],
              'gamma': [0.001, 0.01, 0.1, 1, 10, 100, 1000],
              'alpha': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
tunedKRR = GridSearchCV(cv=3, estimator=krr, scoring='neg_mean_absolute_error', param_grid=param_grid)
scaledAndTunedKRR = make_pipeline(StandardScaler(), tunedKRR)
estimator = scaledAndTunedKRR
