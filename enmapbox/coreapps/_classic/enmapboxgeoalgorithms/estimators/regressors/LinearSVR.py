from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVR

svr = LinearSVR()
param_grid = {'epsilon' : [0.], 'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
tunedSVR = GridSearchCV(cv=3, estimator=svr, scoring='neg_mean_absolute_error', param_grid=param_grid)
scaledAndTunedSVR = make_pipeline(StandardScaler(), tunedSVR)
estimator = MultiOutputRegressor(scaledAndTunedSVR)
