from collections import OrderedDict
from typing import NamedTuple, Any, Dict

from qgis.PyQt.QtGui import QColor
from qgis.core import QgsVectorLayer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol

from _classic.hubdsm.core.category import Category
from _classic.hubdsm.core.color import Color


class QgsVectorClassificationScheme(NamedTuple):
    categories: Dict[Any, Category]
    classAttribute: str

    @staticmethod
    def fromQgsVectorLayer(qgsVectorLayer: QgsVectorLayer) -> 'QgsVectorClassificationScheme':

        if isinstance(qgsVectorLayer, QgsVectorLayer):
            if isinstance(qgsVectorLayer.renderer(), QgsCategorizedSymbolRenderer):
                renderer: QgsCategorizedSymbolRenderer = qgsVectorLayer.renderer()
                categories = OrderedDict()
                idByName = dict()
                for i, c in enumerate(renderer.categories(), 1):
                    assert isinstance(c, QgsRendererCategory)
                    if c.value() == '':
                        continue
                    s = c.symbol()
                    assert isinstance(s, QgsSymbol)
                    qcolor: QColor = s.color()
                    if str(c.value()).isdigit():
                        value = int(c.value())
                        id = value
                    else:
                        value = c.value()
                        id = i
                        idByName[c.value()] = id
                    category = Category(
                        id=id,
                        name=c.label(),
                        color=Color(red=qcolor.red(), green=qcolor.green(), blue=qcolor.blue())
                    )
                    categories[value] = category
            else:
                raise ValueError('not a QgsCategorizedSymbolRenderer')
        else:
            raise ValueError('not a QgsVectorLayer')
        if len(categories) == 0:
            raise ValueError('empty category list')
        return QgsVectorClassificationScheme(categories=categories, classAttribute=renderer.classAttribute())
