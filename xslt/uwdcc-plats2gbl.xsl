<!-- Convert UW Digital Collections Center METS record for historic plat maps to 
GeoblackLight record -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
    xmlns:mets="http://www.loc.gov/METS/"
    xmlns:uwdcGeo="http://digital.library.wisc.edu/1711.dl/UWDC-Geo"
    xmlns:mods="http://www.loc.gov/mods/v3"
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
    
    <!-- Parse title -->    
    <xsl:variable name="townshipLabel">
            <xsl:value-of select="tokenize(/mets:mets/@LABEL,':')[2]"/>             
    </xsl:variable>
   
    <!-- Parse out child object used to grab derived products (IIIF image) --> 
    <xsl:variable name="contentIds">    
        <xsl:value-of select="tokenize(/mets:mets/mets:structMap[@TYPE='physical']/mets:div/mets:div[@ORDER='1']/@CONTENTIDS,':')[3]"/>
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
    <xsl:text>"dc_title_s": "Historic PLSS Plat Map:</xsl:text>    
    <xsl:call-template name="removeBrackets">
        <xsl:with-param name="text" select="$townshipLabel"/>
    </xsl:call-template>
    <xsl:text>",&#xa;</xsl:text>
    
    <!-- Description - hardcoded since description is the same for all maps -->
    <xsl:text>"dc_description_s": "The field notes and plat maps of the public land survey of Wisconsin are a valuable resource for original land survey information, as well as for understanding Wisconsin's landscape history. The survey of Wisconsin was conducted between 1832 and 1866 by the federal General Land Office. This work established the township, range and section grid; the pattern upon which land ownership and land use is based. The survey records were transferred to the Wisconsin Board of Commissioners of Public Lands after the original survey was completed. Since that time, these records have been available for consultation at the BCPL's office in Madison, as hand-transcriptions, and more recently on microfilm. Now, they are being made available via the internet as electronic images.",&#xa;</xsl:text>       
    
    <!-- Rights - Always public for GeoData@WI -->	 
    <xsl:text>"dc_rights_s": "Public",&#xa;</xsl:text>
    
    <!-- Provenance - The name of the organization that holds the resource -->
    <xsl:text>"dct_provenance_s": "UW Digital Collections Center",&#xa;</xsl:text>

    <!-- Layer Slug - This is a string appended to the base URL of a GeoBlacklight installation to create a unique landing page for each resource. It is visible to the user and is used for Permalinks. -->
    <xsl:text>"layer_slug_s": "</xsl:text>
    <xsl:value-of select="$masterObject"/>
    <xsl:text>",&#xa;</xsl:text>
    
    <xsl:text>"layer_geom_type_s": "Image",&#xa;</xsl:text>  
    
    <xsl:text>"dc_format_s": "TIFF",&#xa;</xsl:text>
    
    <!-- Language - Indicates the language of the data or map -->
    <xsl:text>"dc_language_s": "English",&#xa;</xsl:text>
    
    <!-- Is Part Of
	aka, collection names assigned to the dataset -->
    <xsl:text>"dct_isPartOf_sm": "Wisconsin Public Land Survey Records",&#xa;</xsl:text>
    
    <!-- Creator - The person(s) or organization that created the resource -->
    <xsl:text>"dc_creator_sm": "United States General Land Office",&#xa;</xsl:text>
    
    <!-- Subject - These are theme or topic keywords -->
    <xsl:text>"dc_subject_sm": </xsl:text>     
    <xsl:text>"Planning and Cadastral</xsl:text>
    <xsl:text>",&#xa;</xsl:text>
    
    <xsl:text>"dct_spatial_sm": [""]</xsl:text>  
    <xsl:text>,&#xa;</xsl:text>
    
    <!-- If a specific start date is definted, use dct_temporal_sm to set a range; otherwise, set solr_year_i with a single date -->
    <xsl:choose>
        <xsl:when test="/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/mods:mods/mods:originInfo/mods:dateIssued[@point='start']">
            <xsl:text>"dct_temporal_sm": ["</xsl:text>
            <xsl:value-of select="/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/mods:mods/mods:originInfo/mods:dateIssued[@point='start']"/>
            <xsl:text>-</xsl:text>  
            <xsl:value-of select="/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/mods:mods/mods:originInfo/mods:dateIssued[@point='end']"/>    
            <xsl:text>"],&#xa;</xsl:text> 
        </xsl:when> 
        <xsl:otherwise>
            <xsl:text>"solr_year_i": ["</xsl:text>
            <xsl:value-of select="tokenize(/mets:mets/mets:dmdSec/mets:mdWrap/mets:xmlData/mods:mods/mods:originInfo/mods:dateIssued,'-')[1]"/> 
            <xsl-text>"],&#xa;</xsl-text>
        </xsl:otherwise>
    </xsl:choose>
  
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
            <xsl:value-of select="$contentIds"/>
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
    <xsl:text>The original historic plat maps were created from 1832 to 1866. In most cases, the UW Digital Collections Center does not record a specific creation date for each individual map.</xsl:text>
    <xsl:text>",&#xa;</xsl:text>
     
    <!-- Insert placeholder for our per-dataset notices	-->
    <xsl:text>"uw_notice_s": ""&#xa;</xsl:text>   
    
    <xsl:text>}</xsl:text>
    <!-- end of JSON output -->
</xsl:template>    
</xsl:stylesheet>

