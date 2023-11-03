# EnMAP-Box 3

![Logo](enmapbox/gui/ui/icons/enmapbox.svg)

The EnMAP-Box is free and open source [QGIS Plugin ](https://www.qgis.org) to visualize and process remote sensing raster data. 
It is particularly developed to handle imaging spectroscopy data, as from the upcoming EnMAP sensor.

![Screenshot](screenshot.png)

# Highlights

* an easy-to-use graphical user interface for the visualization of vector and raster data sources in parallel and in spatially linked maps.

* collection and visualisation of spectral profiles spectral libraries. Spectral profiles can come from different sources, 
  e.g. raster images, field spectrometer or table-sheets.

* enhances the QGIS Processing Framework with many algorithms commonly used in
  remote sensing and imaging spectroscopy, e.g. support vector machines or random forest based raster classification, 
  regression, cluster approaches from the [scikit-learn](https://scikit-learn.org/stable/index.html) library.

* applications specific to imaging spectroscopy and the EnMAP program, e.g. a simulation of spectral profiles (IIVM), 
  atmospheric correction of EnMAP data, mapping of geological classes from EnMAP data and more...


Documentation: http://enmap-box.readthedocs.io

Git Repository: https://github.com/EnMAP-Box/enmap-box

About EnMAP: https://www.enmap.org/

# Run the EnMAP-Box

The EnMAP-Box is a QGIS Plugin that can be installed from the QGIS Plugin Manager.

However, the following steps show you how to run the EnMAP-Box from python without starting the QGIS Desktop application.

## 1. Install QGIS

### conda / mamba (all OS)

1. Install conda / mamba (preferred), as described [here](https://mamba.readthedocs.io/en/latest/mamba-installation.html#mamba-install)  

2. Install one of the QGIS + EnMAP-Box environments listed in https://github.com/EnMAP-Box/enmap-box/tree/main/.conda
   
   `latest` = the most-recent QGIS version available in the [conda-forge](https://conda-forge.org/) channel.
   
   `light` = basic QGIS installation only. No additional packages. In this environment the EnMAP-Box provides basic 
         visualization features only.
   
   `full` = QGIS + all other python requirements that allow to run all EnMAP-Box features

   Examples:
   ````bash
   mamba env create -f https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/conda/enmapbox_full_latest.yml
   mamba env create -f https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/conda/enmapbox_full_3.28.yml
   mamba env create -f https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/conda/enmapbox_light_latest.yml
   mamba env create -f https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/conda/enmapbox_light_3.28.yml
   ````
   
   The environment name corresponds to the `*.yml` basename. You can change it with  `-n`, e.g. `-n myenvironmennane`.


* You can update an existing environment with `mamba update`, e.g:
   
   ````bash
   mamba env update --prune -f https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.conda/enmapbox_full_3.28.yml
   ````
   * `-n myenvironmentname` allows to overwrite environments with names different to that specified in the `*.yml` file.
   * `--prune` causes conda to remove any dependencies that are no longer required from the environment.

### Windows / Linux / MacOS

 Either use mamba (see above), or follow the OS-specific instructions here: https://qgis.org/en/site/forusers/download.html

## 2. Test the QGIS environment

You need to be able to run the following commands from your shell:
1. Git (to check out the EnMAP-Box repository)
    
    ````shell
    $git --version
    ````
   
   Test if git can connect to the remote EnMAP-Box repository:
   
   * ssh (recommended): `git ls-remote git@github.com:EnMAP-Box/enmap-box.git`
   * https: `git ls-remote https://github.com/EnMAP-Box/enmap-box.git`
  

2. [QGIS](https://qgis.org), [Qt Designer](https://doc.qt.io/qt-6/qtdesigner-manual.html) (to design GUIs) and the [Qt Assistant](https://doc.qt.io/qt-6/assistant-details.html) (superfast browsing of Qt / QGIS API documents)
    
    ````bash
    $qgis --version
    $designer
    $assistant
    ````
3. Check if all environmental variables are set correctly. Start Python and try to use the QGIS API: 

    ````bash
    $python
    Python 3.9.18 | packaged by conda-forge | (main, Aug 30 2023, 03:40:31) [MSC v.1929 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    ````
    Print the QGIS version   
    ````shell
    >>> from qgis.core import Qgis
    >>> print(Qgis.version())
    3.28.10-Firenze
    ````

    Import the QGIS Processing Framework    

    ````
    >>> import processing
    Application path not initialized
    ````
   (Don't worry about the *Application path not initialized* message)


If one of these tests fail, check the values for the follwing variables in your local environment:

* `PATH` - needs to include the directories with your git and qgis executable 

* `PYTHONPATH` - needs to include the QGIS python code directories, including the QGIS-internal plugin folder:
  `PYTHONPATH=F:\mamba_envs\enmapbox_light_longterm\Library\python\plugins;F:\mamba_envs\enmapbox_light_longterm\Library\python;`

* `QT_PLUGN_PATH` - the Qt plugin directory, e.g.:

  ``QT_PLUGIN_PATH=F:\mamba_envs\enmapbox_light_longterm\Library\qtplugins;F:\mamba_envs\enmapbox_light_longterm\Library\plugins;``


## 3. Clone this repository

Use the following commands to clone the EnMAP-Box and update its submodules:

### TLDR:

Open a shell (e.g. OSGeo4W or mamba, see above) that allows to run git and python with PyQGIS, then run:


````bash
# Clone the repository using ssh 
# See https://docs.github.com/en/authentication/connecting-to-github-with-ssh for details on SSH
git clone --recurse-submodules git@github.com:EnMAP-Box/enmap-box.git

# alternatively (but not recommended) you can use https as well:
# git clone --recurse-submodules https://github.com/EnMAP-Box/enmap-box.git

cd enmap-box
git config --local include.path ../.gitconfig

# compile the EnMAP-Box resource files and download QGIS resource files to display icons  
python scripts/setup_repository.py

# start the EnMAP-Box
python enmapbox

# if you have writing access to a submodule, set the remote-URL accordingly, e.g.
cd enmapbox/qgispluginsupport
git git remote set-url origin git@github.com:EnMAP-Box/qgispluginsupport.git
````

 

### Detailed description

In the following we refer to the EnMAP-Box repository ``https://github.com/EnMAP-Box/enmap-box.git``
Replace it with your own EnMAP-Box fork from which you can create pull requests.

1. Ensure that your environment has git available and starts QGIS by calling `qgis` 
   (see[1.](#1-install-qgis) and [2.](#2-test-the-qgis-environment)).
   You copy a bootstrap script like [.env/OSGeo4W/qgis_env.bat](.env/osgeo4w/qgis_env.bat) (windows) or
   [scripts/qgis_env.sh](scripts/qgis_env.sh) (linux) and adjust to your local settings for.

2. Clone the EnMAP-Box repository.
   
    ````bash
    git clone git@github.com:EnMAP-Box/enmap-box.git
    ````
    
   You might also use the url `https://github.com/EnMAP-Box/enmap-box.git` instead. 
   However, ssh access is preferred.

4. Initialize submodules and pull their code, which is hosted in different repositories
    ````bash
    cd enmapbox
    git submodule update --init --remote --recursive
    ````

5. Once initialized, you can update submodules at any later point by:
    ````bash
    git submodule update --remote
    ````

    Of course cloning and submodule updating can be done in one step:
    ````bash
    
    git clone --recurse-submodules git@github.com:EnMAP-Box/enmap-box.git
    ````
    
    At any later point, you can pull in submodule updates by
    ````bash
    git submodule update --remote
    ````
    
    Doing so automatically when pulling the EnMAP-Box project can be enabled by:
    ````bash
    git config --set submodule.recurse true
    ````
    
    This setting (and maybe more in future) is already defined in the `.gitconfig`. 
You can enable it for your local repository by:
    
    ````bash
    git config --local include.path ../.gitconfig
    ````
    
    Submodules use https addresses to pull and push updates (`url` and `pushurl` in [.gitmodules](.gitmodules)), e.g.
`https://bitbucket.org/ecstagriculture/enmap-box-lmu-vegetation-apps.git`.
To enable ssh authentication you can replace them with SSH uris as followed:

    ```bash
    cd enmapbox/apps/lmuapps
    # check existing url
    git remote -v
    # change remote urls
    git remote set-url origin git@bitbucket.org:ecstagriculture/enmap-box-lmu-vegetation-apps.git
    # check changed url
    git remote -v
    ```
    
    

6. you can push changes upstream by:
    
    ````bash
    cd <submodule>
    git add .
    git commit -m "my changes"
    git push origin HEAD:master
    ````
   
    
    
    Finally, announce changes in a submodule to the EnMAP-Box (super) project by:
    ````bash
    cd <EnMAP-Box root>
    git add <submodule path>
    git commit -m "added submodule updates"
    git push
    ````
6. Ensure that PyQGIS is [available to your python enviroment](https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/intro.html#running-custom-applications).
   (This means you can start a python shell and `import qgis`)
   
7. Compile resource files and download the test data. 
    ````bash
    python scripts/setup_repository.py
    ````
   
8. Now you can start the EnMAP-Box from shell by:
    ````bash
    python enmapbox
    ````

## 3. Setup your IDE, e.g. PyCharm

tbd.

## How to contribute

Our online documentation at [http://enmap-box.readthedocs.io](http://enmap-box.readthedocs.io/en/latest/general/contribute.html) describes how you can support the development of the EnMAP-Box.

Please keep the code in a good shape. 

You might use flake8 to check if the EnMAP-Box code applies to the rules defined in 
``.flake8``:

````bash
flake8 
````

To check staged files only, run:
````bash
flake8 $(git status -s | grep -E '\.py$' | cut -c 4-)
````

# Testing

Run `scripts/runtests.sh` (Linux/macOS) or `scripts\runtests.bat` (Win) 
to start the tests defined in `/tests/`.



# License

The EnMAP-Box is released under the GNU Public License (GPL) Version 3 or above. A copy of this licence can be found in 
the LICENSE.txt file that is part of the EnMAP-Box plugin folder and the EnMAP-Box repository, and also at
<http://www.gnu.org/licenses/>

Developing the EnMAP-Box under this license means that you can (if you want to) inspect and modify the source code and guarantees that you 
will always have access to an EnMAP-Box software that is free of cost and can be freely
modified.

# Support
You can get support in the following ways:

 -  Read the EnMAP-Box documentation [http://enmap-box.readthedocs.io](http://enmap-box.readthedocs.io)

 -  Open an issue with your question, bug report, feature request or other enhancement https://github.com/EnMAP-Box/enmap-box/issues/new
 
 -  Write us an email: [enmapbox@enmap.org](mailto:enmapbox@enmap.org)



