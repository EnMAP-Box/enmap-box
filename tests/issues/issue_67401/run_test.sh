#!/bin/bash
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

docker run --rm \
  --network host \
  --user "$(id -u):$(id -g)" \
  --workdir /workspace \
  -e "PYTHONPATH=/usr/share/qgis/python:/usr/share/qgis/python/plugins" \
  -e QT_QPA_PLATFORM=offscreen \
  -v "${SCRIPT_DIR}:/workspace" \
  -v "${HOME}:${HOME}" \
  -v /tmp:/tmp \
  qgis/qgis:stable \
  python3 test_qgsparameterwidgetwrapper.py
