import os.path
import unittest
from pathlib import Path

from osgeo import gdal

from engeomap.enmapboxintegration import EnGeoMAP
from engeomap.userinterfaces import EnGeoMAPGUI, Worker
from enmapbox import initAll
from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase
from enmapbox.testing import start_app
from qgis.core import QgsRasterLayer, QgsFileUtils

start_app()
initAll()


class EnGeoMAPTests(EnMAPBoxTestCase):

    def test_app(self):
        enmapBox = EnMAPBox(load_core_apps=False, load_other_apps=False)

        EGM = EnGeoMAP(enmapBox)
        EGM.startGUI()
        self.showGui(enmapBox.ui)

    def test_ui(self):
        ui = EnGeoMAPGUI()
        self.showGui(ui)

    def test_gamsberg(self):
        from enmapboxtestdata import engeomap_cubus_gamsberg_subset, \
            engeomap_gamsberg_field_library, engeomap_gamesberg_field_library_color_mod

        ui = EnGeoMAPGUI()
        ui.input_image.setText(str(engeomap_cubus_gamsberg_subset))
        ui.speclib.setText(str(engeomap_gamsberg_field_library))
        ui.colormap.setText(str(engeomap_gamesberg_field_library_color_mod))

        params = ui.collectParameters()

        worker = Worker()
        worker.run()

        root = Path(engeomap_cubus_gamsberg_subset).parent
        bn = os.path.basename(Path(engeomap_cubus_gamsberg_subset).name)

        to_delete = []
        for suffix in ['abundance_result',
                       'abundance_unmix__best_unmix_coleur',
                       'abundance_unmix__best_unmix_coleur_class_geotiff.tif',
                       'bestmatches_correlation__best_fit_coleur',
                       'bestmatches_correlation__best_fit_coleur_class_geotiff.tif',
                       'correlation_result']:
            path = root / f'{bn}_{suffix}'
            self.assertTrue(path.is_file(), msg=f'{path} does not exist')

            lyr: QgsRasterLayer = QgsRasterLayer(path.as_posix())
            self.assertTrue(lyr.isValid())
            del lyr
            to_delete.append(path)

        # delete test results
        for p in to_delete:
            ds: gdal.Dataset = gdal.Open(p.as_posix())
            files = set(ds.GetFileList())
            del ds
            files.update(set(QgsFileUtils.sidecarFilesForPath(p.as_posix())))

            for f in files:
                os.remove(f)


if __name__ == "__main__":
    unittest.main(buffer=False)
