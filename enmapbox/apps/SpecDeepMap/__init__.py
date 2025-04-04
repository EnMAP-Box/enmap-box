from enmapbox.apps.SpecDeepMap.processing_algorithm_dataset_maker import DatasetMaker
from enmapbox.apps.SpecDeepMap.processing_algorithm_deep_learning_mapper import DL_Mapper
from enmapbox.apps.SpecDeepMap.processing_algorithm_deep_learning_trainer_MicaSense import DL_Trainer
from enmapbox.apps.SpecDeepMap.processing_algorithm_raster_splitter import RasterSplitter
from enmapbox.apps.SpecDeepMap.processing_algorithm_tensorboard_visualizer import Tensorboard_visualizer
from enmapbox.apps.SpecDeepMap.processing_algorithm_tester import DL_Tester
from enmapbox.gui.applications import EnMAPBoxApplication


# test

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
        return [RasterSplitter(), DatasetMaker(), DL_Trainer(), DL_Mapper(), Tensorboard_visualizer(),
                DL_Tester()]  # ,DL_Train_MOD()] #DL_Train()#DatasetSplitter() #,,DatasetSplitter(),DL_Train(),RasterSplitterR(),DatasetSplitter(),RasterSplitterRP()
