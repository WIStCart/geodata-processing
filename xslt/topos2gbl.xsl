<?xml version="1.0" encoding="UTF-8"?>
<!--
     fgdc2geoBL_uw-geodata.xsl - Transformation from FGDC into GeoBlacklight Solr
     
     Original version from Standford University, with many customizations for UW-Madison

          -->
<xsl:stylesheet 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
  xmlns:uuid="java:java.util.UUID"
  version="2.0">
<xsl:output method="text" version="1.0" omit-xml-declaration="yes" indent="no" media-type="application/json"/>
<xsl:strip-space elements="*"/>

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
 
<!-- Bounding box -->
<xsl:variable name="x2" select="number(metadata/idinfo/spdom/bounding/eastbc)"/><!-- E -->
<xsl:variable name="x1" select="number(metadata/idinfo/spdom/bounding/westbc)"/><!-- W -->
<xsl:variable name="y2" select="number(metadata/idinfo/spdom/bounding/northbc)"/><!-- N -->
<xsl:variable name="y1" select="number(metadata/idinfo/spdom/bounding/southbc)"/><!-- S -->

<xsl:variable name="format">
    <xsl:choose>
      <xsl:when test="contains(metadata/idinfo/citation/citeinfo/geoform, 'raster digital data')">
          <xsl:text>Raster Dataset</xsl:text>
      </xsl:when>
      <xsl:when test="contains(metadata/idinfo/citation/citeinfo/geoform, 'vector digital data')">
          <xsl:text>Shapefile</xsl:text>
      </xsl:when>
      <xsl:when test="contains(metadata/idinfo/citation/citeinfo/geoform, 'GeoPDF')">
        <xsl:text>GeoPDF</xsl:text>
      </xsl:when>
      <xsl:when test="contains(metadata/idinfo/citation/citeinfo/geoform, 'GeoTIFF')">
        <xsl:text>GeoTIFF</xsl:text>
      </xsl:when>
   <xsl:otherwise>
      <xsl:text>File</xsl:text>
   </xsl:otherwise>      
   </xsl:choose>
</xsl:variable>

<!-- Create a fresh UUID.  Danger!  New ID is created every time, so use caution when updating existing data. -->
<xsl:variable name="uuid">
  <xsl:value-of select="uuid:randomUUID()"/> 
</xsl:variable>

