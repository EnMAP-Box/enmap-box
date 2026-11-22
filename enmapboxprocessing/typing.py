from dataclasses import dataclass
from typing import Union, List, Dict, Optional, Any

import numpy as np
from osgeo import gdal

from qgis.core import QgsRasterDataProvider, QgsRasterLayer

try:  # scikit-learn is optional
    from sklearn.base import ClassifierMixin, RegressorMixin, TransformerMixin, ClusterMixin
    from sklearn.pipeline import Pipeline
except Exception:
    ClassifierMixin = Any
    RegressorMixin = Any
    TransformerMixin = Any
    ClusterMixin = Any
    Pipeline = Any

GdalDataType = int
GdalResamplingAlgorithm = int
NumpyDataType = Union[type, np.dtype]
Number = Union[int, float]
Array1d = np.ndarray
Array2d = np.ndarray
Array3d = Union[np.ndarray, List[Array2d]]
MetadataScalarValue = Optional[Union[str, int, float]]
MetadataListValue = List[MetadataScalarValue]
MetadataValue = Union[MetadataScalarValue, MetadataListValue]
MetadataDomain = Dict[str, MetadataValue]
Metadata = Dict[str, MetadataDomain]
RasterSource = Union[str, QgsRasterLayer, QgsRasterDataProvider, gdal.Dataset]
CreationOptions = List[str]
HexColor = str


@dataclass
class Category(object):
    value: Union[int, float, str]
    name: str
    color: HexColor


@dataclass
class Target(object):
    name: str
    color: Optional[HexColor]


Categories = List[Category]
Targets = List[Target]
SampleX = np.ndarray
SampleY = np.ndarray


@dataclass
class TransformerDump(object):
    features: Optional[List[str]]
    X: Optional[SampleX]
    transformer: Optional[Union[TransformerMixin, Pipeline]] = None
    summary: Optional[Dict] = None

    @staticmethod
    def fromDict(d: Dict):
        return TransformerDump(d.get('features'), d.get('X'), d.get('transformer'))

    @classmethod
    def fromFile(cls, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            d = Utils.modelLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['X'] = np.array(d['X'])
            if 'y' in d:
                d['y'] = np.array(d['y'])
                d['transformer'] = None
        else:
            raise ValueError('wrong file extension, only "skops" or "json" is supported')

        return cls.fromDict(d)

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        d = self.__dict__
        if d['summary'] is None:
            d.pop('summary')
        if filename.endswith('.skops'):
            Utils.modelDump(d, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(d, filename)
        else:
            raise ValueError('wrong file extension, use "skops" or "json"')


@dataclass
class ClustererDump(object):
    clusterCount: Optional[int]
    features: Optional[List[str]]
    X: Optional[SampleX]
    clusterer: Optional[Union[ClusterMixin, Pipeline]] = None

    @staticmethod
    def fromDict(d: Dict):
        return ClustererDump(d.get('clusterCount'), d.get('features'), d.get('X'), d.get('clusterer'))

    @classmethod
    def fromFile(cls, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            d = Utils.modelLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['X'] = np.array(d['X'])
            d['y'] = np.array(d['y'])
            d['clusterer'] = None
        else:
            raise ValueError('wrong file extension, only "skops" or "json" is supported')

        return cls.fromDict(d)

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            Utils.modelDump(self.__dict__, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(self.__dict__, filename)
        else:
            raise ValueError('wrong file extension, use "skops" or "json"')


@dataclass
class ClassifierDump(object):
    categories: Optional[Categories]
    features: Optional[List[str]]
    X: Optional[SampleX]
    y: Optional[SampleY]
    classifier: Optional[Union[ClassifierMixin, Pipeline]] = None
    locations: Optional[np.ndarray] = None
    crs: Optional[str] = None

    def __post_init__(self):
        if self.X is not None and self.X.ndim != 2:
            raise ValueError(
                f'X must be a 2-dimensional array, got ndim={self.X.ndim}'
            )
        if self.y is not None and self.y.ndim != 2:
            raise ValueError(
                f'y must be a 2-dimensional array, got ndim={self.y.ndim}'
            )
        if self.locations is not None:
            if self.locations.ndim != 2:
                raise ValueError(
                    f'locations must be a 2-dimensional array, got ndim={self.locations.ndim}'
                )

            if self.locations.shape[1] != 2:
                raise ValueError(
                    f'locations must have shape (n, 2), got shape={self.locations.shape}'
                )

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            Utils.modelDump(self.__dict__, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(self.__dict__, filename)
        else:
            raise ValueError('wrong file extension, use "skops" or "json"')

    @staticmethod
    def fromDict(d: Dict):
        return ClassifierDump(
            d.get('categories'), d.get('features'), d.get('X'), d.get('y'), d.get('classifier'), d.get('locations'),
            d.get('crs')
        )

    @classmethod
    def fromFile(cls, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            d = Utils.modelLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            if 'categories' in d:
                d['categories'] = [Category(**values) for values in d['categories']]
            if 'X' in d:
                d['X'] = np.array(d['X'])
            if 'y' in d:
                d['y'] = np.array(d['y'])
            d['classifier'] = None
            if 'locations' in d:
                if d['locations'] is not None:
                    d['locations'] = np.array(d['locations'])
        else:
            raise ValueError('wrong file extension, only "skops" or "json" is supported')

        return cls.fromDict(d)


@dataclass
class RegressorDump(object):
    targets: Optional[Targets]
    features: Optional[List[str]]
    X: Optional[SampleX]
    y: Optional[SampleY]
    regressor: Optional[Union[RegressorMixin, Pipeline, Any]] = None
    locations: Optional[np.ndarray] = None
    crs: Optional[str] = None

    def __post_init__(self):
        if self.y is not None and self.y.ndim != 2:
            raise ValueError(
                f'y must be a 2-dimensional array, got shape={self.y.shape}'
            )
        if self.locations is not None:
            if self.locations.ndim != 2:
                raise ValueError(
                    f'locations must be a 2-dimensional array, got shape={self.locations.shape}'
                )

            if self.locations.shape[1] != 2:
                raise ValueError(
                    f'locations must have shape (n, 2), got shape={self.locations.shape}'
                )

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            Utils.modelDump(self.__dict__, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(self.__dict__, filename)
        else:
            raise ValueError('wrong file extension, use "skops" or "json"')

    @staticmethod
    def fromDict(d: Dict):
        return RegressorDump(
            d.get('targets'), d.get('features'), d.get('X'), d.get('y'), d.get('regressor'), d.get('locations'),
            d.get('crs')
        )

    @classmethod
    def fromFile(cls, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.skops'):
            d = Utils.modelLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['targets'] = [Target(**values) for values in d['targets']]
            d['X'] = np.array(d['X'])
            d['y'] = np.array(d['y'])
            d['regressor'] = None
            if 'locations' in d:
                if d['locations'] is not None:
                    d['locations'] = np.array(d['locations'])
        else:
            raise ValueError('wrong file extension, only "skops" or "json" is supported')

        return cls.fromDict(d)


def checkSampleShape(X: SampleX, Y: SampleY, raise_=False) -> bool:
    if not (X.ndim == Y.ndim == 2) and (X.shape[0] == Y.shape[0]):
        if raise_:
            raise ValueError(f'X{list(X.shape)} and Y{list(Y.shape)} data not matching')
        return False
    return True
