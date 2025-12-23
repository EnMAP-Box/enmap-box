from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a Robust Scaler (scales features using statistics that are robust to outliers). Click {} for example. See also {}.',
               links=[Link('http://scikit-learn.org/0.18/auto_examples/preprocessing/plot_robust_scaling.html', 'here'),
                      Link('http://scikit-learn.org/stable/auto_examples/preprocessing/plot_all_scaling.html', 'examples for different scaling methods')])

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html',
                            'RobustScaler')
                       ])