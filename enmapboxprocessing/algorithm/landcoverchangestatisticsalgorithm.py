from copy import deepcopy
from typing import Dict, Any, List, Tuple

import plotly.io as pio

from enmapbox.typeguard import typechecked
from enmapboxprocessing.enmapalgorithm import EnMAPProcessingAlgorithm, Group
from qgis.core import QgsProcessingContext, QgsProcessingFeedback, QgsProcessing, QgsProcessingException


@typechecked
class LandCoverChangeStatisticsAlgorithm(EnMAPProcessingAlgorithm):
    P_CLASSIFICATIONS, _CLASSIFICATIONS = 'classifications', 'Classification layers'
    P_NODE_PADDING, _NODE_PADDING = 'nodePadding', 'Node padding'
    P_SHOW_CLASS_NAMES, _SHOW_CLASS_NAMES = 'showClassNames', 'Show class names'
    P_SHOW_LAYER_NAMES, _SHOW_LAYER_NAMES = 'showLayerNames', 'Show layer names'
    P_SHOW_CLASS_SIZES, _SHOW_CLASS_SIZES = 'showClassSizes', 'Show class sizes'
    P_CLASS_SIZE_UNITS, _CLASS_SIZE_UNITS = 'classSizeUnits', 'Class size units'
    O_CLASS_SIZE_UNITS = [
        'Percentages (%)', 'Pixels (px)', 'Square meters (m²)', 'Hectares (ha)', 'Square kilometers (km²)'
    ]
    Percentages, Pixels, SquareMeters, Hectares, SquareKilometers = range(5)
    P_LINK_OPACITY, _LINK_OPACITY = 'linkOpacity', 'Link opacity'
    P_OPEN_REPORT, _OPEN_REPORT = 'openReport', 'Open output report in webbrowser after running algorithm'
    P_OUTPUT_REPORT, _OUTPUT_REPORT = 'outReport', 'Output report'

    @classmethod
    def displayName(cls) -> str:
        return 'Land cover change statistics report'

    def shortDescription(self) -> str:
        return 'Visualize land cover change statistics via Sankey plot.'

    def helpParameters(self) -> List[Tuple[str, str]]:
        return [
            (self._CLASSIFICATIONS, 'A series of (at least two) classification layers to be used.'),
            (self._NODE_PADDING, 'Whether to add a margin around the class nodes.'),
            (self._SHOW_CLASS_NAMES, 'Whether to show class names in the plot.'),
            (self._SHOW_LAYER_NAMES, 'Whether to show layer names in the plot.'),
            (self._SHOW_CLASS_SIZES, 'Whether to show class sizes in the plot.'),
            (self._CLASS_SIZE_UNITS, 'Are units used, when reporting class size.'),
            (self._LINK_OPACITY, 'Opacity used for plotting links between nodes.'),
            (self._OPEN_REPORT, self.ReportOpen),
            (self._OUTPUT_REPORT, self.ReportFileDestination)
        ]

    def group(self):
        return Group.Classification.value

    def initAlgorithm(self, configuration: Dict[str, Any] = None):
        self.addParameterMultipleLayers(
            self.P_CLASSIFICATIONS, self._CLASSIFICATIONS, QgsProcessing.SourceType.TypeRaster
        )
        self.addParameterBoolean(self.P_NODE_PADDING, self._NODE_PADDING, True, True, True)
        self.addParameterBoolean(self.P_SHOW_CLASS_NAMES, self._SHOW_CLASS_NAMES, True, True, True)
        self.addParameterBoolean(self.P_SHOW_LAYER_NAMES, self._SHOW_LAYER_NAMES, True, True, True)
        self.addParameterBoolean(self.P_SHOW_CLASS_SIZES, self._SHOW_CLASS_SIZES, True, True, True)
        self.addParameterEnum(
            self.P_CLASS_SIZE_UNITS, self._CLASS_SIZE_UNITS, self.O_CLASS_SIZE_UNITS, False, self.Percentages,
            True, True
        )
        self.addParameterInt(self.P_LINK_OPACITY, self._LINK_OPACITY, 75, True, 0, 100, True)
        self.addParameterBoolean(self.P_OPEN_REPORT, self._OPEN_REPORT, True, True, False)
        self.addParameterFileDestination(self.P_OUTPUT_REPORT, self._OUTPUT_REPORT, self.ReportFileFilter)

    def processAlgorithm(
            self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        classifications = self.parameterAsLayerList(parameters, self.P_CLASSIFICATIONS, context)
        nodePadding = self.parameterAsBoolean(parameters, self.P_NODE_PADDING, context)
        showClassNames = self.parameterAsBoolean(parameters, self.P_SHOW_CLASS_NAMES, context)
        showLayerNames = self.parameterAsBoolean(parameters, self.P_SHOW_LAYER_NAMES, context)
        showClassSizes = self.parameterAsBoolean(parameters, self.P_SHOW_CLASS_SIZES, context)
        classSizeUnits = self.parameterAsInt(parameters, self.P_CLASS_SIZE_UNITS, context)
        linkOpacity = self.parameterAsInt(parameters, self.P_LINK_OPACITY, context)
        openReport = self.parameterAsBoolean(parameters, self.P_OPEN_REPORT, context)
        filename = self.parameterAsFileOutput(parameters, self.P_OUTPUT_REPORT, context)

        if len(classifications) < 2:
            raise QgsProcessingException('Select at least two classification layer.')

        with open(filename + '.log', 'w') as logfile:
            feedback, feedback2 = self.createLoggingFeedback(feedback, logfile)
            self.tic(feedback, parameters, context)

            grid = classifications[0]
            from landcoverchangestatisticsapp.landcoverchangestatisticsmainwindow import \
                LandCoverChangeSankeyPlotBuilder
            builder = LandCoverChangeSankeyPlotBuilder()
            # builder.setTitle('Land cover change statistics')
            builder.setGrid(grid)
            builder.setLayers(classifications)
            builder.setOptions(
                dict(
                    showClassNames=showClassNames,
                    showClassSizes=showClassSizes,
                    classSizeUnits=classSizeUnits,
                    showLayerNames=showLayerNames,
                    showNodePadding=nodePadding,
                    linkOpacity=linkOpacity,
                    title='Land Cover Change Statistics'
                ))
            builder.readData(grid.extent(), 0)
            classFilter = deepcopy(builder.categoriess)
            for categories in classFilter:
                for i, c in enumerate(categories):
                    categories[i] = c.name
            builder.setClassFilter(classFilter)
            fig = builder.sankeyPlot()
            pio.write_html(fig, file=filename, auto_open=openReport)

            result = {self.P_OUTPUT_REPORT: filename}
            self.toc(feedback, result)

        return result
