# -*- coding: utf-8 -*-

from lmuvegetationapps.Processor.Processor_Inversion_core import ProcessorMainFunction

m = ProcessorMainFunction()
paras = ['LAI', 'LIDF', 'cm', 'cab']  # Predict

# Test setting
model_dir = r"E:\LUTs\MNI_LUT_D_5k.meta"  # Path to model directory (either for training models or to predict from existing models)
algorithm = 'al_gpr'  # 'ann', 'gpr', 'svr', 'rforest'
#ImgIn = r"U:\EnVAL\Campaigns\Tetris_Spectra\MNI_BA_2021_full.bsq"  # Input Image für die Predictions
ImgIn = r"U:\EnVAL\Campaigns\Tetris_Spectra\MNI_MA_2017_2018_2020_2021_full.bsq"  # Input Image für die Predictions
#ImgIn = r"U:\EnVAL\Campaigns\Tetris_Spectra\MNI_WW_2017_2018_2020_2021_2022_full.bsq"  # Input Image für die Predictions
int_boost_geo = 100  # Geometrien von 0 bis 9000 erhalten boost_geo = 100 -> 0° - 90°
ResOut = r"E:\Testdaten\EnMAP_MNI\gpr_test_ma.bsq"  # Output of the predicted variables
out_mode = 'single'  # single: all in one file, individual: all in individual files
mask_image = None

mask_ndvi = False  # Mask values with NDVI > x? Switch True/False
ndvi_thr = 0.37
ndvi_bands = [47, 68]

# GeoIn = r"F:\Flugdaten2\Cali/Test_Snippet/BA_mosaic_su_cut_geo_test.bsq"
GeoIn = None
fixed_geos = [40, 0, 0]  # tts, tto, psi -> fixed values
# fixed_geos = None
spatial_geo = False  # True: use geo per pixel; False: Use mean values of image

m.predict_main.prediction_setup(model_meta=model_dir, algorithm=algorithm, img_in=ImgIn, res_out=ResOut,
                                out_mode=out_mode, mask_ndvi=mask_ndvi, ndvi_thr=ndvi_thr, ndvi_bands=ndvi_bands,
                                mask_image=mask_image, geo_in=GeoIn, fixed_geos=fixed_geos, spatial_geo=spatial_geo,
                                paras=paras, nodat=-999)

m.predict_main.predict_from_dump()
m.predict_main.write_prediction()
