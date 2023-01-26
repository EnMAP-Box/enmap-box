import unittest
from enmapbox.qgispluginsupport.qps.testing import TestCase, TestObjects
from enmapbox.qgispluginsupport.qps.speclib.gui import SpectralLibraryWidget
from enmapbox.qgispluginsupport.qps import initResources
from specmixapp.specmix import *


class SpecMixTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass(cls)
        initResources()

    def test_parameterModel(self):

        speclib = TestObjects.createSpectralLibrary(10)
        p1 = speclib[0]
        p2 = speclib[1]
        p3 = speclib[3]
        m = SpecMixParameterModel()
        m.addProfiles(p1)
        m.addProfiles([p2, p3])
        m.removeProfiles([p1, p3])

        m.setProfileLimit(100)
        self.assertEqual(m.profileLimit(), 100)

        self.assertIsInstance(m, QAbstractTableModel)

    def test_speclibListModel(self):

        m = SpectralLibraryListModel()
        self.assertIsInstance(m, QAbstractListModel)
        sl = TestObjects.createSpectralLibrary(10)
        sl.setName('Speclib 1')
        sl2 = TestObjects.createSpectralLibrary(5)
        sl2.setName('Speclib 2')
        self.assertTrue(len(m) == 0)
        m.addSpectralLibraries(sl)
        self.assertEqual(len(m), 1)

        m.addSpectralLibraries([sl])

        self.assertEqual(len(m), 1)

        w = QListView()
        w.setModel(m)
        self.showGui(w)

    def test_sliderwidget(self):

        w = SpecMixSliderWidget()
        w.setMaximum(10)
        w.setDecimals(2)
        self.showGui(w)

    def test_MainWidget(self):

        slib = TestObjects.createSpectralLibrary(10)
        slib.setName('My Speclib')
        sl2 = TestObjects.createSpectralLibrary(5)
        sl2.setName('SLIB 2')
        slw = SpectralLibraryWidget(speclib=slib)

        w = SpecMixWidget()
        w.addSpectralLibraries(slw.speclib())
        self.assertEqual(w.selectedSpeclib(), slib)
        w.addSpectralLibraries(sl2)

        w.selectSpeclib(sl2)
        self.assertEqual(w.selectedSpeclib(), sl2)

        self.assertEqual(len(w.mSpeclibModel), 2)

        w.selectSpeclib(slib)
        w.cbSyncWithSelection.setChecked(True)
        slib.selectByIds([0, 1, 2, 3, 4])

        if True:
            self.showGui([slw, w])
        else:
            W = QWidget()
            W.setLayout(QVBoxLayout())
            W.layout().addWidget(slw)
            W.layout().addWidget(w)

            self.showGui(W)

    def test_EnMAPBoxApplication(self):

        from specmixapp import SpecMixApp
        from enmapbox import initAll
        from enmapbox.gui.enmapboxgui import EnMAPBox
        initAll()
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        app = SpecMixApp(EB)
        EB.addApplication(app)
        app.startGUI()
        self.showGui(EB.ui)


if __name__ == '__main__':
    unittest.main()
