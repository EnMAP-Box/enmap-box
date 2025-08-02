import webbrowser

from PyQt5.QtWidgets import QMenu

from enmapbox.gui.applications import EnMAPBoxApplication

try:
    from enmapbox.apps.SpecDeepMap.processing_algorithm_dataset_maker import DatasetMaker
    from enmapbox.apps.SpecDeepMap.processing_algorithm_raster_splitter import RasterSplitter
    from enmapbox.apps.SpecDeepMap.processing_algorithm_deep_learning_trainer import DL_Trainer
    from enmapbox.apps.SpecDeepMap.processing_algorithm_deep_learning_mapper import DL_Mapper
    from enmapbox.apps.SpecDeepMap.processing_algorithm_tensorboard_visualizer import Tensorboard_visualizer
    from enmapbox.apps.SpecDeepMap.processing_algorithm_tester import DL_Tester
    import psutil

    wrongEnv = False
    import_error = None
except Exception as ex:
    wrongEnv = True
    import_error = ex

URL_ONLINE_DOCUMENTATION = 'https://enmap-box.readthedocs.io/en/latest/usr_section/application_tutorials/specdeepmap/tutorial_specdeepmap.html'


# test

def enmapboxApplicationFactory(enmapBox):
    return [SpecDeepMap(enmapBox)]


class SpecDeepMap(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = 'SpecDeepMap'
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    def menu(self, appMenu: QMenu):

        m: QMenu = appMenu.addMenu('SpecDeepMap')
        m.setToolTipsVisible(True)

        a = m.addAction('Online Documentation')
        a.triggered.connect(lambda: webbrowser.open(URL_ONLINE_DOCUMENTATION))

        a1 = m.addAction('Raster Splitter')
        a2 = m.addAction('Dataset Maker')
        a3 = m.addAction('Deep Learning Trainer')
        a4 = m.addAction('Deep Learning Mapper')
        a5 = m.addAction('Deep Learning Tester')
        a6 = m.addAction('Tensorboard Visualizer')
        actions = [a1, a2, a3, a4, a5, a6]
        if wrongEnv:
            for a in actions:
                a.setEnabled(False)
                a.setToolTip(f'Import error:<br>{import_error}')
        else:
            algs = [RasterSplitter(),
                    DatasetMaker(),
                    DL_Trainer(),
                    DL_Mapper(),
                    DL_Tester(),
                    Tensorboard_visualizer()]
            for action, alg in zip(actions, algs):
                alg_id = f'enmapbox:{alg.id()}'
                action.triggered.connect(lambda *args, aid=alg_id:
                                         self.enmapbox.showProcessingAlgorithmDialog(aid))
        return m

    # returns a list of EnMAPBoxApplications
    def processingAlgorithms(self):

        if wrongEnv:
            return []
        else:
            return [RasterSplitter(), DatasetMaker(), DL_Trainer(), DL_Mapper(), Tensorboard_visualizer(),
                    DL_Tester()]  # ,DL_Train_MOD()] #DL_Train()#DatasetSplitter() #,,DatasetSplitter(),DL_Train(),RasterSplitterR(),DatasetSplitter(),RasterSplitterRP()
