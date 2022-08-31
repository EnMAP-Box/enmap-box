from enmapboxprocessing.algorithm.createspectralindicesalgorithm import CreateSpectralIndicesAlgorithm

from enmapbox import initAll
from enmapbox.testing import start_app
from processing import run

filename = r'D:\data\issues\1389\20200928_LEVEL2_LND08_BOA.tif'

qgsApp = start_app()
initAll()

alg = CreateSpectralIndicesAlgorithm()
parameters = {
    alg.P_RASTER: filename,
    alg.P_OUTPUT_VRT: r'D:\data\issues\1389\ndvi.vrt'
}

run(alg, parameters)
