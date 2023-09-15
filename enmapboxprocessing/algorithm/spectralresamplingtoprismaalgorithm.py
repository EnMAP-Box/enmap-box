from enmapbox.typeguard import typechecked
from enmapboxprocessing.algorithm.spectralresampling import SpectralSensors
from enmapboxprocessing.algorithm.spectralresamplingtosensoralgorithmbase import SpectralResamplingToSensorAlgorithmBase


@typechecked
class SpectralResamplingToPrismaAlgorithm(SpectralResamplingToSensorAlgorithmBase):
    sensor = SpectralSensors.Prisma
