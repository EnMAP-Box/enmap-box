import enmapbox.exampledata
from enmapbox.coreapps._classic.hubflow.core import Raster, Vector

enmap = Raster(filename=enmapbox.exampledata.enmap)
mask = Vector(filename=enmapbox.exampledata.landcover_polygons)
bandIndicies = 0, 1

statistics = enmap.statistics(bandIndicies=bandIndicies, mask=mask)

scatter = enmap.scatterMatrix(raster2=enmap, bandIndex1=bandIndicies[0], bandIndex2=bandIndicies[1],
                              range1=(statistics[0]['min'], statistics[0]['max']),
                              range2=(statistics[1]['min'], statistics[1]['max']),
                              bins=10, mask=mask)
print(scatter)
