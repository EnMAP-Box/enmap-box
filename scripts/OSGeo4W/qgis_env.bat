@echo off

:: ### CONFIG SECTION ###
:: root of local OSGEO4W installation
set OSGEO4W_ROOT=F:\OSGeo4W
:: PyCharm executable, adjust for version updates
set PYCHARM_EXE="C:\Program Files (x86)\JetBrains\PyCharm 2022.2.4\bin\pycharm64.exe"

:: locations to be added to PATH, e.g. to find git.exe
set _PATH=^
C:\Program Files\Git\bin;^
C:\Program Files\Git LFS;

:: #### CONFIG SECTION END ###

:: start with clean python path
set PYTHONPATH=

:: switch for qgis environment: qgis, qgis-dev, qgis-ltr
IF "%~1"=="" (
  set QGIS_ENV=qgis
) else (
  set QGIS_ENV=%~1
)

:: cleanup required variables
set tmp=%OSGEO4W_ROOT%\bin\%QGIS_ENV%-bin
for /f %%l in (%tmp%.vars) do (
	set %%l=

)

:: set required variables
for /f %%l in (%tmp%.env) do (
	set %%l
)

:: append python path with QGIS plugin directories
set PYTHONPATH=%PYTHONPATH%;^
%OSGEO4W_ROOT%\apps\%QGIS_ENV%\python;^
%OSGEO4W_ROOT%\apps\%QGIS_ENV%\python\plugins

:: append to PATH
set PATH=%PATH%;%_PATH%