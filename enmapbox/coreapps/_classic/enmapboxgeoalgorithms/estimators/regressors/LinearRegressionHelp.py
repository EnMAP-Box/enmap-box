from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a Linear Regression.')

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters. See {} for information on scaling.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html', 'LinearRegression'),
                       Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html', 'StandardScaler')
                       ])
