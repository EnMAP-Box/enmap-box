import typing

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication

from enmapbox.qgispluginsupport.qps.models import TreeNode
from .datasources import DataSource, VectorDataSource, RasterDataSource, ModelDataSource, \
    FileDataSource


class DataSourceSet(TreeNode):

    def __init__(self, *args, name: str = '<source set>', **kwds):
        super().__init__(*args, name=name, **kwds)

        self.mSetName = name
        self.updateName()

    def __iter__(self):
        return iter(self.dataSources())

    def clear(self):
        """Removes all datasources
        """
        self.removeAllChildNodes()
        self.updateName()

    def updateName(self):

        self.setName(f'{self.mSetName} ({len(self.dataSources())})')

    def sources(self) -> typing.List[str]:
        sources = []
        for s in self.dataSources():
            sources.append(s.source())
        return sources

    def dataSources(self) -> typing.List[DataSource]:
        return self.childNodes()

    def removeDataSources(self, dataSources: typing.Union[DataSource, typing.List[DataSource]]) -> \
            typing.List[DataSource]:
        if isinstance(dataSources, DataSource):
            dataSources = [dataSources]
        owned = self.dataSources()
        toremove = [d for d in dataSources if d in owned]

        if len(toremove) > 0:
            self.removeChildNodes(toremove)
            self.updateName()
        return toremove

    def addDataSources(self, dataSources: typing.Union[DataSource, typing.List[DataSource]]) -> typing.List[DataSource]:
        if isinstance(dataSources, DataSource):
            dataSources = [dataSources]

        existing = [ds.source() for ds in self.dataSources()]

        for s in dataSources:
            assert isinstance(s, DataSource)
            assert self.isValidSource(s)
        # ensure unique source names
        newSources = [s for s in dataSources if s.source() not in existing]
        if len(newSources) > 0:
            self.appendChildNodes(newSources)
        self.updateName()
        return newSources

    def isValidSource(self, source) -> bool:
        raise NotImplementedError


class ModelDataSourceSet(DataSourceSet):
    def __init__(self, *args, **kwds):
        super().__init__(*args,
                         name='Models',
                         icon=QgsApplication.getThemeIcon('processingAlgorithm.svg')
                         )

    def isValidSource(self, source) -> bool:
        return isinstance(source, ModelDataSource)


class VectorDataSourceSet(DataSourceSet):

    def __init__(self, *args, **kwds):
        super().__init__(*args,
                         name='Vectors',
                         icon=QgsApplication.getThemeIcon('mIconVector.svg')
                         )

    def isValidSource(self, source) -> bool:
        return isinstance(source, VectorDataSource)


class FileDataSourceSet(DataSourceSet):

    def __init__(self, *args, **kwds):
        super(FileDataSourceSet, self).__init__(*args,
                                                name='Other Files',
                                                icon=QIcon(r':/trolltech/styles/commonstyle/images/file-128.png')
                                                )

    def isValidSource(self, source) -> bool:
        return isinstance(source, FileDataSource)


class RasterDataSourceSet(DataSourceSet):

    def __init__(self, *args, **kwds):
        super(RasterDataSourceSet, self).__init__(*args,
                                                  name='Rasters',
                                                  icon=QgsApplication.getThemeIcon('mIconRaster.svg')
                                                  )

    def isValidSource(self, source) -> bool:
        return isinstance(source, RasterDataSource)
