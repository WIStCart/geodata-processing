<!-- Convert UW Digital Collections Center METS record for historic plat maps to 
GeoblackLight record -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
    xmlns:mets="http://www.loc.gov/METS/"
    xmlns:uwdcGeo="http://digital.library.wisc.edu/1711.dl/UWDC-Geo"
    xmlns:gml="http://www.opengis.net/gml"
    xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    exclude-result-prefixes="xs xd mets uwdcGeo gml oai_dc dc"
    version="2.0">
    <xsl:import href="utilities.xsl"/>
    <xd:doc scope="stylesheet">
        <xd:desc>
            <xd:p><xd:b>Created on:</xd:b> Jun 17, 2019</xd:p>
            <xd:p><xd:b>Author:</xd:b> Jim Lacy</xd:p>
            <xd:p></xd:p>
        </xd:desc>
    </xd:doc>
    
    <xsl:output method="text" version="1.0" omit-xml-declaration="yes" indent="no" media-type="application/json"/>
    <xsl:strip-space elements="*"/>
      
<xsl:template match="/">
    
    <!-- Extract unique dataset ID -->    
    <xsl:variable name="masterObject">
        <xsl:value-of select="tokenize(/mets:mets/@OBJID,':')[2]"/> 
    </xsl:variable>
   
    <!-- Parse out child object used to grab derived products (IIIF image) --> 
    <xsl:variable name="childObject">    
        <xsl:for-each select="/mets:mets/mets:dmdSec">
            <xsl:choose>
                <xsl:when test="mets:mdWrap/mets:xmlData/oai_dc:dc/dc:title = 'Original'">
                 <xsl:value-of select="tokenize(mets:mdWrap/mets:xmlData/oai_dc:dc/dc:identifier,':')[2]"/>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:variable>
     
    <xsl:variable name="westBoundLongitude">
        <xsl:value-of select="tokenize(/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/uwdcGeo:geographicDescription/uwdcGeo:footprint/gml:Envelope/gml:lowerCorner,' ')[2]"/>
    </xsl:variable>  
    <xsl:variable name="eastBoundLongitude">
        <xsl:value-of select="tokenize(/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/uwdcGeo:geographicDescription/uwdcGeo:footprint/gml:Envelope/gml:upperCorner,' ')[2]"/>
    </xsl:variable>   
    <xsl:variable name="northBoundLatitude">
        <xsl:value-of select="tokenize(/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/uwdcGeo:geographicDescription/uwdcGeo:footprint/gml:Envelope/gml:upperCorner,' ')[1]"/>
    </xsl:variable>   
    <xsl:variable name="southBoundLatitude">
        <xsl:value-of select="tokenize(/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/uwdcGeo:geographicDescription/uwdcGeo:footprint/gml:Envelope/gml:lowerCorner,' ')[1]"/>
    </xsl:variable> 
     
    <!-- Start of JSON output -->
    <xsl:text>{&#xa;</xsl:text>
    
    <!-- Schema Version - Indicates which version of the GeoBlacklight schema is in use. -->
    <xsl:text>"geoblacklight_version": "1.0",&#xa;</xsl:text>
    
    <!-- Unique Identifier - Unique identifier for layer as a URI. It should be globally unique across all institutions, assumed not to be end-user visible	-->
    <xsl:text>"dc_identifier_s": "</xsl:text>
    <xsl:value-of select="$masterObject"/>
    <xsl:text>",&#xa;</xsl:text>
    
    <!-- Title - The name of the resource -->
    <xsl:text>"dc_title_s": "</xsl:text>    
    <xsl:call-template name="removeBrackets">
        <xsl:with-param name="text" select="/mets:mets/@LABEL"/>
    </xsl:call-template>  
    <xsl:text>",&#xa;</xsl:text>
    
    <!-- Description - hardcoded since description is the same for all maps -->
    <xsl:text>"dc_description_s": "The field notes and plat maps of the public land survey of Wisconsin are a valuable resource for original land survey information, as well as for understanding Wisconsin's landscape history. The survey of Wisconsin was conducted between 1832 and 1866 by the federal General Land Office. This work established the township, range and section grid; the pattern upon which land ownership and land use is based. The survey records were transferred to the Wisconsin Board of Commissioners of Public Lands after the original survey was completed. Since that time, these records have been available for consultation at the BCPL's office in Madison, as hand-transcriptions, and more recently on microfilm. Now, they are being made available via the internet as electronic images.</xsl:text>       
    <xsl:text>",&#xa;</xsl:text>
    
    <!-- Rights - Always public for GeoData@WI -->	 
    <xsl:text>"dc_rights_s": "</xsl:text>
    <xsl:text>Public",&#xa;</xsl:text>
    
    <!-- Provenance - The name of the organization that holds the resource -->
    <xsl:text>"dct_provenance_s": "</xsl:text>
    <xsl:text>UW Digital Collections Center",&#xa;</xsl:text>
    
    <!-- Layer Slug - This is a string appended to the base URL of a GeoBlacklight installation to create a unique landing page for each resource. It is visible to the user and is used for Permalinks. -->
    <xsl:text>"layer_slug_s": "</xsl:text>
    <xsl:value-of select="$masterObject"/>
    <xsl:text>",&#xa;</xsl:text>
    
    <xsl:text>"layer_geom_type_s": "Image</xsl:text>
    <xsl:text>",&#xa;</xsl:text>
    
    <xsl:text>"dc_format_s": "TIFF</xsl:text>
     <xsl:text>",&#xa;</xsl:text>
    
    <!-- Language - Indicates the language of the data or map -->
    <xsl:text>"dc_language_s": "</xsl:text>
    <xsl:text>English",&#xa;</xsl:text>
    
    <!-- Is Part Of
	aka, collection names assigned to the dataset -->
    <xsl:text>"dct_isPartOf_sm": "Wisconsin Public Land Survey Records</xsl:text>
    <xsl:text>",&#xa;</xsl:text> 
    
    <!-- Creator - The person(s) or organization that created the resource -->
    <xsl:text>"dc_creator_sm": "United States General Land Office</xsl:text>
    <xsl:text>",&#xa;</xsl:text>
    
    <!-- Subject - These are theme or topic keywords -->
    <xsl:text>"dc_subject_sm": </xsl:text>     
    <xsl:text>"Planning and Cadastral</xsl:text>
    <xsl:text>",&#xa;</xsl:text>

    <!-- Spatial Coverage
	This field is for place name keywords
	-->
    <xsl:text>"dct_spatial_sm": [</xsl:text>
   
    
    <xsl:for-each select="/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/ns1:mods/ns1:subject[@authority = 'lcsh']" xmlns:ns1="http://www.loc.gov/mods/v3">
        <xsl:text>"</xsl:text>
        <xsl:value-of select="ns1:geographic"/>
        <xsl:text>"</xsl:text>
        <xsl:if test="position() != last()">
            <xsl:text>,</xsl:text>
        </xsl:if>
    </xsl:for-each>

    <xsl:text>],&#xa;</xsl:text>
    
    
    <!-- Temporal Coverage
	This represents the "Ground Condition" of the resource, meaning the time period data was collected or is intended to represent. Displays on the item page in the Year value.
	-->
    <!-- content date: range YYYY-YYYY if dates differ  -->
    <xsl:text>"dct_temporal_sm": ["</xsl:text>
    <xsl:text>1832-1866</xsl:text>      
    <xsl:text>"],&#xa;</xsl:text>      
             
    <!-- Solr Year
	This is an integer field in the form YYYY that is used for indexing in the Year & Time Period facets.  
	Uses same data as temporal coverage per Jaime
	-->
    <xsl:text>"solr_year_i": ["1866</xsl:text>
    <xsl:text>"],&#xa;</xsl:text>

    <!-- References 
	This element is a hash of key/value pairs for different types of external links. It external services and references using the CatInterOp approach.
	-->
        
    <xsl:text>"dct_references_s": "{</xsl:text> 
        <xsl:text>\"http://schema.org/downloadUrl\":\"</xsl:text> 
            <xsl:text>https://search.library.wisc.edu/digital/A</xsl:text>       
                <xsl:value-of select="$masterObject"/>
            <xsl:text>/datastream/</xsl:text> 
        <xsl:text>\",</xsl:text>
        <xsl:text>\"http://schema.org/url\":\"</xsl:text>
            <xsl:text>https://search.library.wisc.edu/digital/A</xsl:text>
            <xsl:value-of select="$masterObject"/>
        <xsl:text>\",</xsl:text> 
        <xsl:text>\"http://iiif.io/api/image\":\"</xsl:text>
            <xsl:text>https://asset.library.wisc.edu/iiif/1711.dl%2F</xsl:text>
            <xsl:value-of select="$childObject"/>
            <xsl:text>/info.json</xsl:text>
        <xsl:text>\"</xsl:text>             
    <xsl:text>}",&#xa;</xsl:text>
 
    <xsl:text>"solr_geom": "ENVELOPE(</xsl:text>
        <xsl:value-of select="$westBoundLongitude"/>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="$eastBoundLongitude"/>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="$northBoundLatitude"/>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="$southBoundLatitude"/>
    <xsl:text>)",&#xa;</xsl:text>
    
    <!-- Supplemental info	-->
    <xsl:text>"uw_supplemental_s": "</xsl:text> 
    <xsl:text>The historic plat maps range from 1832 to 1866. Each individual map will contain the specific date of creation.</xsl:text>
    <xsl:text>",&#xa;</xsl:text>
     
    <!-- Insert placeholder for our per-dataset notices	-->
    <xsl:text>"uw_notice_s": ""&#xa;</xsl:text>   
    
    <xsl:text>}</xsl:text>
    <!-- end of JSON output -->
</xsl:template>    
</xsl:stylesheet>