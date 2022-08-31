<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" labelsEnabled="0" simplifyMaxScale="1" version="3.24.0-Tisler" maxScale="0" simplifyLocal="1" symbologyReferenceScale="-1" simplifyDrawingHints="1" minScale="100000000" simplifyDrawingTol="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal startExpression="" endExpression="" durationField="" enabled="0" endField="" durationUnit="min" startField="" limitMode="0" fixedDuration="0" accumulate="0" mode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 forceraster="0" type="singleSymbol" symbollevels="0" enableorderby="0" referencescale="-1">
    <symbols>
      <symbol alpha="1" name="0" force_rhr="0" type="marker" clip_to_extent="1">
        <data_defined_properties>
          <Option type="Map">
            <Option name="name" type="QString" value=""/>
            <Option name="properties"/>
            <Option name="type" type="QString" value="collection"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <Option type="Map">
            <Option name="angle" type="QString" value="0"/>
            <Option name="cap_style" type="QString" value="square"/>
            <Option name="color" type="QString" value="145,82,45,255"/>
            <Option name="horizontal_anchor_point" type="QString" value="1"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="name" type="QString" value="circle"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="outline_color" type="QString" value="35,35,35,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0"/>
            <Option name="outline_width_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="scale_method" type="QString" value="diameter"/>
            <Option name="size" type="QString" value="2"/>
            <Option name="size_map_unit_scale" type="QString" value="3x:0,0,0,0,0,0"/>
            <Option name="size_unit" type="QString" value="MM"/>
            <Option name="vertical_anchor_point" type="QString" value="1"/>
          </Option>
          <prop k="angle" v="0"/>
          <prop k="cap_style" v="square"/>
          <prop k="color" v="145,82,45,255"/>
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
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <Option/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks type="StringList">
      <Option type="QString" value=""/>
    </activeChecks>
    <checkConfiguration/>
  </geometryOptions>
  <legend showLabelLegend="0" type="default-vector"/>
  <referencedLayers/>
  <fieldConfiguration>
    <field name="fid" configurationFlags="None">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="name" configurationFlags="None">
      <editWidget type="">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="profiles" configurationFlags="None">
      <editWidget type="SpectralProfile">
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
    <alias name="" index="0" field="fid"/>
    <alias name="" index="1" field="name"/>
    <alias name="" index="2" field="profiles"/>
    <alias name="" index="3" field="roof"/>
    <alias name="" index="4" field="pavement"/>
    <alias name="" index="5" field="low vegetation"/>
    <alias name="" index="6" field="tree"/>
    <alias name="" index="7" field="soil"/>
    <alias name="" index="8" field="water"/>
  </aliases>
  <defaults>
    <default expression="" field="fid" applyOnUpdate="0"/>
    <default expression="" field="name" applyOnUpdate="0"/>
    <default expression="" field="profiles" applyOnUpdate="0"/>
    <default expression="" field="roof" applyOnUpdate="0"/>
    <default expression="" field="pavement" applyOnUpdate="0"/>
    <default expression="" field="low vegetation" applyOnUpdate="0"/>
    <default expression="" field="tree" applyOnUpdate="0"/>
    <default expression="" field="soil" applyOnUpdate="0"/>
    <default expression="" field="water" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint exp_strength="0" unique_strength="1" notnull_strength="1" field="fid" constraints="3"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="name" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="profiles" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="roof" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="pavement" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="low vegetation" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="tree" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="soil" constraints="0"/>
    <constraint exp_strength="0" unique_strength="0" notnull_strength="0" field="water" constraints="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="fid" exp="" desc=""/>
    <constraint field="name" exp="" desc=""/>
    <constraint field="profiles" exp="" desc=""/>
    <constraint field="roof" exp="" desc=""/>
    <constraint field="pavement" exp="" desc=""/>
    <constraint field="low vegetation" exp="" desc=""/>
    <constraint field="tree" exp="" desc=""/>
    <constraint field="soil" exp="" desc=""/>
    <constraint field="water" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions/>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns/>
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
  <editforminitcode><![CDATA[]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable/>
  <labelOnTop/>
  <reuseLastValue/>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression></previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
