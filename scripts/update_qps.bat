
set SUBMODULE=enmapbox/qgispluginsupport
echo "Update %SUBMODULE%"
cd %SUBMODULE%
git checkout master
git fetch
git pull --recurse-submodules
git submodule update --init --recursive
cd ../..
git add %SUBMODULE%
echo 'Submodule status:'
git submodule status %SUBMODULE%
