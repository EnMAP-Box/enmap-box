import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from qgis.PyQt.QtWidgets import QSizePolicy
from qgis.PyQt.QtWidgets import QSlider
from qgis.PyQt.QtWidgets import QToolButton, QMainWindow, QComboBox, QCheckBox
from qgis.PyQt.QtWidgets import QVBoxLayout
from qgis.PyQt.QtWidgets import QWidget
from qgis.PyQt.uic import loadUi
from qgis.core import QgsMapLayerProxyModel, QgsRasterLayer
from qgis.gui import QgsMapLayerComboBox, QgsFieldComboBox

from enmapboxprocessing.libraryreader import LibraryReader
from spectralsurfaceplottingapp.exampledata import getRandomData


class SpectralSurfacePlottingWindow(QMainWindow):
    mPlot: QWidget

    mDataFormat: QComboBox
    mLayer: QgsMapLayerComboBox

    mShowSurface: QCheckBox
    mShowPoints: QCheckBox
    mShowEdges: QCheckBox

    mFieldLfX: QgsFieldComboBox
    mFieldLfY: QgsFieldComboBox
    mFieldLfZ: QgsFieldComboBox
    mLoadData: QToolButton
    mFieldLibraryProfiles: QgsFieldComboBox
    mFieldLibraryY: QgsFieldComboBox

    mScaleX: QSlider
    mScaleY: QSlider
    mScaleZ: QSlider
    mAutoScale: QToolButton

    LongFormat, LibraryFormat = 0, 1

    def __init__(self, *args, **kwds):
        QMainWindow.__init__(self, *args, **kwds)
        loadUi(__file__.replace('.py', '.ui'), self)

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

        self.mScaleX.valueChanged.connect(self.onScaleChanged)
        self.mScaleY.valueChanged.connect(self.onScaleChanged)
        self.mScaleZ.valueChanged.connect(self.onScaleChanged)
        self.mAutoScale.clicked.connect(self.onAutoScale)

        self.mLoadData.clicked.connect(self.onLoadData)

    def readData(self):

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        x = list()
        y = list()
        z = list()
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

            for i, (values, geometry) in enumerate(reader.data(), 1):
                xs = values[fieldProfile]['x']
                zs = values[fieldProfile]['y']
                for xi, zi in zip(xs, zs):
                    yi = values.get(fieldY, i)
                    if not np.isfinite([xi, yi, zi]).all():
                        continue
                    x.append(xi)
                    y.append(yi)
                    z.append(zi)
        else:
            raise ValueError()

        return x, y, z

    def setData(self, x, y, z):
        self.x = np.array(x, dtype=float)
        self.y = np.array(y, dtype=float)
        self.z = np.array(z, dtype=float)
        xyz = np.column_stack((self.x, self.y, self.z))
        if not np.isfinite(xyz).all():
            raise ValueError('Spectral Surface Plotting: data includes non-finite values')
        self.point_cloud = pv.PolyData(xyz)
        self.point_cloud.point_data['Z'] = z
        self.mesh = self.point_cloud.delaunay_2d()
        self.mesh.point_data["Z"] = self.mesh.points[:, 2]

    def plotData(self):

        self.meshActorSurface = self.plotter.add_mesh(
            self.mesh,
            scalars="Z",
            cmap="viridis",
            show_edges=self.mShowEdges.isChecked(),
            edge_color="black",
            line_width=0.4,
            smooth_shading=True,
            opacity=0.8 + 0.2,
            scalar_bar_args={"title": "Z"},
            name='surface'
        )
        self.onShowSurfaceChanged()

        self.meshActorPoints = self.plotter.add_mesh(
            self.point_cloud,
            scalars="Z",
            cmap="viridis",
            render_points_as_spheres=True,
            point_size=8,
            show_scalar_bar=False,
            name='points'
        )
        self.onShowPointsChanged()

        self.plotter.add_axes(
            xlabel="X",
            ylabel="Y",
            zlabel="Z",
        )

        if False:  # need to fix problem with tick values
            self.plotter.show_grid(
                xtitle="X",
                ytitle="Y",
                ztitle="Z",
            )

        self.plotter.enable_parallel_projection()

    def autoScaleFactors(self):
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
        self.plotter.set_scale(xscale, yscale, zscale, reset_camera=True)

    def onShowSurfaceChanged(self):
        self.meshActorSurface.SetVisibility(self.mShowSurface.isChecked())

    def onShowPointsChanged(self):
        self.meshActorPoints.SetVisibility(self.mShowPoints.isChecked())

    def onShowEdgesChanged(self):
        self.meshActorSurface.prop.show_edges = self.mShowEdges.isChecked()
        self.plotter.render()

    def onScaleChanged(self):
        self.setScale(2 ** self.mScaleX.value(), 2 ** self.mScaleY.value(), 2 ** self.mScaleZ.value())
        self.plotter.render()

    def onAutoScale(self):
        xscale, yscale, zscale = self.autoScaleFactors()

        self.mScaleX.setValue(int(np.log2(xscale)))
        self.mScaleY.setValue(int(np.log2(yscale)))
        self.mScaleZ.setValue(int(np.log2(zscale)))

    def onLoadData(self):

        layer: QgsRasterLayer = self.mLayer.currentLayer()
        if layer is None:
            return

            x, y, z = getRandomData()
        else:
            x, y, z = self.readData()

        self.setData(y, x, z)
        self.plotData()
        self.onAutoScale()
