import os.path
import warnings

import enmapboxtestdata
from DASFEnMAPbox.core import DASF_retrieval

path = r'C:\Users\Marion\Desktop\EnMAP_box\MyTool\KROOF03_Viertel_RFC_geo_1m_subset710_790.bsq'

if not os.path.isfile(path):
    warnings.warn(f'File does not exist: {path}\n skip DASF tests')
else:
    DASF_retrieval(inputFile=path,
                   outputName='DASF.bsq',
                   secondoutputName='DASF_RetrievalQuality.bsq',
                   thirdoutputName='CSC.bsq')

    if True: # show the result in a viewer
        from _classic.hubdc.core import openRasterDataset, MapViewer
        rasterDataset = openRasterDataset(filename='DASF.bsq')
        MapViewer().addLayer(rasterDataset.mapLayer()).show()
