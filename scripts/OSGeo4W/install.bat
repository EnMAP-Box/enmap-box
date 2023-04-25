:: This installs QGIS + required packages using the OSGeo4W installer
echo "Install QGIS"
set PACKAGES=qgis setup python3-scipy python3-scikit-learn python3-pip python3-geopandas python3-matplotlib
set BIN_INSTALLER=C:\Users\geo_beja\Downloads\osgeo4w-setup.exe

:: available download mirrors? see: https://download.osgeo.org/osgeo4w/ssl/mirrors.lst
set MIRROR=https://download.osgeo.org/osgeo4w/v2

set OSGEO4W_ROOT=D:\OSGeo4W_TEST
rmdir /S /Q %OSGEO4W_ROOT%
md %OSGEO4W_ROOT%
start /B /wait %BIN_INSTALLER% ^
   -kq ^
   --advanced ^
   --arch x86_64 ^
   --site %MIRROR% ^
   --only-site ^
   --root %OSGEO4W_ROOT% ^
   --autoaccept ^
   --upgrade-also ^
   --quiet-mode ^
   --packages %PACKAGES%

call %OSGEO4W_ROOT%\OSGeo4W.bat
echo Done
