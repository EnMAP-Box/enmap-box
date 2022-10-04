from typing import List

import numpy as np
from sklearn.svm import SVR

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyle, MarkerSymbol
from profileanalyticsapp.profileanalyticsdockwidget import Profile
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor


def updatePlot(profile: Profile, profiles: List[Profile], plotWidget: pg.PlotItem):
    # fit
    svr = SVR(kernel='rbf', gamma=10, C=10000, epsilon=0.1)
    X = np.reshape(profile.xValues, (-1, 1))
    y = profile.yValues
    svr.fit(X, y)

    # predict
    X2 = np.linspace(np.min(X), np.max(X), 1000).reshape(-1, 1)
    y2 = svr.predict(X2)

    # plot
    style = PlotStyle()
    style.setMarkerSymbol(MarkerSymbol.No_Symbol)
    style.linePen.setStyle(Qt.SolidLine)
    style.linePen.setColor(QColor('#ff0000'))
    style.linePen.setWidth(1)
    plotDataItem = plotWidget.plot(X2.flatten(), y2.flatten(), name=f'fitted {profile.name}')
    style.apply(plotDataItem)

    # plot what ever you want using PyQtGraph
    # ... more plotting examples can be added here
