#!/bin/sh

git submodule add https://github.com/EnMAP-Box/qgispluginsupport.git  enmapbox/qgispluginsupport
cd enmapbox/qgispluginsupport
git config remote.origin.pushurl git@github.com:EnMAP-Box/qgispluginsupport.git
