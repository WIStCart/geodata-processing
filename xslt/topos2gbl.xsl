<?xml version="1.0" encoding="UTF-8"?>
<!--
  Stylesheet to process FGDC-format metadata into Geoblacklight for USGS Topographic Maps. Important!  This stylesheet is customized to work for the GeoData@WI collection for USGS Topos.  It is not a generic FGDC converter.
-->
<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns:uuid="java:java.util.UUID"
  version="2.0">
<xsl:import href="utilities.xsl"/>
<xsl:output method="text" version="1.0" omit-xml-declaration="yes" indent="no" media-type="application/json"/>
<xsl:strip-space elements="*"/>

<!-- Bounding box -->
<xsl:variable name="x2" select="number(metadata/idinfo/spdom/bounding/eastbc)"/><!-- E -->
<xsl:variable name="x1" select="number(metadata/idinfo/spdom/bounding/westbc)"/><!-- W -->
<xsl:variable name="y2" select="number(metadata/idinfo/spdom/bounding/northbc)"/><!-- N -->
<xsl:variable name="y1" select="number(metadata/idinfo/spdom/bounding/southbc)"/><!-- S -->

<!-- Create a fresh UUID.  Danger!  New ID is created every time, so use caution when updating existing data. -->
<xsl:variable name="uuid">
  <xsl:value-of select="uuid:randomUUID()"/> 
</xsl:variable>

<xsl:variable name="description">
  <xsl:call-template name="ScrubText">
    <xsl:with-param name="text" select="metadata/idinfo/descript/abstract"/>
  </xsl:call-template> 
</xsl:variable>

  <!-- set location of online web-accessible archive location for all ISO metadata records -->
  <xsl:variable name="metadataBaseURL">https://gisdata.wisc.edu/public/metadata/</xsl:variable>
  
