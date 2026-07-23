from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits Gaussian Process Classifier. See {} for further information.',
               links=[Link('http://scikit-learn.org/stable/modules/gaussian_process.html', 'Gaussian Processes')])

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.GaussianProcessClassifier.html',
                            'GaussianProcessClassifier')])
