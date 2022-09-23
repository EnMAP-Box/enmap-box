from enmapboxapplications.widgets.core import UiWorkflowMainWindow, WorkflowWorker


from _classic.hubflow.core import *

pathUi = join(dirname(__file__), 'ui')

class TestWorkflow(UiWorkflowMainWindow):

    def __init__(self, parent=None):
        UiWorkflowMainWindow.__init__(self, parent)

    def worker(self):
        return Worker()

class Worker(WorkflowWorker):

    def run_(self, progressCallback, *args, **kwargs):
        from _classic.hubflow.core import VectorClassification, Classification, Raster, ApplierOptions
        import enmapboxtestdata


        import time
        time.time()

        vector = VectorClassification(filename=enmapboxtestdata.landcover_polygon, classAttribute='level_2_id')
        Classification.fromClassification(
            filename=r'c:\output\classification{}.bsq'.format(str(time.time())), classification=vector,
            grid=Raster(filename=enmapboxtestdata.enmap).grid().atResolution(10),
            **ApplierOptions(progressCallback=progressCallback))