from _classic.hubdc.applier import Applier, ApplierOperator

def script():

    # use grid from input file, but enlarge the resolution

    applier = Applier()
    applier.controls.setResolution(xRes=3000, yRes=3000)
    applier.setInput('LC8', filename=r'C:\Work\data\gms\LC81940242015235LGN00_sr.img')
    applier.setInputList('LC8_LE7', filenames=[r'C:\Work\data\gms\LC81940242015235LGN00_sr.img', r'C:\Work\data\gms\LE71940242015275NSG00_sr.img'])
    applier.apply(operatorType=SimpleReader)

class SimpleReader(ApplierOperator):

    def ufunc(self):

        print('\nread image array')
        print(self.getArray('LC8').shape)

        print('\nread image band array')
        print(self.getArray('LC8', indicies=3).shape)

        print('\nread image band subset array')
        print(self.getArray('LC8', indicies=[0, 3, 5]).shape)

        print('\nread image band array by wavelength (red)')
        print(self.getArray('LC8', wavelengths=655).shape)

        print('\nread image band array subset by wavelength (red and nir)')
        print(self.getArray('LC8', wavelengths=[655, 865]).shape)

if __name__ == '__main__':
    script()
