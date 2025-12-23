from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a Partial Least Squares Regression.')

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters.',
                links=[Link('https://scikit-learn.org/stable/modules/generated/sklearn.cross_decomposition.PLSRegression.html',
                            'PLSRegression')
                       ])