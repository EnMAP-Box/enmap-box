from random import randint

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap_potsdam

reader = RasterReader(enmap_potsdam)
for bandNo in reader.bandNumbers():
    print(reader.wavelength(bandNo))

for bandNo in range(1, 100):
    print(reader.wavelength(randint(1, reader.bandCount())))
