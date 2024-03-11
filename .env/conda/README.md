# EnMAP-Box in conda environments (Linux, Windows, macOS, ...)

1. Install conda-forge on your operating system

2. Create a new environment that contains QGIS and all package dependencies that are required to run the EnMAP-Box.

   ````bash
      conda env create -f https://raw.githubusercontent.com/EnMAP-Box/enmap-box/main/.env/conda/enmapbox_full_latest.yml
   ````

The .env/conda folder contains different environment files that differ in QGIS version and 
the number of packages:

   `latest` = the most-recent QGIS version available in the [conda-forge](https://conda-forge.org/) channel.
   
   `light` = basic QGIS installation only. No additional packages. In this environment the EnMAP-Box provides basic 
         visualization features only.
   
   `full` = QGIS + all other python requirements that allow to run all EnMAP-Box features


