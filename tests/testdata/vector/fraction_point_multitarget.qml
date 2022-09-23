<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" minScale="100000000" symbologyReferenceScale="-1" readOnly="0" version="3.24.0-Tisler" labelsEnabled="0" simplifyDrawingHints="0" simplifyAlgorithm="0" maxScale="0" simplifyDrawingTol="1" styleCategories="AllStyleCategories" simplifyLocal="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal mode="0" endExpression="" limitMode="0" durationField="" durationUnit="min" startField="" endField="" fixedDuration="0" enabled="0" accumulate="0" startExpression="">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 referencescale="-1" enableorderby="0" type="singleSymbol" symbollevels="0" forceraster="0">
    <symbols>
      <symbol type="marker" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer pass="0" class="SimpleMarker" locked="0" enabled="1">
          <Option type="Map">
            <Option value="0" type="QString" name="angle"/>
            <Option value="square" type="QString" name="cap_style"/>
            <Option value="255,255,3,255" type="QString" name="color"/>
            <Option value="1" type="QString" name="horizontal_anchor_point"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="circle" type="QString" name="name"/>
            <Option value="0,0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="35,35,35,255" type="QString" name="outline_color"/>
            <Option value="solid" type="QString" name="outline_style"/>
            <Option value="0" type="QString" name="outline_width"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
            <Option value="MM" type="QString" name="outline_width_unit"/>
            <Option value="diameter" type="QString" name="scale_method"/>
            <Option value="2" type="QString" name="size"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
            <Option value="MM" type="QString" name="size_unit"/>
            <Option value="1" type="QString" name="vertical_anchor_point"/>
          </Option>
          <prop k="angle" v="0"/>
          <prop k="cap_style" v="square"/>
          <prop k="color" v="255,255,3,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <Option type="Map">
      <Option type="List" name="dualview/previewExpressions">
        <Option value="&quot;fid&quot;" type="QString"/>
      </Option>
      <Option value="0" type="int" name="embeddedWidgets/count"/>
      <Option name="variableNames"/>
      <Option name="variableValues"/>
    </Option>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Text">
    <DiagramCategory lineSizeScale="3x:0,0,0,0,0,0" spacingUnitScale="3x:0,0,0,0,0,0" backgroundAlpha="0" scaleBasedVisibility="0" spacingUnit="MM" sizeType="MapUnit" labelPlacementMethod="XHeight" lineSizeType="MM" maxScaleDenominator="1e+08" scaleDependency="Area" minScaleDenominator="0" width="60" opacity="1" penColor="#000000" direction="0" spacing="5" height="60" diagramOrientation="Up" minimumSize="0" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" barWidth="5" enabled="1" rotationOffset="270" showAxis="1" penWidth="0" penAlpha="0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
      <attribute color="#e60000" field="&quot;roof&quot;" label="roof"/>
      <attribute color="#9c9c9c" field="&quot;pavement&quot;" label="pavement"/>
      <attribute color="#98e600" field="&quot;low vegetation&quot;" label="low vegetation"/>
      <attribute color="#267300" field="&quot;tree&quot;" label="tree"/>
      <attribute color="#a87000" field="&quot;soil&quot;" label="soil"/>
      <attribute color="#0064ff" field="&quot;water&quot;" label="water"/>
      <axisSymbol>
        <symbol type="line" name="" alpha="1" clip_to_extent="1" force_rhr="0">
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <layer pass="0" class="SimpleLine" locked="0" enabled="1">
            <Option type="Map">
              <Option value="0" type="QString" name="align_dash_pattern"/>
              <Option value="square" type="QString" name="capstyle"/>
              <Option value="5;2" type="QString" name="customdash"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
              <Option value="MM" type="QString" name="customdash_unit"/>
              <Option value="0" type="QString" name="dash_pattern_offset"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
              <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
              <Option value="0" type="QString" name="draw_inside_polygon"/>
              <Option value="bevel" type="QString" name="joinstyle"/>
              <Option value="35,35,35,255" type="QString" name="line_color"/>
              <Option value="solid" type="QString" name="line_style"/>
              <Option value="0.26" type="QString" name="line_width"/>
              <Option value="MM" type="QString" name="line_width_unit"/>
              <Option value="0" type="QString" name="offset"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
              <Option value="MM" type="QString" name="offset_unit"/>
              <Option value="0" type="QString" name="ring_filter"/>
              <Option value="0" type="QString" name="trim_distance_end"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
              <Option value="MM" type="QString" name="trim_distance_end_unit"/>
              <Option value="0" type="QString" name="trim_distance_start"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
              <Option value="MM" type="QString" name="trim_distance_start_unit"/>
              <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
              <Option value="0" type="QString" name="use_custom_dash"/>
              <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
            </Option>
            <prop k="align_dash_pattern" v="0"/>
            <prop k="capstyle" v="square"/>
            <prop k="customdash" v="5;2"/>
            <prop k="customdash_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="customdash_unit" v="MM"/>
            <prop k="dash_pattern_offset" v="0"/>
            <prop k="dash_pattern_offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="dash_pattern_offset_unit" v="MM"/>
            <prop k="draw_inside_polygon" v="0"/>
            <prop k="joinstyle" v="bevel"/>
            <prop k="line_color" v="35,35,35,255"/>
            <prop k="line_style" v="solid"/>
            <prop k="line_width" v="0.26"/>
            <prop k="line_width_unit" v="MM"/>
            <prop k="offset" v="0"/>
            <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="offset_unit" v="MM"/>
            <prop k="ring_filter" v="0"/>
            <prop k="trim_distance_end" v="0"/>
            <prop k="trim_distance_end_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="trim_distance_end_unit" v="MM"/>
            <prop k="trim_distance_start" v="0"/>
            <prop k="trim_distance_start_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <prop k="trim_distance_start_unit" v="MM"/>
            <prop k="tweak_dash_pattern_on_corners" v="0"/>
            <prop k="use_custom_dash" v="0"/>
            <prop k="width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
      <effect type="effectStack" enabled="1">
        <effect type="dropShadow">
          <Option type="Map">
            <Option value="13" type="QString" name="blend_mode"/>
            <Option value="2.645" type="QString" name="blur_level"/>
            <Option value="MM" type="QString" name="blur_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="blur_unit_scale"/>
            <Option value="0,0,0,255" type="QString" name="color"/>
            <Option value="2" type="QString" name="draw_mode"/>
            <Option value="1" type="QString" name="enabled"/>
            <Option value="135" type="QString" name="offset_angle"/>
            <Option value="2" type="QString" name="offset_distance"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_unit_scale"/>
            <Option value="1" type="QString" name="opacity"/>
          </Option>
          <prop k="blend_mode" v="13"/>
          <prop k="blur_level" v="2.645"/>
          <prop k="blur_unit" v="MM"/>
          <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="draw_mode" v="2"/>
          <prop k="enabled" v="1"/>
          <prop k="offset_angle" v="135"/>
          <prop k="offset_distance" v="2"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="opacity" v="1"/>
        </effect>
        <effect type="outerGlow">
          <Option type="Map">
            <Option value="0" type="QString" name="blend_mode"/>
            <Option value="2.645" type="QString" name="blur_level"/>
            <Option value="MM" type="QString" name="blur_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="blur_unit_scale"/>
            <Option value="69,116,40,255" type="QString" name="color1"/>
            <Option value="188,220,60,255" type="QString" name="color2"/>
            <Option value="0" type="QString" name="color_type"/>
            <Option value="ccw" type="QString" name="direction"/>
            <Option value="0" type="QString" name="discrete"/>
            <Option value="2" type="QString" name="draw_mode"/>
            <Option value="0" type="QString" name="enabled"/>
            <Option value="0.5" type="QString" name="opacity"/>
            <Option value="gradient" type="QString" name="rampType"/>
            <Option value="255,255,255,255" type="QString" name="single_color"/>
            <Option value="rgb" type="QString" name="spec"/>
            <Option value="2" type="QString" name="spread"/>
            <Option value="MM" type="QString" name="spread_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="spread_unit_scale"/>
          </Option>
          <prop k="blend_mode" v="0"/>
          <prop k="blur_level" v="2.645"/>
          <prop k="blur_unit" v="MM"/>
          <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color1" v="69,116,40,255"/>
          <prop k="color2" v="188,220,60,255"/>
          <prop k="color_type" v="0"/>
          <prop k="direction" v="ccw"/>
          <prop k="discrete" v="0"/>
          <prop k="draw_mode" v="2"/>
          <prop k="enabled" v="0"/>
          <prop k="opacity" v="0.5"/>
          <prop k="rampType" v="gradient"/>
          <prop k="single_color" v="255,255,255,255"/>
          <prop k="spec" v="rgb"/>
          <prop k="spread" v="2"/>
          <prop k="spread_unit" v="MM"/>
          <prop k="spread_unit_scale" v="3x:0,0,0,0,0,0"/>
        </effect>
        <effect type="drawSource">
          <Option type="Map">
            <Option value="0" type="QString" name="blend_mode"/>
            <Option value="2" type="QString" name="draw_mode"/>
            <Option value="1" type="QString" name="enabled"/>
            <Option value="1" type="QString" name="opacity"/>
          </Option>
          <prop k="blend_mode" v="0"/>
          <prop k="draw_mode" v="2"/>
          <prop k="enabled" v="1"/>
          <prop k="opacity" v="1"/>
        </effect>
        <effect type="innerShadow">
          <Option type="Map">
            <Option value="13" type="QString" name="blend_mode"/>
            <Option value="2.645" type="QString" name="blur_level"/>
            <Option value="MM" type="QString" name="blur_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="blur_unit_scale"/>
            <Option value="0,0,0,255" type="QString" name="color"/>
            <Option value="2" type="QString" name="draw_mode"/>
            <Option value="0" type="QString" name="enabled"/>
            <Option value="135" type="QString" name="offset_angle"/>
            <Option value="2" type="QString" name="offset_distance"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_unit_scale"/>
            <Option value="1" type="QString" name="opacity"/>
          </Option>
          <prop k="blend_mode" v="13"/>
          <prop k="blur_level" v="2.645"/>
          <prop k="blur_unit" v="MM"/>
          <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="draw_mode" v="2"/>
          <prop k="enabled" v="0"/>
          <prop k="offset_angle" v="135"/>
          <prop k="offset_distance" v="2"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="opacity" v="1"/>
        </effect>
        <effect type="innerGlow">
          <Option type="Map">
            <Option value="0" type="QString" name="blend_mode"/>
            <Option value="2.645" type="QString" name="blur_level"/>
            <Option value="MM" type="QString" name="blur_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="blur_unit_scale"/>
            <Option value="69,116,40,255" type="QString" name="color1"/>
            <Option value="188,220,60,255" type="QString" name="color2"/>
            <Option value="0" type="QString" name="color_type"/>
            <Option value="ccw" type="QString" name="direction"/>
            <Option value="0" type="QString" name="discrete"/>
            <Option value="2" type="QString" name="draw_mode"/>
            <Option value="0" type="QString" name="enabled"/>
            <Option value="0.5" type="QString" name="opacity"/>
            <Option value="gradient" type="QString" name="rampType"/>
            <Option value="255,255,255,255" type="QString" name="single_color"/>
            <Option value="rgb" type="QString" name="spec"/>
            <Option value="2" type="QString" name="spread"/>
            <Option value="MM" type="QString" name="spread_unit"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="spread_unit_scale"/>
          </Option>
          <prop k="blend_mode" v="0"/>
          <prop k="blur_level" v="2.645"/>
          <prop k="blur_unit" v="MM"/>
          <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color1" v="69,116,40,255"/>
          <prop k="color2" v="188,220,60,255"/>
          <prop k="color_type" v="0"/>
          <prop k="direction" v="ccw"/>
          <prop k="discrete" v="0"/>
          <prop k="draw_mode" v="2"/>
          <prop k="enabled" v="0"/>
          <prop k="opacity" v="0.5"/>
          <prop k="rampType" v="gradient"/>
          <prop k="single_color" v="255,255,255,255"/>
          <prop k="spec" v="rgb"/>
          <prop k="spread" v="2"/>
          <prop k="spread_unit" v="MM"/>
          <prop k="spread_unit_scale" v="3x:0,0,0,0,0,0"/>
        </effect>
      </effect>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" linePlacementFlags="18" zIndex="0" priority="0" dist="0" showAll="1" placement="1">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <legend showLabelLegend="0" type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field name="fid" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="roof" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="pavement" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="low vegetation" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="tree" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="soil" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="water" configurationFlags="None">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="fid" index="0" name=""/>
    <alias field="roof" index="1" name=""/>
    <alias field="pavement" index="2" name=""/>
    <alias field="low vegetation" index="3" name=""/>
    <alias field="tree" index="4" name=""/>
    <alias field="soil" index="5" name=""/>
    <alias field="water" index="6" name=""/>
  </aliases>
  <defaults>
    <default applyOnUpdate="0" expression="" field="fid"/>
    <default applyOnUpdate="0" expression="" field="roof"/>
    <default applyOnUpdate="0" expression="" field="pavement"/>
    <default applyOnUpdate="0" expression="" field="low vegetation"/>
    <default applyOnUpdate="0" expression="" field="tree"/>
    <default applyOnUpdate="0" expression="" field="soil"/>
    <default applyOnUpdate="0" expression="" field="water"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" constraints="3" unique_strength="1" field="fid" notnull_strength="1"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" field="roof" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" field="pavement" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" field="low vegetation" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" field="tree" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" field="soil" notnull_strength="0"/>
    <constraint exp_strength="0" constraints="0" unique_strength="0" field="water" notnull_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" desc="" field="fid"/>
    <constraint exp="" desc="" field="roof"/>
    <constraint exp="" desc="" field="pavement"/>
    <constraint exp="" desc="" field="low vegetation"/>
    <constraint exp="" desc="" field="tree"/>
    <constraint exp="" desc="" field="soil"/>
    <constraint exp="" desc="" field="water"/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="&quot;fid&quot;">
    <columns>
      <column type="field" name="fid" hidden="0" width="-1"/>
      <column type="field" name="roof" hidden="0" width="-1"/>
      <column type="field" name="pavement" hidden="0" width="-1"/>
      <column type="field" name="low vegetation" hidden="0" width="-1"/>
      <column type="field" name="tree" hidden="0" width="-1"/>
      <column type="field" name="soil" hidden="0" width="-1"/>
      <column type="field" name="water" hidden="0" width="-1"/>
      <column type="actions" hidden="1" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
    geom = feature.geometry()
    control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="fid"/>
    <field editable="1" name="low vegetation"/>
    <field editable="1" name="pavement"/>
    <field editable="1" name="roof"/>
    <field editable="1" name="soil"/>
    <field editable="1" name="tree"/>
    <field editable="1" name="water"/>
  </editable>
  <labelOnTop>
    <field name="fid" labelOnTop="0"/>
    <field name="low vegetation" labelOnTop="0"/>
    <field name="pavement" labelOnTop="0"/>
    <field name="roof" labelOnTop="0"/>
    <field name="soil" labelOnTop="0"/>
    <field name="tree" labelOnTop="0"/>
    <field name="water" labelOnTop="0"/>
  </labelOnTop>
  <reuseLastValue>
    <field reuseLastValue="0" name="fid"/>
    <field reuseLastValue="0" name="low vegetation"/>
    <field reuseLastValue="0" name="pavement"/>
    <field reuseLastValue="0" name="roof"/>
    <field reuseLastValue="0" name="soil"/>
    <field reuseLastValue="0" name="tree"/>
    <field reuseLastValue="0" name="water"/>
  </reuseLastValue>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"fid"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
