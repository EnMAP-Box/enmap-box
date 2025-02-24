from enmapbox.gui.applications import EnMAPBoxApplication

try:
    from enmapbox.apps.SpecDeepMap.processingalgorithm_dataset_maker import DatasetMaker
    from enmapbox.apps.SpecDeepMap.processingalgorithm_raster_splitter import RasterSplitter
    from enmapbox.apps.SpecDeepMap.processingalgorithm_deep_learning_trainer import DL_Trainer
    from enmapbox.apps.SpecDeepMap.processingalgorithm_deep_learning_mapper import DL_Mapper
    from enmapbox.apps.SpecDeepMap.processingalgorithm_Tensorboard2 import Tensorboard
    from enmapbox.apps.SpecDeepMap.processingalgorithm_Tester4 import DL_Tester

    wrongEnv = False
except Exception as ex:
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
            return [RasterSplitter(), DatasetMaker(), DL_Trainer(), DL_Mapper(), Tensorboard(),DL_Tester()]  # ,DL_Train_MOD()] #DL_Train()#DatasetSplitter() #,,DatasetSplitter(),DL_Train(),RasterSplitterR(),DatasetSplitter(),RasterSplitterRP()
