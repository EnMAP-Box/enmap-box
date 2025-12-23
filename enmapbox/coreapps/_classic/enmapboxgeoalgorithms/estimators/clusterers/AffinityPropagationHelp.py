from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text = 'Fits a Affinity Propagation clusterer (input data will be scaled).')

helpCode = Help(
    text='Scikit-learn python code. For information on different parameters have a look at {}. See {} for information on scaling',
    links=[
        Link('http://scikit-learn.org/stable/modules/generated/sklearn.cluster.AffinityPropagation.html',
             'AffinityPropagation'),
        Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html',
             'StandardScaler')
    ])
