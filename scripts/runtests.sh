#!/bin/bash
export QT_QPA_PLATFORM=offscreen
export CI=True

rm -Rf test-outputs
rm -Rf test-reports

export PYTHONPATH="${PYTHONPATH}"\
":$(pwd)"\
":/usr/share/qgis/python/plugins"\
":$(pwd)/enmapbox/apps"\
":$(pwd)/enmapbox/coreapps"\
":$(pwd)/enmapbox/eo4qapps"\
":$(pwd)/tests"

echo $PYTHONPATH
pytest --no-cov-on-fail "$@"

