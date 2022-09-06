from typing import Optional

from qgis.PyQt.QtGui import QColor
from osgeo import gdal, ogr
from qgis.core import QgsPalettedRasterRenderer, QgsRendererCategory, QgsSymbol

from _classic.hubdsm.algorithm.importenmapl1b import importEnmapL1B
from _classic.hubdsm.algorithm.remaprastervalues import remapRasterValues
from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color
from _classic.hubdsm.core.gdalraster import GdalRaster
from _classic.hubdsm.core.gdaldriver import GdalDriver, VRT_DRIVER
from _classic.hubdsm.core.grid import Grid
from _classic.hubdsm.core.ogrdriver import MEMORY_DRIVER
from _classic.hubdsm.core.ogrlayer import OgrLayer
from _classic.hubdsm.core.ogrvector import OgrVector
from _classic.hubdsm.core.typing import GdalCreationOptions
from _classic.hubdsm.processing.enmapalgorithm import *
from _classic.hubdsm.core.raster import Raster


class SaveLayerAsClassification(EnMAPAlgorithm):
    def displayName(self):
        return 'Save as Classification'

    def description(self):
        return 'Save map layer with "Paletted/Unique values" or "Categorized" renderer as classification with proper class names and colors. In case of a vector layer, the pixel grid has to be specified for rasterization.'

    def group(self):
        return Group.CreateRaster.value

    P_MAP = 'map'
    P_GRID = 'grid'
    P_OUTRASTER = 'outraster'

    def defineCharacteristics(self):
        self.addParameter(
            EnMAPProcessingParameterMapLayer(
                name=self.P_MAP, description='Styled map layer',
                help=Help(text='Raster layer with "Paletted/Unique values" renderer or vector layer with "Categorized" renderer.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterLayer(
                name=self.P_GRID, description='Pixel Grid', optional=True,
                help=Help(text='Specify pixel grid in case of a vector layer.')
            )
        )

        self.addParameter(
            EnMAPProcessingParameterRasterDestination(
                name=self.P_OUTRASTER, description='Classification', defaultValue='outClassification.bsq'
            )
        )

    def processAlgorithm_(self, parameters: Dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        if self.parameter(parameters, self.P_GRID, context) is None:
            grid = None
        else:
            qgsRasterLayer: QgsRasterLayer = self.parameter(parameters, self.P_GRID, context)
            grid = GdalRaster.open(qgsRasterLayer.source()).grid

        classification = saveLayerAsClassification(
            qgsMapLayer=self.parameter(parameters, self.P_MAP, context),
            grid=grid,
            filename=self.parameter(parameters, self.P_OUTRASTER, context)
        )
        return {self.P_OUTRASTER: classification.band(1).filename}


def saveLayerAsClassification(
        qgsMapLayer: QgsMapLayer, grid: Grid = None, filename: str = None, allTouched: bool = False,
        filterSQL: str = None, gco: GdalCreationOptions = None
) -> Raster:
    assert isinstance(qgsMapLayer, QgsMapLayer), str(qgsMapLayer)
    driver = GdalDriver.fromFilename(filename=filename)

    if isinstance(qgsMapLayer, QgsRasterLayer):
        if isinstance(qgsMapLayer.renderer(), QgsPalettedRasterRenderer):
            renderer: QgsPalettedRasterRenderer = qgsMapLayer.renderer()
            raster = Raster.open(qgsMapLayer.source()).select(selectors=[renderer.band()])
            categories = Category.fromQgsPalettedRasterRenderer(renderer=qgsMapLayer.renderer())
            gdalBand = raster.band(1).gdalBand.translate(grid=grid, filename=filename, driver=driver)
            classification = Raster.open(gdalBand.raster)
        else:
            raise ValueError('not a "Paletted/Unique values" renderer')
    elif isinstance(qgsMapLayer, QgsVectorLayer):
        assert isinstance(grid, Grid)
        if isinstance(qgsMapLayer.renderer(), QgsCategorizedSymbolRenderer):
            renderer: QgsCategorizedSymbolRenderer = qgsMapLayer.renderer()
            categories = list()
            idByName = dict()
            for i, c in enumerate(renderer.categories(), 1):
                assert isinstance(c, QgsRendererCategory)
                s = c.symbol()
                assert isinstance(s, QgsSymbol)
                qcolor: QColor = s.color()
                if isinstance(c.value(), (int, float)):
                    id = c.value()
                else:
                    id = i
                    idByName[c.value()] = id
                category = Category(
                    id=id,
                    name=c.label(),
                    color=Color(red=qcolor.red(), green=qcolor.green(), blue=qcolor.blue())
                )
                if category.name != '':
                    categories.append(category)

            ogrLayer = OgrLayer.open(qgsMapLayer.source())
            isClassAttributeString = ogrLayer.fieldType(name=renderer.classAttribute()) in [
                ogr.OFTString, ogr.OFTWideString
            ]
            if isClassAttributeString:
                ogrDataSource2 = MEMORY_DRIVER.createVector()
                burnLayer = ogrDataSource2.copyLayer(
                    layer=ogrLayer, name=ogrLayer.name, fieldNames=[renderer.classAttribute()]
                )

                def createIdField(feature: ogr.Feature) -> int:
                    name = feature.GetField(feature.GetFieldIndex(renderer.classAttribute()))
                    return idByName[name]

                burnLayer.fieldCalculator(name='id', oft=ogr.OFTInteger64, ufunc=createIdField)
                burnAttribute = 'id'
            else:
                burnLayer = ogrLayer
                burnAttribute = renderer.classAttribute()

            gdalRaster = burnLayer.rasterize(
                grid=grid, gdt=gdal.GDT_UInt16, initValue=0, burnAttribute=burnAttribute, allTouched=allTouched,
                filterSQL=filterSQL, filename=filename, gco=gco)
            classification = Raster.open(gdalRaster)
        else:
            raise ValueError('not a "Categorized" renderer')
    else:
        raise ValueError(str(qgsMapLayer))

    classification.setCategories(categories=categories)
    return classification
