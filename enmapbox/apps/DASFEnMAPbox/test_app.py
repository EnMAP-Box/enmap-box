import unittest
from enmapbox.testing import start_app, TestCase
from enmapbox import registerEnMAPBoxProcessingProvider

start_app()
registerEnMAPBoxProcessingProvider()


class DASFTests(TestCase):

    def test_dasf(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox()
        enmapBox.run()
        enmapBox.openExampleData(mapWindows=1)
        from DASFEnMAPbox import DASFretrievalApp
        enmapBox.addApplication(DASFretrievalApp(enmapBox=enmapBox))

        self.showGui(enmapBox.ui)
        enmapBox.close()


if __name__ == '__main__':
    unittest.main(buffer=False)
