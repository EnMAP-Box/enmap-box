EnMAP-Box 3 Example Dataset
-----------------------------------------------

1. enmap_potsdam.tif
	Hyperspectral EnMAP Level 2A data acquired on the 24th of July 2022 over the City of Potsdam, Germany,
	Provider: DLR (german aerospace center)
	EnMAP L2A scene ID: ENMAP01-____L2A-DT0000001867_20220724T104526Z_008_V010302_20230628T165614Z (processing v1.3.2)
	Ground sampling distance: 30 m
	Number of bands: 224 (from 400 to 2450 nm)
	Number of bad bands: 6 (filled with no data value)
	Data: 330x200x244 (Float32)


2. aerial_potsdam.tif
	Aerial image acquired on the 1st of April 2019 over the City of Potsdam, Germany.
	Provider: LGB (Landesvermessung und Geobasisinformation Brandenburg)
	Ground sampling distance: 0.2 m resampled to 1 m	
	Number of bands: 4 (red, green, blue, near-infrared)
	Data: 9000x9000x4 (Byte)
	Copyrights:
		GeoBasis-DE/LGB, dl-de/by-2-0 and
		Geoportal Berlin, dl-de/by-2-0 (data modified)
		Also see https://geobroker.geobasis-bb.de/gbss.php?MODE=GetProductInformation&PRODUCTID=253b7d3d-6b42-47dc-b127-682de078b7ae


3. landcover_potsdam_polygon.gpkg
	Land cover reference polygons derived from the aerial imagery described above.
	Number of polygons: 9677
	Level 1 classes: Impervious, Vegetation, Soil, Water
	Level 2 classes: Impervious, Low Vegetation, Soil, Tree, Water
	Level 3 classes: Roof, Pavement, Low Vegetation, Soil, Tree, Water


4. landcover_potsdam_point.gpkg
	Land cover reference points derived from the aerial imagery described above.	
	Number of points: 120
	Level 1 classes: Impervious, Vegetation, Soil, Water
	Level 2 classes: Impervious, Low Vegetation, Soil, Tree, Water

