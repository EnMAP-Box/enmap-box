@echo off

:: ### CONFIG SECTION ###
:: root of local OSGEO4W installation
set OSGEO4W_ROOT=D:\OSGeo4W
:: PyCharm executable, adjust for version updates
set PYCHARM_EXE="C:\Program Files (x86)\JetBrains\PyCharm 2022.1.2\bin\pycharm64.exe"

:: git binaries and git lfs binaries
set BIN_GIT=C:\Program Files\Git\bin
set BIN_LFS=C:\Program Files\Git LFS
:: #### CONFIG SECTION END ###

:: start with clean python path
set PYTHONPATH=

:: switch for qgis environment: qgis, qgis-dev, qgis-ltr
IF "%~1"=="" (
  :: use qgis by default
  set QGIS_ENV=qgis
) else (
  ::
  set QGIS_ENV=%~1
)
echo QGIS_ENV=%QGIS_ENV%

IF "%QGIS_ENV%" == "qgis" goto std_setup
IF "%QGIS_ENV%" == "qgis-dev" goto dev_setup
IF "%QGIS_ENV%" == "qgis-ltr" goto std_setup

:unknown
echo unknown environment: %QGIS_ENV%
exit /b -1

:std_setup
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
goto common

:dev_setup
call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\gdal-dev-py-env.bat"
goto common

:common
path %OSGEO4W_ROOT%\apps\%QGIS_ENV%\bin;%PATH%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT:\=/%/apps/%QGIS_ENV%
set GDAL_FILENAME_IS_UTF8=YES
rem Set VSI cache to be used as buffer, see #6448
set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=^
%OSGEO4W_ROOT%\apps\%QGIS_ENV%\qtplugins;^
%OSGEO4W_ROOT%\apps\qt5\plugins

set PYTHONPATH=%PYTHONPATH%;^
%OSGEO4W_ROOT%\apps\%QGIS_ENV%\python;^
%OSGEO4W_ROOT%\apps\%QGIS_ENV%\python\plugins

goto EOF

:EOF
echo QGIS_PREFIX_PATH=%QGIS_PREFIX_PATH%
echo PYTHONPATH=%PYTHONPATH%
echo PATH=%PATH%
echo QT_PLUGIN_PATH=%QT_PLUGIN_PATH%