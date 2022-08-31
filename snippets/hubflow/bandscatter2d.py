import enmapboxtestdata
from _classic.hubflow.core import *

enmap = Raster(filename=enmapboxtestdata.enmap)
mask = Vector(filename=enmapboxtestdata.landcover)
bandIndicies = 0, 1

statistics = enmap.statistics(bandIndicies=bandIndicies, mask=mask)

scatter = enmap.scatterMatrix(raster2=enmap, bandIndex1=bandIndicies[0], bandIndex2=bandIndicies[1],
                              range1=(statistics[0]['min'], statistics[0]['max']),
                              range2=(statistics[1]['min'], statistics[1]['max']),
                              bins=10, mask=mask)
print(scatter)