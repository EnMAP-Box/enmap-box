from os.path import splitext
from _classic.hubflow.core import LoggerFlowObject

global estimator, estimatorFilename

filename = '{}.info.txt'.format(splitext(estimatorFilename)[0])
LoggerFlowObject(filename=filename).setSklEstimatorItems(estimator=estimator).logItems()

