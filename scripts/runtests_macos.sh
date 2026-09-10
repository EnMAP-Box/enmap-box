#!/bin/bash
QGIS_APP=${QGIS_APP:-/Applications/QGIS-final-4_2_2.app}
export PYTHON_EXECUTABLE=${QGIS_APP}/Contents/MacOS/python
export PYTHONPATH="${PYTHONPATH}"\
":${QGIS_APP}/Contents/Resources/qgis/python"\
":${QGIS_APP}/Contents/Resources/qgis/python/plugins"
$(dirname "$0")/runtests.sh "$@"
