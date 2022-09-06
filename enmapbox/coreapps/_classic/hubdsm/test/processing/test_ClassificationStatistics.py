import numpy as np
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRasterLayer, QgsPalettedRasterRenderer

from _classic.hubdsm.core.category import Category  # needed for eval
from _classic.hubdsm.core.color import Color  # needed for eval
from _classic.hubdsm.core.extent import Extent
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.location import Location
from _classic.hubdsm.core.projection import Projection
from _classic.hubdsm.core.raster import Raster
from _classic.hubdsm.core.resolution import Resolution
from _classic.hubdsm.core.size import Size
from _classic.hubdsm.processing.classificationstatistics import ClassificationStatistics, ClassificationStatisticsPlot
from _classic.hubdsm.test.processing.testcase import TestCase


class TestClassificationStatistics(TestCase):

    def test(self):
        filename = '/vsimem/c.bsq'
        res = 100
        raster = Raster.createFromArray(
            array=np.atleast_3d([0, 1, 1, 2, 3, 10]),
            grid=Grid(
                extent=Extent(ul=Location(0, 0), size=Size(1 * res, 6 * res)),
                resolution=Resolution(res, res),
                projection=Projection.fromEpsg(4326),
            ),
            filename=filename
        )
        del raster

        layer = QgsRasterLayer(filename)
        classes = [
            QgsPalettedRasterRenderer.Class(value=1, color=QColor(255, 0, 0), label='C1'),
            QgsPalettedRasterRenderer.Class(value=3, color=QColor(0, 255, 0), label='C2'),
        ]
        renderer = QgsPalettedRasterRenderer(input=layer.dataProvider(), bandNumber=1, classes=classes)
        layer.setRenderer(renderer=renderer)

        assert isinstance(layer.renderer(), QgsPalettedRasterRenderer)
        alg = ClassificationStatistics()
        io = {alg.P_CLASSIFICATION: layer}
        result = self.runalg(alg=alg, io=io)

        self.assertEqual(
            "[Category(id=1, name='C1', color=Color(red=255, green=0, blue=0, alpha=255)), Category(id=3, name='C2', color=Color(red=0, green=255, blue=0, alpha=255))]",
            result[alg.P_OUTPUT_CATEGORIES]
        )
        self.assertEqual(
            "[2, 1]",
            result[alg.P_OUTPUT_COUNTS]
        )

        showPlot = True
        if showPlot:
            categories = eval(result[alg.P_OUTPUT_CATEGORIES])
            counts = eval(result[alg.P_OUTPUT_COUNTS])
            from enmapbox.testing import initQgisApplication
            qgsApp = initQgisApplication()
            widget = ClassificationStatisticsPlot(
                categories=categories,
                counts=counts,
                layer=layer
            )
            widget.show()
            qgsApp.exec_()
