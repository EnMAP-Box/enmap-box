from random import randint

from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import enmap_potsdam

reader = RasterReader(enmap_potsdam)
for bandNo in reader.bandNumbers():
    print(reader.wavelength(bandNo))

for bandNo in range(1, 100):
    # load 100x the wavelengths for a random band
    print(
        reader.wavelength(
            randint(1, reader.bandCount())  # nosec B311 # random sampling is not security relevant here
        )
    )
