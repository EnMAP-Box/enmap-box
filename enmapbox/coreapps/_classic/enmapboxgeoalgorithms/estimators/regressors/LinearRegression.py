from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

linearRegression = LinearRegression()
estimator = make_pipeline(StandardScaler(), linearRegression)
