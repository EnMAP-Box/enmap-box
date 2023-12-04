:: This installs QGIS + required packages using the OSGeo4W installer
echo "Install QGIS"

:: Packages to install. Available package names see https://download.osgeo.org/osgeo4w/v2/x86_64/setup.ini
set PACKAGES=qgis setup python3-scipy python3-scikit-learn python3-pip python3-geopandas python3-matplotlib python3-pyopengl

:: The downloaded OSGeo4W installer exe
set BIN_INSTALLER=C:\Users\geo_beja\Downloads\osgeo4w-setup.exe
set BIN_INSTALLER=setup.bat
:: available download mirrors? see: https://download.osgeo.org/osgeo4w/ssl/mirrors.lst
set MIRROR=https://download.osgeo.org/osgeo4w/v2

set OSGEO4W_ROOT=D:\OSGeo4W_TEST
rmdir /S /Q %OSGEO4W_ROOT%
md %OSGEO4W_ROOT%
start /B /wait %BIN_INSTALLER% ^
   -kq ^
   -P %PACKAGES% ^
   --advanced ^
   --arch x86_64 ^
   --site %MIRROR% ^
   --only-site ^
   --root %OSGEO4W_ROOT% ^
   --autoaccept ^
   --upgrade-also ^
   --quiet-mode ^

start /B /wait %BIN_INSTALLER% -kq -P %PACKAGES% --advanced --arch x86_64 --site %MIRROR% --only-site --autoaccept --upgrade-also --quiet-mode

echo "Installation finished"
