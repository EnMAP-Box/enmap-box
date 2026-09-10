from math import inf

import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from qgis.PyQt.QtCore import QDateTime
from qgis.PyQt.QtWidgets import QSizePolicy, QSlider, QToolButton, QMainWindow, QComboBox, QCheckBox, QVBoxLayout, \
    QWidget
from qgis.PyQt.uic import loadUi
from qgis.core import QgsRasterLayer, QgsColorRamp, QgsStyle, QgsMapLayerProxyModel
from qgis.gui import QgsColorRampButton, QgsMessageBar, QgsMapLayerComboBox, QgsFieldComboBox, QgsFilterLineEdit

from enmapboxprocessing.libraryreader import LibraryReader
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils


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

    mDataFormat: QComboBox
    mTable: QgsMapLayerComboBox
    mLibrary: QgsMapLayerComboBox
    mCollection: QgsMapLayerComboBox
    mXMin: QgsFilterLineEdit
    mXMax: QgsFilterLineEdit
    mYMin: QgsFilterLineEdit
    mYMax: QgsFilterLineEdit
    mZMin: QgsFilterLineEdit
    mZMax: QgsFilterLineEdit
    mXScale: QgsFilterLineEdit
    mYScale: QgsFilterLineEdit
    mZScale: QgsFilterLineEdit

    mShowSurface: QCheckBox
    mShowPoints: QCheckBox
    mShowEdges: QCheckBox
    mShowGrid: QCheckBox
    mShowAxes: QCheckBox
    mColorRamp: QgsColorRampButton

    mFieldLfX: QgsFieldComboBox
    mFieldLfY: QgsFieldComboBox
    mFieldLfZ: QgsFieldComboBox
    mFieldLibraryProfiles: QgsFieldComboBox
    mFieldLibraryY: QgsFieldComboBox
    mFieldLibraryC: QgsFieldComboBox
    mFieldCollectionY: QgsFieldComboBox
    mFieldCollectionC: QgsFieldComboBox
    mLoadData: QToolButton

    scaleBase = 2
    mScaleX: QSlider
    mScaleY: QSlider
    mScaleZ: QSlider
    mAutoScale: QToolButton

    LongFormat, LibraryFormat, CollectionFormat = 0, 1, 2

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

        from enmapbox.gui.enmapboxgui import EnMAPBox
        self.enmapBox = EnMAPBox.instance()

        for w in [self.mTable, self.mLibrary, self.mCollection]:
            w.setProject(self.enmapBox.project())
            w.setFilters(QgsMapLayerProxyModel.Filter.VectorLayer)

        self.mShowSurface.checkStateChanged.connect(self.onShowSurfaceChanged)
        self.mShowPoints.checkStateChanged.connect(self.onShowPointsChanged)
        self.mShowEdges.checkStateChanged.connect(self.onShowEdgesChanged)
        self.mShowGrid.checkStateChanged.connect(self.onShowGridChanged)
        self.mShowAxes.checkStateChanged.connect(self.onShowAxesChanged)
        self.mColorRamp.colorRampChanged.connect(self.onColorRampChanged)

        self.mScaleX.valueChanged.connect(self.onScaleChanged)
        self.mScaleY.valueChanged.connect(self.onScaleChanged)
        self.mScaleZ.valueChanged.connect(self.onScaleChanged)
        self.mAutoScale.clicked.connect(self.onAutoScale)

        self.mLoadData.clicked.connect(self.onLoadData)

        colorRamp: QgsColorRamp = QgsStyle().defaultStyle().colorRamp('Turbo')
        self.mColorRamp.setColorRamp(colorRamp)

        self.scaleX = 1
        self.scaleY = 1
        self.scaleZ = 1

    def readData(self):
        xmin = parseFloat(self.mXMin, -inf)
        ymin = parseFloat(self.mYMin, -inf)
        zmin = parseFloat(self.mZMin, -inf)
        xmax = parseFloat(self.mXMax, inf)
        ymax = parseFloat(self.mYMax, inf)
        zmax = parseFloat(self.mZMax, inf)

        # read, filter and scale data
        x = list()
        y = list()
        z = list()
        c = list()

        fx = parseFloat(self.mXScale, 1)
        fy = parseFloat(self.mYScale, 1)
        fz = parseFloat(self.mZScale, 1)

        if self.mDataFormat.currentIndex() == self.LongFormat:
            layer = self.mTable.currentLayer()
            fieldX = self.mFieldLfX.currentField()
            fieldY = self.mFieldLfY.currentField()
            fieldZ = self.mFieldLfZ.currentField()
            for feature in layer.getFeatures():
                xi = feature[fieldX]
                yi = feature[fieldY]
                zi = feature[fieldZ]
                ci = float(feature[fieldZ])
                valid = xi >= xmin and xi <= xmax
                valid &= yi >= ymin and yi <= ymax
                valid &= zi >= zmin and zi <= zmax
                if valid:
                    x.append(xi / fx)
                    y.append(yi / fy)
                    z.append(zi / fz)
                    c.append(ci)

        elif self.mDataFormat.currentIndex() == self.LibraryFormat:
            layer = self.mLibrary.currentLayer()
            reader = LibraryReader(layer)
            fieldProfile = self.mFieldLibraryProfiles.currentField()
            fieldY = self.mFieldLibraryY.currentField()
            fieldC = self.mFieldLibraryC.currentField()
            try:
                for i, (values, geometry) in enumerate(reader.data(), 1):
                    xs = values[fieldProfile]['x']
                    zs = values[fieldProfile]['y']
                    yi = values.get(fieldY, i)

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
                self.mMessageBar.pushWarning('Load data', 'select required inputs')
                return
        elif self.mDataFormat.currentIndex() == self.CollectionFormat:
            collectionLayer = self.mCollection.currentLayer()
            collectionReader = LibraryReader(collectionLayer)
            fieldSource = 'source'
            fieldProvider = 'provider'
            fieldY = self.mFieldCollectionY.currentField()
            fieldC = self.mFieldCollectionC.currentField()

            point = self.enmapBox.currentLocation()
            if point is None:
                self.mMessageBar.pushWarning('Load data', 'select a map location')
                return

            for i, (values, geometry) in enumerate(collectionReader.data(), 1):
                # if i==5:
                #    break
                yi = values.get(fieldY, i)
                if isinstance(yi, QDateTime):
                    yi = Utils.dateTimeToDecimalYear(yi)

                source = values.get(fieldSource, i)
                provider = values.get(fieldProvider, i)
                rasterLayer = QgsRasterLayer(source, '', provider)
                rasterReader = RasterReader(rasterLayer)
                pixel = point.toPixel(rasterReader)
                zs = np.array(rasterReader.arrayFromPixelOffsetAndSize(pixel.x(), pixel.y(), 1, 1)).flatten()  # / 10000
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

        self.mesh = self.point_cloud.delaunay_2d()
        self.mesh.point_data["C"] = c

    def updateGrid(self):
        if self.meshActorSurface is None:
            return

        # remove previous CubeAxesActor
        self.plotter.remove_bounds_axes()

        # use the current transformed bounds of the surface actor
        bounds = self.meshActorSurface.GetBounds()

        self.gridActor = self.plotter.show_grid(
            bounds=bounds,
            xtitle='',
            ytitle='',
            ztitle='',
            show_xaxis=True,
            show_yaxis=True,
            show_zaxis=True
        )
        self.onShowGridChanged()

        self.gridActor.x_axis_range = (bounds[0] / self.scaleX, bounds[1] / self.scaleX)
        self.gridActor.y_axis_range = (bounds[2] / self.scaleY, bounds[3] / self.scaleY)
        # number of decimal places
        self.gridActor.x_label_format = '{0:.2f}'
        self.gridActor.y_label_format = '{0:.2f}'

        print('BOUNDS')
        print(bounds[0] / self.scaleX, bounds[1] / self.scaleX)
        print(bounds[2] / self.scaleY, bounds[3] / self.scaleY)

    def plotData(self):

        self.meshActorSurface = self.plotter.add_mesh(
            self.mesh,
            scalars="C",
            cmap="viridis",
            show_edges=self.mShowEdges.isChecked(),
            edge_color="black",
            line_width=0.4,
            smooth_shading=True,
            opacity=0.8 + 0.2,
            scalar_bar_args={"title": "C"},
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

        self.meshActorSurface.SetVisibility(self.mShowSurface.isChecked())

    def onShowPointsChanged(self):
        if self.meshActorSurface is None:
            return

        self.meshActorPoints.SetVisibility(self.mShowPoints.isChecked())

    def onShowEdgesChanged(self):
        if self.meshActorSurface is None:
            return

        self.meshActorSurface.prop.show_edges = self.mShowEdges.isChecked()
        self.plotter.render()

    def onShowGridChanged(self):
        if self.meshActorSurface is None:
            return

        self.gridActor.SetVisibility(self.mShowGrid.isChecked())
        self.plotter.render()

    def onShowAxesChanged(self):
        if self.meshActorSurface is None:
            return

        self.axesActor.SetVisibility(self.mShowAxes.isChecked())
        self.plotter.render()

    def onColorRampChanged(self):
        if self.meshActorSurface is None:
            return

        ramp = self.mColorRamp.colorRamp()
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

        self.scaleX = self.scaleBase ** self.mScaleX.value()
        self.scaleY = self.scaleBase ** self.mScaleY.value()
        self.scaleZ = self.scaleBase ** self.mScaleZ.value()
        self.setScale(self.scaleX, self.scaleY, self.scaleZ)
        self.plotter.render()

    def onAutoScale(self):
        if self.meshActorSurface is None:
            return

        xscale, yscale, zscale = self.autoScaleFactors()
        self.mScaleX.setValue(int(np.log(xscale) / np.log(self.scaleBase)))
        self.mScaleY.setValue(int(np.log(yscale) / np.log(self.scaleBase)))
        self.mScaleZ.setValue(int(np.log(zscale) / np.log(self.scaleBase)))

    def onLoadData(self):

        if self.mDataFormat.currentIndex() == self.LongFormat and self.mTable.currentLayer() is None:
            return
        if self.mDataFormat.currentIndex() == self.LibraryFormat and self.mLibrary.currentLayer() is None:
            return
        if self.mDataFormat.currentIndex() == self.CollectionFormat and self.mCollection.currentLayer() is None:
            return

        x, y, z, c = self.readData()
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
