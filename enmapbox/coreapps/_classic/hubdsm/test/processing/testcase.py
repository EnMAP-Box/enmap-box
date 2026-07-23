import unittest

from _classic.hubdsm.processing.enmapalgorithm import EnMAPAlgorithm

from qgis.core import *

# init QGIS
from processing.core.Processing import Processing
from qgis.core import QgsApplication

qgsApp = QgsApplication([], True)
qgsApp.initQgis()


# activate QGIS log in PyCharm
def printQgisLog(tb, error, level):
    print(tb)


QgsApplication.instance().messageLog().messageReceived.connect(printQgisLog)

Processing.initialize()


class ProcessingFeedback(QgsProcessingFeedback):
    pass


class TestCase(unittest.TestCase):

    @staticmethod
    def runalg(alg: EnMAPAlgorithm, io: dict):
        assert isinstance(alg, EnMAPAlgorithm)
        print(f'\n{"#" * 80}')
        alg.defineCharacteristics()
        print(alg.__class__.__name__,
            '({} -> {}), {}, {}'.format(alg.group(), alg.displayName(), alg.groupId(), alg.name()))
        print('parameters = {}'.format(repr(io)))
        return Processing.runAlgorithm(alg, parameters=io, feedback=ProcessingFeedback())
