from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.spectralresampling import SpectralSensors
from enmapboxprocessing.algorithm.spectralresamplingtosensoralgorithmbase import SpectralResamplingToSensorAlgorithmBase


@typechecked
class SpectralResamplingToSentinel2aAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.Sentinel2a


@typechecked
class SpectralResamplingToSentinel2bAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.Sentinel2b
