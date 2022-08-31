
:: use this script to run unit tests locally
::
@echo off
set CI=True
set PYTHONPATH=%~dp0/..;%PYTHONPATH%
set PYTHONPATH
set PYTHON=python
::WHERE python3 >nul 2>&1 && (
::    echo Found "python3" command
::    set PYTHON=python3
::) || (
::    echo Did not found "python3" command. use "python" instead
::    set PYTHON=python
::)

::start %PYTHON% scripts/setup_repository.py

%PYTHON% -m coverage run --rcfile=.coveragec   tests/src/coreapps/test_enmapboxapplications.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/coreapps/test_imagecube.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/coreapps/test_metadataeditorapp.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/coreapps/test_reclassifyapp.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/coreapps/test_vrtbuilderapp.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/issues/test_issue_478.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/issues/test_issue_711.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/issues/test_issue_724.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/issues/test_issue_747.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/otherapps/test_enpt_enmapboxapp.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/otherapps/test_ensomap.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/otherapps/test_lmuvegetationapps.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_applications.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_crosshair.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_cursorlocationsvalues.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_datasources.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_datasourcesV2.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_dependencycheck.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_docksanddatasources.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_enmapbox.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_enmapboxplugin.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_enmapboxprocessingprovider.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_hiddenqgislayers.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_mapcanvas.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_mimedata.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_options.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_repo.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_settings.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_speclibs.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_splashscreen.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_template.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_testdata_dependency.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_testing.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_utils.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  tests/src/test_vectorlayertools.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_AppendEnviHeaderToGTiffRasterAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ApplyMaskAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ClassificationPerformanceSimpleAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ClassificationPerformanceStratifiedAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ClassificationToFractionAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ClassifierPerformanceAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ClassifierPermutationFeatureImportanceAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ConvolutionFilterAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_CreateDefaultPalettedRasterRendererAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_CreateGridAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_CreateMaskAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_CreateRgbImageFromClassProbabilityAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_FeatureClusteringHierarchicalAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_FitClassifierAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_GeolocateRasterAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportDesisL1BAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportDesisL1CAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportDesisL2AAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportEnmapL1BAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportEnmapL1CAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportEnmapL2AAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportLandsatL2Algorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportPrismaL1Algorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportPrismaL2DAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_ImportSentinel2L2AAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_LayerToMaskAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PredictClassificationAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PredictClassProbabilityAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromCategorizedLibraryAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromCategorizedRasterAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromCategorizedVectorAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromCategorizedVectorAndFieldsAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromCodeAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromFilesAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareClassificationDatasetFromTableAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_PrepareRegressionSampleFromCsvAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_RandomPointsInMaskAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_RandomPointsInStratificationAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_RasterizeCategorizedVectorAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_RasterizeVectorAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_RasterMathAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SampleRasterValuesAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SaveRasterAsAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SelectFeaturesFromDatasetAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SpatialFilterFunctionAlgorithmBase.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SpectralResamplingByResponseFunctionConvolutionAlgorithmBase.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SpectralResamplingByResponseFunctionLibraryAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SpectralResamplingBySpectralRasterWavelengthAndFwhmAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SubsampleClassificationSampleAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_SynthMixAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_TranslateClassificationAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/algorithm/test_TranslateRasterAlgorithm.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_extentwalker.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_glossary.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_gridwalker.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_rasterdriver.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_rastermetadataeditor.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_rasterprocessing.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_rasterreader.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_reportwriter.py
%PYTHON% -m coverage run --rcfile=.coveragec --append  enmapboxprocessing/test/test_utils.py
%PYTHON% -m coverage report