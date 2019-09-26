<!--
    Geodata@Wisconsin - Transformation from ISO 19139 XML into GeoBlacklight Solr json
    September 2019
	 
    Based on the work of the Big Ten Academic Alliance Geoportal
	 
-->
<xsl:stylesheet 
	xmlns="http://www.loc.gov/mods/v3" 
	xmlns:gco="http://www.isotc211.org/2005/gco"
	xmlns:gmi="http://www.isotc211.org/2005/gmi" 
	xmlns:gmd="http://www.isotc211.org/2005/gmd"
	xmlns:gml="http://www.opengis.net/gml" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	version="2.0" exclude-result-prefixes="gml gmd gco gmi xsl">
	
	<xsl:output method="text" version="1.0" omit-xml-declaration="yes" indent="no" media-type="application/json"/>
	<xsl:strip-space elements="*"/>

  <!-- template used for converting strings to Title Case -->
  <xsl:template name="TitleCase">
    <xsl:param name="text" /> 
    <xsl:param name="lastletter" select="' '"/>
    <xsl:if test="$text">
      <xsl:variable name="thisletter" select="substring($text,1,1)"/>
      <xsl:choose>
        <xsl:when test="$lastletter=' '">
          <xsl:value-of select="translate($thisletter,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ')"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$thisletter"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:call-template name="TitleCase">
        <xsl:with-param name="text" select="substring($text,2)"/>
        <xsl:with-param name="lastletter" select="$thisletter"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

<!-- Template to strip double-quotes, escape characters, and extra line feeds.  Spaces are also normalized to futher clean
up the specified text -->
<xsl:template name="ScrubText">
    <xsl:param name="text" />
    <!-- some standardized constants -->
    <xsl:variable name="vQ">"</xsl:variable>
    <xsl:variable name="sQ">'</xsl:variable>
    <xsl:variable name="escapeChar">\</xsl:variable>
    <xsl:value-of select="normalize-space(translate(translate(translate($text, $vQ, $sQ),$escapeChar,' '),'&#xA;',''))"/>
  </xsl:template>
  
<xsl:template match="/">

<!-- set location of online web-accessible archive location for all ISO metadata records -->
<xsl:variable name="metadataBaseURL">https://gisdata.wisc.edu/public/metadata/</xsl:variable>

<!-- construct metadata file name from xml input file -->
<xsl:variable name="metadataFile"> 
   <xsl:value-of select="tokenize(base-uri(),'/')[last()]"/>
</xsl:variable>

  <!-- Format Variables -->
<xsl:variable name="format">
      <xsl:choose>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Raster Dataset')">
          <xsl:text>Raster Dataset</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'GeoTIFF')">
          <xsl:text>GeoTIFF</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'TIFF')">
          <xsl:text>TIFF</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'JPEG')">
          <xsl:text>JPEG</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Arc')">
          <xsl:text>ArcGRID</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'ArcGRID')">
          <xsl:text>ArcGRID</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Shapefile')">
          <xsl:text>Shapefile</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'shapefile')">
          <xsl:text>Shapefile</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'KMZ')">
          <xsl:text>KMZ</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Geodatabase')">
          <xsl:text>Geodatabase</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Feature Class')">
          <xsl:text>Feature Class</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Text')">
          <xsl:text>Text</xsl:text>
        </xsl:when>
        <xsl:when
          test="contains(gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:distributionFormat/gmd:MD_Format/gmd:name, 'Mixed')">
          <xsl:text>Mixed</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>File</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
</xsl:variable>

<!-- Extract unique dataset ID -->    
<xsl:variable name="uuid">
    <xsl:value-of select="gmd:MD_Metadata/gmd:fileIdentifier"/>
</xsl:variable>

<!-- Extract supplemental information -->    
<xsl:variable name="supplemental">
    <xsl:value-of select="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:supplementalInformation"/>
</xsl:variable>

