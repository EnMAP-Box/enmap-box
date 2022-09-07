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

from typeguard import typechecked, check_type

GdalDataType = int
GdalResamplingAlgorithm = int
NumpyDataType = Union[type, np.dtype]
QgisDataType = int
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
    value: Union[int, str]
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

    @staticmethod
    def fromDict(d: Dict):
        return TransformerDump(d.get('features'), d.get('X'), d.get('transformer'))


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

    @staticmethod
    def fromDict(d: Dict):
        return ClassifierDump(
            d.get('categories'), d.get('features'), d.get('X'), d.get('y'), d.get('classifier'))


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


@typechecked
def checkSampleShape(X: SampleX, Y: SampleY, raise_=False) -> bool:
    if not (X.ndim == Y.ndim == 2) and (X.shape[0] == Y.shape[0]):
        if raise_:
            raise ValueError(f'X{list(X.shape)} and Y{list(Y.shape)} data not matching')
        return False
    return True
