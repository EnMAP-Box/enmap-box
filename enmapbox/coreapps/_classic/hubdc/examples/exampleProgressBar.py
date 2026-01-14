from _classic.hubdc.applier import Grid, Applier, ApplierOperator, CUIProgressBar, SilentProgressBar

def script():

    #filename = r'H:\EuropeanDataCube\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_sr_band1.img'
    filename = r'C:\Work\data\gms\landsat\194\024\LC81940242015235LGN00\LC81940242015235LGN00_sr_band1.img'
    applier = Applier()
    applier.controls.setProgressBar(progressBar=None)
    applier.setInput('in', filename=filename)
    applier.apply(operatorType=SimpleIO)

class SimpleIO(ApplierOperator):
    def ufunc(self):
        pass


if __name__ == '__main__':
    script()
