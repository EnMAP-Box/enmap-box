from typing import List

import numpy as np

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyle, MarkerSymbol
from profileanalyticsapp.profileanalyticsdockwidget import Profile
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor


def updatePlot(profile: Profile, profiles: List[Profile], plotWidget: pg.PlotItem):
    # fit
    X = profile.xValues
    y = profile.yValues
    coefs = np.polyfit(X, y, 3)

    # predict
    X2 = np.linspace(np.min(X), np.max(X), 1000)
    y2 = np.polyval(coefs, X2)

    # plot
    style = PlotStyle()
    style.setMarkerSymbol(MarkerSymbol.No_Symbol)
    style.linePen.setStyle(Qt.SolidLine)
    style.linePen.setColor(QColor('#ff0000'))
    style.linePen.setWidth(1)
    plotDataItem = plotWidget.plot(X2, y2, name=f'fitted {profile.name}')
    style.apply(plotDataItem)

    # plot what ever you want using PyQtGraph
    # ... more plotting examples can be added here
