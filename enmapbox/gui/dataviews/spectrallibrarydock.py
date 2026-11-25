from typing import Optional, List

from enmapbox.gui.dataviews.docks import Dock
from enmapbox.gui.mimedata import extractMapLayers
from enmapbox.qgispluginsupport.qps.speclib.core import profile_fields
from enmapbox.qgispluginsupport.qps.speclib.core.spectrallibrary import SpectralLibraryUtils
from enmapbox.qgispluginsupport.qps.speclib.gui.spectrallibrarywidget import SpectralLibraryWidget
from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtGui import QDragEnterEvent
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import QgsVectorLayer, QgsProject, edit, QgsField


class SpectralLibraryDock(Dock):
    """
    A Dock to show SpectralProfiles
    """

    DEFAULT_PROFILE_FIELD = 'profiles'

    # sigLoadFromMapRequest = pyqtSignal()

    def __init__(self, *args,
                 speclib: Optional[QgsVectorLayer] = None,
                 project: Optional[QgsProject] = None,
                 **kwds):
        super(SpectralLibraryDock, self).__init__(*args, **kwds)
        # self.setAcceptDrops(True)
        self.mSpeclibWidget: SpectralLibraryWidget = SpectralLibraryWidget(speclib=speclib,
                                                                           project=project)

        self.mSpeclibWidget.spectralLibraryPlotWidget().sigDragEnterEvent.connect(self.onSpeclibDragEnterEvent)
        self.mSpeclibWidget.spectralLibraryPlotWidget().sigDropEvent.connect(self.onSpeclibDropEvent)
        self.mSpeclibWidget.setDelegateOpenRequests(True)
        # self.mSpeclibWidget.spectralLibraryPlotWidget().optionShowVisualizationSettings.setChecked(False)
        # self.mSpeclibWidget.sigLoadFromMapRequest.connect(self.sigLoadFromMapRequest)
        self.layout.addWidget(self.mSpeclibWidget)

        # speclib: QgsVectorLayer = self.mSpeclibWidget.speclib()
        # name = kwds.get('name')
        # if isinstance(name, str):
        #    speclib.setName(name)

        # self.setTitle(speclib.name())
        # speclib.nameChanged.connect(lambda slib=speclib: self.setTitle(slib.name()))
        # self.sigTitleChanged.connect(speclib.setName)
        self.mDefaultSpeclibId: str = ''
        if isinstance(speclib, QgsVectorLayer):
            self.mDefaultSpeclibId = speclib.id()

    def onSpeclibDragEnterEvent(self, event: QDragEnterEvent):
        # print(event.mimeData().formats())
        supported_formats = [
            'application/x-vnd.qgis.qgis.uri',
            'text/uri-list',
            'application/qgis.layertree.source',
            'application/qgis.layertreemodeldata']

        for f in event.mimeData().formats():
            if f in supported_formats:
                event.setAccepted(True)
                return

    # forward to EnMAPBox
    def onSpeclibDropEvent(self, event):

        md = event.mimeData()
        slw = self.speclibWidget()
        layers = extractMapLayers(md, project=slw.project())
        speclibs = [lyr for lyr in layers if SpectralLibraryUtils.isSpectralLibrary(lyr)]
        slw.project().addMapLayers(speclibs)
        for speclib in speclibs:
            for pfield in profile_fields(speclib):
                slw.createProfileVisualization(speclib, pfield)

    def createDefaultSpeclib(self, profile_fields: List[str] = ['profiles']) -> QgsVectorLayer:
        """
        Creates an in-memory spectral library whose layer name is linked to the dock's name
        """
        sl = SpectralLibraryUtils.createSpectralLibrary(profile_fields=profile_fields)
        sl.setName(f'{self.title()}')
        with edit(sl):
            sl.addAttribute(QgsField('name', QMetaType.Type.QString))
        self.speclibWidget().project().addMapLayer(sl)
        # self.dataSourceManager().addDataSources([sl])
        self.mDefaultSpeclibId = sl.id()

        # for n in profile_fields:
        #    self.speclibWidget().createProfileVisualization(sl, n)

        def updateName():
            """Updates the name of the dock or default layer if the other has changed its name"""
            s = self.sender()
            if isinstance(s, SpectralLibraryDock):
                # change the layer name
                title = s.title()
                lyr = s.defaultSpeclib()
                if isinstance(lyr, QgsVectorLayer) and lyr.name() != title:
                    lyr.setName(title)
            elif isinstance(s, QgsVectorLayer):
                # change the dock title
                sid = s.id()
                title = s.name()
                if self.mDefaultSpeclibId == sid and self.title() != title:
                    self.setTitle(title)

        self.sigTitleChanged.connect(updateName)
        sl.nameChanged.connect(updateName)
        return sl

    def defaultSpeclib(self) -> Optional[QgsVectorLayer]:
        """
        Returns the default speclib
        """
        return self.speclibWidget().project().mapLayer(self.mDefaultSpeclibId)

    def close(self):
        self.mSpeclibWidget.plotModel().close()
        super().close()
        # self.layout.removeWidget(self.mSpeclibWidget)
        # self.mSpeclibWidget.plotModel().close()
        # self.mSpeclibWidget = None

        #     self.mSpeclibWidget = None

    def speclibWidget(self) -> SpectralLibraryWidget:
        """
        Returns the SpectralLibraryWidget
        :return: SpectralLibraryWidget
        """
        return self.mSpeclibWidget

    # def speclib(self) -> QgsVectorLayer:
    #    """Returns the underlying spectral library"""
    #    return self.mSpeclibWidget.speclib()

    def populateContextMenu(self, menu: QMenu):
        """
        Returns the Spectral Library Dock context menu
        :return: QMenu
        """
        super(SpectralLibraryDock, self).populateContextMenu(menu)

        # here we might add Spectral Library Widget specific action
        # speclib / vector layer specific ones are accessible via the lower node
