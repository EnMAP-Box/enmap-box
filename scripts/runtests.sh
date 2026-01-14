#!/bin/bash
export CI=True
export QT_QPA_PLATFORM=offscreen

#Xvfb :99 -screen 0 1920x1080x24 &
#export DISPLAY=:99
#export QT_QPA_PLATFORM=Xvfb
# ":/usr/share/qgis/python/plugins"\

rm -Rf test-outputs
rm -Rf test-reports

export PYTHONPATH="${PYTHONPATH}"\
":$(pwd)"\
":$(pwd)/enmapbox/apps"\
":$(pwd)/enmapbox/coreapps"\
":$(pwd)/enmapbox/eo4qapps"\
":$(pwd)/tests"

echo $PYTHONPATH
qgis --version
python3 scripts/systeminfo.py
pytest "$@"

