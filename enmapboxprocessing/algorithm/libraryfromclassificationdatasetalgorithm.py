from math import ceil
from typing import Dict, Any, List, Tuple

import numpy as np

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from enmapboxprocessing.librarydriver import LibraryDriver
from enmapboxprocessing.typing import ClassifierDump
from enmapboxprocessing.utils import Utils
from qgis.core import QgsGeometry, QgsPointXY, Qgis, QgsCoordinateReferenceSystem, QgsMapLayer, QgsVectorLayer, \
    QgsProcessingContext, QgsProcessingFeedback


@typechecked
class LibraryFromClassificationDatasetAlgorithm(EnMAPProcessingAlgorithm):
    P_DATASET, _DATASET = 'dataset', 'Dataset'
    P_OUTPUT_LIBRARY, _OUTPUT_LIBRARY = 'outputLibrary', 'Output spectral library'

    @classmethod
    def displayName(cls) -> str:
        return 'Create spectral library (from classification dataset)'

    def shortDescription(self) -> str:
        return 'Create a spectral library from a classification dataset.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._DATASET, 'A classification dataset.'),
            (self._OUTPUT_LIBRARY, self.VectorFileDestination)
        ]

    def group(self):
        return Group.SpectralLibrary.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterClassificationDataset(self.P_DATASET, self._DATASET)
        self.addParameterVectorDestination(self.P_OUTPUT_LIBRARY, self._OUTPUT_LIBRARY)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        filenameDataset = self.parameterAsFile(parameters, self.P_DATASET, context)
        filename = self.parameterAsOutputLayer(parameters, self.P_OUTPUT_LIBRARY, context)

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            dump = ClassifierDump.fromFile(filenameDataset)
            categoryNames = {c.value: c.name for c in dump.categories}
            data = list()
            geometries = list()

            for i, (xvalues, yvalue) in enumerate(zip(dump.X, dump.y.flatten().tolist())):
                values = {
                    'profiles': {'y': xvalues.tolist()},
                    'CategoryValue': yvalue, 'CategoryName': categoryNames[yvalue]
                }

                data.append(values)
                if dump.locations is None:
                    # even without locations, we need to create a layer WITH geometries,
                    # otherwise we can't properly style the layer (because it's just a table, which can't be styles)
                    geometry = QgsGeometry.fromPointXY(QgsPointXY())
                else:
                    geometry = QgsGeometry.fromPointXY(QgsPointXY(*dump.locations[i]))
                geometries.append(geometry)

            name = 'Spectral Library from Classification Dataset'
            if dump.crs is None:
                crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)
            else:
                crs = QgsCoordinateReferenceSystem.fromWkt(dump.crs)

            writer = LibraryDriver().createFromData(data, geometries, name, Qgis.WkbType.Point, crs)
            writer.writeToSource(filename)
            library = QgsVectorLayer(filename)
            assert library.isValid()
            renderer = Utils().categorizedSymbolRendererFromCategories('CategoryValue', dump.categories)
            library.setRenderer(renderer)
            library.saveDefaultStyle(QgsMapLayer.StyleCategory.AllStyleCategories)

            result = {self.P_OUTPUT_LIBRARY: filename}
            self.toc(feedback, result)
        return result

    @classmethod
    def makeKernel(cls, xres: float, yres: float, radius: float) -> np.ndarray:
        nx = ceil((radius - xres / 2) / xres) * 2 + 1
        ny = ceil((radius - yres / 2) / yres) * 2 + 1
        kernel = np.ones((ny, nx), dtype=np.uint8)

        for yi, y in enumerate(np.linspace(- (ny // 2) * yres, (ny // 2) * yres, ny)):
            for xi, x in enumerate(np.linspace(- (nx // 2) * xres, (nx // 2) * xres, nx)):
                kernel[yi, xi] = (x ** 2 + y ** 2) ** 0.5 > radius

        return kernel.astype(np.uint8)
