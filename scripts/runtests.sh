#!/bin/bash
QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORM
CI=True
export CI
rm -Rf test-outputs
rm -Rf test-reports
export PYTHONPATH="${PYTHONPATH}"\
":$(pwd)"\
":/usr/share/qgis/python/plugins"\
":$(pwd)/enmapbox/apps"\
":$(pwd)/enmapbox/coreapps"\
":$(pwd)/enmapbox/eo4qapps"

echo $PYTHONPATH
pytest
# python3 scripts/setup_repository.py
