from enmapbox.gui.applications import EnMAPBoxApplication

try:
    from enmapbox.apps.SpecDeepMap.processingalgorithmDS_SUM12 import DatasetSplitter_SUM
    from enmapbox.apps.SpecDeepMap.processingalgorithmRSRASTER_PERCENT7 import RasterSplitterRP
    from enmapbox.apps.SpecDeepMap.processingalgorithm_DL_UNET50_MOD_15_059_16 import DL_Train_MOD
    from enmapbox.apps.SpecDeepMap.processingalgorithm_PRED_GT_NO_DATA_mod11 import DL_Mapper
    from enmapbox.apps.SpecDeepMap.processingalgorithm_Tensorboard2 import Tensorboard
    from enmapbox.apps.SpecDeepMap.processingalgorithm_Tester4 import DL_Tester

    wrongEnv = False
except Exception:
    wrongEnv= True

#test

def enmapboxApplicationFactory(enmapBox):
    return [SpecDeepMap(enmapBox)]


class SpecDeepMap(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'SpecDeepMap'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    # returns a list of EnMAPBoxApplications
    def processingAlgorithms(self):

        if wrongEnv:
            return []
        else:
            return [RasterSplitterRP(), DatasetSplitter_SUM(), DL_Train_MOD(), DL_Mapper(), Tensorboard(),DL_Tester()]  # ,DL_Train_MOD()] #DL_Train()#DatasetSplitter() #,,DatasetSplitter(),DL_Train(),RasterSplitterR(),DatasetSplitter(),RasterSplitterRP()