<xsl:template match="metadata">
    <xsl:text>{&#xa;</xsl:text>
    
    <!-- set location of online web-accessible archive location for all ISO metadata records -->
    <xsl:variable name="metadataBaseURL">https://gisdata.wisc.edu/public/metadata/</xsl:variable>

    <xsl:text>"geoblacklight_version": "1.0",&#xa;</xsl:text>

    <xsl:text>"dc_identifier_s": "</xsl:text>
    <xsl:value-of select="$uuid"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"dc_title_s": "</xsl:text>
    <xsl:value-of select="idinfo/citation/citeinfo/title"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"dc_description_s": "</xsl:text>  
    <xsl:call-template name="ScrubText">
      <xsl:with-param name="text" select="idinfo/descript/abstract"/>
    </xsl:call-template> 
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"dc_rights_s": "Public",&#xa;</xsl:text>

    <xsl:text>"dct_provenance_s": [</xsl:text>
  
  <xsl:for-each select="idinfo/citation/citeinfo/origin">
    <xsl:text>"</xsl:text>
    <xsl:value-of select="."/>
    <xsl:text>"</xsl:text>
    <xsl:if test="position() != last()">
      <xsl:text>,</xsl:text>
    </xsl:if>
  </xsl:for-each>
  
    <xsl:text>],&#xa;</xsl:text>

    <xsl:text>"layer_id_s": "</xsl:text>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:text>"layer_slug_s": "</xsl:text>
    <xsl:value-of select="$uuid"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:choose>
      <xsl:when test="contains(metadata/spdoinfo/ptvctinf/sdtsterm/sdtstype, 'G-polygon')">
        <xsl:text>"layer_geom_type_s": "</xsl:text>
        <xsl:text>Polygon</xsl:text>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>
      <xsl:when test="contains(metadata/spdoinfo/ptvctinf/sdtsterm/sdtstype, 'Entity point')">
        <xsl:text>"layer_geom_type_s": "</xsl:text>
        <xsl:text>Point</xsl:text>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>

      <xsl:when test="contains(metadata/spdoinfo/ptvctinf/sdtsterm/sdtstype, 'String')">
        <xsl:text>"layer_geom_type_s": "</xsl:text>
        <xsl:text>Line</xsl:text>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>
      <xsl:when test="contains(metadata/spdoinfo/direct, 'Raster')">
        <xsl:text>"layer_geom_type_s": "</xsl:text>
        <xsl:text>Raster</xsl:text>
        <xsl:text>",&#xa;</xsl:text>
      </xsl:when>
    </xsl:choose>

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

    <xsl:text>"dc_format_s": "</xsl:text>
    <xsl:value-of select="$format"/>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:if test="contains(idinfo/descript/langdata, 'en')">
      <xsl:text>"dc_language_s": "</xsl:text>
      <xsl:text>English</xsl:text>
      <xsl:text>",&#xa;</xsl:text>
    </xsl:if>

    <!-- DCMI Type vocabulary: defaults to dataset -->
    <xsl:text>"dc_type_s": "</xsl:text>
    <xsl:text>Dataset</xsl:text>
    <xsl:text>",&#xa;</xsl:text>

    <xsl:if test="idinfo/keywords/theme">
      <xsl:text>"dc_subject_sm": [</xsl:text>
      <xsl:for-each select="idinfo/keywords/theme">    
        <xsl:for-each select="themekey">
        <xsl:choose>
          <xsl:when test="(.) =  'biota'">
            <xsl:text>"Biota"</xsl:text>
          </xsl:when>    
          <xsl:when test="(.)=  'boundaries'">
            <xsl:text>"Boundaries"</xsl:text>
          </xsl:when>     
          <xsl:when test="(.) =  'climatologyMeteorologyAtmosphere'">
            <xsl:text>"Climatology, Meteorology and Atmosphere"</xsl:text>
          </xsl:when>       
          <xsl:when test="(.) =  'economy'">
            <xsl:text>"Economy"</xsl:text>
          </xsl:when>       
          <xsl:when test="(.) = 'elevation'">
            <xsl:text>"Elevation"</xsl:text>
          </xsl:when>        
          <xsl:when test="(.) =  'environment'">
            <xsl:text>"Environment"</xsl:text>
          </xsl:when>        
          <xsl:when test="(.) =  'farming'">
            <xsl:text>"Farming"</xsl:text>
          </xsl:when>         
          <xsl:when test="(.) =  'geoscientificInformation'">
            <xsl:text>"Geoscientific Information"</xsl:text>
          </xsl:when>       
          <xsl:when test="(.) =  'health'">
            <xsl:text>"Health"</xsl:text>
          </xsl:when>          
          <xsl:when test="(.) =  'imageryBaseMapsEarthCover'">
            <xsl:text>"Imagery and Base Maps"</xsl:text>
          </xsl:when>         
          <xsl:when test="(.) =  'Imagery base maps earth cover'">
            <xsl:text>"Imagery and Base Maps"</xsl:text>
          </xsl:when>       
          <xsl:when test="(.) = 'inlandWaters'">
            <xsl:text>"Inland Waters"</xsl:text>
          </xsl:when>         
          <xsl:when test="(.) =  'Inland waters'">
            <xsl:text>"Inland Waters"</xsl:text>
          </xsl:when>        
          <xsl:when test="(.)=  'intelligenceMilitary'">
            <xsl:text>"Intelligence and Military"</xsl:text>
          </xsl:when>       
          <xsl:when test="(.) = 'location'">
            <xsl:text>"Location"</xsl:text>
          </xsl:when>       
          <xsl:when test="(.) =  'oceans'">
            <xsl:text>"Oceans"</xsl:text>
          </xsl:when>        
          <xsl:when test="(.)=  'planningCadastre'">
            <xsl:text>"Planning and Cadastral"</xsl:text>
          </xsl:when>        
          <xsl:when test="(.) =  'society'">
            <xsl:text>"Society"</xsl:text>
          </xsl:when>        
          <xsl:when test="(.) =  'structure'">
            <xsl:text>"Structure"</xsl:text>
          </xsl:when>         
          <xsl:when test="(.) =  'transportation'">
            <xsl:text>"Transportation"</xsl:text>
          </xsl:when>         
          <xsl:when test="(.) =  'utilitiesCommunication'">
            <xsl:text>"Utilities and Communication"</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>"</xsl:text>
            <xsl:value-of select="(.)"/>
            <xsl:text>"</xsl:text>
          </xsl:otherwise>         
        </xsl:choose>
        <xsl:if test="position() != last()">
            <xsl:text>,</xsl:text>
        </xsl:if>   
        </xsl:for-each>
        <xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>  
      </xsl:for-each>
      <xsl:text>],&#xa;</xsl:text>
    </xsl:if>

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

    <!-- singular content date: YYYY -->
<!--
    <xsl:for-each select="idinfo/timeperd/timeinfo/sngdate/caldate">
      <xsl:if test="text() !='' ">
        <xsl:text>"dct_temporal_sm": ["</xsl:text>
        <xsl:value-of select="substring(.,1,4)"/>
        <xsl:text>"],&#xa;</xsl:text>
      </xsl:if>
    </xsl:for-each>


    <xsl:for-each select="idinfo/timeperd/timeinfo/mdattim/sngdate">
      <xsl:text>"dct_temporal_sm": ["</xsl:text>
      <xsl:value-of select="substring(caldate,1,4)"/>
      <xsl:text>"],&#xa;</xsl:text>
    </xsl:for-each>

    <xsl:for-each select="idinfo/timeperd/timeinfo/rngdates">
      <xsl:text>"dct_temporal_sm": ["</xsl:text>
      <xsl:value-of select="substring(begdate, 1,4)"/>
      <xsl:if test="substring(begdate,1,4) != substring(enddate,1,4)">
        <xsl:text>-</xsl:text>
        <xsl:value-of select="substring(enddate,1,4)"/>
      </xsl:if>
      <xsl:text>"],&#xa;</xsl:text>
    </xsl:for-each>

    <xsl:for-each select="idinfo/keywords/temporal/tempkey">
      <xsl:if test="text() != substring(idinfo/timeperd/timeinfo/sngdate/caldate,1,4)">
        <xsl:text>"dct_temporal_sm": ["</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>"],&#xa;</xsl:text>
      </xsl:if>
    </xsl:for-each>
-->
    <!-- collection -->

    <xsl:if test="idinfo/citation/citeinfo/lworkcit/citeinfo | idinfo/citation/citeinfo/serinfo/sername">
      <xsl:text>"dct_isPartOf_sm": [</xsl:text>
      <xsl:for-each select="idinfo/citation/citeinfo/lworkcit/citeinfo | idinfo/citation/citeinfo/serinfo">
      <xsl:text>"</xsl:text>
      <xsl:value-of select="title | sername"/>
      <xsl:text>"</xsl:text>
        <xsl:if test="position() != last()">
          <xsl:text>,</xsl:text>
        </xsl:if>
    </xsl:for-each>
      <xsl:text>],&#xa;</xsl:text>
    </xsl:if>

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
  <xsl:text>"solr_year_i": "</xsl:text>  
  <xsl:if test="idinfo/timeperd/timeinfo">
      <xsl:choose>
        <xsl:when test="idinfo/timeperd/timeinfo/sngdate/caldate/text() != ''">
            
            <xsl:value-of select="substring(idinfo/timeperd/timeinfo/sngdate/caldate,1,4)"/>
        </xsl:when>
        <xsl:when test="idinfo/timeperd/timeinfo/mdattim/sngdate/caldate">
          <xsl:if test="position() = 1">
            <xsl:text>"solr_year_i": </xsl:text>
            <xsl:value-of select="substring(caldate,1,4)"/>
          </xsl:if>
        </xsl:when>
        <xsl:when test="idinfo/timeperd/timeinfo/rngdates/enddate/text() != ''">
          <xsl:value-of select="substring(idinfo/timeperd/timeinfo/rngdates/enddate/text(), 1,4)"/>          
        </xsl:when>
        <xsl:when test="//metadata/idinfo/keywords/temporal/tempkey">
          <xsl:for-each select="//metadata/idinfo/keywords/temporal/tempkey[1]">
            <xsl:if test="text() != ''">
             
              <xsl:value-of select="."/>
            </xsl:if>
          </xsl:for-each>
        </xsl:when>
      </xsl:choose>      
  </xsl:if>
  <xsl:text>",&#xa;</xsl:text>
  
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
      <xsl:when test="digtinfo/formname = 'GeoPDF'">
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
  <xsl:text>,\"http://www.opengis/net/cat/csw/csdgm/\":\"</xsl:text>
  <xsl:value-of select="concat($metadataBaseURL,tokenize(base-uri(.), '/')[last()])"/>
  <xsl:text>/formatters/xml\"</xsl:text>


  
  <xsl:text>}",&#xa;</xsl:text>
  
  <!-- Supplemental info	-->
  <xsl:text>"uw_supplemental_s": "</xsl:text> 
  <xsl:text>",&#xa;</xsl:text>
  
  <!-- Insert placeholder for our per-dataset notices	-->
  <xsl:text>"uw_notice_s": ""&#xa;</xsl:text>   


    <xsl:text>}</xsl:text>
   </xsl:template>
</xsl:stylesheet>