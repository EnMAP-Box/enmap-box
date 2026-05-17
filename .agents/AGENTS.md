# EnMAP-Box Developer Guide for AI Agents

This document provides project-specific information for developers and AI agents working on the EnMAP-Box project.

### 1. Build and Configuration Instructions

The EnMAP-Box is a QGIS plugin that can also run as a standalone Python application.

* **Environment Setup**: Use `mamba` or `conda` to create an environment with QGIS and required dependencies.
  ```bash
  mamba env create -f .env/conda/enmapbox_full_latest.yml
  ```
* **Repository Initialization**: After cloning, initialize submodules and compile resource files:
  ```bash
  git submodule update --init --recursive
  python scripts/setup_repository.py
  ```
  The `setup_repository.py` script is crucial as it compiles resources and downloads necessary test data.
* **Running the Application**:
  ```bash
  python enmapbox
  ```

### 2. Testing Information

#### Running Tests

Tests are executed using `pytest` via a wrapper script that sets up the necessary environment (offscreen rendering,
PYTHONPATH):

* **Linux/macOS**: `./scripts/runtests.sh`
* **Windows**: `scripts\runtests.bat`

To run a specific test file or method:

```bash
./scripts/runtests.sh tests/enmap-box/enmapbox/gui/test_mapcanvas.py
```

#### Adding New Tests

New tests should inherit from `enmapbox.testing.EnMAPBoxTestCase`. Use `start_app()` to initialize the QGIS environment.

Example of a simple test:

```python
import unittest
from enmapbox.testing import start_app, EnMAPBoxTestCase

# Ensure the QGIS application is started for testing
start_app()

class MyFeatureTest(EnMAPBoxTestCase):
    def test_feature_logic(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
```

### 3. Additional Development Information

* **Code Style**: The project follows PEP8. `flake8` is used for linting with the `flake8-qgis` plugin.
    * Run linting: `flake8`
* **Git Submodules**: This project heavily relies on git submodules located in `enmapbox/qgispluginsupport`,
  `enmapbox/apps`, etc. Always ensure submodules are up to date.
* **QGIS Dependency**: Most of the core logic depends on the PyQGIS API. Ensure QGIS is correctly installed and
  accessible in your Python environment.
* **Resource Files**: UI files (`.ui`) and resource files (`.qrc`) are used. Changes to `.qrc` files require re-running
  `scripts/setup_repository.py`.
