"""
This script shows how to create an EnMAP-Box spectral library
with Spectrometer profiles (*.sig, *.asd) stored in a folder `path_input_dir`.
"""
from pathlib import Path

from enmapbox.qgispluginsupport.qps.speclib.processing.importspectralprofiles import ImportSpectralProfiles
from enmapbox.testing import TestCase

# uncomment the following lines to run the code from plain python
if True:
    from enmapbox import initAll
    from enmapbox.testing import start_app

    start_app()
    initAll()

alg = ImportSpectralProfiles()
alg.initAlgorithm({})

path_input_dir = Path(r'C:\<input directory>')
path_output = path_input_dir / 'spectral_library3.gpkg'

parameters = {
    alg.P_INPUT: str(path_input_dir),
    alg.P_OUTPUT: str(path_output),
}

context, feedback = TestCase.createProcessingContextFeedback()
alg.run(parameters, context, feedback)
print(feedback.textLog())
