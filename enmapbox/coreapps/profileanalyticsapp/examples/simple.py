from typing import List

import numpy as np
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyle, MarkerSymbol
from profileanalyticsapp.profileanalyticsdockwidget import Profile


def updatePlot(profile: Profile, profiles: List[Profile], plotWidget: pg.PlotItem):

    # plot a point
    x = [np.mean(profile.xValues)]
    y = [np.mean(profile.yValues)]
    style = PlotStyle()
    style.setMarkerSymbol(MarkerSymbol.Cross)
    style.markerBrush.setColor(QColor('#ff0000'))
    style.markerSize = 15
    plotDataItem = plotWidget.plot(x, y, name='My Point')
    style.apply(plotDataItem)

    # plot a line
    x = [np.min(profile.xValues), np.max(profile.xValues)]
    y = [np.mean(profile.yValues)] * 2
    style = PlotStyle()
    style.setMarkerSymbol(MarkerSymbol.No_Symbol)
    style.linePen.setColor(QColor('#0000ff'))
    style.linePen.setWidth(2)
    style.linePen.setStyle(Qt.DashLine)
    plotDataItem = plotWidget.plot(x, y, name='My Line')
    style.apply(plotDataItem)

    # plot what ever you want using PyQtGraph
    # ... more plotting examples can be added here
