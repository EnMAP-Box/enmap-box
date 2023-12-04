:: This installs QGIS + required packages using the OSGeo4W installer
echo "Install QGIS with EnMAP-Box packages"

set URL_INSTALLER=https://download.osgeo.org/osgeo4w/v2/osgeo4w-setup.exe
set PATH_INSTALLER=%USERPROFILE%\Downloads\osgeo4w-setup.exe
:: available download mirrors? see: https://download.osgeo.org/osgeo4w/ssl/mirrors.lst
set OSGEO4W_MIRROR=https://download.osgeo.org/osgeo4w/v2
set OSGEO4W_ARCH=x86_64
set OSGEO4W_ROOT=F:\OSGEO4W_TEST
set QGIS_RELEASE=qgis

if not exist %PATH_INSTALLER% (
    bitsadmin /transfer "Download osgeo4w-setup.exe" /download /priority normal %URL_INSTALLER% %PATH_INSTALLER%
    echo "Downloaded osgeo4w-setup.exe to %PATH_INSTALLER%"
) else (
    echo 'File exists'
)

:: Packages to install. Available package names see https://download.osgeo.org/osgeo4w/v2/x86_64/setup.ini
set PACKAGES=python3-pip %QGIS_RELEASE% setup python3-scipy python3-scikit-learn python3-pip python3-geopandas python3-matplotlib python3-pyopengl

start /B /wait %PATH_INSTALLER% -kq -P %PACKAGES% --root %OSGEO4W_ROOT% --advanced --arch x86_64 --site %OSGEO4W_MIRROR% --only-site --autoaccept --upgrade-also --quiet-mode
:: start /B /wait %PATH_INSTALLER% -kq -P python3-pip --root %OSGEO4W_ROOT% --advanced --arch x86_64 --site %OSGEO4W_MIRROR% --only-site --autoaccept --upgrade-also --quiet-mode
echo "QGIS installed to %OSGEO4W_ROOT%"
