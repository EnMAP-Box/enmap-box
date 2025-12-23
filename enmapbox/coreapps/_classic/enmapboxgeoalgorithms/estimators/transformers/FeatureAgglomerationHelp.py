from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a Feature Agglomeration.')

helpCode = Help(text='Scikit-learn python code. See {} for information on different parameters.',
                links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.cluster.FeatureAgglomeration.html',
                            'FeatureAgglomeration')
                       ])