from typing import List

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyle, MarkerSymbol
from profileanalyticsapp.profileanalyticsdockwidget import Profile
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor


def updatePlot(profile: Profile, profiles: List[Profile], plotWidget: pg.PlotItem):
    xValues = profile.xValues
    yValues = profile.yValues

    # plot something
    style = PlotStyle()
    style.setMarkerSymbol(MarkerSymbol.Cross)  # options: Circle, Triangle_Down, Triangle_Up, Triangle_Right, Triangle_Left, Pentagon, Hexagon, Square, Star, Plus, Diamond, Cross, ArrowUp, ArrowRight, ArrowDown, ArrowLeft, No_Symbol
    style.markerBrush.setColor(QColor('#ff0000'))
    style.markerSize = 15
    style.linePen.setColor(QColor('#0000ff'))
    style.linePen.setWidth(2)
    style.linePen.setStyle(Qt.DashLine)
    plotDataItem = plotWidget.plot(xValues, yValues, name='My Line')
    style.apply(plotDataItem)
