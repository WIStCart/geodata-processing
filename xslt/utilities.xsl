<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
    exclude-result-prefixes="xs xd"
    version="2.0">
    <xd:doc scope="stylesheet">
        <xd:desc>
            <xd:p><xd:b>Created on:</xd:b> Jun 17, 2019</xd:p>
            <xd:p><xd:b>Author:</xd:b> Jim Lacy</xd:p>
            <xd:p></xd:p>
        </xd:desc>
    </xd:doc>

<!-- Template to strip double-quotes, escape characters, and extra line feeds.  Spaces are also normalized to futher clean up the specified text -->
    <xsl:template name="ScrubText">
        <xsl:param name="text" />
        <!-- some standardized constants -->
        <xsl:variable name="vQ">"</xsl:variable>
        <xsl:variable name="sQ">'</xsl:variable>
        <xsl:variable name="escapeChar">\</xsl:variable>
        <xsl:value-of select="normalize-space(translate(translate(translate($text, $vQ, $sQ),$escapeChar,' '),'&#xA;',''))"/>
    </xsl:template>
    
   
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
</xsl:stylesheet>