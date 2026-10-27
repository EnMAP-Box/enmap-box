import logging
import traceback
from math import inf

import numpy as np
import pyvista as pv
import vtk
from pyvistaqt import QtInteractor
from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QSizePolicy, QMainWindow, QVBoxLayout, QWidget
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsColorRamp, QgsStyle, QgsMapLayerProxyModel
from qgis.gui import QgsMessageBar, QgsFilterLineEdit

from enmapboxprocessing.libraryreader import LibraryReader
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from spectralsurfaceplottingapp.spectralsurfaceplottingdatadockwidget import SpectralSurfacePlottingDataDockWidget
from spectralsurfaceplottingapp.spectralsurfaceplottingsettingsdockwidget import \
    SpectralSurfacePlottingSettingsDockWidget

pv.vtk_verbosity("off")


class VtkLogFilter(logging.Filter):

    def filter(self, record):
        message = record.getMessage()
        return "vtkVectorText" not in message


logging.getLogger().addFilter(VtkLogFilter())


def parseFloat(w: QgsFilterLineEdit, default):
    text = w.text().strip()
    try:
        return float(text)
    except (ValueError, TypeError):
        w.setValue('')  # clear wrong inputs
        return default


class SpectralSurfacePlottingWindow(QMainWindow):
    mMessageBar: QgsMessageBar
    mPlot: QWidget

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

        self.meshActorSurface = None
        self.meshActorPoints = None

        self.plotLayout = QVBoxLayout(self.mPlot)
        self.plotLayout.setContentsMargins(0, 0, 0, 0)
        self.plotLayout.setSpacing(0)
        self.plotter = QtInteractor(self.mPlot)
        # Z should always be "up"
        self.plotter.camera.up = (0, 0, 1)
        # Mouse rotation = azimuth/elevation, no free trackball rolling
        self.plotter.enable_terrain_style()

        self.plotter.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        self.plotter.set_background('white')
        self.plotLayout.addWidget(self.plotter)

        self.plotter.add_text(
            "Select input data", position=(50., 50.), font_size=16, color="gray", name="startup_message"
        )
        self.plotter.show()

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        # add dock widgets
        self.mDataDock = SpectralSurfacePlottingDataDockWidget(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.mDataDock)
        self.mSettingsDock = SpectralSurfacePlottingSettingsDockWidget(parent=self)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.mSettingsDock)

        for w in [self.mDataDock.mTable, self.mDataDock.mLibrary, self.mDataDock.mCollection]:
            w.setProject(self.enmapBox.project())
            w.setFilters(QgsMapLayerProxyModel.Filter.VectorLayer)

        self.mSettingsDock.mShowSurface.checkStateChanged.connect(self.onShowSurfaceChanged)
        self.mSettingsDock.mShowPoints.checkStateChanged.connect(self.onShowPointsChanged)
        self.mSettingsDock.mShowEdges.checkStateChanged.connect(self.onShowEdgesChanged)
        self.mSettingsDock.mShowGrid.checkStateChanged.connect(self.onShowGridChanged)
        self.mSettingsDock.mShowAxes.checkStateChanged.connect(self.onShowAxesChanged)
        self.mSettingsDock.mColorRamp.colorRampChanged.connect(self.onColorRampChanged)

        self.mSettingsDock.mScaleX.valueChanged.connect(self.onScaleChanged)
        self.mSettingsDock.mScaleY.valueChanged.connect(self.onScaleChanged)
        self.mSettingsDock.mScaleZ.valueChanged.connect(self.onScaleChanged)
        self.mSettingsDock.mAutoScale.clicked.connect(self.onAutoScale)

        self.mSettingsDock.mResetCamera.clicked.connect(self.onResetCamera)

        for w in [
            self.mSettingsDock.mShowAxisX, self.mSettingsDock.mShowAxisY, self.mSettingsDock.mShowAxisZ,
            self.mSettingsDock.mShowAxisLabelX, self.mSettingsDock.mShowAxisLabelY, self.mSettingsDock.mShowAxisLabelZ
        ]:
            w.checkStateChanged.connect(self.updateGrid)

        self.mSettingsDock.mAxisLabelX.textChanged.connect(self.updateGrid)
        self.mSettingsDock.mAxisLabelY.textChanged.connect(self.updateGrid)
        self.mSettingsDock.mAxisLabelZ.textChanged.connect(self.updateGrid)

        self.mDataDock.mLoadData.clicked.connect(self.onLoadData)

        colorRamp: QgsColorRamp = QgsStyle().defaultStyle().colorRamp('Turbo')
        self.mSettingsDock.mColorRamp.setColorRamp(colorRamp)

        self.scaleX = 1
        self.scaleY = 1
        self.scaleZ = 1

    def readData(self):
        xmin = parseFloat(self.mDataDock.mXMin, -inf)
        ymin = parseFloat(self.mDataDock.mYMin, -inf)
        zmin = parseFloat(self.mDataDock.mZMin, -inf)
        xmax = parseFloat(self.mDataDock.mXMax, inf)
        ymax = parseFloat(self.mDataDock.mYMax, inf)
        zmax = parseFloat(self.mDataDock.mZMax, inf)

        # read, filter and scale data
        x = list()
        y = list()
        z = list()
        c = list()

        fx = parseFloat(self.mDataDock.mXScale, 1)
        fy = parseFloat(self.mDataDock.mYScale, 1)
        fz = parseFloat(self.mDataDock.mZScale, 1)

        if self.mDataDock.mDataFormat.currentIndex() == self.mDataDock.LongFormat:
            layer = self.mDataDock.mTable.currentLayer()
            fieldX = self.mDataDock.mFieldLfX.currentField()
            fieldY = self.mDataDock.mFieldLfY.currentField()
            fieldZ = self.mDataDock.mFieldLfZ.currentField()

            try:
                for feature in layer.getFeatures():
                    xi = float(feature[fieldX])
                    yi = float(feature[fieldY])
                    zi = float(feature[fieldZ])
                    ci = float(feature[fieldZ])
                    valid = xi >= xmin and xi <= xmax
                    valid &= yi >= ymin and yi <= ymax
                    valid &= zi >= zmin and zi <= zmax
                    if valid:
                        x.append(xi / fx)
                        y.append(yi / fy)
                        z.append(zi / fz)
                        c.append(ci)
            except Exception:
                traceback.print_exc()
                self.mMessageBar.pushWarning('Load data', 'inputs missing/incorrect')
                return

        elif self.mDataDock.mDataFormat.currentIndex() == self.mDataDock.LibraryFormat:
            layer = self.mDataDock.mLibrary.currentLayer()
            reader = LibraryReader(layer)
            fieldProfile = self.mDataDock.mFieldLibraryProfiles.currentField()
            fieldY = self.mDataDock.mFieldLibraryY.currentField()
            fieldC = self.mDataDock.mFieldLibraryC.currentField()
            selectedOnly = self.mDataDock.mLibrarySelectedOnly.isChecked()
            try:

                # read y-values
                ys = list()
                for i, (values, geometry) in enumerate(reader.data(selectedOnly)):
                    yi = values.get(fieldY, i)
                    ys.append(yi / fy)
                if self.mDataDock.mFieldLibraryYSorted.isChecked():
                    ys = np.argsort(ys)

                # read profiles
                for i, (values, geometry) in enumerate(reader.data(selectedOnly)):
                    xs = values[fieldProfile]['x']
                    zs = values[fieldProfile]['y']
                    yi = ys[i]

                    for xi, zi in zip(xs, zs):
                        if not np.isfinite([xi, yi, zi]).all():
                            continue
                        ci = values.get(fieldC, zi / fz)  # default color is zi
                        valid = xi >= xmin and xi <= xmax
                        valid &= yi >= ymin and yi <= ymax
                        valid &= zi >= zmin and zi <= zmax
                        if valid:
                            x.append(xi / fx)
                            y.append(yi / fy)
                            z.append(zi / fz)
                            c.append(ci)
            except Exception:
                traceback.print_exc()
                self.mMessageBar.pushWarning('Load data', 'inputs missing/incorrect')
                return
        elif self.mDataDock.mDataFormat.currentIndex() == self.mDataDock.CollectionFormat:
            collectionLayer = self.mDataDock.mCollection.currentLayer()
            collectionReader = LibraryReader(collectionLayer)
            fieldSource = 'source'
            fieldProvider = 'provider'
            fieldY = self.mDataDock.mFieldCollectionY.currentField()
            fieldC = self.mDataDock.mFieldCollectionC.currentField()

            point = self.enmapBox.currentLocation()
            if point is None:
                self.mMessageBar.pushWarning('Load data', 'select a map location')
                return

            try:
                for i, (values, geometry) in enumerate(collectionReader.data(), 1):
                    yi = values.get(fieldY, i)
                    if isinstance(yi, QDateTime):
                        yi = Utils.dateTimeToDecimalYear(yi)

                    source = values.get(fieldSource, i)
                    provider = values.get(fieldProvider, i)
                    rasterLayer = QgsRasterLayer(source, '', provider)
                    rasterReader = RasterReader(rasterLayer)
                    pixel = point.toPixel(rasterReader)
                    zs = np.array(rasterReader.arrayFromPixelOffsetAndSize(pixel.x(), pixel.y(), 1, 1)).flatten()
                    xs = [rasterReader.wavelength(bandNo) for bandNo in rasterReader.bandNumbers()]
                    for xi, zi in zip(xs, zs):
                        if not np.isfinite([xi, yi, zi]).all():
                            continue
                        ci = values.get(fieldC, zi / fz)  # default color is zi
                        valid = xi >= xmin and xi <= xmax
                        valid &= yi >= ymin and yi <= ymax
                        valid &= zi >= zmin and zi <= zmax
                        if valid:
                            x.append(xi / fx)
                            y.append(yi / fy)
                            z.append(zi / fz)
                            c.append(ci)
            except Exception:
                traceback.print_exc()
                self.mMessageBar.pushWarning('Load data', 'inputs missing/incorrect')
                return

        else:
            raise ValueError()

        return x, y, z, c

    def setData(self, x, y, z, c):
        x, y = y, x  # swap data for plotting
        self.x = np.array(x, dtype=float)
        self.y = np.array(y, dtype=float)
        self.z = np.array(z, dtype=float)
        xyz = np.column_stack((self.x, self.y, self.z))
        if not np.isfinite(xyz).all():
            raise ValueError('Spectral Surface Plotting: data includes non-finite values')
        self.point_cloud = pv.PolyData(xyz)
        self.point_cloud.point_data["C"] = c

        delaunay = vtk.vtkDelaunay2D()
        delaunay.SetInputData(self.point_cloud)
        delaunay.SetProjectionPlaneMode(vtk.VTK_DELAUNAY_XY_PLANE)
        delaunay.Update()
        self.mesh = pv.wrap(delaunay.GetOutput())

        self.mesh.point_data["C"] = c

    def updateGrid(self):
        if self.meshActorSurface is None:
            return

        def niceAxis(minValue, maxValue, targetTicks=5):
            span = maxValue - minValue
            if span <= 0:
                return minValue, maxValue, 2

            rawStep = span / (targetTicks - 1)
            magnitude = 10 ** np.floor(np.log10(rawStep))

            for factor in [1, 2, 5, 10]:
                step = factor * magnitude
                if step >= rawStep:
                    break

            niceMin = np.floor(minValue / step) * step
            niceMax = np.ceil(maxValue / step) * step
            nTicks = int(round((niceMax - niceMin) / step)) + 1

            return niceMin, niceMax, nTicks

        # Remove previous CubeAxesActor
        self.plotter.remove_bounds_axes()

        # Current transformed bounds of the surface actor
        bounds = self.meshActorSurface.GetBounds()

        # Convert bounds back to original axis coordinates
        xmin, xmax, nx = niceAxis(
            bounds[0] / self.scaleX,
            bounds[1] / self.scaleX
        )
        ymin, ymax, ny = niceAxis(
            bounds[2] / self.scaleY,
            bounds[3] / self.scaleY
        )
        zmin, zmax, nz = niceAxis(
            bounds[4] / self.scaleZ,
            bounds[5] / self.scaleZ
        )

        # Convert rounded bounds to scaled plot coordinates
        niceBounds = (
            xmin * self.scaleX, xmax * self.scaleX,
            ymin * self.scaleY, ymax * self.scaleY,
            zmin * self.scaleZ, zmax * self.scaleZ
        )

        # Create grid
        self.gridActor = self.plotter.show_grid(
            bounds=niceBounds,
            xtitle=self.mSettingsDock.mAxisLabelX.text() if self.mSettingsDock.mShowAxisLabelX.isChecked() else '',
            ytitle=self.mSettingsDock.mAxisLabelY.text() if self.mSettingsDock.mShowAxisLabelY.isChecked() else '',
            ztitle=self.mSettingsDock.mAxisLabelZ.text() if self.mSettingsDock.mShowAxisLabelZ.isChecked() else '',
            show_xaxis=self.mSettingsDock.mShowAxisX.isChecked(),
            show_yaxis=self.mSettingsDock.mShowAxisY.isChecked(),
            show_zaxis=self.mSettingsDock.mShowAxisZ.isChecked()
        )

        # Display original (unscaled) values
        self.gridActor.x_axis_range = (xmin, xmax)
        self.gridActor.y_axis_range = (ymin, ymax)
        self.gridActor.z_axis_range = (zmin, zmax)

        # Number of labels
        self.gridActor.n_xlabels = nx
        self.gridActor.n_ylabels = ny
        self.gridActor.n_zlabels = nz

        # Clean number formatting
        self.gridActor.x_label_format = '{0:g}'
        self.gridActor.y_label_format = '{0:g}'
        self.gridActor.z_label_format = '{0:g}'

        # Apply grid visibility
        self.onShowGridChanged()

    def plotData(self):

        self.plotter.remove_actor("startup_message")
        self.meshActorSurface = self.plotter.add_mesh(
            self.mesh,
            scalars="C",
            cmap="viridis",
            show_edges=self.mSettingsDock.mShowEdges.isChecked(),
            edge_color="black",
            line_width=0.4,
            smooth_shading=True,
            opacity=0.8 + 0.2,
            scalar_bar_args={"title": ""},
            name='surface'
        )
        self.onShowSurfaceChanged()

        self.meshActorPoints = self.plotter.add_mesh(
            self.point_cloud,
            scalars="C",
            cmap="viridis",
            render_points_as_spheres=True,
            point_size=8,
            show_scalar_bar=False,
            name='points'
        )
        self.onShowPointsChanged()

        self.onColorRampChanged()

        self.axesActor = self.plotter.add_axes(
            xlabel="X",
            ylabel="Y",
            zlabel="Z",
        )
        self.onShowAxesChanged()

        self.updateGrid()

        # self.plotter.enable_parallel_projection()

    def autoScaleFactors(self):
        if self.meshActorSurface is None:
            return

        x_range = np.ptp(self.x)
        y_range = np.ptp(self.y)
        z_range = np.ptp(self.z)

        if x_range == 0:
            x_range = 1.0
        if y_range == 0:
            y_range = 1.0
        if z_range == 0:
            z_range = 1.0

        reference = x_range
        xscale = 1
        yscale = reference / y_range
        zscale = reference / z_range
        return xscale, yscale, zscale

    def setScale(self, xscale, yscale, zscale):
        if self.meshActorSurface is None:
            return

        self.plotter.remove_bounds_axes()
        self.plotter.set_scale(xscale, yscale, zscale, reset_camera=True)
        self.updateGrid()

    def onShowSurfaceChanged(self):
        if self.meshActorSurface is None:
            return

        self.meshActorSurface.SetVisibility(self.mSettingsDock.mShowSurface.isChecked())

    def onShowPointsChanged(self):
        if self.meshActorSurface is None:
            return

        self.meshActorPoints.SetVisibility(self.mSettingsDock.mShowPoints.isChecked())

    def onShowEdgesChanged(self):
        if self.meshActorSurface is None:
            return

        self.meshActorSurface.prop.show_edges = self.mSettingsDock.mShowEdges.isChecked()
        self.plotter.render()

    def onShowGridChanged(self):
        if self.meshActorSurface is None:
            return

        self.gridActor.SetVisibility(self.mSettingsDock.mShowGrid.isChecked())
        self.plotter.render()

    def onShowAxesChanged(self):
        if self.meshActorSurface is None:
            return

        self.axesActor.SetVisibility(self.mSettingsDock.mShowAxes.isChecked())
        self.plotter.render()

    def onColorRampChanged(self):
        if self.meshActorSurface is None:
            return

        ramp = self.mSettingsDock.mColorRamp.colorRamp()
        n = 256
        cmap = []
        for i in range(n):
            value = i / (n - 1)
            color = ramp.color(value).name()
            cmap.append(color)

        self.meshActorSurface.mapper.lookup_table.apply_cmap(cmap, n_values=256)
        self.meshActorPoints.mapper.lookup_table.apply_cmap(cmap, n_values=256)
        self.plotter.render()

    def onScaleChanged(self):
        if self.meshActorSurface is None:
            return

        self.scaleX = self.mSettingsDock.scaleBase ** self.mSettingsDock.mScaleX.value()
        self.scaleY = self.mSettingsDock.scaleBase ** self.mSettingsDock.mScaleY.value()
        self.scaleZ = self.mSettingsDock.scaleBase ** self.mSettingsDock.mScaleZ.value()
        self.setScale(self.scaleX, self.scaleY, self.scaleZ)
        self.plotter.render()

    def onAutoScale(self):
        if self.meshActorSurface is None:
            return

        xscale, yscale, zscale = self.autoScaleFactors()
        self.mSettingsDock.mScaleX.setValue(int(np.log(xscale) / np.log(self.mSettingsDock.scaleBase)))
        self.mSettingsDock.mScaleY.setValue(int(np.log(yscale) / np.log(self.mSettingsDock.scaleBase)))
        self.mSettingsDock.mScaleZ.setValue(int(np.log(zscale) / np.log(self.mSettingsDock.scaleBase)))

    def onResetCamera(self):
        if self.meshActorSurface is None:
            return

        # set default camera
        self.plotter.camera_position = [
            (1, -1, 1),  # Camera position
            (0, 0, 0),  # Focal point
            (0, 0, 1),  # Z points upward
        ]
        self.plotter.reset_camera()
        self.plotter.render()

    def onLoadData(self):

        if self.mDataDock.mDataFormat.currentIndex() == self.mDataDock.LongFormat:
            if self.mDataDock.mTable.currentLayer() is None:
                return
        if self.mDataDock.mDataFormat.currentIndex() == self.mDataDock.LibraryFormat:
            if self.mDataDock.mLibrary.currentLayer() is None:
                return
        if self.mDataDock.mDataFormat.currentIndex() == self.mDataDock.CollectionFormat:
            if self.mDataDock.mCollection.currentLayer() is None:
                return

        xyzc = self.readData()
        if xyzc is None:
            return

        x, y, z, c = xyzc

        if len(x) == 0:
            self.mMessageBar.pushWarning('Load data', 'empty data set')
            return

        self.setData(y, x, z, c)
        self.plotData()
        self.onAutoScale()

    def closeEvent(self, event):
        try:
            if self.plotter is not None:
                self.plotter.Finalize()
                self.plotter.close()
                self.plotter = None
        finally:
            super().closeEvent(event)


def niceAxis(minValue, maxValue, targetTicks=5):
    span = maxValue - minValue
    if span <= 0:
        return minValue, maxValue, 2

    rawStep = span / (targetTicks - 1)
    magnitude = 10 ** np.floor(np.log10(rawStep))

    for factor in [1, 2, 5, 10]:
        step = factor * magnitude
        if step >= rawStep:
            break

    niceMin = np.floor(minValue / step) * step
    niceMax = np.ceil(maxValue / step) * step
    nTicks = int(round((niceMax - niceMin) / step)) + 1

    return niceMin, niceMax, nTicks
