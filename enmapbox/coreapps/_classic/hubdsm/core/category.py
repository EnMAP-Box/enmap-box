from typing import List

from qgis.PyQt.QtGui import QColor
from dataclasses import dataclass
from qgis.core import QgsPalettedRasterRenderer, QgsCategorizedSymbolRenderer

from _classic.hubdsm.core.color import Color


@dataclass(frozen=True)
class Category(object):
    id: int
    name: str
    color: Color

    def __post_init__(self):
        assert isinstance(id, int) >= 0
        assert isinstance(self.name, str)
        assert isinstance(self.color, Color)

    @staticmethod
    def fromQgsPalettedRasterRenderer(renderer: QgsPalettedRasterRenderer) -> List['Category']:
        assert isinstance(renderer, QgsPalettedRasterRenderer)
        categories = list()
        for c in renderer.classes():
            assert isinstance(c, QgsPalettedRasterRenderer.Class)
            qcolor: QColor = c.color
            category = Category(
                id=c.value,
                name=c.label,
                color=Color(red=qcolor.red(), green=qcolor.green(), blue=qcolor.blue())
            )
            categories.append(category)
        return categories

    @staticmethod
    def fromQgsCategorizedSymbolRenderer(renderer: QgsCategorizedSymbolRenderer) -> List['Category']:
        assert isinstance(renderer, QgsCategorizedSymbolRenderer)
        categories = list()
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
