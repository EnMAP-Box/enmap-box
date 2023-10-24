from dataclasses import dataclass
from typing import Union, List, Dict, Optional, Any

import numpy as np
from osgeo import gdal

from qgis.core import QgsRasterDataProvider, QgsRasterLayer

try:  # scikit-learn is optional
    from sklearn.base import ClassifierMixin, RegressorMixin, TransformerMixin, ClusterMixin
    from sklearn.pipeline import Pipeline
except Exception as error:
    ClassifierMixin = Any
    RegressorMixin = Any
    TransformerMixin = Any
    ClusterMixin = Any
    Pipeline = Any

from enmapbox.typeguard import typechecked, check_type

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


@typechecked
@dataclass
class Category(object):
    value: Union[int, float, str]
    name: str
    color: HexColor


@typechecked
@dataclass
class Target(object):
    name: str
    color: Optional[HexColor]


Categories = List[Category]
Targets = List[Target]
SampleX = np.ndarray
SampleY = np.ndarray


@typechecked
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
        if filename.endswith('.pkl'):
            d = Utils.pickleLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['X'] = np.array(d['X'])
            if 'y' in d:
                d['y'] = np.array(d['y'])
                d['transformer'] = None
        else:
            raise ValueError('wrong file extension, only "pkl" or "json" is supported')

        return cls.fromDict(d)

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        d = self.__dict__
        if d['summary'] is None:
            d.pop('summary')
        if filename.endswith('.pkl'):
            Utils.pickleDump(d, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(d, filename)
        else:
            raise ValueError('wrong file extension, use "pkl" or "json"')


@typechecked
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
        if filename.endswith('.pkl'):
            d = Utils.pickleLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['X'] = np.array(d['X'])
            d['y'] = np.array(d['y'])
            d['clusterer'] = None
        else:
            raise ValueError('wrong file extension, only "pkl" or "json" is supported')

        return cls.fromDict(d)

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.pkl'):
            Utils.pickleDump(self.__dict__, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(self.__dict__, filename)
        else:
            raise ValueError('wrong file extension, use "pkl" or "json"')


@typechecked
@dataclass
class ClassifierDump(object):
    categories: Optional[Categories]
    features: Optional[List[str]]
    X: Optional[SampleX]
    y: Optional[SampleY]
    classifier: Optional[Union[ClassifierMixin, Pipeline]] = None

    def __post_init__(self):
        check_type('categories', self.categories, Optional[Categories])
        check_type('features', self.features, Optional[List[str]])
        check_type('X', self.X, Optional[SampleX])
        check_type('y', self.y, Optional[SampleY])
        try:
            check_type('classifier', self.classifier, Optional[Union[ClassifierMixin, Pipeline]])
        except Exception:
            from sklearn.base import is_classifier
            if not is_classifier(self.classifier):
                raise TypeError('classifier is not a valid scikit-learn classifier')

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.pkl'):
            Utils.pickleDump(self.__dict__, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(self.__dict__, filename)
        else:
            raise ValueError('wrong file extension, use "pkl" or "json"')

    @staticmethod
    def fromDict(d: Dict):
        return ClassifierDump(
            d.get('categories'), d.get('features'), d.get('X'), d.get('y'), d.get('classifier'))

    @classmethod
    def fromFile(cls, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.pkl'):
            d = Utils.pickleLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['categories'] = [Category(**values) for values in d['categories']]
            d['X'] = np.array(d['X'])
            d['y'] = np.array(d['y'])
            d['classifier'] = None
        else:
            raise ValueError('wrong file extension, only "pkl" or "json" is supported')

        return cls.fromDict(d)


@typechecked
@dataclass
class RegressorDump(object):
    targets: Optional[Targets]
    features: Optional[List[str]]
    X: Optional[SampleX]
    y: Optional[SampleY]
    regressor: Optional[Union[RegressorMixin, Pipeline]] = None

    def __post_init__(self):
        check_type('targets', self.targets, Optional[Targets])
        check_type('features', self.features, Optional[List[str]])
        check_type('X', self.X, Optional[SampleX])
        check_type('y', self.y, Optional[SampleY])
        try:
            check_type('regressor', self.regressor, Optional[Union[RegressorMixin, Pipeline]])
        except Exception:
            from sklearn.base import is_regressor
            if not is_regressor(self.regressor):
                raise TypeError('regressor is not a valid scikit-learn regressor')

    @staticmethod
    def fromDict(d: Dict):
        return RegressorDump(
            d.get('targets'), d.get('features'), d.get('X'), d.get('y'), d.get('regressor'))

    @classmethod
    def fromFile(cls, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.pkl'):
            d = Utils.pickleLoad(filename)
        elif filename.endswith('.json'):
            d = Utils.jsonLoad(filename)
            d['targets'] = [Target(**values) for values in d['targets']]
            d['X'] = np.array(d['X'])
            d['y'] = np.array(d['y'])
            d['regressor'] = None
        else:
            raise ValueError('wrong file extension, only "pkl" or "json" is supported')

        return cls.fromDict(d)

    def write(self, filename: str):
        from enmapboxprocessing.utils import Utils
        if filename.endswith('.pkl'):
            Utils.pickleDump(self.__dict__, filename)
        elif filename.endswith('.json'):
            Utils.jsonDump(self.__dict__, filename)
        else:
            raise ValueError('wrong file extension, use "pkl" or "json"')


@typechecked
def checkSampleShape(X: SampleX, Y: SampleY, raise_=False) -> bool:
    if not (X.ndim == Y.ndim == 2) and (X.shape[0] == Y.shape[0]):
        if raise_:
            raise ValueError(f'X{list(X.shape)} and Y{list(Y.shape)} data not matching')
        return False
    return True
