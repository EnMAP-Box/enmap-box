from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits an Imputer (Imputation transformer for completing missing values).')

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.Imputer.html',
                            'Imputer')
                       ])