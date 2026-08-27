import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from qgis.PyQt.QtWidgets import QSizePolicy, QSlider, QToolButton, QMainWindow, QComboBox, QCheckBox, QVBoxLayout, \
    QWidget
from qgis.PyQt.uic import loadUi
from qgis.core import QgsColorRamp, QgsStyle, QgsMapLayerProxyModel, QgsRasterLayer
from qgis.gui import QgsColorRampButton, QgsMessageBar, QgsMapLayerComboBox, QgsFieldComboBox
from vtkmodules.vtkCommonCore import vtkStringArray

from enmapboxprocessing.libraryreader import LibraryReader


class SpectralSurfacePlottingWindow(QMainWindow):
    mMessageBar: QgsMessageBar
    mPlot: QWidget

    mDataFormat: QComboBox
    mLayer: QgsMapLayerComboBox

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
    mLoadData: QToolButton

    scaleBase = 2
    mScaleX: QSlider
    mScaleY: QSlider
    mScaleZ: QSlider
    mAutoScale: QToolButton

    LongFormat, LibraryFormat = 0, 1

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

        self.mLayer.setProject(self.enmapBox.project())
        self.mLayer.setFilters(QgsMapLayerProxyModel.Filter.VectorLayer)

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

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        x = list()
        y = list()
        z = list()
        c = list()

        if self.mDataFormat.currentIndex() == self.LongFormat:
            fieldX = self.mFieldLfX.currentField()
            fieldY = self.mFieldLfY.currentField()
            fieldZ = self.mFieldLfZ.currentField()
            for feature in layer.getFeatures():
                x.append(feature[fieldX])
                y.append(feature[fieldY])
                z.append(feature[fieldZ])

        elif self.mDataFormat.currentIndex() == self.LibraryFormat:
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
                        ci = values.get(fieldC, zi)  # default color is zi
                        x.append(xi)
                        y.append(yi)
                        z.append(zi)
                        c.append(ci)
            except Exception:
                self.mMessageBar.pushWarning('Load data', 'select a spectral profile attribute')

        else:
            raise ValueError()

        return x, y, z, c

    def setData(self, x, y, z, c):
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

        # scale tick values
        xlabels = self.gridActor.x_labels
        ylabels = self.gridActor.y_labels
        # zlabels = self.gridActor.z_labels
        xlabels2 = vtkStringArray()
        ylabels2 = vtkStringArray()
        # zlabels2 = vtkStringArray()
        for i, (vx, vy) in enumerate(zip(xlabels, ylabels)):
            xlabels2.InsertNextValue(str(float(vx) / self.scaleX))
            ylabels2.InsertNextValue(str(float(vy) / self.scaleY))
            # zlabels2.InsertNextValue(str(float(vz) / self.scaleZ))
        self.gridActor.SetAxisLabels(0, xlabels2)
        self.gridActor.SetAxisLabels(1, ylabels2)
        # self.gridActor.SetAxisLabels(2, zlabels2)

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

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
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
