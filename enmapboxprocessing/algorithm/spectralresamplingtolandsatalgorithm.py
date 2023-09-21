from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.spectralresampling import SpectralSensors
from enmapboxprocessing.algorithm.spectralresamplingtosensoralgorithmbase import SpectralResamplingToSensorAlgorithmBase


@typechecked
class SpectralResamplingToLandsatOliAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.LandsatOli


@typechecked
class SpectralResamplingToLandsatEtmAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.LandsatEtm


@typechecked
class SpectralResamplingToLandsatTmAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.LandsatTm
