from enmapboxprocessing.algorithm.spectralresampling import SpectralSensors
from enmapboxprocessing.algorithm.spectralresamplingtosensoralgorithmbase import SpectralResamplingToSensorAlgorithmBase


class SpectralResamplingToLandsatOliAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.LandsatOli


class SpectralResamplingToLandsatEtmAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.LandsatEtm


class SpectralResamplingToLandsatTmAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.LandsatTm
