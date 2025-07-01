:: This installs QGIS + required packages using the OSGeo4W installer
echo "Install QGIS with EnMAP-Box packages"

@echo off
rem -------------------------------------------------------------------
rem  Install QGIS + Python packages with the OSGeo4W v2 network installer
rem -------------------------------------------------------------------

rem ---- Configuration -------------------------------------------------
set URL_INSTALLER=https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe
set PATH_INSTALLER=%USERPROFILE%\Downloads\osgeo4w-setup.exe
:: available download mirrors? see: https://download.osgeo.org/osgeo4w/ssl/mirrors.lst
set OSGEO4W_MIRROR=https://download.osgeo.org/osgeo4w/v2
set OSGEO4W_ARCH=x86_64
set OSGEO4W_ROOT=F:\OSGEO4W_TEST

:: QGIS package, e.g. qgis, qgis-ltr, qgis-dev
set QGIS_RELEASE=qgis

if not exist %PATH_INSTALLER% (
    curl -L -o "%PATH_INSTALLER%" "%URL_INSTALLER%"
    echo "Downloaded osgeo4w-setup.exe to %PATH_INSTALLER%"
) else (
    echo 'Installer already exists'
)

:: Packages to install. Available package names see https://download.osgeo.org/osgeo4w/v2/x86_64/setup.ini
set "PACKAGES=%QGIS_RELEASE%,python3-pip,python3-scipy,python3-scikit-learn,python3-geopandas,python3-matplotlib,python3-pyopengl"

"%PATH_INSTALLER%" ^
    --advanced ^
    --arch %OSGEO4W_ARCH% ^
    --root "%OSGEO4W_ROOT%" ^
    --site "%OSGEO4W_MIRROR%" ^
    --only-site ^
    --autoaccept ^
    --upgrade-also ^
    --quiet-mode ^
    --packages %PACKAGES%

if errorlevel 1 (
    echo ERROR: OSGeo4W installer returned an error & exit /b 1
)

::start /B /wait %PATH_INSTALLER% -kq -P setup python3-pip --root %OSGEO4W_ROOT% --advanced --arch x86_64 --site %OSGEO4W_MIRROR% --only-site --autoaccept --upgrade-also --quiet-mode

::call %OSGEO4W_ROOT%\OSGeo4W.bat
::call setup -kq -P -P %PACKAGES% --root %OSGEO4W_ROOT% --advanced --arch x86_64 --site %OSGEO4W_MIRROR% --only-site --autoaccept --upgrade-also --quiet-mode
::echo "QGIS installed to %OSGEO4W_ROOT%"


