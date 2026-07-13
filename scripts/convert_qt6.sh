#!/usr/bin/env bash
# script to call the
# https://github.com/qgis/pyqgis4-checker

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker run --rm --pull always \
  --user $(id -u):$(id -g) \
  --workdir /workspace/ \
  -v "$REPO_ROOT:/workspace/" \
  ghcr.io/qgis/pyqgis4-checker:main-ubuntu \
  pyqt5_to_pyqt6.py --logfile /workspace/pyqt6_checker.log "$@"