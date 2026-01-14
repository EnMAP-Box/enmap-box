from _classic.hubdc.applier import Applier, ApplierOperator


def script():

    # use grid from input file, but enlarge the resolution

    applier = Applier()
    applier.controls.setResolution(xRes=300, yRes=300)
    applier.controls.setWindowFullSize()
    applier.setInput('LC8', filename=r'C:\Work\data\gms\LC81940242015235LGN00_sr.img')
    applier.setOutputRaster('out', filename=r'c:\output\resampled.img')
    applier.apply(operatorType=SimpleReader)

class SimpleReader(ApplierOperator):

    def ufunc(self):

        sentinel2Wavelength = [443, 490, 560, 665, 705, 740, 783, 842, 865, 945, 1375, 1610, 2190]
        #wl = [440, 480, 560, 655, 865, 1585, 2200]
        array = self.getWavebandArray('LC8', wavelengths=sentinel2Wavelength, linear=True)
        self.setArray('out', array=array)
        self.setMetadataWavelengths('out', wavelengths=sentinel2Wavelength)

if __name__ == '__main__':
    script()
