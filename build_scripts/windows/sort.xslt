<?xml version="1.0"?>
<!-- Define WiX namespace twice: template matches and selections don't work with default namespace, but default handy for simply emitting elements. -->
<xsl:stylesheet version="1.0" xmlns="http://schemas.microsoft.com/wix/2006/wi" xmlns:wix="http://schemas.microsoft.com/wix/2006/wi" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xml" indent="yes" />
  <xsl:template match="node()|text()|@*">
    <xsl:copy>
      <xsl:apply-templates select="node()|text()|@*" />
    </xsl:copy>
  </xsl:template>
  <xsl:template match="wix:ComponentGroup">
    <xsl:element name="ComponentGroup">
      <xsl:copy-of select="@*" />
      <xsl:apply-templates select="wix:Component">
        <xsl:sort select="@Directory" />
        <xsl:sort select="wix:File/@Source" />
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>
