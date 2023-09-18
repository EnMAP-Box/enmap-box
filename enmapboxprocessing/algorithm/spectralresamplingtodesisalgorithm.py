from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.spectralresampling import SpectralSensors
from enmapboxprocessing.algorithm.spectralresamplingtosensoralgorithmbase import SpectralResamplingToSensorAlgorithmBase


@typechecked
class SpectralResamplingToDesisAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.Desis
