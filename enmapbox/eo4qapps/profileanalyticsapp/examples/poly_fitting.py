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

    # instead of plotting the fit, we can return it as a Profile object
    xValues = X2.tolist()
    yValues = y2.tolist()
    style = PlotStyle()
    name = f'fitted {profile.name}'
    style.setMarkerSymbol(MarkerSymbol.No_Symbol)
    style.linePen.setStyle(Qt.SolidLine)
    style.linePen.setColor(QColor('#ff0000'))
    style.linePen.setWidth(1)

    return [Profile(xValues, yValues, profile.xUnit, name, style)]
