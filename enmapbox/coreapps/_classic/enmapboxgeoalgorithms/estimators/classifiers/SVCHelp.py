from _classic.enmapboxgeoalgorithms.provider import Help, Link

helpAlg = Help(text='Fits a Support Vector Classification. Input data will be scaled and grid search is used for model selection.')

helpCode = Help(
    text='Scikit-learn python code. For information on different parameters have a look at {}. See {} for information on grid search and {} for scaling.',
    links=[Link('http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html', 'SVC'),
           Link('http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html',
                'GridSearchCV'),
           Link('http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html',
                'StandardScaler')]
)
