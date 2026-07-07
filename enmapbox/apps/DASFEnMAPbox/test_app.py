import unittest

from enmapbox import registerEnMAPBoxProcessingProvider
from enmapbox.apps.DASFEnMAPbox import DASFretrievalApp
from enmapbox.testing import start_app, TestCase

start_app()
registerEnMAPBoxProcessingProvider()


class DASFTests(TestCase):

    def test_dasf(self):
        from enmapbox.gui.enmapboxgui import EnMAPBox
        enmapBox = EnMAPBox()
        enmapBox.run()
        enmapBox.openExampleData(mapWindows=1)
        enmapBox.addApplication(DASFretrievalApp(enmapBox=enmapBox))

        self.showGui(enmapBox.ui)
        enmapBox.close()


if __name__ == '__main__':
    unittest.main(buffer=False)
