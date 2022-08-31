from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a Support Vector Regression.')

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters. See {} for information on grid search and {} for scaling.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html',
                            'SVR'),
                       Link('http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html','GridSearchCV'),
                       Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html','StandardScaler')
                       ])
