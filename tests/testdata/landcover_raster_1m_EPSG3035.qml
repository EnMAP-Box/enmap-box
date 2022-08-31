<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" version="3.14.16-Pi" maxScale="0" styleCategories="AllStyleCategories" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal enabled="0" mode="0" fetchMode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <rasterrenderer alphaBand="-1" band="1" nodataColor="" opacity="1" type="paletted">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry label="roof" color="#e60000" value="1" alpha="255"/>
        <paletteEntry label="pavement" color="#9c9c9c" value="2" alpha="255"/>
        <paletteEntry label="low vegetation" color="#98e600" value="3" alpha="255"/>
        <paletteEntry label="tree" color="#267300" value="4" alpha="255"/>
        <paletteEntry label="soil" color="#a87000" value="5" alpha="255"/>
        <paletteEntry label="water" color="#0064ff" value="6" alpha="255"/>
      </colorPalette>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeOn="0" colorizeRed="255" colorizeStrength="100" saturation="0" grayscaleMode="0" colorizeBlue="128" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
