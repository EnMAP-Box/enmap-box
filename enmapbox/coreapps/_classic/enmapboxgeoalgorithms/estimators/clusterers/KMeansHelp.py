from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text = 'Fits a KMeans clusterer (input data will be scaled).')

helpCode = Help(
    text='Scikit-learn python code. For information on different parameters have a look at {}. See {} for information on scaling',
    links=[
        Link('http://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html',
             'KMeans'),
        Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html',
             'StandardScaler')
    ])