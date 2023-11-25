# CHANGELOG
## Version 3.13

_This release was tested with QGIS 3.28 (LTR), 3.32 and 3.34 (latest release)_

### Example Dataset

* the previous _Berlin_ example dataset (based on simulated data) was replaced by a new dataset derived from real EnMAP L2A data, covering the _Potsdam_ region
* the underlying full EnMAP L2A scene can be downloaded from within the _EnMAP-Box Menu > Project > Download Example Scene_ (without user registration etc.) 
* updated the EnMAP sensor model (wavelength and fwhm) ([#496](https://github.com/EnMAP-Box/enmap-box/issues/496))


#### QGIS Expressions / QGIS Field Calculator

* ``raster_array`` and ``raster_profile`` function can use polygon input

### Python Dependencies

* updated [PyQtGraph](https://www.pyqtgraph.org/) to version 0.13.4 (via update of QPS)

### Earth Observation for QGIS (EO4Q) Applications

* _Profile Analytics_ application: added option for linking profiles from _GEE Time Series Explorer_ ([#531](https://github.com/EnMAP-Box/enmap-box/issues/531))
* _Profile Analytics_ application: added option for linking profiles into _Spectral Views_ ([#530](https://github.com/EnMAP-Box/enmap-box/issues/530))

### GUI

* _Spectral View_: added distance units (e.g. m, km) for properly plotting spatial profiles ([#525](https://github.com/EnMAP-Box/enmap-box/issues/525))
* 

### Processing Algorithms

* added _Classification layer from rendered image_ algorithm: allows to create a classification layer from a rendered image; classes are derived from the unique RGB values ([#611](https://github.com/EnMAP-Box/enmap-box/issues/611))
* added _Random points from raster layer value-ranges_ algorithm: allows to create a point layer with a given number of random points, all of them within specified value-ranges of the given raster band ([#593](https://github.com/EnMAP-Box/enmap-box/issues/593))
* added _Spectral resampling (to wavelength)_ algorithm: allows to spectrally resample a spectral raster layer by applying linear interpolation at given wavelengths ([#580](https://github.com/EnMAP-Box/enmap-box/issues/580))
* added _Class separability report_ algorithm: allows to evaluate the pair-wise class separability in terms of the Jeffries Matusita distance ([#469](https://github.com/EnMAP-Box/enmap-box/issues/469))

* _Create classification|regression|unsupervised dataset_ algorithms: added _Exclude bad bands_ ([#560](https://github.com/EnMAP-Box/enmap-box/issues/560))
* _Subset raster layer bands_ algorithm: added _Exclude bad bands_ and _Derive and exclude additional bad bands_ ([#638](https://github.com/EnMAP-Box/enmap-box/issues/638))
* _Spectral resampling (to spectral raster layer wavelength and FWHM)_ algorithm: the wavelength anf fwhm information can now also provided via a) an ENVI Spectral Library, b) an ENVI Header file, or c) a CSV table ([#574](https://github.com/EnMAP-Box/enmap-box/issues/574))
* _Edit raster source band properties_ algorithm: allow expressions using counter variables to derive value lists, e.g. to specify band names list ([#539](https://github.com/EnMAP-Box/enmap-box/issues/539))
* _Raster math_ algorithm: output band names are now enumerated by defaults, which avoids empty band names ([#532](https://github.com/EnMAP-Box/enmap-box/issues/532))
* _Import EnMAP L2A product_ algorithm: added _Order by detector (VNIR, SWIR)_ option, which allows to reorder the spectral bands: all VNIR bands first, followed by all SWIR bands ([#515](https://github.com/EnMAP-Box/enmap-box/issues/515))

### Data Formats / Metadata Handling

* we now support sensor models (used for spectral resampling) provided as CSV tables with center wavelength and fwhm information; one row for each band; two column, i.e. "wavelength" and "fwhm" in nanometers  

### Bugfixes

* [v3.13.1](https://github.com/EnMAP-Box/enmap-box/milestone/13?closed=1)
* [v3.13.0](https://github.com/EnMAP-Box/enmap-box/milestone/10?closed=1)

## Version 3.12

_This release was tested under QGIS LTR 3.28.4_

### Applications

* added range-slider in _Raster Layer Styling_ for interactively masking values to be displayed ([#247](https://github.com/EnMAP-Box/enmap-box/issues/247))
* _QGIS Temporal Controller_: added support for temporal raster stacks ([#245](https://github.com/EnMAP-Box/enmap-box/issues/245))

#### Earth Observation for QGIS (EO4Q) Applications

The label _EO4Q_ refers to a new collection of EnMAP-Box tools and applications designed to integrate well in both, EnMAP-Box and QGIS environments.
Also see https://enmap-box.readthedocs.io/en/latest/usr_section/usr_manual/eo4q.html.

* added _Location Browser_ application: allows to navigate to a map location directly, or to send a request to the Nominatim geocoding service. ([#200](https://github.com/EnMAP-Box/enmap-box/issues/200))
* added _Raster Band Stacking_ application: allows to easily stack bands into a new VRT raster layer ([#155](https://github.com/EnMAP-Box/enmap-box/issues/155))
* added _Sensor Product Import_ application: allows to import various sensor products via drag&drop ([#211](https://github.com/EnMAP-Box/enmap-box/issues/211))
* note that _Profile Analytics_ app was already released with EnMAP-Box 3.11 ([#81](https://github.com/EnMAP-Box/enmap-box/issues/81))
* note that _GEE Time Series Explorer_ app was already released with EnMAP-Box 3.10
* added _Profile Analytics_ UFUNC for RBF-based Timeseries Fitting ([#273](https://github.com/EnMAP-Box/enmap-box/issues/273))


#### QGIS Expressions / QGIS Field Calculator

* ``raster_array(layer[,geometry='@geometry'])`` returns an array with the pixel values at geometry (point) position (point).
* ``raster_profile(layer[,geometry='@geometry'][,encoding='text'])`` returns the pixel values at the geometry (point) position as spectral profile (json/string/map/blob)
* renamed some Spectral Libraries functions for consistency with other QGIS functions


### Spectral Library Viewer

* Spectral profiles are plotted by default in the same color as used to plot map symbols (`@symbol_color`)

### Processing Algorithms

* added _Import EMIT L2A product_ processing algorithm: added support for EMIT L2A products ([#278](https://github.com/EnMAP-Box/enmap-box/issues/278))
* added _Sum-to-one constraint_ option to _Regression-based unmixing_ algorithm ([#239](https://github.com/EnMAP-Box/enmap-box/issues/239))
* _Aggregate Spectral Profiles_ (`enmapbox:aggregateprofiles`) takes a spectral library vector layer and aggregates profiles based on a group-by expression. Spectral profiles for which the group-by expression return the same value aggregated by min, mean, max or median.

### Data Formats / Metadata Handling

* added support for _NETCDF_DIM_time_ format ([#251](https://github.com/EnMAP-Box/enmap-box/issues/251))

### Bugfixes

* [v3.12.2](https://github.com/EnMAP-Box/enmap-box/milestone/11?closed=1)
* [v3.12.1](https://github.com/EnMAP-Box/enmap-box/milestone/8?closed=1)
* [v3.12.0](https://github.com/EnMAP-Box/enmap-box/milestone/7?closed=1)


## Version 3.11

_This release was tested under QGIS 3.26.2_

_Important Notice: the EnMAP-Box repository moved to https://github.com/EnMAP-Box/enmap-box

### Applications

* added _Profile Analytics_ app: ([#81](https://github.com/EnMAP-Box/enmap-box/issues/81))
    * allows various profile plot types like spectral profiles, temporal profiles, spatial profiles.
    * profile data can be analysed by user-defined function; the user-function has access to the plot widget and can draw additional plot items

* improved _Scatter Plot_ app:
    * added support for vector data ([#1393](https://bitbucket.org/hu-geomatics/enmap-box/issues/1393/scatter-plot-app-allow-vector-sources-as))
    * added support for simple scatter plots with symbols plotted, instead count density ([#1410](https://bitbucket.org/hu-geomatics/enmap-box/issues/1410/scatter-plot-app-allow-to-plot-scatter))
    * added support for showing 1:1 line ([#1394](https://bitbucket.org/hu-geomatics/enmap-box/issues/1394/scatter-plot-app-add-performance-measures))
    * added support for fitting a line to the data and report goodness of fit measures ([#1394](https://bitbucket.org/hu-geomatics/enmap-box/issues/1394/scatter-plot-app-add-performance-measures))

### Renderer

* added custom _Bivariate Color Raster Renderer_: allows to visualize two bands using a 2d color ramp. Find a mapping example here: https://www.joshuastevens.net/cartography/make-a-bivariate-choropleth-map/ ([#70](https://github.com/EnMAP-Box/enmap-box/issues/70))
* added custom _CMYK Color Raster Renderer_: allows to visualize four bands using the CMYK (Cyan, Magenta, Yellow, and Key (black)) color model. Find a mapping example here: https://adventuresinmapping.com/2018/10/31/cmyk-vice/ ([#74](https://github.com/EnMAP-Box/enmap-box/issues/74))
* added custom _HSV Color Raster Renderer_: allows to visualize three bands using the HSV (Hue, Saturation, Value (black)) color model. Find a mapping example here: https://landmonitoring.earth/portal/ ; select Maps > Global Landcover Dynamics 2016-2020 ([#73](https://github.com/EnMAP-Box/enmap-box/issues/73))
* added custom _Multisource Multiband Color Raster Renderer_: same functionality as the default QGIS Multiband Color Raster Renderer, but the Red, Green and Blue bands can come from different raster sources ([#112](https://github.com/EnMAP-Box/enmap-box/issues/112))

### Data Formats / Metadata Handling

* GDAL metadata like band names can be edited in layer properties (support for ENVI images available with [GDAL 3.6](https://github.com/OSGeo/gdal/issues/6444)
* added support for JSON files for storing classification/regression datasets used in ML algorithms ([#21](https://github.com/EnMAP-Box/enmap-box/issues/21))
* added support for marking a raster bands as bad inside the _Raster Layer Styling_ panel ([#31](https://github.com/EnMAP-Box/enmap-box/issues/31))
* added support for FORCE v1.2 TSI format ([#111](https://github.com/EnMAP-Box/enmap-box/issues/111))

### Bugfixes

* [v3.11.1](https://github.com/EnMAP-Box/enmap-box/milestone/5?closed=1)
* [v3.11.0](https://github.com/EnMAP-Box/enmap-box/milestone/2?closed=1)

## Version 3.10

_This release was tested under QGIS 3.24.1_

### GUI

* _Project -> Create Data Source_ to create new shapefiles, Geopackages or in-memory vector layers
* refactored layer handling and added layer groups ([#649](https://bitbucket.org/hu-geomatics/enmap-box/issues/649))
* connected attribute table context menu 'Zoom/Pan to/Flash Feature' with EnMAP-Box maps ([#1250](https://bitbucket.org/hu-geomatics/enmap-box/issues/1250), [#1260](https://bitbucket.org/hu-geomatics/enmap-box/issues/1260))

### Data Sources

* added 16 predefined RGB band combinations in the raster source context menu (thanks to the _GEE Data Catalog_ plugin)
* added _Create/update ENVI header_ option in raster source context menu: allows to quickly create an ENVI header with proper metadata required for ENVI Software; works for ENVI and GeoTiff raster
* added option for opening a band in an existing map view
* added _Save as_ option in the layer source context menu
* shows in-memory vector layers
* shows sub-dataset names ([#1145](https://bitbucket.org/hu-geomatics/enmap-box/issues/1145))
* source properties are updated in regular intervals ([#1230](https://bitbucket.org/hu-geomatics/enmap-box/issues/1230))

### Data Views

* added _Add Group_ to create layer groups
* added _Copy layer to QGIS_ option in layer context menu
* added _Apply model_ option in raster layer context menu: allows to quickly apply a machine learner to predict a map using the raster
* fixed drag & drop ([#1143](https://bitbucket.org/hu-geomatics/enmap-box/issues/1143))
* fixed floating & unfloating issues ([#1231](https://bitbucket.org/hu-geomatics/enmap-box/issues/1231))

### Spectral Libraries

* spectral profiles can be stored in text and JSON fields
* added functions to access and modify spectral profiles within field calculator expressions, e.g.
  _encodeProfile(field, encoding)_ to convert a profile into its binary or JSON string representation
* added first aggregation functions: maxProfile, meanProfile, medianProfile, minProfile ([#1130](https://bitbucket.org/hu-geomatics/enmap-box/issues/1130))
* added Spectral Processing allows to create and modify spectral profiles using raster processing algorithms / models
* revised import and export of spectral profiles from/to other formats (e.g. [#1249](https://bitbucket.org/hu-geomatics/enmap-box/issues/1249), [#1274](https://bitbucket.org/hu-geomatics/enmap-box/issues/1274))
* new editor to modify single spectral profiles
* reads profiles from Spectral Evolution .sed files (reference, target, reflectance)

### Spectral Profile plot

* moved plot settings like background and crosshair color from context menu to the visualization settings tree view
* color and line style of temporary profiles can be defined in spectral profile source panel
* fixed smaller plot update issues and optimized profile plot speed
* allows to show/hide bad band values
* allows to show renderer band positions (RGB / single band)
* allows to show/hide current/temporary profiles

### Applications

* Metadata Viewer revised ([#1185](https://bitbucket.org/hu-geomatics/enmap-box/issues/1185), [#1329](https://bitbucket.org/hu-geomatics/enmap-box/issues/1329)), added more band-specific settings

* included the _GEE Timeseries Explorer_ plugin into the EnMAP-Box
    * (slightly) new name _GEE Time Series Explorer_ app
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

* added _Classification Dataset Manager_ app: allows to edit existing datasets (change class names and colors) and supports random subsampling
* added _Raster Layer Styling_ panel
    * allows to quickly select an RGB, Gray or Pseudocolor visualization
    * supports band selection by wavelength
    * provides predefined RGB band combinations (e.g. Natural color, False color etc.)
    * supports the linking of the style between multiple raster layer
* added _Spectral Index Creator_ app: allows to calculated over 100 spectral indices (thanks to the Awesome Spectral Indices project: https://awesome-ee-spectral-indices.readthedocs.io)
* added _Raster Source Band Properties Editor_ application: allows to view and edit band properties of GDAL raster sources; with special support for ENVI metadata
* added _Color Space Explorer_ application: allows to animate RGB / Gray bands of a raster layer (comparable to the ENVI Band Animator, but more advanced)
* replaced the old _Band statistics_ application with a new more interactive application
* replaced the old _Classification statistics_ application with a new more interactive application
* replaced the old _Scatter plot_ application with a new more interactive application
* added _Python Console_ option under Tools > Developers menu: mainly for debugging in EnMAP-Box stand-alone mode, where the QGIS GUI and QGIS Python Console isn't available
* added _Remove non-EnMAP-Box layers from project_ option under Tools > Developers menu: mainly for closing layers that aren't accessible in EnMAP-Box stand-alone mode, where the QGIS GUI isn't available

### Renderer

* added custom _Enhanced Multiband Color Rendering_ raster renderer: allows to visualize arbitrary many bands at the same time using individual color canons for each band (it's currently more a prototype)

### Processing algorithms

* added _Classification workflow_ processing algorithm: combines model fitting, map prediction and model performance assessment in one algorithm
* added _Regression workflow_ processing algorithm: combines model fitting, map prediction and model performance assessment in one algorithm
* added _Receiver operating characteristic (ROC) and detection error tradeoff (DET) curves_ processing algorithm
* added _Create regression dataset (SynthMix from classification dataset)_ processing algorithm
* added _Fit Spectral Angle Mapper_ processing algorithm
* added _Fit Spectral Angle Mapper_ processing algorithm
* added _Edit raster source band properties_ processing algorithm: allows to set band names, center wavelength, FWHM, bad band multipliers, acquisition start and end times, data offset and scale, and no data values, to a GDAL raster source
* added _Stack raster layers_ processing algorithm: a simple way to stack the bands of a list of rasters
* added _Fit CatBoostClassifier_ processing algorithm
* added _Fit LGBMClassifier_ processing algorithm
* added _Fit XGBClassifier_ processing algorithm
* added _Fit XGBRFClassifier_ processing algorithm
* added _Fit CatBoostRegressor_ processing algorithm
* added _Fit LGBMRegressor_ processing algorithm
* added _Fit XGBRegressor_ processing algorithm
* added _Fit XGBRFRegressor_ processing algorithm
* added _Merge classification datasets_ processing algorithm
* added _Import PRISMA L2B product_ processing algorithm
* added _Import PRISMA L2C product_ processing algorithm
* improved _Import Landsat L2 product_ processing algorithm: added support for Landsat 9
* improved _Import PRISMA \<XYZ\> product_ processing algorithms: set default style for QA masks with nice colors
* improved _Import PRISMA L2D product_ processing algorithm: allow to identify bad bands, based on the amount of bad pixels observed in the band
* improved _Translate raster layer_ processing algorithm: remove several items from the ENVI dataset metadata domain, to avoid inconsistencies after band subsetting
* improved _Aggregate raster layer bands_ processing algorithm: we support more aggregation functions and multi-band output
* overhauled _Regression layer accuracy report_ processing algorithm
* overhauled _Regressor performance report_ processing algorithm
* overhauled _Import PRISMA L1 product_ processing algorithms: now supports all sub-datasets
* replaced _Regression-based unmixing_ application by a processing algorithm
* added _Aggregate Spectral Profiles_ (enmapbox:aggregrateprofiles) ([#1130](https://bitbucket.org/hu-geomatics/enmap-box/issues/1130))

* added custom processing widgets for selecting predefined classifier, regressor, clusterer and transformer specifications (i.e. code snippets)
* added custom processing widgets for selecting, and on-the-fly creating, training datasets: this makes ML workflows more convenient
* added custom processing widgets for selecting raster output format and creation options in the _Translate raster layer_ processing algorithm

### Miscellaneous

* plugin settings are now defined in _.plugin.ini_
* refactored unit tests
* new vector layers are added on top of the map canvas layer stack ([#1210](https://bitbucket.org/hu-geomatics/enmap-box/issues/1210))
* fixed bug in cursor location value panel in case of failed CRS transformation ([#1221](https://bitbucket.org/hu-geomatics/enmap-box/issues/1221))
* fixed crosshair distance measurements
* introduces EnMAPBoxProject, a QgsProject to keep EnMAP-Box QgsMapLayer references alive ([#1227](https://bitbucket.org/hu-geomatics/enmap-box/issues/1227))
* fixe bug in Spectral Profile import dialog

## Version 3.9

 _This release was tested under QGIS 3.18 and 3.20._

 _Note that we are currently in a transition phase, where we're overhauling all processing algorithms.
Already overhauled algorithms are placed in groups prefixed by an asterisk, e.g. "Classification"._


### GUI

* added drag&drop functionality for opening external products (PRISMA, DESIS, Sentinel-2, Landsat) by simply dragging and dropping the product metadata file from the system file explorer onto the map view area.
* added map view context menu _Set background color_ option

* new _Save as_ options in data source and data view panel context menus:

    * opens _Translate raster layer_ dialog for raster sources
    * opens _Save Features_ dialog for vector sources

* added data sources context menu _Append ENVI header_ option: opens _Append ENVI header to GeoTiff raster layer_ algorithm dialog
* added single pixel movement in map view using \<Ctrl\> + \<Arrow\> keys, \<Ctrl\> + S to save a selected profile in a Spectral Library

* revised Data Source Panel and Data Source handling ([#430](https://bitbucket.org/hu-geomatics/enmap-box/issues/430))
* revised Spectral Library concept:

    * each vector layer that allows storing binary data can become a spectral library
      (e.g. Geopackage, PostGIS, in-memory layers)
    * spectral libraries can define multiple spectral profile fields

* revised Spectral Profile Source panel:

    * tree view defines how spectral profile features will be generated when using the Identify
      map tool with activated pixel profile option
    * allows to extract spectral profiles from different raster sources into different
      spectral profile fields of the same feature or into different features
    * values of extracted spectral profiles can be scaled by a (new) offset and a multiplier
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



### Renderer

We started to introduced new raster renderer into the EnMAP-Box / QGIS.
Unfortunately, QGIS currently doesn't support registering custom Python raster renderer.
Because of this, our renderers aren't visible in the _Renderer type_ list inside the _Layer Properties_ dialog under _Symbology > Band Rendering_.

To actually use one of our renderers, you need to choose it from the _Custom raster renderer_ submenu inside the raster layer context menu in the _Date Views_ panel.

* added custom _Class fraction/probability_ raster renderer: allows to visualize arbitrary many fraction/probability bands at the same time; this will replace the _Create RGB image from class probability/fraction layer_ processing algorithm
* added custom _Decorrelation stretch_ raster renderer: remove the high correlation commonly found in optical bands to produce a more colorful color composite image; this will replace the _Decorrelation stretch_ processing algorithm

### Processing algorithms

* added PRISMA L1 product import
* added Landsat 4-8 Collection 1-2 L2 product import
* added Sentinel-2 L2A product import
* added custom processing widget for selecting classification datasets from various sources; improves consistency and look&feel in algorithm dialogs and application GUIs
* added custom processing widget for Python code with highlighting
* added custom processing widget for building raster math expressions and code snippets
* improved raster math algorithms dialog and provided comprehensive cookbook usage recipe on ReadTheDocs
* added _Layer to mask layer_ processing algorithm
* added _Create mask raster layer_ processing algorithm
* overhauled all spatial and spectral filter algorithms
* added _Spatial convolution 2D Savitzki-Golay filter_ processing algorithm
* overhauled all spectral resampling algorithms; added more custom sensors for spectral resampling: we now support EnMAP, DESIS, PRISMA, Landsat 4-8 and Sentinel-2; predefined sensor response functions are editable in the algorithm dialog
* added _Spectral resampling (to response function library)_ processing algorithm: allows to specify the target response functions via a spectral library
* added _Spectral resampling (to spectral raster layer wavelength and FWHM)_ processing algorithm: allows to specify the target response functions via a spectral raster layer
* added _Spectral resampling (to custom sensor)_ processing algorithm: allows to specify the target response function via Python code
* improved _Translate raster layer_ processing algorithm: 1) improved source and target no data handling, 2) added option for spectral subsetting to another spectral raster layer, 3) added options for setting/updating band scale and offset values, 4) added option for creating an ENVI header sidecar file for better compatibility to ENVI software
* added _Save raster layer as_ processing algorithm: a slimmed down version of "Translate raster layer"
* added _Append ENVI header to GeoTiff raster layer_ processing algorithm: places a \_.hdr ENVI header file next to a GeoTiff raster to improve compatibility to ENVI software
_ added _Geolocate raster layer_ processing algorithm: allows to geolocate a raster given in sensor geometry using X/Y location bands; e.g. usefull for geolocating PRISMA L1 Landcover into PRISMA L2 pixel grid using the Lat/Lon location bands

### Miscellaneous

* added EnMAP spectral response function library as example dataset
* change example data vector layer format from Shapefile to GeoPackage
* added example data to enmapbox repository
* added unittest data to enmapbox repository


## Version 3.8

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
* added processing algorithm for rasterizing categorized vector layers
* overhauled processing algorithm for rasterizing vector layers (improved performance)
* added processing algorithm for translating categorized raster layers
* overhauled processing algorithm for translating raster layers
* added processing algorithms for creating random points from mask and categorized raster layers
* added processing algorithm for sampling of raster layer values
* added processing algorithm for decorrelation stretching
* rename layers, map views and spectral library views with F2
* model browser: improved visualization ([#645](https://bitbucket.org/hu-geomatics/enmap-box/issues/645), [#646](https://bitbucket.org/hu-geomatics/enmap-box/issues/646), [#647](https://bitbucket.org/hu-geomatics/enmap-box/issues/647)), array values can be copied to clipboard ([#520](https://bitbucket.org/hu-geomatics/enmap-box/issues/520))
* layers can be moved between maps ([#437](https://bitbucket.org/hu-geomatics/enmap-box/issues/437))
* updated pyqtgraph to 0.12.1

## Version 3.7

* added EnMAP L1B, L1C and L2A product reader
* added PRISMA L2D product import
* added DESIS L2A product reader
* added Classification Statistics PA
* added Save As ENVI Raster PA: saves a raster in ENVI format and takes care of proper metadata storage inside ENVI header file
* added Aggregate Raster Bands PA: allows to aggregate multiband raster into a single band using aggregation functions like min, max, mean, any, all, etc.
* classification scheme is now defined by the layer renderer
* _Spectral Resampling PA_ reworked spectral resampling
* _Classification Workflow_ support libraries as input
* _ImageMath_ added predefined code snippets
* _Subset Raster Wavebands PA_ support band selection via wavelength
* LayerTreeView: enhanced context menus:
  double-click on map layer opens Properties Dialog,
  double-click on a vector layers' legend item opens a Symbol dialog
* GDAL raster metadata can be modified (resolves [#181](https://bitbucket.org/hu-geomatics/enmap-box/issues/181))
* map canvas preserves scale on window resize ([#409](https://bitbucket.org/hu-geomatics/enmap-box/issues/409))
* Reclassify Tool: can save and reload the class mapping, fixed ([#501](https://bitbucket.org/hu-geomatics/enmap-box/issues/501))
* several fixed in Image Cube App
* updated PyQtGraph to version 0.11
* Virtual Raster Builder and Image Cube can select spatial extents from other QGIS / EnMAP-Box maps
* several improvements to SpectralLibrary, e.g. to edit SpectralProfile values
* QGIS expression builder:
    added 'format_py' to create strings with python-string-format syntax,
    added spectralData() to access SpectralProfile values
    added spectralMath(...) to modify  / create new SpectralProfiles
* fixes some bugs in imageCube app


## Version 3.6

(including hotfixes from 2020-06-22)

* added workaround for failed module imports, e.g. numba on windows ([#405](https://bitbucket.org/hu-geomatics/enmap-box/issues/405))
* EnMAP-Box plugin can be installed and started without having none-standard python packages installed ([#366](https://bitbucket.org/hu-geomatics/enmap-box/issues/366))
* Added installer to install missing python packages ([#371](https://bitbucket.org/hu-geomatics/enmap-box/issues/371))
* Map Canvas Crosshair can now show the pixel boundaries of any raster source known to QGIS
* Spectral Profile Source panel
    * is properly updated on removal/adding of raster sources or spectral libraries
    * allows to define source-specific profile plot styles ([#422](https://bitbucket.org/hu-geomatics/enmap-box/issues//422), [#468](https://bitbucket.org/hu-geomatics/enmap-box/issues/468))

### Spectral Library Viewer & Spectral Libraries

  * added color schemes to set plot and profile styles
  * fixed color scheme issue (# fixed [#467](https://bitbucket.org/hu-geomatics/enmap-box/issues/467) )
  * profile styles can be changed per profile ([#268](https://bitbucket.org/hu-geomatics/enmap-box/issues/268))
  * current/temporary profiles are shown in the attribute table
  * added workaround for [#345](https://bitbucket.org/hu-geomatics/enmap-box/issues/345) (Spectral library create new field: problems with default fields)
  * loading profiles based in vector position is done in a background process (closed [#329](https://bitbucket.org/hu-geomatics/enmap-box/issues/329))
  * profile data point can be selected to show point specific information, e.g. the band number ([#462](https://bitbucket.org/hu-geomatics/enmap-box/issues/462), [#267](https://bitbucket.org/hu-geomatics/enmap-box/issues/267))
  * closed [#252](https://bitbucket.org/hu-geomatics/enmap-box/issues/252)
  * implemented SpectralProfileRenderer to maintain profile-specific plot styles

### Miscellaneous

* Classification Scheme Widget allows to paste/copy classification schemes from/to the clipboard.
  This can be used to copy classes from other raster or vector layers, or to set the layer renderer
  according to the classification scheme
* updated in LMU vegetation app
* updated EnPTEnMAPBoxApp (see https://git-pages.gfz-potsdam.de/EnMAP/GFZ_Tools_EnMAP_BOX/enpt_enmapboxapp for documentation)
* added EnSoMAP and EnGeoMAP applications provided by GFZ
* added ONNS application provided by HZG
* removed several bugs, e.g. [#285](https://bitbucket.org/hu-geomatics/enmap-box/issues/285), [#206](https://bitbucket.org/hu-geomatics/enmap-box/issues/206),

## Version 3.5


(including last hotfixes from 2019-11-12)


* removed numba imports from LMU vegetation app
* vector layer styling is loaded by default
* fixed error that was thrown when closing the EnMAP-Box
* fixed bug in SynthMixApplication
* Spectral Library Viewer: import and export of ASD, EcoSIS and SPECCHIO csv/binary files
* Spectral Profile Source panel: controls how to extract SpectralProfiles and where to show them
* supports import of multidimensional raster formats, like HDF and netCDF
* ImageCube viewer to visualize hyperspectral data cubes (requires opengl)
* Added CONTRIBUTORS.md and "How to contribute" section to online documention
* Documentation uses HYPERedu stylesheet (https://eo-college.org/members/hyperedu/)
* fixed start up of EO Time Series Viewer and Virtual Raster Builder QGIS Plugins from EnMAP-Box

## Version 3.4


* Spectral Library Viewer: import spectral profiles from raster file based on vector positions
* Classification Widgets: copy / paste single class information
* Map tools to select / add vector features
* fixed critical bug in IVVRM
* several bug fixed and minor improvements

## Version 3.3


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

## Version 3.2


* ... _sorry, but we forgot to track the changes here_

## Version 3.1


* EnMAP-Box is now based on QGIS 3, Qt 5.9,Python 3 and GDAL 2.2
* QGISP lugin Installation from ZIP File
* readthedocs documentation
  https://enmap-box.readthedocs.io/en/latest/index.html

## Previous versions ...


* version scheme following build dates

