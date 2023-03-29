#!/bin/bash
QT_QPA_PLATFORM=offscreen
export QT_QPA_PLATFORM
CI=True
export CI

export PYTHONPATH="${PYTHONPATH}:$(pwd):/usr/share/qgis/python/plugins"
export PYTHONPATH="${PYTHONPATH}:$(pwd):enmapbox/apps"
export PYTHONPATH="${PYTHONPATH}:$(pwd):enmapbox/coreapps"
export PYTHONPATH="${PYTHONPATH}:$(pwd):enmapbox/eo4qapps"
echo $PYTHONPATH
pytest
# python3 scripts/setup_repository.py
