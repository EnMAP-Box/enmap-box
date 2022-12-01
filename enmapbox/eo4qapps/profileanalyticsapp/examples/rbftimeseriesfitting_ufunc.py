from typing import List
import numpy as np

import enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph as pg
from enmapbox.qgispluginsupport.qps.plotstyling.plotstyling import PlotStyle, MarkerSymbol
from profileanalyticsapp.examples.rbftimeseriesfitting import rbfEnsemblePrediction
from profileanalyticsapp.profileanalyticsdockwidget import Profile
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor


def updatePlot(profile: Profile, profiles: List[Profile], plotWidget: pg.PlotItem):

    rbfCutOffValue = 0.01  # minimal value concidered as weights in convolution (value between 0 and 1)
    rbfFwhms = [day / 365 for day in [10, 30, 60]]  # RBF kernel sizes [decimal years]
    rbfUserWeights = [10,3,1]

    X = np.array(profile.xValues)  # X[ndates]
    Y = np.array(profile.yValues).reshape((1, -1))  # Y[nsamples, ndates]

    X2 = np.linspace(X.min(), X.max(), 1000)
    X2 = X
    Y2 = rbfEnsemblePrediction(X, Y, X2, rbfFwhms, rbfUserWeights, rbfCutOffValue)

    # plot something
    style = PlotStyle()
    style.setMarkerSymbol(MarkerSymbol.No_Symbol)  # options: Circle, Triangle_Down, Triangle_Up, Triangle_Right, Triangle_Left, Pentagon, Hexagon, Square, Star, Plus, Diamond, Cross, ArrowUp, ArrowRight, ArrowDown, ArrowLeft, No_Symbol
    style.markerBrush.setColor(QColor('#ff0000'))
    style.markerSize = 15
    style.linePen.setColor(QColor('#ff0000'))
    style.linePen.setWidth(2)
    style.linePen.setStyle(Qt.SolidLine)
    plotDataItem = plotWidget.plot(X2.flatten(), Y2.flatten(), name='RBF Ensemble Fit')
    style.apply(plotDataItem)
