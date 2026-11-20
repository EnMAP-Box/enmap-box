import numpy as np


def getRandomData():
    rng = np.random.default_rng(seed=42)
    number_of_points = 500
    x = rng.random(number_of_points) * 100
    y = rng.random(number_of_points) * 100
    z = np.sinc((x - 20) / 100 * np.pi) + np.sinc((y - 50) / 100 * np.pi)
    return x, y, z


def getLmuWeizen():
    data = np.genfromtxt(r'C:\Users\janzandr\Downloads\STS_Weizen_2017_orig.csv', delimiter=';')
    wavelength = data[0, 3:]
    doys = data[2:, 0]
    values = data[2:, 3:]
    x = list()
    y = list()
    z = list()
    for xi, doyi in enumerate(doys):
        for yi, wli in enumerate(wavelength):
            x.append(doyi)
            y.append(wli)
            z.append(values[xi, yi])
    return x, y, z
