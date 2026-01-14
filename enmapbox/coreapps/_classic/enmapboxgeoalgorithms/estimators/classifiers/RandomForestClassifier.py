from sklearn.ensemble import RandomForestClassifier
estimator = RandomForestClassifier(n_estimators=100, oob_score=True)
