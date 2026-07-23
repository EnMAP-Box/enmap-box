from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text = 'Fits a Random Forest Classifier')

helpCode = Help(
    text="Scikit-learn python code. See {} for information on different parameters. If this code is not altered, scikit-learn default settings will be used. 'Hint: you might want to alter e.g. the n_estimators value (number of trees), as the default is 10. So the line of code might be altered to 'estimator = RandomForestClassifier(n_estimators=100).'",
    links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html', 'RandomForestClassifier')]
)