<xsl:template match="metadata">
    <xsl:text>{&#xa;</xsl:text>
    <xsl:text>"geoblacklight_version": "1.0",&#xa;</xsl:text>

    <xsl:text>"dc_identifier_s": "</xsl:text>
    <xsl:value-of select="$uuid"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"dc_title_s": "</xsl:text>
    <xsl:value-of select="idinfo/citation/citeinfo/title"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"dc_description_s": "</xsl:text>  
    <xsl:value-of select="$description"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"dc_rights_s": "Public",&#xa;</xsl:text>

    <xsl:text>"dct_provenance_s": ["U.S. Geological Survey"],&#xa;</xsl:text>

    <xsl:text>"layer_id_s": "</xsl:text>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"layer_slug_s": "</xsl:text>
    <xsl:value-of select="$uuid"/>
    <xsl:text>",&#xa;</xsl:text>

     <xsl:text>"layer_geom_type_s": "Image",&#xa;</xsl:text>
      
    <!-- not used for GeoData@WI -->
    <xsl:text>"layer_modified_dt": "</xsl:text>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:if test="idinfo/citation/citeinfo/origin">
      <xsl:text>"dc_creator_sm": [</xsl:text>
      <xsl:for-each select="idinfo/citation/citeinfo/origin">
        <xsl:text>"</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>"</xsl:text>
        <xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>
      </xsl:for-each>
      <xsl:text>],&#xa;</xsl:text>
    </xsl:if>

    <!-- We typically do not use publisher info, but left in place for now -->
    <xsl:if test="idinfo/citation/citeinfo/pubinfo/publish">
      <xsl:text>"dc_publisher_sm": [</xsl:text>
      <xsl:for-each select="idinfo/citation/citeinfo/pubinfo/publish">
        <xsl:text>"</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>"</xsl:text>
        <xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>
      </xsl:for-each>
      <xsl:text>],&#xa;</xsl:text>
    </xsl:if>

    <xsl:text>"dc_format_s": "Raster Dataset",&#xa;</xsl:text>

    <xsl:if test="contains(idinfo/descript/langdata, 'en')">
      <xsl:text>"dc_language_s": "</xsl:text>
      <xsl:text>English</xsl:text>
      <xsl:text>",&#xa;</xsl:text>
    </xsl:if>

    <xsl:text>"dc_type_s": "Image",&#xa;</xsl:text>

    <xsl:text>"dc_subject_sm": ["Imagery and Base Maps"],&#xa;</xsl:text>
    
    <xsl:if test="idinfo/keywords/place/placekey">
      <xsl:text>"dc_spatial_sm": [</xsl:text>
      <xsl:for-each select="idinfo/keywords/place/placekey">
        <xsl:text>"</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>"</xsl:text>
        <xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>
      </xsl:for-each>
      <xsl:text>],&#xa;</xsl:text>
    </xsl:if>
   
  <xsl:choose>
      
<!-- Date Issued -->
      <xsl:when test="string-length(idinfo/citation/citeinfo/pubdate)=4">
        <xsl:text>"dct_issued_s": "</xsl:text>
        <xsl:value-of select="idinfo/citation/citeinfo/pubdate"/>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>

      <xsl:when test="string-length(idinfo/citation/citeinfo/pubdate)=6">
        <xsl:text>"dct_issued_s": "</xsl:text>
        <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,1,4)"/>
        <xsl:text>-</xsl:text>
        <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,5,2)"/>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>

      <xsl:when test="string-length(idinfo/citation/citeinfo/pubdate)=8">
        <xsl:text>"dct_issued_s": "</xsl:text>
        <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,1,4)"/>
        <xsl:text>-</xsl:text>
        <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,5,2)"/>
        <xsl:text>-</xsl:text>
        <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,7,2)"/>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>
    </xsl:choose>

    <!-- collection -->
    <xsl:text>"dct_isPartOf_sm": ["USGS Topographic Maps"],&#xa;</xsl:text>
  
    <xsl:text>"solr_geom": "ENVELOPE(</xsl:text>
    <xsl:value-of select="$x1"/>
    <xsl:text>, </xsl:text>
    <xsl:value-of select="$x2"/>
    <xsl:text>, </xsl:text>
    <xsl:value-of select="$y2"/>
    <xsl:text>, </xsl:text>
    <xsl:value-of select="$y1"/>
    <xsl:text>)",&#xa;</xsl:text>

 
    <!-- content date for solr year: choose singular, or beginning date of range: YYYY -->
  <xsl:choose> 
  <xsl:when test="string-length(idinfo/citation/citeinfo/pubdate)=4">
    <xsl:text>"solr_year_i": "</xsl:text>
    <xsl:value-of select="idinfo/citation/citeinfo/pubdate"/>
    <xsl:text>",&#xa;</xsl:text>
  </xsl:when>
  
  <xsl:when test="string-length(idinfo/citation/citeinfo/pubdate)=6">
    <xsl:text>"solr_year_i": "</xsl:text>
    <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,1,4)"/>
    <xsl:text>",&#xa;</xsl:text>
  </xsl:when>
  
  <xsl:when test="string-length(idinfo/citation/citeinfo/pubdate)=8">
    <xsl:text>"solr_year_i": "</xsl:text>
    <xsl:value-of select="substring(idinfo/citation/citeinfo/pubdate,1,4)"/>
    <xsl:text>",&#xa;</xsl:text>
  </xsl:when>
  </xsl:choose>
  
 
  
  <!-- References 
	This element is a hash of key/value pairs for different types of external links. It external services and references using the CatInterOp approach.
	-->
  <xsl:text>"dct_references_s": "{</xsl:text>
  
  <!-- 
  /metadata/distinfo/stdorder/digform/digtopt/onlinopt/computer/networka/networkr
  
  /metadata/distinfo/stdorder/digform/digtinfo/formname
  
  contains(metadata/distinfo/stdorder/digform/digtinfo/formname, 'TIFF')
  -->
  
  <!-- IMPORTANT: Distribution formats currently limited to GeoPDF and GeoTIFF. This needs to be expanded!! -->
  <xsl:for-each select="/metadata/distinfo/stdorder/digform">
    <xsl:choose>
      <xsl:when test="(digtinfo/formname = 'GeoPDF') or (digtinfo/formname = 'Geospatial PDF')">
        <xsl:text>\"http://schema.org/downloadUrl\":\"</xsl:text>
        <xsl:value-of select="digtopt/onlinopt/computer/networka/networkr"/>
        <xsl:text>\"</xsl:text>
      </xsl:when>
      <xsl:when test="digtinfo/formname = 'GeoTIFF'">
        <xsl:text>\"http://schema.org/downloadUrl\":\"</xsl:text>
        <xsl:value-of select="digtopt/onlinopt/computer/networka/networkr"/>
        <xsl:text>\"</xsl:text>
      </xsl:when>
    </xsl:choose>   
    <xsl:text>,</xsl:text>
  </xsl:for-each>
 
  <xsl:text>\"http://schema.org/url\":\"</xsl:text>
  <xsl:value-of select="/metadata/idinfo/citation/citeinfo/onlink"/>
  <xsl:text>\"</xsl:text>
  <xsl:text>,\"http://www.opengis.net/cat/csw/csdgm\":\"</xsl:text>
  <xsl:value-of select="concat($metadataBaseURL,tokenize(base-uri(.), '/')[last()])"/>
  <xsl:text>\"</xsl:text>
  <xsl:text>}",&#xa;</xsl:text>
  
  <!-- Supplemental info	-->
  <xsl:text>"uw_supplemental_s": "</xsl:text> 
  <xsl:text>",&#xa;</xsl:text>
  
  <!-- Insert placeholder for our per-dataset notices	-->
  <xsl:text>"uw_notice_s": ""&#xa;</xsl:text>   


    <xsl:text>}</xsl:text>
   </xsl:template>
</xsl:stylesheet>