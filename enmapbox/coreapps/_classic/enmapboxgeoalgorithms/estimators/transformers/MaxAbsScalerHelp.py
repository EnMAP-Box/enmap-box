from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a MaxAbsScaler (scale each feature by its maximum absolute value). See also {}.',
               links=[Link('http://scikit-learn.org/stable/auto_examples/preprocessing/plot_all_scaling.html', 'examples for different scaling methods')])

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MaxAbsScaler.html',
                            'MaxAbsScaler')
                       ])