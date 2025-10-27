
set SUBMODULE=enmapbox/qgispluginsupport
echo "Update %SUBMODULE%"
cd %SUBMODULE%
git checkout enmapbox_3.17
git fetch
git pull
cd ../..
git add %SUBMODULE%
echo 'Submodule status:'
git submodule status %SUBMODULE%
