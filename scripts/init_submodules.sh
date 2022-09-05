#!/bin/sh

git submodule add https://github.com/EnMAP-Box/qgispluginsupport.git  enmapbox/qgispluginsupport
cd enmapbox/qgispluginsupport
git config remote.origin.pushurl git@github.com:EnMAP-Box/qgispluginsupport.git

cd ../..

git submodule add https://bitbucket.org/ecstagriculture/enmap-box-lmu-vegetation-apps.git enmapbox/apps/lmuapps
cd enmapbox/apps/lmuapps
git config remote.origin.pushurl git@bitbucket.org:ecstagriculture/enmap-box-lmu-vegetation-apps.git
