from typing import Dict, Tuple
#import statistics

import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from _classic.hubdc.core import *
# 1
from _classic.hubflow.core import RegressionSample, Raster, Regression, RegressionPerformance
from _classic.hubflow.report import Report, ReportImage, ReportHeading, ReportPlot, ReportParagraph


def spectralIndexOptimizer(filenamePrediction, filenameReport, featuresFilename, labelsFilename, rasterFilename,
        indexType=0, performanceType=0):
    '''
    The Spectral Index Optimizer is a tool for the EnMAP box.
	It is supposed to find the best two-band spectral index for the estimation
	of a measured variable via linear regression.
	Input: Spectra (explaining variable) and measurements (depending variable)
	The tool will calculate all possible combinations of spectral indices,
	either 
	- Normalized Difference: [(a - b) / (a + b)], or
	- Ratio Index: (a / b), or
	- Difference Index: (a - b).
	Then, a linear regression between the index values and the measurements is
	calculated. A performance indicator for the estimated values is calculated,
	either
	- Root mean squared error (RMSE), or
	- Mean absolute error (MAE), or
	- Coefficient of determination (R²).
	When all waveband combinations have been calculated, the optimal solution 
	is found. The respective final model is calculated and applied to the input
	raster. The matrix of performance indicators, the selected bands, the final
	regression model and the performance are output to an HTML report.
    '''

    # 2
    features = Raster(featuresFilename) # Raster File with Spectral information
    labels = Regression(labelsFilename) # Raster File with measurements
    raster = Raster(rasterFilename)     # Raster File to apply the model on (may be the same as feature file)
    regressionSample = RegressionSample(raster=features, regression=labels) # Collects data for regression
    x, y = regressionSample.extractAsArray()
    #x = x[::10] # Speed up calculation by only using every tenth band (for development and testing)
    nbands, nsamples = x.shape
    bnds = np.linspace(1, nbands, nbands)

    if indexType == 0:
        siFunc = lambda a, b: (a - b) / (a + b)
        siStr = '(w1 - w2) / (w1 + w2)'
    elif indexType == 1:
        siFunc = lambda a, b: a / b
        siStr = 'w1 / w2'
    elif indexType == 2:
        siFunc = lambda a, b: a - b
        siStr = 'w1 - w2'
    else:
        assert 0 # give error message in case of wrong index type

    if performanceType == 0:  # RMSE
        errorFunc = lambda y, yP: mean_squared_error(y, yP) ** 0.5
    elif performanceType == 1:  # MAE
        errorFunc = lambda y, yP: mean_absolute_error(y, yP)
    elif performanceType == 2:  # R^2
        errorFunc = lambda y, yP: r2_score(y, yP)
    else:
        assert 0 # give error message in case of wrong performance type

    olsr = LinearRegression() # Object for ordinary least squares regression
    errors: Dict[Tuple[int, int], float] = dict() # performances collected in dictionary
    for i1 in range(nbands): # Outer Loop
        x1 = x[i1]
        for i2 in range(i1 + 1, nbands): # Inner Loop
            x2 = x[i2]
            si = siFunc(x1, x2) # Calculate spectral index
            if np.all(np.isfinite(si)):
                olsr.fit(X=si.T.reshape(-1, 1), y=y[0]) # Fit
                yP = olsr.predict(X=si.T.reshape(-1, 1))# Predict
                e = errorFunc(y[0], yP)                 # Calc. Performance
            else:
                e = np.inf   # Performance = inf if division by zero etc.
            errors[i1, i2] = e # Fill performance matrix
            # print(i1, i2, e) # print performance (for development and testing)

    img = np.full(shape=(nbands, nbands), fill_value=np.nan)
    for (i1, i2), e in errors.items():
        img[i1, i2] = e
    #    img[i2, i1] = e

    # find best wavebands
    if performanceType == 0:  # RMSE
        best1, best2 = list(errors.keys())[np.argmin(list(errors.values()))]
    elif performanceType == 1:  # MAE
        best1, best2 = list(errors.keys())[np.argmin(list(errors.values()))]
    elif performanceType == 2:  # R^2
        best1, best2 = list(errors.keys())[np.argmax(list(errors.values()))]

    # train final model
    bestSi = siFunc(x[best1], x[best2])
    olsr.fit(X=bestSi.T.reshape(-1, 1), y=y[0])
    yP = olsr.predict(X=bestSi.T.reshape(-1, 1))
    efinal = img[best1, best2]
    #bestRMSE = mean_squared_error(y, yP) ** 0.5
    #bestMAE  = mean_absolute_error(y, yP)
    #bestR2   = r2_score(y, yP)

    # apply model to raster
    a1 = raster.dataset().band(index=best1).readAsArray()
    a2 = raster.dataset().band(index=best2).readAsArray()
    si = siFunc(a1, a2)
    X = si.flatten().reshape(-1, 1)
    invalid = np.logical_not(np.isfinite(X))
    X[invalid] = 0
    yPImage = olsr.predict(X=X)
    yPImage[invalid[:, 0]] = 0
    yPImage = yPImage.reshape(si.shape)[None]
    Raster.fromArray(array=yPImage, grid=raster.dataset().grid(), filename=filenamePrediction)

    # report
    from spectralindexoptimizerapp import SpectralIndexOptimizerProcessingAlgorithm

    plot = None
    siName = SpectralIndexOptimizerProcessingAlgorithm.INDEX_TYPE_OPTIONS[indexType]
    report = Report(title='Spectral Index Optimizer')
    report.append(ReportParagraph(text=f'Index Type: {siName}, SI = f(w1, w2) = {siStr}'))
    #report.append(ReportParagraph(text=f'SI = f(w1, w2) = {siStr}'))
    report.append(ReportParagraph(text=f'Selected Waveband1 (w1): Band {best1 + 1}: {features.dataset().band(best1).description()}'))
    report.append(ReportParagraph(text=f'Selected Waveband2 (w2): Band {best2 + 1}: {features.dataset().band(best2).description()}'))
    report.append(ReportParagraph(text=f'Regression Function f(SI) = {olsr.coef_[0]:10.4f} * SI {olsr.intercept_:+10.4f}'))
    #report.append(ReportParagraph(text=f'Performance = {efinal:9.4f}'))
    #report.append(ReportParagraph(text=f'Performance Type: {SpectralIndexOptimizerProcessingAlgorithm.PERFORMANCE_TYPE_OPTIONS[performanceType]}'))
    report.append(ReportParagraph(text=f'Best {SpectralIndexOptimizerProcessingAlgorithm.PERFORMANCE_TYPE_OPTIONS[performanceType]} = {efinal:9.4f}'))
    # todo performance measures -> use y, yP

    report.append(ReportHeading('Figures'))
    #fig, (ax1, ax2) = plt.subplots(1, 2, facecolor='white', figsize=(9, 5))
    #ax1.plot(x)
    #im = ax2.imshow(img, origin='lower')
    #plt.xlabel('Band 1')
    #plt.ylabel('Band 2')
    #fig.colorbar(im)
    #plt.tight_layout()
    #report.append(ReportPlot(figure=fig, caption='Spectra'))
    #plt.close()

    fig = plt.figure( figsize=(9, 7.5)) #constrained_layout=True,
    ax1 = plt.subplot2grid((3, 3), (2, 0))
    ax1.scatter(np.transpose(y), yP, marker='.', color='#ee7f0e', alpha=0.5)
    plt.xlabel('Measured')
    plt.ylabel('Estimated')
    ax2 = plt.axes((0.4, 0.072, 0.48, 0.27))
    ax2.plot(bnds,x, '-k', alpha=0.5)
    ax2.axvline(x=best1, color='b')
    ax2.axvline(x=best2, color='b')
    plt.xlabel('Band Number')
    ax3 = plt.subplot2grid((3, 3), (0, 0), rowspan=2)
    ax3.plot(x, bnds, '-k', alpha=0.5)
    ax3.axhline(y=best1, color='b')
    ax3.axhline(y=best2, color='b')
    plt.ylabel('Band Number')
    ax4 = plt.subplot2grid((3, 3), (0, 1), colspan=2, rowspan=2)
    im = ax4.imshow(img, origin='lower')
    plt.ylabel('Band 1')
    plt.ylabel('Band 2')
    fig.colorbar(im)
    plt.tight_layout()
    report.append(ReportPlot(figure=fig, caption='Correlogram, Spectra, and Scatterplot'))
    plt.close()

    #fig, ax = plt.subplots(facecolor='white', figsize=(7, 5))
    #im=ax.imshow(img, origin='lower')
    #plt.xlabel('Band 1')
    #plt.ylabel('Band 2')
    #fig.colorbar(im)
    #fig.tight_layout()
    #report.append(ReportPlot(figure=fig, caption='Map of Performance'))
    #plt.close()

    #fig, ax = plt.subplots(facecolor='white', figsize=(5, 5))
    #ax.scatter(np.transpose(y), yP, marker='.', color='#ee7f0e', alpha=0.5)
    #fig.tight_layout()
    #report.append(ReportPlot(figure=fig, caption='Scatter plot'))
    #plt.close()

    report.saveHTML(filename=filenameReport, open=True)
