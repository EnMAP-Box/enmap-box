# Install EnMAP-Box on Linux

## Ubuntu / Mint

1. Install QGIS as described in [qgis.org](https://www.qgis.org/en/site/forusers/alldownloads.html#debian-ubuntu)

2. Install additional packages that are available by the linux package manager

   ``sudo apt install python3-pip python3-venv pyqt5-dev-tools python3-matplotlib python3-h5py python3-pyqt5.qtopengl python3-netcdf4``

3. There may be many python installations on your system. Ensure that you use the QGIS python in the following steps:
   
   * Open QGIS and the QGIS Python Console (Ctrl+Alt+P)
   * Run ``import sys; sys.executable`` to get the path of the used python executable. It should be the same path 
     as the command ``which python3`` executed in the Terminal returns! 
   * Close QGIS.

4. Create a [virtual python environment](https://docs.python.org/3/library/venv.html) in a directory of choice, e.g.
   ``~/.virtualenvs/enmapbox``
   
   ``python3 -m venv --upgrade-deps --system-site-packages ~/.virtualenvs/enmapbox``

5. Activate the environment and install missing python dependencies.

   ````
   source ~/.virtualenvs/enmapbox/bin/activate
   python3 -m pip install -r https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/linux/requirements_ubuntu.txt
   ````

4. Start QGIS.

   ````
   source ~/.virtualenvs/enmapbox/bin/activate
   qgis
   ````
## Fedora

tbd.

python3 -m venv --upgrade-deps --system-site-packages ~/.virtualenvs/enmapbox
python3 -m pip install -r https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/linux/requirements_ubuntu.txt
## Flatpack

