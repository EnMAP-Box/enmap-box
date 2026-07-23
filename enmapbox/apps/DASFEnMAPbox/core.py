# Script: DASF function retrieval#
# Author: Msc Lusseau Marion, PhD Student at Trier University under the supervision of Prof. Dr. Hill Joachim
# Adapted from Dr. Buddenbaum Henning's Matlab script, Post Doc researcher at Trier University
# Based on the on work of Knyazikhin et al. 10.1073/pnas.1210196109

# 0
import numpy as np
from scipy import interpolate, stats
from _classic.hubdc.core import *

def DASF_retrieval(inputFile, outputName, secondoutputName, thirdoutputName):

	# ...
	# This function derives the directional area scattering factor or DASF function for vegetation canopy with dark background
	# or sufficiently dense vegetation where the impact of canopy background is negligible.
	#
	# param inputFile: input raster file
	# param outputFile: name of the outputFile
	# ...


# 1 open datasets
	Data = openRasterDataset(filename= inputFile)
	GridData = Data.grid() # set the Grid to

	BRFs = Data.readAsArray()
	mask_BRFs = BRFs == 0 # mask of 0 values to avoid future error later
	BRFs[mask_BRFs] = 99999 # apply the mask

	# get single item (list with wavelength casted to float), must be in .hdr file
	banddata = Data.metadataItem(key='wavelength', domain='ENVI', dtype=float)
	WL = np.array(banddata) # convert to ndarray

	# Set pre-calculated reference Albedo using PROSPECT and the parameters given by Knyazikhin et al. (2012)
	albedo = np.array ([0.519116253197260,0.543791042621256,0.567102210319844,0.589290220472722,0.610242046668829,
						  0.629960818556671,0.648593042785735,0.666228424467400,0.682974987746569,0.698849036245537,
						  0.714026564493359,0.728504553871227,0.742301722931950,0.755559358905909,0.768291041303186,
						  0.780515914095742,0.792214374938579,0.803419616239661,0.814121929233789,0.824420926071766,
						  0.834226102229190,0.843591214952454,0.852532491364881,0.861014096466874,0.869111547439901,
						  0.876737221523391,0.883916768500255,0.890736497061422,0.897114975766896,0.903147508964747,
						  0.908811986036894,0.914092140809846,0.919103022674281,0.923765215921136,0.928089293347180,
						  0.932093890996106,0.935807726673285,0.939267969885490,0.942474349260873,0.945449520258242,
						  0.948182596476830,0.950687509796322,0.952997534519883,0.955109220259525,0.957051658187493,
						  0.958819783863400,0.960439949478907,0.961887072561399,0.963199769121276,0.964389645777322,
						  0.965443516224290,0.966369665881569,0.967198841644925,0.967962111719516,0.968650073165328,
						  0.969279968964743,0.969856272852708,0.970362852890091,0.970831351419077,0.971242778844331,
						  0.971574514603716,0.971908999116214,0.972234266289144,0.972554065623516,0.972867699461081,
						  0.973175160337359,0.973475749667189,0.973769459698932,0.974059136824334,0.974339412995108,
						  0.974616321550897,0.974882769561767,0.975142632989307,0.975397036291905,0.975643480722166,
						  0.975882663316402,0.976113847520869,0.976337392330965,0.976552658587245,0.976759279092041,
						  0.976960431004288,0.977152863938899,0.977335170933460,0.977508135524968,0.977672454741569,
						  0.977831203478948,0.977983673058726,0.978128959814846,0.978257692644161,0.978378570053274,
						  0.978493884907733,0.978597338996321,0.978695956727252,0.978781203885217,0.978856703004409,
						  0.978920218096822,0.978975953346379,0.979021673846921,0.979056960805221,0.979081397352204,
						  0.979097657904236])

	#corresponding wavelength
	wl_albedo = np.arange(700,801,1)

# 2 Interpolation of the Albedo to the Spectrum's wavelength
	albedo_interp = []
	# method = linear, fill_value 'extraoplate' allows x_new blow the interpolation range to be extrapolated
	f = interpolate.interp1d(wl_albedo, albedo, fill_value = "extrapolate")
	albedo_interp.append(f(WL))

# 3a Ratio calculation using BRFs and reference albedo
	a = Data.yprofile(column=Column(x=1, z=0))
	b = Data.xprofile(row=Row(y=1, z=0))
	c = Data.zprofile(pixel=Pixel(x=1, y=1))

	ratio = np.empty((len(c),len(a),len(b)))

	for x in range(len(a)):
		for y in range(len (b)):
			ratio[:,x,y] = BRFs[:,x,y] / albedo_interp

# 3b Linear Regression between BRFs/Albedo ratio and BRFs + retrieval of regressions coefficients
	slope = np.empty((len(a),len(b)))
	intercept = np.empty((len(a),len(b)))
	p_value = np.empty((len(a),len(b)))
	std_err = np.empty((len(a),len(b)))
	r_value = np.empty((len(a),len(b)))

# from MyTool.linregress_3D import linregress_3D
	for i in range(len(a)):
		for j in range(len (b)):
			# cov[i, j], cor[i, j], slope[i, j], intercept[i, j], pval[i, j], stderr[i, j] = linregress_3D(
			# x=BRFs[:, i, j], y=ratio[:, i, j])
			slope[i,j], intercept[i,j], r_value[i,j], p_value[i,j], std_err [i,j]= stats.linregress(BRFs[:, i, j], ratio[:, i, j])


# Step 4 - Ratio estimation of the DASF
	DASF = intercept / (1-slope)

# Step 5 - Optional retrieval of R² as retrieval quality indicator
	R2 = r_value**2
	retrieval_quality = np.stack((R2,p_value), axis = 0)

# Step 6 - Applying DASF correction
	CSC = BRFs/DASF

# Print output raster from array
	RasterDataset.fromArray(array=DASF, grid=GridData, filename=outputName, driver=GTiffDriver())
	RasterDataset.fromArray(array=retrieval_quality, grid=GridData, filename=secondoutputName, driver=GTiffDriver())
	RasterDataset.fromArray(array=CSC, grid=GridData, filename=thirdoutputName, driver=GTiffDriver())