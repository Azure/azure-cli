<?xml version="1.0"?>
<!-- Define WiX namespace twice: template matches and selections don't work with default namespace, but default handy for simply emitting elements. -->
<xsl:stylesheet version="1.0" xmlns="http://schemas.microsoft.com/wix/2006/wi" xmlns:wix="http://schemas.microsoft.com/wix/2006/wi" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes" />
  <xsl:key name="componentDirectory" match="wix:Component" use="@Directory" />
  <xsl:template match="node()|text()|@*">
    <xsl:copy>
      <xsl:apply-templates select="node()|text()|@*" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="wix:ComponentGroup">
    <xsl:element name="ComponentGroup">
      <xsl:copy-of select="@*" />
      <!-- Use the Muenchian Method of grouping. -->
      <!-- TODO: To increase likelihood we're generating consistent component IDs, we should really select the primary component for each directory using the algorithm for the `keyPath` variable below. -->
      <xsl:for-each select="wix:Component[generate-id() = generate-id(key('componentDirectory', @Directory)[1])]">
        <xsl:sort select="@Directory" />
        <xsl:sort select="wix:File/@Source" />
        <!-- Use the first EXE or DLL as the key path, or use the first file if no EXE or DLL are found within each grouping. -->
        <xsl:variable name="keyPath">
          <xsl:choose>
            <xsl:when test="key('componentDirectory', @Directory)/wix:File[substring(@Source, string-length(@Source) - 3) = '.exe']">
              <xsl:value-of select="key('componentDirectory', @Directory)/wix:File[substring(@Source, string-length(@Source) - 3) = '.exe'][1]/@Source" />
            </xsl:when>
            <xsl:when test="key('componentDirectory', @Directory)/wix:File[substring(@Source, string-length(@Source) - 3) = '.dll']">
              <xsl:value-of select="key('componentDirectory', @Directory)/wix:File[substring(@Source, string-length(@Source) - 3) = '.dll'][1]/@Source" />
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="key('componentDirectory', @Directory)/wix:File[1]/@Source" />
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:copy>
          <xsl:copy-of select="@*" />
          <xsl:for-each select="key('componentDirectory', @Directory)">
            <xsl:apply-templates select="wix:File">
              <xsl:with-param name="keyPath" select="$keyPath" />
            </xsl:apply-templates>
          </xsl:for-each>
        </xsl:copy>
      </xsl:for-each>
    </xsl:element>
  </xsl:template>
  <xsl:template match="wix:File">
    <xsl:param name="keyPath" />
    <xsl:copy>
      <xsl:copy-of select="@*[name() != 'KeyPath']" />
      <xsl:if test="@Source = $keyPath">
        <xsl:attribute name="KeyPath">yes</xsl:attribute>
      </xsl:if>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
