@echo off
:: This installs QGIS + required packages using the OSGeo4W installer
echo "Install QGIS with EnMAP-Box packages"

setlocal
:: ---- Configuration -------------------------------------------------
set URL_INSTALLER=https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe
set PATH_INSTALLER=%USERPROFILE%\Downloads\osgeo4w-setup.exe
:: available download mirrors? see: https://download.osgeo.org/osgeo4w/ssl/mirrors.lst

:: Default Settings
set DEFAULT_OSGEO4W_MIRROR=https://download.osgeo.org/osgeo4w/v2
set DEFAULT_OSGEO4W_ARCH=x86_64

if defined OSGEO4W_ROOT (
    set DEFAULT_OSGEO4W_ROOT=%OSGEO4W_ROOT%
) else (
    set DEFAULT_OSGEO4W_ROOT=C:\OSGEO4W
)

:: QGIS release, e.g. qgis, qgis-ltr, qgis-dev
set DEFAULT_QGIS_RELEASE=qgis

if not exist %PATH_INSTALLER% (
    curl -L -o "%PATH_INSTALLER%" "%URL_INSTALLER%"
    echo "Downloaded osgeo4w-setup.exe to %PATH_INSTALLER%"
) else (
    echo 'Installer already exists'
)

:: Ask user for OSGEO4W_ROOT
set /p OSGEO4W_ROOT=Enter the installation directory OSGEO4W_ROOT (default: %DEFAULT_OSGEO4W_ROOT%):
if "%OSGEO4W_ROOT%"=="" set OSGEO4W_ROOT=%DEFAULT_OSGEO4W_ROOT%


:: Ask user for QGIS Release
:cho Choose QGIS release:
echo 1. qgis
echo 2. qgis-ltr
echo 3. qgis-dev
set /p QGIS_RELEASE="Select QGIS release (1-3, default: 1): "
if "%QGIS_RELEASE%"=="1" set QGIS_RELEASE=%DEFAULT_QGIS_RELEASE%
if "%QGIS_RELEASE%"=="2" set QGIS_RELEASE=qgis-ltr
if "%QGIS_RELEASE%"=="3" set QGIS_RELEASE=qgis-dev

:: todo: allow to change ARCH and Mirror
set OSGEO4W_ARCH=%DEFAULT_OSGEO4W_ARCH%
set OSGEO4W_MIRROR=%DEFAULT_OSGEO4W_MIRROR%

:: Packages to install. Available package names see https://download.osgeo.org/osgeo4w/v2/x86_64/setup.ini
set "PACKAGES=%QGIS_RELEASE%,python3-pip,python3-scipy,python3-scikit-learn,python3-geopandas,python3-matplotlib,python3-pyopengl"


echo OSGEO4W_MIRROR=%OSGEO4W_MIRROR%
echo OSGEO4W_ROOT=%OSGEO4W_ROOT%
echo OSGEO4W_ARCH=%OSGEO4W_ARCH%
echo QGIS_RELEASE=%QGIS_RELEASE%
echo PACKAGES=%PACKAGES%

%PATH_INSTALLER% --advanced --arch %OSGEO4W_ARCH% --root %OSGEO4W_ROOT% ^
     --site %OSGEO4W_MIRROR% ^
     --only-site ^
     --autoaccept ^
     --upgrade-also ^
     --quiet-mode ^
     --packages %PACKAGES%

if errorlevel 1 (
     echo ERROR: OSGeo4W installer returned an error & exit /b 1
)
echo Open OSGeo4W shell calling %OSGEO4W_ROOT%\OSGeo4W.bat...
call %OSGEO4W_ROOT%\OSGeo4W.bat
