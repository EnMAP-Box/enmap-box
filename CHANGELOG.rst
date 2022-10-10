CHANGELOG
=========

Version 3.11
------------
*This release was tested under QGIS 3.26.2*

*Important Notice: the EnMAP-Box repository moved to https://github.com/EnMAP-Box/enmap-box*

**Applications**

* added *Profile Analytics* app: (`#81: <https://github.com/EnMAP-Box/enmap-box/issues/81>`_)

  * allows various profile plot types like spectral profiles, temporal profiles, spatial profiles.
  * profile data can by analysed by user-defined function; the user-function has access to the plot widget and can draw additional plot items

* improved *Scatter Plot* app:

  * added support for vector data (`#1393: <https://bitbucket.org/hu-geomatics/enmap-box/issues/1393/scatter-plot-app-allow-vector-sources-as>`_)
  * added support for simple scatter plots with symbols plotted, instead count density (`#1410: <https://bitbucket.org/hu-geomatics/enmap-box/issues/1410/scatter-plot-app-allow-to-plot-scatter>`_)
  * added support for showing 1:1 line (`#1394: <https://bitbucket.org/hu-geomatics/enmap-box/issues/1394/scatter-plot-app-add-performance-measures>`_)
  * added support for fitting a line to the data and report goodness of fit measures (`#1394: <https://bitbucket.org/hu-geomatics/enmap-box/issues/1394/scatter-plot-app-add-performance-measures>`_)

**Renderer**

* added custom *Bivariate Color Raster Renderer*: allows to visualize two bands using a 2d color ramp. Find a mapping example here: https://www.joshuastevens.net/cartography/make-a-bivariate-choropleth-map/ (`#70: <https://github.com/EnMAP-Box/enmap-box/issues/70>`_)
* added custom *CMYK Color Raster Renderer*: allows to visualize four bands using the CMYK (Cyan, Magenta, Yellow, and Key (black)) color model. Find a mapping example here: https://adventuresinmapping.com/2018/10/31/cmyk-vice/ (`#74: <https://github.com/EnMAP-Box/enmap-box/issues/74>`_)
* added custom *HSV Color Raster Renderer*: allows to visualize three bands using the HSV (Hue, Saturation, Value (black)) color model. Find a mapping example here: https://landmonitoring.earth/portal/ ; select Maps > Global Landcover Dynamics 2016-2020 (`#73: <https://github.com/EnMAP-Box/enmap-box/issues/73>`_)
* added custom *Multisource Multiband Color Raster Renderer*: same functionality as the default QGIS Multiband Color Raster Renderer, but the Red, Green and Blue bands can come from different raster sources (`#112: <https://github.com/EnMAP-Box/enmap-box/issues/112>`_)

**Data Formats / Metadata Handling**

* GDAL metadata like band names can be edited in layer properties (support for ENVI images available with `GDAL 3.6+ <https://github.com/OSGeo/gdal/issues/6444>`_)
* added support for JSON files for storing classification/regression datasets used in ML algorithms (`#21: <https://github.com/EnMAP-Box/enmap-box/issues/21>`_)
* added support for marking a raster bands as bad inside the *Raster Layer Styling* panel (`#31: <https://github.com/EnMAP-Box/enmap-box/issues/31>`_)
* added support for FORCE v1.2 TSI format (`#111: <https://github.com/EnMAP-Box/enmap-box/issues/111>`_)

**Bugfixes**

* `v3.11.0 <https://github.com/EnMAP-Box/enmap-box/milestone/2?closed=1>`_

Version 3.10
------------
*This release was tested under QGIS 3.24.1*

**GUI**