<!-- Start of JSON output -->
<xsl:text>{&#xa;</xsl:text>

    <!-- Schema Version - Indicates which version of the GeoBlacklight schema is in use. -->
	<xsl:text>"geoblacklight_version": "1.0",&#xa;</xsl:text>
	
    <!-- Unique Identifier - Unique identifier for layer as a URI. It should be globally unique across all institutions, assumed not to be end-user visible	-->
	<xsl:text>"dc_identifier_s": "</xsl:text>
        <xsl:value-of select="$uuid"/>
        <xsl:text>",&#xa;</xsl:text>

    <!-- Title - The name of the resource -->
	<xsl:text>"dc_title_s": "</xsl:text>
        <xsl:value-of select="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title"/>
        <xsl:text>",&#xa;</xsl:text>

	<!-- Description -->
    <xsl:text>"dc_description_s": "</xsl:text>           
        <xsl:call-template name="ScrubText">
            <xsl:with-param name="text" select="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract"/>
        </xsl:call-template>    
        <xsl:text>",&#xa;</xsl:text>

    <!-- Rights - Always public for GeoData@WI -->	 
	<xsl:text>"dc_rights_s": "</xsl:text>
        <xsl:text>Public",&#xa;</xsl:text>
	
    <!-- Provenance - The name of the organization that holds the resource -->
	<xsl:text>"dct_provenance_s": "</xsl:text>
        <xsl:text>UW-Madison Robinson Map Library",&#xa;</xsl:text>

	<!-- Layer ID - This indicates the layer id for any WMS or WFS web services listed in the dct_references_s field -->
	<xsl:text>"layer_id_s": "</xsl:text>
        <xsl:value-of select="gmd:MD_Metadata/gmd:dataSetURI"/>
        <xsl:text>",&#xa;</xsl:text> 

	<!-- Layer Slug - This is a string appended to the base URL of a GeoBlacklight installation to create a unique landing page for each resource. It is visible to the user and is used for Permalinks. -->
    <xsl:text>"layer_slug_s": "</xsl:text>
        <xsl:value-of select="$uuid"/>
        <xsl:text>",&#xa;</xsl:text>

	<!-- Geometry Type
	This shows up as Data type in GeoBlacklight and each value has an associated icon. It differentiates between vector types (point, line, polygon, etc.) and raster types (raster data, image, paper map)
	
	**** this needs more work, not sure about code types -->
	<xsl:text>"layer_geom_type_s": "</xsl:text>
		<xsl:choose>
          <xsl:when test="gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects[1]/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode[@codeListValue='composite']">
              <xsl:text>Polygon</xsl:text>
          </xsl:when>
          <xsl:when test="contains(gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects[1]/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode, 'composite')">
              <xsl:text>Polygon</xsl:text>
          </xsl:when>
          <xsl:when test="gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects[1]/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode[@codeListValue='curve']">
              <xsl:text>Line</xsl:text>
          </xsl:when>
          <xsl:when test="contains(gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects[1]/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode, 'curve')">
              <xsl:text>Line</xsl:text>
          </xsl:when>
          <xsl:when test="gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects[1]/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode[@codeListValue='point']">
              <xsl:text>Point</xsl:text>
          </xsl:when>   
          <xsl:when test="contains(gmd:MD_Metadata/gmd:spatialRepresentationInfo/gmd:MD_VectorSpatialRepresentation/gmd:geometricObjects[1]/gmd:MD_GeometricObjects/gmd:geometricObjectType/gmd:MD_GeometricObjectTypeCode, 'point')">
              <xsl:text>Point</xsl:text>
          </xsl:when>
          <xsl:when test="contains(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode, 'grid')">
              <xsl:text>Raster</xsl:text>
          </xsl:when>         
      </xsl:choose>
	<xsl:text>",&#xa;</xsl:text>

	<!-- Modified Date - Last modification date for the metadata record.  Not used for GeoData@WI -->
    <xsl:text>"layer_modified_dt": "",&#xa;</xsl:text>

	<!-- Dataset Format  -	This indicates the file format of the data. If a download link is included, this value shows up on the item page display in the download widget.
	-->
    <xsl:text>"dc_format_s": "</xsl:text>
        <xsl:value-of select="$format"/>
        <xsl:text>",&#xa;</xsl:text>

    <!-- Language - Indicates the language of the data or map -->
	<xsl:text>"dc_language_s": "</xsl:text>
        <xsl:text>English",&#xa;</xsl:text>

	<!-- Is Part Of
	aka, collection names assigned to the dataset
    Jaime enters collection names in a single field in ArcCatalog, separated by commas.  These collections end up in ISO field collectiveTitle.
	--> 
    <xsl:variable name="collections" select="tokenize(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:collectiveTitle,',')"></xsl:variable>
    <xsl:text>"dct_isPartOf_sm": [</xsl:text>
    <xsl:for-each
    select="$collections">
        <xsl:text>"</xsl:text>
        <xsl:call-template name="TitleCase">
            <xsl:with-param name="text" select="normalize-space(.)"/>
        </xsl:call-template>
        <xsl:text>"</xsl:text>
        <xsl:if test="position() != last()">
            <xsl:text>,</xsl:text>
        </xsl:if>
    </xsl:for-each>
    <xsl:text>],&#xa;</xsl:text> 	
  
    <!-- Source - This is used for parent/child relationships and activates the Data Relations widget in GeoBlacklight.-->
    <xsl:choose>
      <xsl:when test="gmd:MD_Metadata/gmd:parentIdentifier">
        <xsl:text>"dc_source_sm": "</xsl:text>
        <xsl:value-of select="gmd:MD_Metadata/gmd:parentIdentifier"/>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>
    </xsl:choose>

    <!-- Creator - The person(s) or organization that created the resource -->
      <xsl:text>"dc_creator_sm": [</xsl:text>

      <xsl:for-each
        select="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/gmd:CI_ResponsibleParty/gmd:role/gmd:CI_RoleCode[@codeListValue = 'originator']">
        <xsl:choose>
          <xsl:when
            test="ancestor-or-self::*/gmd:organisationName and not(ancestor-or-self::*/gmd:individualName)">
            <xsl:text>"</xsl:text>
            <xsl:value-of select="ancestor-or-self::*/gmd:organisationName"/>
            <xsl:text>"</xsl:text>
            <xsl:if test="position() != last()">
              <xsl:text>,</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:when
            test="ancestor-or-self::*/gmd:individualName and not(ancestor-or-self::*/gmd:organisationName)">
            <xsl:for-each select="ancestor-or-self::*/gmd:individualName">
              <xsl:text>"</xsl:text>
              <xsl:value-of select="ancestor-or-self::*/gmd:individualName"/>
              <xsl:text>"</xsl:text>
              <xsl:if test="position() != last()">
                <xsl:text>,</xsl:text>
              </xsl:if>
            </xsl:for-each>
          </xsl:when>
          <xsl:when
            test="ancestor-or-self::*/gmd:individualName and ancestor-or-self::*/gmd:organisationName">
            <xsl:text>"</xsl:text>
            <xsl:value-of select="ancestor-or-self::*/gmd:individualName"/>
            <xsl:text>", </xsl:text>
            <xsl:text>"</xsl:text>
            <xsl:value-of select="ancestor-or-self::*/gmd:organisationName"/>
            <xsl:text>"</xsl:text>
          </xsl:when>
        </xsl:choose>
        <!--<xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>-->
      </xsl:for-each>
      <xsl:text>],&#xa;</xsl:text>
    
	<!-- Publisher - Not used by GeoData@WI	-->
    <xsl:text>"dc_publisher_sm": "",&#xa;</xsl:text>

    <!-- from DCMI type vocabulary 
	This is a general element to indicate the larger genre of the resource.
	-->
    <xsl:choose>
      <xsl:when
        test="contains(gmd:MD_Metadata/gmd:hierarchyLevelName/gco:CharacterString, 'dataset')">
        <xsl:text>"dc_type_s": "Dataset",&#xa;</xsl:text>
      </xsl:when>

      <xsl:when
        test="contains(gmd:MD_Metadata/gmd:hierarchyLevelName/gco:CharacterString, 'Dataset')">
        <xsl:text>"dc_type_s": "Dataset",&#xa;</xsl:text>
      </xsl:when>

      <xsl:when
        test="contains(gmd:MD_Metadata/gmd:hierarchyLevelName/gco:CharacterString, 'service')">
        <xsl:text>"dc_type_s": "Service",&#xa;</xsl:text>
      </xsl:when>

      <xsl:when
        test="contains(gmd:MD_Metadata/gmd:hierarchyLevelName/gco:CharacterString, 'Service')">
        <xsl:text>"dc_type_s": "Service",&#xa;</xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:text>"dc_type_s": "Dataset",&#xa;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>

    <!-- Subject - ISO Category only -->
    <xsl:text>"dc_subject_sm": [</xsl:text>
    <xsl:if
      test="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory/gmd:MD_TopicCategoryCode">
      
      <xsl:for-each
        select="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:topicCategory">

        <xsl:choose>
          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'biota')">
            <xsl:text>"Biota"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'boundaries')">
            <xsl:text>"Boundaries"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'climatologyMeteorologyAtmosphere')">
            <xsl:text>"Climatology, Meteorology and Atmosphere"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'economy')">
            <xsl:text>"Economy"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'elevation')">
            <xsl:text>"Elevation"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'environment')">
            <xsl:text>"Environment"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'farming')">
            <xsl:text>"Farming"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'geoscientificInformation')">
            <xsl:text>"Geoscientific Information"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'health')">
            <xsl:text>"Health"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'imageryBaseMapsEarthCover')">
            <xsl:text>"Imagery and Base Maps"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'Imagery base maps earth cover')">
            <xsl:text>"Imagery and Base Maps"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'inlandWaters')">
            <xsl:text>"Inland Waters"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'Inland waters')">
            <xsl:text>"Inland Waters"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'intelligenceMilitary')">
            <xsl:text>"Intelligence and Military"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'location')">
            <xsl:text>"Location"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'oceans')">
            <xsl:text>"Oceans"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'planningCadastre')">
            <xsl:text>"Planning and Cadastral"</xsl:text>
          </xsl:when>
 
          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'society')">
            <xsl:text>"Society"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'structure')">
            <xsl:text>"Structure"</xsl:text>
          </xsl:when>
 
          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'transportation')">
            <xsl:text>"Transportation"</xsl:text>
          </xsl:when>

          <xsl:when test="contains(gmd:MD_TopicCategoryCode, 'utilitiesCommunication')">
            <xsl:text>"Utilities and Communication"</xsl:text>
          </xsl:when>
        </xsl:choose>

        <xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>
      </xsl:for-each>
    </xsl:if>
    <xsl:text>],&#xa;</xsl:text>


    <!-- Spatial Coverage - Not used -->
    <xsl:text>"dct_spatial_sm": [],&#xa;</xsl:text>


	<!-- Date Issued - We don't use dct_issued_s, aka date of the metadata record. -->
    <xsl:text>"dct_issued_s": "",&#xa;</xsl:text>

	<!-- Temporal Coverage
	This represents the "Ground Condition" of the resource, meaning the time period data was collected or is intended to represent. Displays on the item page in the Year value.
	-->
    <!-- content date: range YYYY-YYYY if dates differ  -->
    <xsl:choose>
      <xsl:when
        test="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition/text() != ''">
        <xsl:text>"dct_temporal_sm": ["</xsl:text>
        <xsl:value-of
          select="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition, 1, 4)"/>
        <xsl:if
          test="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition, 1, 4) != substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition, 1, 4)">
          <xsl:text>-</xsl:text>
          <xsl:value-of
            select="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition, 1, 4)"
          />
        </xsl:if>
        <xsl:text>"],&#xa;</xsl:text>
      </xsl:when>

      <xsl:when
        test="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant">
        <xsl:text>"dct_temporal_sm": ["</xsl:text>
        <xsl:value-of
          select="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition, 1, 4)"/>
        <xsl:text>"],&#xa;</xsl:text>
      </xsl:when>
    </xsl:choose>
  
    <!-- Solr Year
	This is an integer field in the form YYYY that is used for indexing in the Year & Time Period facets.  
	Uses same data as temporal coverage per Jaime
	-->

    <xsl:choose>
        <xsl:when
      test="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition/text() != ''">
      <xsl:text>"solr_year_i": ["</xsl:text>
      <xsl:value-of
        select="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition, 1, 4)"/>
      <xsl:if
        test="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition, 1, 4) != substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition, 1, 4)">
        <xsl:text>-</xsl:text>
        <xsl:value-of
          select="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition, 1, 4)"
        />
      </xsl:if>
      <xsl:text>"],&#xa;</xsl:text>
    </xsl:when>
    
       <xsl:when
      test="gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant">
      <xsl:text>"solr_year_i": ["</xsl:text>
      <xsl:value-of
        select="substring(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent[1]/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition, 1, 4)"/>
      <xsl:text>"],&#xa;</xsl:text>
    </xsl:when>
  </xsl:choose>
  

    <!-- References 
	This element is a hash of key/value pairs for different types of external links. It external services and references using the CatInterOp approach.
	-->
    <xsl:text>"dct_references_s": "{</xsl:text>

    <xsl:for-each select="//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource">
      <xsl:choose>
        <xsl:when
          test="gmd:protocol/gco:CharacterString/text() = 'ESRI:ArcGIS'">
          <!-- TODO test url for which reference to utilize -->
          <xsl:choose>
            <xsl:when test="contains(gmd:linkage/gmd:URL, 'FeatureServer')">
              <xsl:text>\"urn:x-esri:serviceType:ArcGIS#FeatureLayer\":\"</xsl:text>
            </xsl:when>

            <xsl:when test="contains(gmd:linkage/gmd:URL, 'MapServer')">
              <xsl:text>\"urn:x-esri:serviceType:ArcGIS#DynamicMapLayer\":\"</xsl:text>
            </xsl:when>

            <xsl:when test="contains(gmd:linkage/gmd:URL, 'ImageServer')">
              <xsl:text>\"urn:x-esri:serviceType:ArcGIS#ImageMapLayer\":\"</xsl:text>
            </xsl:when>
          </xsl:choose>

          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'download')">
          <xsl:text>\"http://schema.org/downloadUrl\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'WWW:LINK')">
          <xsl:text>\"http://schema.org/url\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <!-- Note: there is an untraceable bug that results in some protocols being listed as "WW:LINK-1.0..." instead of "WWW:LINK-1.0... -->
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'WW:LINK')">
          <xsl:text>\"http://schema.org/url\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'WWW:IIIF')">
          <xsl:text>\"http://iiif.io/api/image\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'WMS')">
          <xsl:text>\"http://www.opengis.net/def/serviceType/ogc/wms\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'WFS')">
          <xsl:text>\"http://www.opengis.net/def/serviceType/ogc/wfs\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:when test="contains(gmd:protocol/gco:CharacterString/text(), 'metadata')">
          <xsl:text>\"http://www.opengis.net/cat/csw/csdgm\":\"</xsl:text>
          <xsl:value-of select="gmd:linkage/gmd:URL"/>
          <xsl:text>\"</xsl:text>
        </xsl:when>
        <xsl:otherwise>
            <!-- Sometimes the protocol is missing, in which case we don't know what the URL represents. -->
            <xsl:text>\"\":\"</xsl:text><xsl:text>\"</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
		  
            <!-- add a comma if not the last dist element.  The trick here is sometimes OnlineResources are missing the protocol as noted above.  Without the "otherwise" clause above, the net results is a ,, in the dct_references_s field... which causes a fatal error in GBL -->
      <xsl:if test="position() != last()">
        <xsl:text>,</xsl:text>
      </xsl:if>
    </xsl:for-each>
    
    <!-- only insert a metadata link if we actually found other protocols above.  There are some edge cases where a file is missing all linkage information. -->
    <xsl:if test="//gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource">
        <xsl:text>,\"http://www.isotc211.org/schemas/2005/gmd/\":\"</xsl:text>
        <xsl:value-of select="concat($metadataBaseURL,$metadataFile)"/>
        <xsl:text>\"</xsl:text>
    </xsl:if>
    <xsl:text>}",&#xa;</xsl:text>
    
    
    <!-- Our ISO metadata sometimes contains multiple <extent> elements for unknown reasons.  Each of these may (or may not) contain bounding geographic coordinates.  We have numerous instances with one ISO file containing multiple slightly different bounding boxes!  The code below is an attempt at picking only the first EX_GeographicBoundingBox and setting the envelope using those values. 
    -->
    <xsl:choose>
    <xsl:when test="(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox)[1]">
     <!-- test statement translated: if any instance of EX_GeographicBoundingBox is found, pick the first instance and proceed -->
            <xsl:text>"solr_geom": "ENVELOPE(</xsl:text>
            <xsl:value-of select="(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement[1]/gmd:EX_GeographicBoundingBox/gmd:westBoundLongitude/gco:Decimal)[1]"/>
            <xsl:text>, </xsl:text>
            <xsl:value-of select="(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement[1]/gmd:EX_GeographicBoundingBox/gmd:eastBoundLongitude/gco:Decimal)[1]"/>
            <xsl:text>, </xsl:text>          
            <xsl:value-of select="(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement[1]/gmd:EX_GeographicBoundingBox/gmd:northBoundLatitude/gco:Decimal)[1]"/>
            <xsl:text>, </xsl:text>
            <xsl:value-of select="(gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement[1]/gmd:EX_GeographicBoundingBox/gmd:southBoundLatitude/gco:Decimal)[1]"/>
            <xsl:text>)",&#xa;</xsl:text>
    </xsl:when>
    <xsl:otherwise>
        <!-- no EX_GeographicBoundingBox found (this should not happen unless there is an error in Metadata) -->
        <xsl:text>"solr_geom": "ENVELOPE(NaN,NaN,NaN,NaN)",&#xa;</xsl:text>
    </xsl:otherwise>
    </xsl:choose>
    
    <!-- Supplemental info	-->
    <xsl:text>"uw_supplemental_s": "</xsl:text> 
        <xsl:call-template name="ScrubText">
            <xsl:with-param name="text" select="$supplemental"/>
        </xsl:call-template>  
    <xsl:text>",&#xa;</xsl:text>
     
    <!-- Insert placeholder for our per-dataset notices	-->
    <xsl:text>"uw_notice_s": ""&#xa;</xsl:text>   
   
    <xsl:text>}</xsl:text>
    <!-- end of JSON output -->
  </xsl:template>
</xsl:stylesheet>