from sklearn.ensemble import RandomForestRegressor
estimator = RandomForestRegressor(n_estimators=100, oob_score=True)