* *Project -> Create Data Source* to create new shapefiles, Geopackages or in-memory vector layers
* refactored layer handling and added layer groups (#649)
* connected attribute table context menu 'Zoom/Pan to/Flash Feature' with EnMAP-Box maps (#1250, #1260)

Data Sources

* added 16 predefined RGB band combinations in the raster source context menu (thanks to the *GEE Data Catalog* plugin)
* added *Create/update ENVI header* option in raster source context menu: allows to quickly create an ENVI header with proper metadata required for ENVI Software; works for ENVI and GeoTiff raster
* added option for opening a band in an existing map view
* added *Save as* option in the layer source context menu
* shows in-memory vector layers
* shows sub-dataset names (#1145)
* source properties are updated in regular intervals (#1230)

Data Views

* added *Add Group* to create layer groups
* added *Copy layer to QGIS* option in layer context menu
* added *Apply model* option in raster layer context menu: allows to quickly apply a machine learner to predict a map using the raster
* fixed drag & drop (#1143)
* fixed floating & unfloating issues (#1231)

**Spectral Libraries**

* spectral profiles can be stored in text and JSON fields
* added functions to access and modify spectral profiles within field calculator expressions, e.g.
  *encodeProfile(field, encoding)* to convert a profile into its binary or JSON string representation
* added first aggregation functions: maxProfile, meanProfile, medianProfile, minProfile (#1130)
* added Spectral Processing allows to create and modify spectral profiles using raster processing algorithms / models
* revised import and export of spectral profiles from/to other formats (e.g. #1249, #1274)
* new editor to modify single spectral profiles
* reads profiles from Spectral Evolution .sed files (reference, target, reflectance)

**Spectral Profile plot**

* moved plot settings like background and crosshair color from context menu to the visualization settings tree view
* color and line style of temporary profiles can be defined in spectral profile source panel
* fixed smaller plot update issues and optimized profile plot speed
* allows to show/hide bad band values
* allows to show renderer band positions (RGB / single band)
* allows to show/hide current/temporary profiles

**Applications**

* Metadata Viewer revised (#1185, #1329), added more band-specific settings

* included the *GEE Timeseries Explorer* plugin into the EnMAP-Box

  * (slightly) new name *GEE Time Series Explorer* app
  * can be used inside EnMAP-Box GUI and stand-alone QGIS GUI
  * overhauled the GUI

    * highlighted the most important satellite archive collections like Landsat, MODIS, Sentinel, and the only hyperspectral collection available (i.e. EO-1 Hyperion Hyperspectral Imager)
    * added a band properties table showing band names, wavelength, data offset and gain, and a description
    * added over 100 predefined spectral indices (thanks to the Awesome Spectral Indices project: https://awesome-ee-spectral-indices.readthedocs.io)
    * improved collection filtering by date range and image properties
    * added pixel quality filtering
    * improved temporal profile plot styling
    * requests to Google Earth Engine server is now asyncronized (i.e. not blocking the GUI)

  * made better use of collection metadata

    * use spectral wavelength for showing spectral profiles
    * use offset and scale values for proper data scaling
    * use band descriptions in tooltips
    * use band properties to enable pixel quality screening
    * use predefined RGB visualizations for band rendering

  * improved bulk download
  * added bulk download for image chips (500x500 pixel around the data point location)

* added *Classification Dataset Manager* app: allows to edit existing datasets (change class names and colors) and supports random subsampling

* added *Raster Layer Styling* panel

  * allows to quickly select a RGB, Gray or Pseudocolor visualization
  * supports band selection by wavelength
  * provides predefined RGB band combinations (e.g. Natural color, False color etc.)
  * supports the linking of the style between multiple raster layer

* added *Spectral Index Creator* app: allows to calculated over 100 spectral indices (thanks to the Awesome Spectral Indices project: https://awesome-ee-spectral-indices.readthedocs.io)
* added *Raster Source Band Properties Editor* application: allows to view and edit band properties of GDAL raster sources; with special support for ENVI metadata
* added *Color Space Explorer* application: allows to animate RGB / Gray bands of a raster layer (comparable to the ENVI Band Animator, but more advanced)
* replaced the old *Band statistics* application with a new more interactive application
* replaced the old *Classification statistics* application with a new more interactive application
* replaced the old *Scatter plot* application with a new more interactive application

* added *Python Console* option under Tools > Developers menu: mainly for debugging in EnMAP-Box stand-alone mode, where the QGIS GUI and QGIS Python Console isn't available
* added *Remove non-EnMAP-Box layers from project* option under Tools > Developers menu: mainly for closing layers that aren't accessible in EnMAP-Box stand-alone mode, where the QGIS GUI isn't available

**Renderer**

* added custom *Enhanced Multiband Color Rendering* raster renderer: allows to visualize arbitrary many bands at the same time using individual color canons for each band (it's currently more a prototype)

**Processing algorithms**

* added *Classification workflow* processing algorithm: combines model fitting, map prediction and model performance assessment in one algorithm
* added *Regression workflow* processing algorithm: combines model fitting, map prediction and model performance assessment in one algorithm
* added *Receiver operating characteristic (ROC) and detection error tradeoff (DET) curves* processing algorithm
* added *Create regression dataset (SynthMix from classification dataset)* processing algorithm
* added *Fit Spectral Angle Mapper* processing algorithm
* added *Fit Spectral Angle Mapper* processing algorithm
* added *Edit raster source band properties* processing algorithm: allows to set band names, center wavelength, FWHM, bad band multipliers, acquisition start and end times, data offset and scale, and no data values, to a GDAL raster source
* added *Stack raster layers* processing algorithm: a simple way to stack the bands of a list of rasters
* added *Fit CatBoostClassifier* processing algorithm
* added *Fit LGBMClassifier* processing algorithm
* added *Fit XGBClassifier* processing algorithm
* added *Fit XGBRFClassifier* processing algorithm
* added *Fit CatBoostRegressor* processing algorithm
* added *Fit LGBMRegressor* processing algorithm
* added *Fit XGBRegressor* processing algorithm
* added *Fit XGBRFRegressor* processing algorithm
* added *Merge classification datasets* processing algorithm
* added *Import PRISMA L2B product* processing algorithm
* added *Import PRISMA L2C product* processing algorithm
* improved *Import Landsat L2 product* processing algorithm: added support for Landsat 9
* improved *Import PRISMA <XYZ> product* processing algorithms: set default style for QA masks with nice colors
* improved *Import PRISMA L2D product* processing algorithm: allow to identify bad bands, based on the amount of bad pixels observed in the band
* improved *Translate raster layer* processing algorithm: remove several items from the ENVI dataset metadata domain, to avoid inconsistencies after band subsetting
* improved *Aggregate raster layer bands* processing algorithm: we support more aggregation functions and multi-band output
* overhauled *Regression layer accurary report* processing algorithm
* overhauled *Regressor performance report* processing algorithm
* overhauled *Import PRISMA L1 product* processing algorithms: now supports all sub-datasets
* replaced *Regression-based unmixing* application by a processing algorithm
* added *Aggregate Spectral Profiles* (enmapbox:aggregrateprofiles) (#1130)

* added custom processing widgets for selecting predefined classifier, regressor, clusterer and transformer specifications (i.e. code snippets)
* added custom processing widgets for selecting, and on-the-fly creating, training datasets: this makes ML workflows more convenient
* added custom processing widgets for selecting raster output format and creation options in the *Translate raster layer* processing algorithm

**Miscellaneous**

* plugin settings are now defined in *.plugin.ini*
* refactored unit tests
* new vector layers are added on top of the map canvas layer stack (#1210)
* fixed bug in cursor location value panel in case of failed CRS transformation (#1221)
* fixed crosshair distance measurements
* introduces EnMAPBoxProject, a QgsProject to keep EnMAP-Box QgsMapLayer references alive (#1227)

* fixe bug in Spectral Profile import dialog (#

Version 3.9
-----------
*This release was tested under QGIS 3.18 and 3.20.*

*Note that we are currently in a transition phase, where we're overhauling all processing algorithms.
Already overhauled algorithms are placed in groups prefixed by an asterisk, e.g. "*Classification".*


**GUI**

* added drag&drop functionality for opening external products (PRISMA, DESIS, Sentinel-2, Landsat) by simply dragging and dropping the product metadata file from the system file explorer onto the map view area.
* added map view context menu *Set background color* option

* new *Save as* options in data source and data view panel context menus:

  * opens *Translate raster layer* dialog for raster sources
  * opens *Save Features* dialog for vector sources

* added data sources context menu *Append ENVI header* option: opens *Append ENVI header to GeoTiff raster layer* algorithm dialog
* added single pixel movement in map view using <Ctrl> + <Arrow> keys, <Ctrl> + S to save a selected profile in a Spectral Library

* revised Data Source Panel and Data Source handling (#430)
* revised Spectral Library concept:

  * each vector layer that allows storing binary data can become a spectral library
    (e.g. Geopackage, PostGIS, in-memory layers)
  * spectral libraries can define multiple spectral profile fields

* revised Spectral Profile Source panel:

  * tree view defines how spectral profile features will be generated when using the Identify
    map tool with activated pixel profile option
  * allows to extract spectral profiles from different raster sources into different
    spectral profile fields of the same feature or into different features
  * values of extracted spectral profiles can be scaled by an (new) offset and a multiplier
  * other attributes of new features, e.g. for text and numeric fields, can be
    added by static values or expressions

* revised Spectral Library Viewer:

  * each vector layer can be opened in a Spectral Library Viewer
  * spectral profile visualizations allow to define colors, lines styles and
    profile labels
  * spectral profile visualizations are applied to individual sets of spectral profiles,
    e.g. all profiles of a spectral profile field, or only to profiles that match
    filter expressions like ``"name" = 'vegetation'``
  * profile colors can be defined as static color, attribute value or expression
  * profile plot allows to select multiple data points, e.g. to compare individual
    bands between spectral profiles
  * dialog to add new fields shows data type icons for available field types



**Renderer**

We started to introduced new raster renderer into the EnMAP-Box / QGIS.
Unfortunately, QGIS currently doesn't support registering custom Python raster renderer.
Because of this, our renderers aren't visible in the *Renderer type* list inside the *Layer Properties* dialog under *Symbology > Band Rendering*.

To actually use one of our renderers, you need to choose it from the *Custom raster renderer* submenu inside the raster layer context menu in the *Date Views* panel.

* added custom *Class fraction/probability* raster renderer: allows to visualize arbitrary many fraction/probability bands at the same time; this will replace the *Create RGB image from class probability/fraction layer* processing algorithm
* added custom *Decorrelation stretch* raster renderer: remove the high correlation commonly found in optical bands to produce a more colorful color composite image; this will replace the *Decorrelation stretch* processing algorithm

**Processing algorithms**

* added PRISMA L1 product import
* added Landsat 4-8 Collection 1-2 L2 product import
* added Sentinel-2 L2A product import
* added custom processing widget for selecting classification datasets from various sources; improves consistency and look&feel in algorithm dialogs and application GUIs
* added custom processing widget for Python code with highlighting
* added custem processing widget for building raster math expressions and code snippets
* improved raster math algorithms dialog and provided comprehensive cookbook usage recipe on ReadTheDocs
* added *Layer to mask layer* processing algorithm
* added *Create mask raster layer* processing algorithm
* overhauled all spatial and spectral filter algorithms
* added *Spatial convolution 2D Savitzki-Golay filter* processing algorithm
* overhauled all spectral resampling algorithms; added more custom sensors for spectral resampling: we now support EnMAP, DESIS, PRISMA, Landsat 4-8 and Sentinel-2; predefined sensor response functions are editable in the algorithm dialog
* added *Spectral resampling (to response function library)* processing algorithm: allows to specify the target response functions via a spectral library
* added *Spectral resampling (to spectral raster layer wavelength and FWHM)* processing algorithm: allows to specify the target response functions via a spectral raster layer
* added *Spectral resampling (to custom sensor)* processing algorithm: allows to specify the target response function via Python code
* improved *Translate raster layer* processing algorithm: 1) improved source and target no data handling, 2) added option for spectral subsetting to another spectral raster layer, 3) added options for setting/updating band scale and offset values, 4) added option for creating an ENVI header sidecar file for better compatibility to ENVI software
* added *Save raster layer as* processing algorithm: a slimmed down version of "Translate raster layer"
* added *Append ENVI header to GeoTiff raster layer* processing algorithm: places a \*.hdr ENVI header file next to a GeoTiff raster to improve compatibility to ENVI software
* added *Geolocate raster layer* processing algorithm: allows to geolocate a raster given in sensor geometry using X/Y location bands; e.g. usefull for geolocating PRISMA L1 Landcover into PRISMA L2 pixel grid using the Lat/Lon location bands

**Miscellaneous**

* added EnMAP spectral response function library as example dataset
* change example data vector layer format from Shapefile to GeoPackage
* added example data to enmapbox repository
* added unittest data to enmapbox repository


Version 3.8
-----------
* introduced a Glossary explaining common terms
* added processing algorithm for creating default style (QML sidecar file) with given categories
* overhauled Classification Workflow app; old version is still available as Classification Workflow (Classic)
* overhauled several processing algorithms related to classification fit, predict, accuracy accessment and random sub-sampling
* overhauled processing algorithms show command line and Python commands for re-executing the algorithms with same inputs
* added a processing algorithm for calculating a classification change map from two classifications
* overhauled existing and introduced new processing algorithms for prepare classification (training/testing) datasets;
  currently we support classification data from raster/vector layers, from table; from text file; from spectral library
* added processing algorithm for supervised classifier feature ranking using permutation importances
* added processing algorithm for unsupervised feature clustering
* overhauled processing algorithm for creating RGB images from class probability or class fraction layer
* added processing algorithm for creating a grid (i.e. an empty raster layer) by specifying target CRS, extent and size
* added processing algorithm for doing raster math with a list of input raster layers
* added processing algorithm for rasterizing categoriezed vector layers
* overhauled processing algorithm for rasterizing vector layers (improved performance)
* added processing algorithm for translating categorized raster layers
* overhauled processing algorithm for translating raster layers
* added processing algorithms for creating random points from mask and categorized raster layers
* added processing algorithm for sampling of raster layer values
* added processing algorithm for decorrelation stretching
* rename layers, map views and spectral library views with F2
* model browser: improved visualization (#645, #646, #647), array values can be copied to clipboard (#520)
* layers can be moved between maps (#437)
* updated pyqtgraph to 0.12.1

Version 3.7
-----------
* added EnMAP L1B, L1C and L2A product reader
* added PRISMA L2D product import
* added DESIS L2A product reader
* added Classification Statistics PA
* added Save As ENVI Raster PA: saves a raster in ENVI format and takes care of proper metadata storage inside ENVI header file
* added Aggregate Raster Bands PA: allows to aggregate multiband raster into a single band using aggregation functions like min, max, mean, any, all, etc.
* classification scheme is now defined by the layer renderer
* [Spectral Resampling PA] reworked spectral resampling
* [Classification Workflow] support libraries as input
* [ImageMath] added predefined code snippets
* [Subset Raster Wavebands PA] support band selection via wavelength
* LayerTreeView: enhanced context menus:
  double click on map layer opens Properties Dialog,
  double click on a vector layers' legend item opens a Symbol dialog
* GDAL raster metadata can be modified (resolves #181)
* map canvas preserves scale on window resize (#409)
* Reclassify Tool: can save and reload the class mapping, fixed (#501)
* several fixed in Image Cube App
* updated PyQtGraph to version 0.11
* Virtual Raster Builder and Image Cube can select spatial extents from other QGIS / EnMAP-Box maps
* several improvements to SpectralLibrary, e.g. to edit SpectralProfile values
* QGIS expression builder:
    added 'format_py' to create strings with python-string-format syntax,
    added spectralData() to access SpectralProfile values
    added spectralMath(...) to modify  / create new SpectralProfiles
* fixes some bugs in imageCube app


Version 3.6
-----------
(including hotfixes from 2020-06-22)

* added workaround for failed module imports, e.g. numba on windows (#405)
* EnMAP-Box plugin can be installed and started without having none-standard python packages installed (#366)
* Added installer to install missing python packages (#371)
* Map Canvas Crosshair can now show the pixel boundaries of any raster source known to QGIS
* Spectral Profile Source panel
    * is properly updated on removal/adding of raster sources or spectral libraries
    * allows to define source-specific profile plot styles (#422, #468)
* Spectral Library Viewer
    * added color schemes to set plot and profile styles
    * fixed color scheme issue (# fixed #467 )
    * profile styles can be changed per profile (#268)
    * current/temporary profiles are shown in the attribute table
    * added workaround for #345 (Spectral library create new field: problems with default fields)
    * loading profiles based in vector position is done in a background process (closed #329)
    * profile data point can be selected to show point specific information, e.g. the band number (#462, #267)
    * closed #252
* SpectralLibrary
    * implemented SpectralProfileRenderer to maintain profile-specific plot styles
* Classification Scheme Widget allows to paste/copy classification schemes from/to the clipboard.
  This can be used to copy classes from other raster or vector layers, or to set the layer renderer
  according to the classification scheme
* updated in LMU vegetation app
* updated EnPTEnMAPBoxApp (see https://git-pages.gfz-potsdam.de/EnMAP/GFZ_Tools_EnMAP_BOX/enpt_enmapboxapp for documentation)
* added EnSoMAP and EnGeoMAP applications provided by GFZ
* added ONNS application provided by HZG
* removed several bugs, e.g. #285, #206,

Version 3.5
-----------

(including last hotfixes from 2019-11-12)

* removed numba imports from LMU vegetation app
* vector layer styling is loaded by default
* fixed error that was thrown when closing the EnMAP-Box
* fixed bug in SynthMixApplication
* Spectral Library Viewer: import and export of ASD, EcoSIS and SPECCHIO csv/binary files
* Spectral Profile Source panel: controls how to extract SpectralProfiles and where to show them
* supports import of multi-dimensional raster formats, like HDF and netCDF
* ImageCube viewer to visualize hyperspectral data cubes (requires opengl)
* Added CONTRIBUTORS.md and "How to contribute" section to online documention
* Documentation uses HYPERedu stylesheet (https://eo-college.org/members/hyperedu/)
* fixed start up of EO Time Series Viewer and Virtual Raster Builder QGIS Plugins from EnMAP-Box

Version 3.4
-------------------------------------------

* Spectral Library Viewer: import spectral profiles from raster file based on vector positions
* Classification Widgets: copy / paste single class informations
* Map tools to select / add vector features
* fixed critical bug in IVVRM
* several bug fixed and minor improvements

Version 3.3
-------------------------------------------

* added user +  developer example to RTF documentation
* renamed plugin folder to "EnMAP-Box"
* SpectralLibraries can be renamed and added to
  map canvases to show profile locations
* SpectraProfiles now styled like point layers:
  point color will be line color in profile plot
* Workaround for macOS bug that started
  new QGIS instances again and again and ...
* Classification Workflow App
* Re-designed Metadata Editor
* Several bug fixes

Version 3.2
-------------------------------------------

* ...

Version 3.1
-------------------------------------------

* EnMAP-Box is now based on QGIS 3, Qt 5.9,Python 3 and GDAL 2.2
* QGISP lugin Installation from ZIP File
* readthedocs documentation
  https://enmap-box.readthedocs.io/en/latest/index.html

previous versions
-------------------------------------------

* version scheme following build dates

