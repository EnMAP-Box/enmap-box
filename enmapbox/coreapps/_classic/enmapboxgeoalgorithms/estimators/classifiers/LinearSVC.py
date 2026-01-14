from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

svc = LinearSVC()
param_grid = {'C': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}
tunedSVC = GridSearchCV(cv=3, estimator=svc, scoring='f1_macro', param_grid=param_grid)
estimator = make_pipeline(StandardScaler(), tunedSVC)
